"""Model training by nested cross-validation and the pre-registered rules P1, P2, P3 and P6.

Each fitted model is saved to data/phase4/ immediately; repeating a command skips saved models,
so an interrupted run resumes.

Usage:
    python src/train_models.py baselines    (majority class and physics rule)
    python src/train_models.py features     (rule P1: feature set)
    python src/train_models.py compare      (rules P2, P3, P6: model comparison)
    python src/train_models.py final        (settings of the selected model)
    python src/train_models.py lifetime     (lifetime-class task)
"""

import argparse
import json
import platform
import sys
import time
from importlib import metadata

import numpy as np
import pandas as pd
from sklearn.tree import export_text

import cv
from explore import isotropic_weights
from features import config, feature_columns, training_data
from horizons import ROOT

OUT = ROOT / "data" / "phase4"
DECISIONS = OUT / "decisions.json"
SELECTED = ROOT / "configs" / "selected_model.json"
PACKAGES = ("scikit-learn", "xgboost", "numpy", "pandas", "scipy")


def versions():
    return {"python": platform.python_version(),
            **{name: metadata.version(name) for name in PACKAGES}}


def load_decisions():
    return json.loads(DECISIONS.read_text(encoding="utf-8")) if DECISIONS.exists() else {}


def save_decision(**items):
    decisions = load_decisions()
    decisions.update(items)
    DECISIONS.write_text(json.dumps(decisions, indent=2) + "\n", encoding="utf-8")


def evaluate(key, name, df, feature_set, target="y", tune=True, calibrate=False, params=None):
    """Run (or load) one cross-validated model; save results and OOF probabilities."""
    OUT.mkdir(parents=True, exist_ok=True)
    result_path, oof_path = OUT / f"{key}.json", OUT / f"{key}_oof.csv"
    y = df[target].to_numpy()
    if result_path.exists() and oof_path.exists():
        print(f"  {key}: already saved, skipped", flush=True)
        oof = pd.read_csv(oof_path)
        return json.loads(result_path.read_text(encoding="utf-8")), oof.filter(like="p").to_numpy()
    print(f"  {key}: started {time.strftime('%H:%M')}", flush=True)
    started = time.perf_counter()
    X = df[feature_columns(feature_set)]
    oof, folds = cv.run_cv(name, X, y, tune=tune, calibrate=calibrate, params=params)
    survived = 3 if target == "y_lifetime" else 0
    result = {
        "key": key, "model": name, "feature_set": feature_set, "target": target, "tune": tune,
        "calibrate": calibrate, "moons": int(len(y)),
        "metrics": cv.metrics(y, oof, survived=survived),
        "metrics_isotropic": cv.metrics(y, oof, weights=isotropic_weights(df), survived=survived),
        "fold_spread": {k: cv.fold_spread(folds, k) for k in ("macro_f1", "balanced_accuracy",
                                                            "accuracy", "log_loss")},
        "folds": folds, "seconds": time.perf_counter() - started, "versions": versions(),
    }
    if target == "y_lifetime":
        pred = oof.argmax(axis=1)
        result["within_one_bin"] = float(np.mean(np.abs(pred - y) <= 1))
    result_path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    frame = pd.DataFrame(oof, columns=[f"p{k}" for k in range(oof.shape[1])])
    frame.insert(0, "y", y)
    frame.insert(0, "id", df["id"].to_numpy())
    frame.to_csv(oof_path, index=False)
    m = result["metrics"]
    print(f"  {key}: macro-F1 {m['macro_f1']:.3f}, balanced accuracy "
          f"{m['balanced_accuracy']:.3f}, {result['seconds'] / 60:.1f} min", flush=True)
    return result, oof


def compare(y, oof_a, oof_b, statistic):
    diffs = cv.paired_bootstrap(y, oof_a, oof_b, statistic)
    return {"mean": float(diffs.mean()), "interval": cv.interval(diffs)}


def physics_rule_text(df):
    """The physics-rule tree fitted (and tuned) on all training moons, as if-else text."""
    model, best = cv.fit_model("physics_rule", df[feature_columns("F3")], df["y"].to_numpy(),
                               tune=True, seed=config()["seed"], n_jobs=config()["n_jobs"])
    tree = model.named_steps["model"]
    return export_text(tree, feature_names=config()["physics_rule_features"],
                       class_names=config()["classes"], decimals=3), best


def cmd_baselines(df):
    print("BASELINES")
    shares = df["y_lifetime"].value_counts(normalize=True).sort_index()
    print("  Lifetime class shares: " + ", ".join(
        f"{n} {shares[k]:.1%}" for k, n in enumerate(config()["lifetime_classes"])))
    evaluate("majority", "majority", df, "F3", tune=False)
    evaluate("physics_rule", "physics_rule", df, "F3")
    text, best = physics_rule_text(df)
    print("  Physics rule fitted on all training moons " + json.dumps(best) + ":\n" + text)
    save_decision(physics_rule_text=text, physics_rule_params=best,
                  lifetime_shares={n: float(shares[k])
                                   for k, n in enumerate(config()["lifetime_classes"])})


def cmd_features(df):
    print("RULE P1: feature set (Random Forest, fixed default settings)")
    y = df["y"].to_numpy()
    oofs = {}
    for name in ("F1", "F2", "F3"):
        _, oofs[name] = evaluate(f"rf_default_{name}", "random_forest_default", df, name,
                                 tune=False)
    gains = {name: compare(y, oofs[name], oofs["F1"], cv.macro_f1) for name in ("F2", "F3")}
    qualifying = [n for n, g in gains.items() if g["interval"][0] > 0]
    chosen = max(qualifying, key=lambda n: gains[n]["mean"]) if qualifying else "F1"
    for name, g in gains.items():
        print(f"  {name} minus F1: {g['mean']:+.4f} (95% {g['interval'][0]:+.4f} to "
              f"{g['interval'][1]:+.4f})")
    print(f"  Chosen feature set: {chosen}")
    save_decision(P1={"gains_over_F1": gains, "chosen": chosen})


def cmd_compare(df):
    decisions = load_decisions()
    if "P1" not in decisions:
        raise SystemExit("run 'features' first")
    fs = decisions["P1"]["chosen"]
    y = df["y"].to_numpy()
    print(f"RULES P2, P3, P6: model comparison on {fs} (nested cross-validation)")
    results, oofs = {}, {}
    for name in config()["simplicity_order"]:
        results[name], oofs[name] = evaluate(f"{name}_{fs}", name, df, fs)
    best = max(results, key=lambda n: results[n]["metrics"]["macro_f1"])
    order = config()["simplicity_order"]
    selected, gaps = best, {}
    for simpler in order[:order.index(best)]:
        gaps[simpler] = compare(y, oofs[best], oofs[simpler], cv.macro_f1)
        if gaps[simpler]["interval"][0] <= 0:  # the gain over the simpler model is not shown
            selected = simpler
            break
    print(f"  Highest macro-F1: {best}; selected by P2: {selected}")
    for simpler, g in gaps.items():
        print(f"    {best} minus {simpler}: {g['mean']:+.4f} (95% {g['interval'][0]:+.4f} to "
              f"{g['interval'][1]:+.4f})")

    _, rule_oof = evaluate("physics_rule", "physics_rule", df, "F3")
    p3 = compare(y, oofs[selected], rule_oof, cv.balanced_accuracy)
    p3["beats_physics_rule"] = p3["interval"][0] > 0
    print(f"  P3, balanced accuracy gain over the physics rule: {p3['mean']:+.4f} "
          f"(95% {p3['interval'][0]:+.4f} to {p3['interval'][1]:+.4f}): "
          f"{'beats it' if p3['beats_physics_rule'] else 'not shown'}")

    ece = results[selected]["metrics"]["survived_ece"]
    p6 = {"ece": ece, "limit": config()["rules"]["P6_max_ece"], "calibrated": False}
    if ece > p6["limit"]:
        calibrated, _ = evaluate(f"{selected}_{fs}_calibrated", selected, df, fs, calibrate=True)
        p6.update({"calibrated_ece": calibrated["metrics"]["survived_ece"],
                   "log_loss": results[selected]["metrics"]["log_loss"],
                   "calibrated_log_loss": calibrated["metrics"]["log_loss"]})
        p6["calibrated"] = p6["calibrated_log_loss"] < p6["log_loss"]
    print(f"  P6, ECE of P(survived) {ece:.4f} (limit {p6['limit']}): "
          + ("calibration kept" if p6["calibrated"] else "no calibration")
          + (f" (log loss {p6['log_loss']:.4f} -> {p6['calibrated_log_loss']:.4f})"
             if "calibrated_log_loss" in p6 else ""))
    save_decision(P2={"highest": best, "selected": selected, "gaps": gaps,
                      "macro_f1": {n: r["metrics"]["macro_f1"] for n, r in results.items()}},
                  P3=p3, P6=p6)


def cmd_final(df):
    decisions = load_decisions()
    if "P2" not in decisions:
        raise SystemExit("run 'compare' first")
    name, fs = decisions["P2"]["selected"], decisions["P1"]["chosen"]
    cfg = config()
    print(f"FINAL SETTINGS: {name} on {fs}, search on all {len(df):,} training moons")
    started = time.perf_counter()
    previous = cfg["inner_folds"]
    cfg["inner_folds"] = cfg["final_folds"]  # 5-fold search on the full training set
    try:
        _, best = cv.fit_model(name, df[feature_columns(fs)], df["y"].to_numpy(), tune=True,
                               seed=cfg["seed"], n_jobs=cfg["n_jobs"])
    finally:
        cfg["inner_folds"] = previous
    selected = {
        "description": "Model selected in Phase 4 for the Phase 5 test evaluation",
        "model": name, "feature_set": fs, "features": feature_columns(fs), "params": best,
        "calibrate": decisions["P6"]["calibrated"], "classes": cfg["classes"],
        "seed": cfg["seed"], "search": {"candidates": cfg["search_candidates"],
                                        "folds": cfg["final_folds"]},
        "seconds": time.perf_counter() - started, "versions": versions(),
    }
    if SELECTED.exists():
        selected["phase5_criteria"] = json.loads(SELECTED.read_text()).get("phase5_criteria")
    SELECTED.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  Settings: {json.dumps(best)}")
    print(f"Saved configs/{SELECTED.name}")


def cmd_lifetime(df):
    decisions = load_decisions()
    if "P2" not in decisions:
        raise SystemExit("run 'compare' first")
    name, fs = decisions["P2"]["selected"], decisions["P1"]["chosen"]
    print(f"LIFETIME CLASSES: {name} on {fs} (nested cross-validation)")
    result, _ = evaluate(f"lifetime_{name}_{fs}", name, df, fs, target="y_lifetime")
    majority, _ = evaluate("lifetime_majority", "majority", df, fs, target="y_lifetime",
                           tune=False)
    m = result["metrics"]
    print(f"  macro-F1 {m['macro_f1']:.3f}, accuracy {m['accuracy']:.3f}, within one bin "
          f"{result['within_one_bin']:.3f}; majority accuracy {majority['metrics']['accuracy']:.3f}")


COMMANDS = {"baselines": cmd_baselines, "features": cmd_features, "compare": cmd_compare,
            "final": cmd_final, "lifetime": cmd_lifetime}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=COMMANDS)
    args = parser.parse_args()
    df = training_data()
    print(f"started {time.strftime('%Y-%m-%d %H:%M')}: {args.command}", flush=True)
    COMMANDS[args.command](df)
    print(f"finished {time.strftime('%Y-%m-%d %H:%M')}: {args.command}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
