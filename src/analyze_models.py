"""Analyses of the selected model: chaos reference, rules P4 and P5, learning curve,
grouped permutation importance, and the pass criteria for the test evaluation.

The learning curve and importances refit the selected model within each outer fold using that
fold's tuned hyperparameters (stored by train_models.py), so no model is scored on data it was
trained on. Writes data/phase4_analysis.json and the criteria in configs/selected_model.json.

Usage:
    python src/analyze_models.py
"""

import json
import sys

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split

import cv
from analyze_pilot import wilson
from features import config, feature_columns, training_data
from horizons import ROOT
from models import make_model
from train_models import OUT, SELECTED, load_decisions

TWINS = ROOT / "data" / "twins_1m.csv"
RESULTS = ROOT / "data" / "phase4_analysis.json"
FRACTIONS = (0.1, 0.2, 0.4, 0.7, 1.0)
PERMUTATION_REPEATS = 5


def selected_run():
    decisions = load_decisions()
    name, fs = decisions["P2"]["selected"], decisions["P1"]["chosen"]
    key = f"{name}_{fs}" + ("_calibrated" if decisions["P6"]["calibrated"] else "")
    result = json.loads((OUT / f"{key}.json").read_text(encoding="utf-8"))
    oof = pd.read_csv(OUT / f"{key}_oof.csv")
    return name, fs, decisions["P6"]["calibrated"], result, oof


def twin_labels(df):
    """Original and twin labels (4 classes) for the twin moons, aligned by id."""
    twins = pd.read_csv(TWINS, keep_default_na=False)
    if (twins["result_label"].isin(["timeout", "error"])).any():
        raise RuntimeError("twins contain timeouts or errors")
    codes = {n: k for k, n in enumerate(config()["classes"])}
    twins["y_twin"] = twins["result_label"].replace(config()["merge"]).map(codes)
    merged = df[["id", "y", "input_distance_lunar", "input_inclination_deg"]].merge(
        twins[["id", "y_twin"]], on="id")
    if len(merged) != len(twins):
        raise RuntimeError("some twins are not training moons")
    return merged


def chaos_reference(pairs):
    agree = pairs["y"] == pairs["y_twin"]
    alive = (pairs["y"] == 0) == (pairs["y_twin"] == 0)
    n = len(pairs)
    out = {"moons": n, "agreement": float(agree.mean()),
           "agreement_interval": wilson(int(agree.sum()), n),
           "binary_agreement": float(alive.mean()),
           "binary_agreement_interval": wilson(int(alive.sum()), n), "by_distance": [],
           "by_inclination": []}
    for column, bins, key in (("input_distance_lunar", np.geomspace(0.1, 3.0, 7), "by_distance"),
                              ("input_inclination_deg", np.linspace(0, 180, 7), "by_inclination")):
        index = np.clip(np.digitize(pairs[column], bins) - 1, 0, len(bins) - 2)
        for b in range(len(bins) - 1):
            part = ~agree[index == b]
            low, high = wilson(int(part.sum()), len(part))
            out[key].append({"low": float(bins[b]), "high": float(bins[b + 1]),
                             "moons": int(len(part)), "changed": float(part.mean()),
                             "interval": [low, high]})
    return out


def rule_p5(pairs, oof):
    """OOF error rate on twin-disagreeing vs twin-agreeing moons."""
    probs = oof.set_index("id").loc[pairs["id"]].filter(like="p").to_numpy()
    wrong = probs.argmax(axis=1) != pairs["y"].to_numpy()
    chaotic = (pairs["y"] != pairs["y_twin"]).to_numpy()
    rng = np.random.default_rng(config()["bootstrap_seed"])
    diffs = []
    for _ in range(config()["bootstrap_samples"]):
        idx = rng.integers(0, len(wrong), len(wrong))
        w, c = wrong[idx], chaotic[idx]
        diffs.append(w[c].mean() - w[~c].mean())
    low, high = cv.interval(np.array(diffs))
    return {"error_chaotic": float(wrong[chaotic].mean()),
            "error_stable": float(wrong[~chaotic].mean()),
            "accuracy_stable": float(1 - wrong[~chaotic].mean()),
            "chaotic_moons": int(chaotic.sum()), "difference_interval": [low, high],
            "concentrated": low > 0}


def rule_p4(df, oof):
    probs = oof.filter(like="p").to_numpy()
    pred = probs.argmax(axis=1)
    rare = config()["classes"].index("moon_interaction")
    y = oof["y"].to_numpy()
    recall = float((pred[y == rare] == rare).mean())
    low, high = wilson(int((pred[y == rare] == rare).sum()), int((y == rare).sum()))
    labels = df.set_index("id").loc[oof["id"], "result_label"].to_numpy()
    sub = {name: float((pred[labels == name] == rare).mean()) for name in ("hit_moon", "moon_lost")}
    limit = config()["rules"]["P4_min_rare_recall"]
    return {"recall": recall, "interval": [low, high], "sub_recall": sub, "limit": limit,
            "targeted_sampling_recommended": recall < limit}


def fold_model(name, params, calibrated, seed):
    model = make_model(name, seed=seed, params=params)
    return CalibratedClassifierCV(model, method="isotonic", cv=3) if calibrated else model


def learning_curve_and_importance(df, name, fs, calibrated, result):
    cfg = config()
    X, y = df[feature_columns(fs)], df["y"].to_numpy()
    rare = cfg["classes"].index("moon_interaction")
    groups = {g: [c for c in cols if c in X.columns] for g, cols in cfg["importance_groups"].items()}
    groups = {g: cols for g, cols in groups.items() if cols}
    curve = {f: {"moons": [], "macro_f1": [], "rare_recall": []} for f in FRACTIONS}
    importance = {g: [] for g in groups}
    rng = np.random.default_rng(cfg["seed"])
    for fold in result["folds"]:
        test = np.array(fold["test_index"])
        train = np.setdiff1d(np.arange(len(y)), test)
        seed = cfg["seed"] + fold["fold"]
        for fraction in FRACTIONS:
            part = train if fraction == 1.0 else train_test_split(
                train, train_size=fraction, stratify=y[train], random_state=seed)[0]
            model = fold_model(name, fold["best_params"], calibrated, seed)
            model.fit(X.iloc[part], y[part])
            prob = model.predict_proba(X.iloc[test])
            pred = prob.argmax(axis=1)
            curve[fraction]["moons"].append(len(part))
            curve[fraction]["macro_f1"].append(cv.macro_f1(y[test], prob))
            curve[fraction]["rare_recall"].append(float((pred[y[test] == rare] == rare).mean()))
        base = cv.macro_f1(y[test], prob)  # model trained on the full training part
        for group, cols in groups.items():
            drops = []
            for _ in range(PERMUTATION_REPEATS):
                shuffled = X.iloc[test].copy()
                order = rng.permutation(len(test))
                shuffled[cols] = shuffled[cols].to_numpy()[order]
                drops.append(base - cv.macro_f1(y[test], model.predict_proba(shuffled)))
            importance[group].append(float(np.mean(drops)))
        print(f"  fold {fold['fold']}: learning curve and importance done", flush=True)
    curve_out = [{"fraction": f, "moons": float(np.mean(v["moons"])),
                  "macro_f1": [float(np.mean(v["macro_f1"])), float(np.std(v["macro_f1"], ddof=1))],
                  "rare_recall": [float(np.mean(v["rare_recall"])),
                                  float(np.std(v["rare_recall"], ddof=1))]}
                 for f, v in curve.items()]
    importance_out = {g: [float(np.mean(v)), float(np.std(v, ddof=1))] for g, v in importance.items()}
    return curve_out, importance_out, groups


def phase5_criteria(y, oof):
    probs = oof.filter(like="p").to_numpy()
    rng = np.random.default_rng(config()["bootstrap_seed"])
    values = [cv.macro_f1(y[idx], probs[idx])
              for idx in (rng.integers(0, len(y), len(y)) for _ in range(config()["bootstrap_samples"]))]
    low, high = cv.interval(np.array(values))
    return {
        "fixed_on": "end of Phase 4, before the test set is opened",
        "test_set": "2,400 moons in configs/split.json, evaluated once",
        "C1_generalization": {"metric": "test macro-F1",
                              "criterion": "inside the cross-validated 95% interval",
                              "interval": [low, high]},
        "C2_beats_physics_rule": {"metric": "balanced accuracy",
                                  "criterion": "paired bootstrap interval of the gain over the "
                                               "physics rule above 0 on the test set"},
        "C3_calibration": {"metric": "ECE of P(survived)", "criterion": "at most 0.05"},
        "C4_rare_class": {"metric": "moon_interaction recall",
                          "criterion": "reported with a Wilson interval (descriptive)"},
        "speedup": {"metric": "median prediction time per moon versus median simulation time "
                              "(1.456 s per moon, configs/dataset_manifest.json)"},
    }


def main():
    df = training_data()
    name, fs, calibrated, result, oof = selected_run()
    y = oof["y"].to_numpy()
    print(f"SELECTED: {name} on {fs}{' (calibrated)' if calibrated else ''}")
    pairs = twin_labels(df)
    chaos = chaos_reference(pairs)
    p5 = rule_p5(pairs, oof)
    p4 = rule_p4(df, oof)
    print(f"Chaos reference ({chaos['moons']} twins): 4-class agreement {chaos['agreement']:.1%}, "
          f"binary {chaos['binary_agreement']:.1%}")
    print(f"P5: error on chaotic moons {p5['error_chaotic']:.1%} ({p5['chaotic_moons']}), on stable "
          f"moons {p5['error_stable']:.1%}; difference 95% {p5['difference_interval'][0]:+.3f} to "
          f"{p5['difference_interval'][1]:+.3f}: "
          f"{'concentrated on chaotic moons' if p5['concentrated'] else 'not shown'}")
    print(f"P4: moon_interaction recall {p4['recall']:.1%} ({p4['interval'][0]:.1%} to "
          f"{p4['interval'][1]:.1%}); hit_moon {p4['sub_recall']['hit_moon']:.1%}, moon_lost "
          f"{p4['sub_recall']['moon_lost']:.1%}: targeted sampling "
          f"{'recommended' if p4['targeted_sampling_recommended'] else 'not needed'}")
    curve, importance, groups = learning_curve_and_importance(df, name, fs, calibrated, result)
    for point in curve:
        print(f"  {point['moons']:6.0f} moons: macro-F1 {point['macro_f1'][0]:.3f} "
              f"+/- {point['macro_f1'][1]:.3f}, rare recall {point['rare_recall'][0]:.1%}")
    for group, (mean, sd) in sorted(importance.items(), key=lambda kv: -kv[1][0]):
        print(f"  importance {group:22s} {mean:+.4f} +/- {sd:.4f}")
    criteria = phase5_criteria(y, oof)
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    selected["phase5_criteria"] = criteria
    SELECTED.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Phase 5 criteria written to configs/{SELECTED.name}; C1 interval "
          f"{criteria['C1_generalization']['interval'][0]:.3f} to "
          f"{criteria['C1_generalization']['interval'][1]:.3f}")
    analysis = {"selected": {"model": name, "feature_set": fs, "calibrated": calibrated},
                "metrics": result["metrics"], "metrics_isotropic": result["metrics_isotropic"],
                "chaos": chaos, "P4": p4, "P5": p5, "learning_curve": curve,
                "importance": importance, "importance_groups": groups}
    RESULTS.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(f"Saved data/{RESULTS.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
