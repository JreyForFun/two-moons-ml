"""One-time evaluation of the selected model on the held-out test set (Phase 5).

Run:  venv/Scripts/python src/evaluate_test.py --dry-run   training holdout only, no test moons
      venv/Scripts/python src/evaluate_test.py             the single test evaluation

This is the only script that loads the test set. The real run checks, before opening it, that the
Git tree is clean, that the Phase 5 criteria are unchanged since commit 975d7fb, that the test
split is unchanged since commit ccb9bbc, that the dataset matches its manifest, and that no
earlier results exist. It records the commit and file fingerprints with the results.
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from importlib import metadata

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

import cv
from analyze_pilot import wilson
from explore import DATASET, MANIFEST, isotropic_weights, load_dataset
from features import add_features, add_targets, config, feature_columns, training_data
from horizons import ROOT
from make_manifest import sha256
from models import make_model

PROTOCOL = ROOT / "configs" / "phase5_protocol.json"
SELECTED = ROOT / "configs" / "selected_model.json"
DECISIONS = ROOT / "data" / "phase4" / "decisions.json"
CV_OOF = ROOT / "data" / "phase4" / "random_forest_F3_oof.csv"
RESULTS_DIR = ROOT / "results"
DRY_DIR = ROOT / "data" / "phase5_dry"
CRITERIA_COMMIT, SPLIT_COMMIT = "975d7fb", "ccb9bbc"
PACKAGES = ("scikit-learn", "xgboost", "numpy", "pandas", "scipy")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def preflight(dry):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checks = {
        "criteria_unchanged_since_975d7fb":
            git("diff", "--quiet", CRITERIA_COMMIT, "--", "configs/selected_model.json").returncode == 0,
        "split_unchanged_since_ccb9bbc":
            git("diff", "--quiet", SPLIT_COMMIT, "--", "configs/split.json").returncode == 0,
        "dataset_matches_manifest": sha256(DATASET) == manifest["data_sha256"],
    }
    if not dry:
        checks["clean_git_tree"] = git("status", "--porcelain").stdout.strip() == ""
        checks["no_previous_results"] = not (RESULTS_DIR / "phase5_test.json").exists()
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Pre-flight failed: {', '.join(failed)}")
    return checks


def provenance(dry, checks):
    return {
        "dry_run": dry,
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "commit": git("rev-parse", "HEAD").stdout.strip(),
        "selected_model_sha256": sha256(SELECTED),
        "protocol_sha256": sha256(PROTOCOL),
        "preflight": checks,
        "versions": {"python": platform.python_version(),
                     **{p: metadata.version(p) for p in PACKAGES}},
    }


def split_data(dry, protocol):
    """Training and evaluation sets. The dry run never touches the test set."""
    train = training_data()
    if dry:
        fit, holdout = train_test_split(train, test_size=protocol["dry_run"]["holdout_share"],
                                        stratify=train["y"], random_state=protocol["dry_run"]["seed"])
        return fit.reset_index(drop=True), holdout.reset_index(drop=True)
    test = add_targets(add_features(load_dataset("test")))
    if set(test["id"]) & set(train["id"]):
        raise RuntimeError("test and training moons overlap")
    return train, test


def fit_models(train, selected, seed):
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    X, y = train[feature_columns(selected["feature_set"])], train["y"].to_numpy()
    models = {
        "selected": make_model(selected["model"], seed=seed, params=selected["params"]),
        "physics_rule": make_model("physics_rule", seed=seed,
                                   params=decisions["physics_rule_params"]),
        "majority": make_model("majority"),
    }
    for model in models.values():
        model.fit(X, y)
    return models


def bootstrap_interval(y, prob, statistic, rng, samples):
    n = len(y)
    values = [statistic(y[idx], prob[idx]) for idx in (rng.integers(0, n, n) for _ in range(samples))]
    return cv.interval(np.array(values))


def accuracy(y, prob):
    return float((prob.argmax(axis=1) == y).mean())


def survived_auc(y, prob):
    return roc_auc_score((y == 0).astype(int), prob[:, 0])


def per_class_ece(y, prob):
    return {name: cv.ece(prob[:, k], (y == k).astype(float))
            for k, name in enumerate(config()["classes"])}


def criteria(y, probs, selected, protocol, rng):
    """C1, C1b, C2, C3, C4 on the evaluation set."""
    prob = probs["selected"]
    samples = protocol["bootstrap_samples"]
    pre = selected["phase5_criteria"]
    test_f1 = cv.macro_f1(y, prob)
    low, high = pre["C1_generalization"]["interval"]
    oof = pd.read_csv(CV_OOF)
    oy, oprob = oof["y"].to_numpy(), oof.filter(like="p").to_numpy()
    diffs = []
    for _ in range(samples):
        i = rng.integers(0, len(y), len(y))
        j = rng.integers(0, len(oy), len(oy))
        diffs.append(cv.macro_f1(y[i], prob[i]) - cv.macro_f1(oy[j], oprob[j]))
    c1b = cv.interval(np.array(diffs))
    c2 = cv.paired_bootstrap(y, prob, probs["physics_rule"], cv.balanced_accuracy,
                             samples=samples, seed=protocol["bootstrap_seed"])
    c2_interval = cv.interval(c2)
    ece = cv.ece(prob[:, 0], (y == 0).astype(float))
    rare = config()["classes"].index("moon_interaction")
    pred = prob.argmax(axis=1)
    hits, total = int((pred[y == rare] == rare).sum()), int((y == rare).sum())
    return {
        "C1": {"value": test_f1, "interval": [low, high], "passed": low <= test_f1 <= high},
        "C1b": {"cv_macro_f1": cv.macro_f1(oy, oprob), "difference": test_f1 - cv.macro_f1(oy, oprob),
                "interval": c1b, "passed": c1b[0] <= 0 <= c1b[1]},
        "C2": {"gain": float(c2.mean()), "interval": c2_interval, "passed": c2_interval[0] > 0},
        "C3": {"ece": ece, "limit": 0.05, "passed": ece <= 0.05},
        "C4": {"recall": hits / total, "interval": list(wilson(hits, total)), "moons": total},
    }


def lifetime(train, evaluation, selected, seed):
    X = train[feature_columns(selected["feature_set"])]
    model = make_model(selected["model"], seed=seed, params=selected["params"])
    model.fit(X, train["y_lifetime"].to_numpy())
    prob = model.predict_proba(evaluation[feature_columns(selected["feature_set"])])
    y = evaluation["y_lifetime"].to_numpy()
    pred = prob.argmax(axis=1)
    return prob, {"accuracy": float((pred == y).mean()),
                  "macro_f1": float(f1_score(y, pred, average="macro")),
                  "within_one_class": float(np.mean(np.abs(pred - y) <= 1))}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="training holdout instead of test")
    args = parser.parse_args()
    dry = args.dry_run
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    checks = preflight(dry)
    out_dir = DRY_DIR if dry else RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{'DRY RUN (training holdout)' if dry else 'TEST EVALUATION'}: "
          f"{time.strftime('%Y-%m-%d %H:%M')}", flush=True)

    train, evaluation = split_data(dry, protocol)
    features = feature_columns(selected["feature_set"])
    X_eval, y = evaluation[features], evaluation["y"].to_numpy()
    started = time.perf_counter()
    models = fit_models(train, selected, protocol["seed"])
    train_seconds = time.perf_counter() - started
    probs = {name: model.predict_proba(X_eval) for name, model in models.items()}
    rng = np.random.default_rng(protocol["bootstrap_seed"])
    samples = protocol["bootstrap_samples"]

    results = {"provenance": provenance(dry, checks), "moons": {"train": len(train),
                                                               "evaluated": len(evaluation)},
               "training_seconds": train_seconds,
               "criteria": criteria(y, probs, selected, protocol, rng), "metrics": {},
               "intervals": {}}
    for name, prob in probs.items():
        results["metrics"][name] = cv.metrics(y, prob)
        results["intervals"][name] = {
            stat.__name__: bootstrap_interval(y, prob, stat, rng, samples)
            for stat in (cv.macro_f1, accuracy, cv.balanced_accuracy, survived_auc)}
    sel = probs["selected"]
    results["metrics_isotropic"] = cv.metrics(y, sel, weights=isotropic_weights(evaluation))
    results["per_class_ece"] = per_class_ece(y, sel)
    seed_scores = []
    for s in protocol["seed_luck_seeds"]:
        model = make_model(selected["model"], seed=s, params=selected["params"])
        model.fit(train[features], train["y"].to_numpy())
        seed_scores.append(cv.macro_f1(y, model.predict_proba(X_eval)))
    results["seed_luck"] = {"seeds": protocol["seed_luck_seeds"], "macro_f1": seed_scores,
                            "spread": [float(min(seed_scores)), float(max(seed_scores))]}
    life_prob, results["lifetime"] = lifetime(train, evaluation, selected, protocol["seed"])

    columns = ["id"] + [c for c in evaluation.columns if c.startswith("input_")] + [
        "result_label", "result_survival_days", "y", "y_lifetime"]
    frame = evaluation[columns].copy()
    for name, prob in probs.items():
        for k in range(prob.shape[1]):
            frame[f"{name}_p{k}"] = prob[:, k]
    for k in range(life_prob.shape[1]):
        frame[f"lifetime_p{k}"] = life_prob[:, k]
    frame.to_csv(out_dir / ("predictions.csv" if dry else "phase5_test_predictions.csv"), index=False)
    (out_dir / ("results.json" if dry else "phase5_test.json")).write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    c = results["criteria"]
    m = results["metrics"]
    print(f"Selected model: macro-F1 {m['selected']['macro_f1']:.3f}, accuracy "
          f"{m['selected']['accuracy']:.3f}, balanced accuracy {m['selected']['balanced_accuracy']:.3f}")
    print(f"Physics rule: macro-F1 {m['physics_rule']['macro_f1']:.3f}, accuracy "
          f"{m['physics_rule']['accuracy']:.3f}; majority accuracy {m['majority']['accuracy']:.3f}")
    print(f"C1  macro-F1 {c['C1']['value']:.3f} in {c['C1']['interval'][0]:.3f}-{c['C1']['interval'][1]:.3f}: "
          f"{'PASS' if c['C1']['passed'] else 'FAIL'}")
    print(f"C1b difference from CV {c['C1b']['difference']:+.3f} (95% {c['C1b']['interval'][0]:+.3f} to "
          f"{c['C1b']['interval'][1]:+.3f}): {'PASS' if c['C1b']['passed'] else 'FAIL'}")
    print(f"C2  balanced-accuracy gain over physics rule {c['C2']['gain']:+.3f} (95% "
          f"{c['C2']['interval'][0]:+.3f} to {c['C2']['interval'][1]:+.3f}): "
          f"{'PASS' if c['C2']['passed'] else 'FAIL'}")
    print(f"C3  ECE {c['C3']['ece']:.3f} (limit 0.05): {'PASS' if c['C3']['passed'] else 'FAIL'}")
    print(f"C4  moon_interaction recall {c['C4']['recall']:.1%} (95% {c['C4']['interval'][0]:.1%} to "
          f"{c['C4']['interval'][1]:.1%}, {c['C4']['moons']} moons)")
    print(f"Seed luck: macro-F1 {results['seed_luck']['spread'][0]:.3f} to {results['seed_luck']['spread'][1]:.3f}")
    print(f"Lifetime: accuracy {results['lifetime']['accuracy']:.3f}, within one class "
          f"{results['lifetime']['within_one_class']:.3f}")
    print(f"Saved {out_dir.relative_to(ROOT).as_posix()}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
