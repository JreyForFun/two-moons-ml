"""Check the batch runner: workers, stop and resume, and protection of old data.

Run:  venv/Scripts/python src/check_generate.py
"""

import sys
import tempfile
from pathlib import Path

from generate_dataset import COLUMNS, generate, read_rows, simulate_one
from horizons import ROOT, load_state
from simulate import load_config

CONFIG = ROOT / "configs" / "pilot.json"
COUNT = 10
DAYS = 730


def comparable(path):
    """Rows sorted by id, without the computing time (never identical)."""
    rows = sorted(read_rows(path), key=lambda row: int(row["id"]))
    return [{k: v for k, v in row.items() if k != "result_computing_s"} for row in rows]


def check_workers(config, folder):
    generate(config, folder / "one.csv", workers=1)
    generate(config, folder / "four.csv", workers=4)
    one, four = comparable(folder / "one.csv"), comparable(folder / "four.csv")
    complete = [int(row["id"]) for row in one] == list(range(COUNT))
    return one == four and complete, f"{len(one)} and {len(four)} rows"


def check_resume(config, folder):
    path = folder / "resumed.csv"
    first = generate(config, path, workers=2, stop_after=4)
    with open(path, "a", encoding="utf-8") as f:
        f.write("7,0.5,0.3")  # like a crash in the middle of writing a row
    second = generate(config, path, workers=2)
    same = comparable(path) == comparable(folder / "one.csv")
    nothing_left = generate(config, path, workers=2) == 0
    ok = first == 4 and second == COUNT - 4 and same and nothing_left
    return ok, f"{first} rows, then {second} more"


def check_longer_batch(config, folder):
    path = folder / "four.csv"
    added = generate({**config, "count": COUNT + 2}, path, workers=2)
    same = comparable(path)[:COUNT] == comparable(folder / "one.csv")
    return added == 2 and same, f"{added} added, old rows unchanged"


def check_changed_settings_refused(config, folder):
    path = folder / "one.csv"
    before = path.read_bytes()
    for change in ({"seed": 1}, {"epsilon": 1e-11}, {"duration_days": DAYS + 1}):
        try:
            generate({**config, **change}, path, workers=1)
            return False, f"accepted {change}"
        except SystemExit:
            pass
    return path.read_bytes() == before, "seed, accuracy and duration changes refused"


def check_error_is_recorded(config, folder):
    broken = {**config, "integrator": "does-not-exist"}
    row = simulate_one((0, load_state(), broken))
    ok = row["result_label"] == "error" and row["result_error"]
    return ok, row["result_error"]


def check_columns(config, folder):
    """Nothing about the result may be named like an ML input."""
    row = read_rows(folder / "one.csv")[0]
    known = ("id", "sampling_redraws")
    ok = list(row) == COLUMNS and all(
        c in known or c.startswith(("input_", "result_")) for c in COLUMNS
    )
    return ok, f"{len(COLUMNS)} columns"


def main():
    config = {**load_config(CONFIG), "count": COUNT, "duration_days": DAYS}
    passed = True
    with tempfile.TemporaryDirectory() as name:
        for label, check in (
            ("1 and 4 workers give the same rows", check_workers),
            ("Stop, crash and resume", check_resume),
            ("Longer batch", check_longer_batch),
            ("Changed settings are refused", check_changed_settings_refused),
            ("Error is recorded", check_error_is_recorded),
            ("Columns", check_columns),
        ):
            ok, detail = check(config, Path(name))
            passed &= bool(ok)
            print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
