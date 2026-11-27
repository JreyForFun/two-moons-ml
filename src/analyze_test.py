"""Phase 5 failure analysis: test chaos twins (rule T5), error map, coverage-accuracy curve,
and cross-validated versus test metrics.

Run after evaluate_test.py and the test twins:  venv/Scripts/python src/analyze_test.py

Reads only the committed test results (results/), the Phase 4 results and the twin simulations;
it does not load the test set itself. Saves results/phase5_analysis.json.
"""

import json
import sys

import numpy as np
import pandas as pd

import cv
from analyze_pilot import wilson
from features import config
from horizons import ROOT

RESULTS = ROOT / "results" / "phase5_test.json"
PREDICTIONS = ROOT / "results" / "phase5_test_predictions.csv"
TWINS = ROOT / "data" / "twins_test_1m.csv"
CV_RESULT = ROOT / "data" / "phase4" / "random_forest_F3.json"
PROTOCOL = ROOT / "configs" / "phase5_protocol.json"
OUTPUT = ROOT / "results" / "phase5_analysis.json"
COVERAGES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


def selected_probs(frame):
    return frame[[f"selected_p{k}" for k in range(len(config()["classes"]))]].to_numpy()


def twin_pairs(frame):
    """Original test predictions joined with the twins' labels; checks the 1 m shift."""
    twins = pd.read_csv(TWINS, keep_default_na=False).set_index("id")
    if twins["result_label"].isin(["timeout", "error"]).any():
        raise RuntimeError("test twins contain timeouts or errors")
    original = frame.set_index("id").loc[twins.index]
    others = [c for c in twins.columns if c.startswith("input_") and c != "input_x_km"]
    same = all(np.array_equal(twins[c].to_numpy(float), original[c].to_numpy(float)) for c in others)
    shift = twins["input_x_km"].astype(float) - original["input_x_km"]
    if not same or not np.allclose(shift, 0.001, atol=1e-9):
        raise RuntimeError("test twins differ from their originals by more than the 1 m shift")
    codes = {n: k for k, n in enumerate(config()["classes"])}
    pairs = original.copy()
    pairs["y_twin"] = twins["result_label"].replace(config()["merge"]).map(codes)
    return pairs.reset_index()


def rule_t5(pairs, seed, samples):
    probs = selected_probs(pairs)
    wrong = probs.argmax(axis=1) != pairs["y"].to_numpy()
    chaotic = (pairs["y"] != pairs["y_twin"]).to_numpy()
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(samples):
        idx = rng.integers(0, len(wrong), len(wrong))
        w, c = wrong[idx], chaotic[idx]
        if c.any() and (~c).any():
            diffs.append(w[c].mean() - w[~c].mean())
    low, high = cv.interval(np.array(diffs))
    agree = ~chaotic
    alive = (pairs["y"] == 0) == (pairs["y_twin"] == 0)
    return {"twins": int(len(pairs)), "agreement": float(agree.mean()),
            "agreement_interval": list(wilson(int(agree.sum()), len(pairs))),
            "binary_agreement": float(alive.mean()), "chaotic_moons": int(chaotic.sum()),
            "error_chaotic": float(wrong[chaotic].mean()), "error_stable": float(wrong[~chaotic].mean()),
            "accuracy_stable": float(1 - wrong[~chaotic].mean()),
            "difference_interval": [low, high], "passed": low > 0}


def error_map(frame):
    probs = selected_probs(frame)
    wrong = probs.argmax(axis=1) != frame["y"].to_numpy()
    bins_a, bins_i = np.geomspace(0.1, 3.0, 7), np.linspace(0, 180, 7)
    ia = np.clip(np.digitize(frame["input_distance_lunar"], bins_a) - 1, 0, 5)
    ii = np.clip(np.digitize(frame["input_inclination_deg"], bins_i) - 1, 0, 5)
    cells = []
    for r in range(6):
        for c in range(6):
            mask = (ii == r) & (ia == c)
            n = int(mask.sum())
            k = int(wrong[mask].sum())
            low, high = wilson(k, n) if n else (np.nan, np.nan)
            cells.append({"a_low": float(bins_a[c]), "a_high": float(bins_a[c + 1]),
                          "i_low": float(bins_i[r]), "i_high": float(bins_i[r + 1]),
                          "moons": n, "errors": k, "error_rate": k / n if n else None,
                          "interval": [low, high]})
    return {"a_bins": bins_a.tolist(), "i_bins": bins_i.tolist(), "cells": cells}


def coverage_curve(frame):
    probs = selected_probs(frame)
    y = frame["y"].to_numpy()
    order = np.argsort(-probs.max(axis=1))
    correct = (probs.argmax(axis=1) == y)[order]
    out = []
    for coverage in COVERAGES:
        n = int(round(coverage * len(y)))
        k = int(correct[:n].sum())
        out.append({"coverage": coverage, "moons": n, "accuracy": k / n,
                    "interval": list(wilson(k, n)),
                    "min_confidence": float(probs.max(axis=1)[order][n - 1])})
    return out


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    frame = pd.read_csv(PREDICTIONS, keep_default_na=False,
                        na_values={"result_survival_days": [""]})
    cv_result = json.loads(CV_RESULT.read_text(encoding="utf-8"))
    pairs = twin_pairs(frame)
    t5 = rule_t5(pairs, protocol["bootstrap_seed"], protocol["bootstrap_samples"])
    keys = ("macro_f1", "accuracy", "balanced_accuracy", "log_loss", "survived_auc",
            "survived_accuracy", "survived_ece")
    analysis = {
        "T5": t5, "error_map": error_map(frame), "coverage_accuracy": coverage_curve(frame),
        "cv_vs_test": {k: {"cv": cv_result["metrics"][k], "test": results["metrics"]["selected"][k]}
                       for k in keys},
        "recall_cv_vs_test": {"cv": cv_result["metrics"]["recall"],
                              "test": results["metrics"]["selected"]["recall"]},
    }
    OUTPUT.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Test twins {t5['twins']}: agreement {t5['agreement']:.1%} (binary {t5['binary_agreement']:.1%}), "
          f"{t5['chaotic_moons']} chaotic")
    print(f"T5: error on chaotic {t5['error_chaotic']:.1%}, stable {t5['error_stable']:.1%}; difference "
          f"95% {t5['difference_interval'][0]:+.3f} to {t5['difference_interval'][1]:+.3f}: "
          f"{'PASS' if t5['passed'] else 'FAIL'}")
    for point in analysis["coverage_accuracy"]:
        print(f"  keep {point['coverage']:.0%}: accuracy {point['accuracy']:.1%} "
              f"(confidence >= {point['min_confidence']:.2f})")
    for k, v in analysis["cv_vs_test"].items():
        print(f"  {k:18s} cv {v['cv']:.3f}  test {v['test']:.3f}")
    print(f"Saved results/{OUTPUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
