"""Check the Phase 5 safeguards, the dry run and (once it exists) the prediction tool.

Run:  venv/Scripts/python src/check_evaluation.py      (after evaluate_test.py --dry-run)
"""

import json
import re
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from features import config, feature_columns, training_data
from horizons import ROOT
from models import make_model

SELECTED = ROOT / "configs" / "selected_model.json"
PROTOCOL = ROOT / "configs" / "phase5_protocol.json"
DRY_DIR = ROOT / "data" / "phase5_dry"
# check_explore.py reads the test part only to confirm the split's size and stratification.
ALLOWED_TEST_ACCESS = {"evaluate_test.py", "check_explore.py"}


def git_unchanged(commit, path):
    return subprocess.run(["git", "diff", "--quiet", commit, "--", path], cwd=ROOT).returncode == 0


def check_test_access():
    # The pattern is assembled from pieces so this file does not match itself.
    pattern = re.compile("load_dataset" + r"\(\s*[\"']" + "te" + "st" + r"[\"']")
    found = {p.name for p in (ROOT / "src").glob("*.py")
             if pattern.search(p.read_text(encoding="utf-8"))}
    ok = found <= ALLOWED_TEST_ACCESS and "evaluate_test.py" in found
    return ok, f"test set loaded only in {', '.join(sorted(found))}"


def check_frozen():
    ok = git_unchanged("975d7fb", "configs/selected_model.json") and \
        git_unchanged("ccb9bbc", "configs/split.json")
    return ok, "criteria unchanged since 975d7fb, split unchanged since ccb9bbc"


def check_protocol():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    needed = {"amendment", "seed", "seed_luck_seeds", "rule_T5", "speed_benchmark",
              "outcome_handling", "no_model_switching"}
    ok = needed <= set(protocol) and protocol["seed"] == selected["seed"] and \
        set(protocol["primary_criteria"]) <= set(selected["phase5_criteria"])
    return ok, f"{len(protocol)} protocol entries; primary criteria match the selected model"


def check_deterministic():
    df = training_data()
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    fit, hold = train_test_split(df, test_size=0.2, stratify=df["y"], random_state=1)
    cols = feature_columns(selected["feature_set"])
    predictions = []
    for _ in range(2):
        model = make_model(selected["model"], seed=selected["seed"], params=selected["params"])
        model.fit(fit[cols], fit["y"].to_numpy())
        predictions.append(model.predict_proba(hold[cols]))
    return np.array_equal(*predictions), "final model training is deterministic"


def check_dry_run():
    path, csv = DRY_DIR / "results.json", DRY_DIR / "predictions.csv"
    if not path.exists() or not csv.exists():
        return False, "run evaluate_test.py --dry-run first"
    results = json.loads(path.read_text(encoding="utf-8"))
    frame = pd.read_csv(csv)
    k = len(config()["classes"])
    probs = frame[[f"selected_p{i}" for i in range(k)]].to_numpy()
    complete = (results["provenance"]["dry_run"]
                and {"C1", "C1b", "C2", "C3", "C4"} <= set(results["criteria"])
                and len(frame) == results["moons"]["evaluated"]
                and np.allclose(probs.sum(axis=1), 1)
                and len(results["seed_luck"]["macro_f1"]) == 5)
    return complete, f"{len(frame):,} holdout moons, all criteria and outputs present"


def check_predict_tool():
    predictions = ROOT / "results" / "phase5_test_predictions.csv"
    if not (ROOT / "src" / "predict.py").exists() or not predictions.exists():
        return True, "prediction tool not built yet (skipped)"
    from predict import predict_frame
    frame = pd.read_csv(predictions).head(50)
    k = len(config()["classes"])
    expected = frame[[f"selected_p{i}" for i in range(k)]].to_numpy()
    got = predict_frame(frame)[[f"p_{c}" for c in config()["classes"]]].to_numpy()
    return np.allclose(expected, got), "predict.py reproduces the evaluated predictions"


def main():
    passed = True
    for label, check in (
        ("Test access", check_test_access),
        ("Frozen criteria and split", check_frozen),
        ("Protocol", check_protocol),
        ("Deterministic final model", check_deterministic),
        ("Dry run", check_dry_run),
        ("Prediction tool", check_predict_tool),
    ):
        ok, detail = check()
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
