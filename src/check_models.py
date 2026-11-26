"""Check the Phase 4 inputs, targets and cross-validation for leaks and errors.

Run:  venv/Scripts/python src/check_models.py      (about 3 minutes)
"""

import json
import math
import re
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from cv import macro_f1, run_cv
from features import check_inputs_only, config, feature_columns, moon_direction, training_data
from horizons import ROOT
from models import BalancedXGB

PHASE4_SCRIPTS = ("features.py", "models.py", "cv.py", "train_models.py", "analyze_models.py",
                  "plot_models.py", "select_twins.py")


def check_inputs(df):
    bad = check_inputs_only()
    missing = [c for name in config()["feature_sets"] for c in feature_columns(name)
               if c not in df.columns]
    return not bad and not missing, f"{len(config()['feature_sets'])} feature sets, inputs only"


def check_training_only(df):
    test = set(json.loads((ROOT / "configs" / "split.json").read_text())["test_ids"])
    ok = len(df) == 9600 and not test & set(df["id"])
    return ok, f"{len(df):,} training moons, no test id"


def check_no_test_access():
    pattern = re.compile(r"load_dataset\(\s*[\"'](test|all)[\"']")
    found = [name for name in PHASE4_SCRIPTS
             if (ROOT / "src" / name).exists()
             and pattern.search((ROOT / "src" / name).read_text(encoding="utf-8"))]
    return not found, "no Phase 4 script loads the test or full dataset" if not found else str(found)


def check_derived(df):
    moon = moon_direction()
    worst = 0.0
    for _, r in df.sample(5, random_state=1).iterrows():
        a, e = r["input_distance_lunar"], r["input_eccentricity"]
        inc = math.radians(r["input_inclination_deg"])
        pos = np.array([r["input_x_km"], r["input_y_km"], r["input_z_km"]])
        expected = {
            "log_a": math.log10(a), "cos_i": math.cos(inc), "abs_cos_i": abs(math.cos(inc)),
            "periapsis_lunar": a * (1 - e), "apoapsis_lunar": a * (1 + e),
            "kozai": math.sqrt(1 - e * e) * math.cos(inc),
            "sin_node": math.sin(math.radians(r["input_node_deg"])),
            "cos_moon_angle": float(pos @ moon / np.linalg.norm(pos)),
            "crosses_moon": float(a * (1 - e) < 1 < a * (1 + e)),
        }
        worst = max(worst, max(abs(r[k] - v) for k, v in expected.items()))
    return worst < 1e-12, f"largest difference {worst:.1e}"


def check_targets(df):
    names = config()["classes"]
    counts = df["y"].value_counts().sort_index()
    merged_ok = counts[names.index("moon_interaction")] == df["result_label"].isin(
        ["hit_moon", "moon_lost"]).sum()
    life = df["y_lifetime"]
    survivors_ok = ((life == 3) == (df["result_label"] == "survived")).all()
    ends = df.loc[life < 3, "result_survival_days"] / 365.25
    bins_ok = ((ends[life[life < 3] == 0] < 1).all() and (ends[life[life < 3] == 2] >= 10).all()
               and (ends < 100).all())
    shares = ", ".join(f"{n} {c / len(df):.1%}" for n, c in zip(names, counts))
    return merged_ok and survivors_ok and bins_ok, shares


def check_folds(df):
    y = df["y"].to_numpy()
    outer = StratifiedKFold(config()["outer_folds"], shuffle=True, random_state=config()["seed"])
    overall = np.bincount(y) / len(y)
    worst = max(np.abs(np.bincount(y[test], minlength=4) / len(test) - overall).max()
                for _, test in outer.split(df, y))
    return worst < 0.005, f"class shares within {worst:.4f} of overall in every fold"


def check_reproducible(df):
    X, y = df[feature_columns("F1")], df["y"].to_numpy()
    first, _ = run_cv("random_forest_default", X, y, tune=False, params={"n_estimators": 50})
    second, _ = run_cv("random_forest_default", X, y, tune=False, params={"n_estimators": 50})
    return np.array_equal(first, second), "same seed, identical out-of-fold probabilities"


def check_label_permutation(df):
    """A leak-free pipeline cannot predict shuffled labels."""
    X, y = df[feature_columns("F3")], df["y"].to_numpy()
    shuffled = np.random.default_rng(7).permutation(y)
    fake, _ = run_cv("random_forest_default", X, shuffled, tune=False, params={"n_estimators": 100})
    real, _ = run_cv("random_forest_default", X, y, tune=False, params={"n_estimators": 100})
    fake_f1, real_f1 = macro_f1(shuffled, fake), macro_f1(y, real)
    return fake_f1 < 0.30 and real_f1 > fake_f1 + 0.2, (
        f"macro-F1 {fake_f1:.3f} on shuffled labels vs {real_f1:.3f} on real labels")


def check_xgboost_wrapper(df):
    X, y = df[feature_columns("F1")].iloc[:2000], df["y"].to_numpy()[:2000]
    plain = BalancedXGB(n_estimators=50, random_state=0).fit(X, y).predict_proba(X)
    weighted = BalancedXGB(n_estimators=50, balanced=True, random_state=0).fit(X, y).predict_proba(X)
    ok = np.allclose(plain.sum(axis=1), 1) and not np.allclose(plain, weighted)
    return ok, "probabilities sum to 1; balancing changes the model"


def check_twins(df):
    """Each twin equals its original moon except for the 1 m shift in x."""
    path = ROOT / "data" / "twins_1m.csv"
    if not path.exists():
        return True, "no twins file yet (skipped)"
    twins = pd.read_csv(path, keep_default_na=False).set_index("id")
    original = df.set_index("id").loc[twins.index]
    settings = [c for c in twins.columns if c.startswith("input_") and c != "input_x_km"]
    same = all(np.array_equal(twins[c].to_numpy(float), original[c].to_numpy(float))
               for c in settings)
    shift = (twins["input_x_km"].astype(float) - original["input_x_km"]).to_numpy()
    timeouts = int(twins["result_label"].isin(["timeout", "error"]).sum())
    ok = same and np.allclose(shift, 0.001, atol=1e-9) and timeouts == 0
    return ok, (f"{len(twins):,} twins: other inputs identical, x shifted by "
                f"{shift.mean() * 1000:.6f} m, {timeouts} timeouts or errors")


def main():
    df = training_data()
    passed = True
    for label, check in (
        ("Inputs only", lambda: check_inputs(df)),
        ("Training moons only", lambda: check_training_only(df)),
        ("No test access in code", check_no_test_access),
        ("Derived features", lambda: check_derived(df)),
        ("Targets", lambda: check_targets(df)),
        ("Stratified folds", lambda: check_folds(df)),
        ("Reproducible", lambda: check_reproducible(df)),
        ("Label permutation", lambda: check_label_permutation(df)),
        ("XGBoost wrapper", lambda: check_xgboost_wrapper(df)),
        ("Chaos twins", lambda: check_twins(df)),
    ):
        ok, detail = check()
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
