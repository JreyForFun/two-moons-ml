"""Integrity checks of a finished dataset: manifest checksum, labels, inputs and reruns.

Every input is regenerated from the seed, labels are checked against the raw outcomes, and 20
random moons are integrated again and must reproduce their outcomes exactly.

Usage:
    python src/check_dataset.py configs/dataset.json
"""

import argparse
import json
import multiprocessing
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from generate_dataset import COLUMNS, make_inputs, read_rows, simulate_one, state_path
from horizons import ROOT
from labels import LABELS, make_label
from make_manifest import sha256
from sampling import closest_point_km, roche_limit_km
from simulate import load_config

RERUNS = 20
RERUN_SEED = 2026
MAX_TIMEOUTS = 0.02
SETTINGS = ("mass_lunar", "distance_lunar", "eccentricity", "inclination_deg")


def check_manifest(rows, config, state, config_path):
    path = ROOT / "configs" / f"{config_path.stem}_manifest.json"
    if not path.exists():
        return False, f"configs/{path.name} is missing; run make_manifest.py first"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    csv_path = ROOT / manifest["data_file"]
    same = sha256(csv_path) == manifest["data_sha256"] and manifest["rows"] == len(rows)
    return same, "CSV matches the saved SHA-256" if same else "CSV differs from the manifest"


def check_ids(rows, config, state, config_path):
    ids = Counter(int(row["id"]) for row in rows)
    repeated = [i for i, n in ids.items() if n > 1]
    missing = sorted(set(range(config["count"])) - set(ids))
    ok = not repeated and not missing and len(ids) == config["count"]
    return ok, f"{len(ids):,} ids, {len(repeated)} repeated, {len(missing)} missing"


def check_complete(rows, config, state, config_path):
    empty = [row["id"] for row in rows
             if any(row[c] == "" for c in COLUMNS if c.startswith("input_"))]
    errors = sum(row["result_label"] == "error" for row in rows)
    timeouts = sum(row["result_label"] == "timeout" for row in rows)
    ok = not empty and errors == 0 and timeouts <= MAX_TIMEOUTS * len(rows)
    return ok, f"{len(empty)} rows with empty inputs, {errors} errors, {timeouts} timeouts"


def check_ranges(rows, config, state, config_path):
    ranges = config["sampling"]
    for name in SETTINGS:
        low, high = ranges[name]
        values = [float(row[f"input_{name}"]) for row in rows]
        if min(values) < low or max(values) > high:
            return False, f"{name}: {min(values)} to {max(values)}"
    limit = roche_limit_km(state)
    closest = min(closest_point_km({s: float(row[f"input_{s}"]) for s in SETTINGS})
                  for row in rows)
    return closest >= limit, f"all settings in range, closest approach {closest:,.0f} km"


def check_labels(rows, config, state, config_path):
    """Label follows from outcome, and survival time fits the label."""
    duration = config["duration_days"]
    for row in rows:
        involved = tuple(row["result_involved"].split("+")) if row["result_involved"] else ()
        days = float(row["result_survival_days"])
        if make_label(row["result_outcome"], involved) != row["result_label"]:
            return False, f"moon {row['id']}: label does not match outcome"
        if (row["result_label"] == "survived") != (abs(days - duration) < 1e-6):
            return False, f"moon {row['id']}: {row['result_label']} after {days} days"
        if not 0 <= days <= duration:
            return False, f"moon {row['id']}: {days} days"
    return True, f"{len(rows):,} labels match outcomes and times"


def check_inputs(rows, config, state, config_path):
    """Every saved input is rebuilt from the seed and must match to the last digit."""
    for row in rows:
        _, inputs = make_inputs(state, config, int(row["id"]))
        for name, value in inputs.items():
            if str(value) != row[name]:
                return False, f"moon {row['id']}: {name} differs"
    return True, f"{len(rows):,} moons rebuilt from seed {config['seed']}"


def check_reruns(rows, config, state, config_path):
    """Re-simulate random moons; outcomes and survival times must be identical."""
    chosen = np.random.default_rng(RERUN_SEED).choice(len(rows), RERUNS, replace=False)
    saved = {int(rows[k]["id"]): rows[k] for k in chosen}
    tasks = [(i, state, config) for i in sorted(saved)]
    with multiprocessing.get_context("spawn").Pool(4) as pool:
        again = pool.map(simulate_one, tasks)
    keys = ("result_label", "result_outcome", "result_involved", "result_survival_days")
    different = [row["id"] for row in again
                 if any(row.get(k, "") != saved[row["id"]][k] for k in keys)]
    labels = Counter(saved[i]["result_label"] for i in saved)
    return not different, (f"{RERUNS - len(different)}/{RERUNS} identical "
                           f"({', '.join(f'{k} {v}' for k, v in labels.most_common())})"
                           + (f", differ: {different}" if different else ""))


def print_classes(rows):
    counts = Counter(row["result_label"] for row in rows)
    n = len(rows)
    print("\nCLASSES")
    for label in LABELS:
        if counts[label]:
            print(f"  {label:10s} {counts[label]:6,d}  {counts[label] / n:6.1%}")
    common, k = counts.most_common(1)[0]
    print(f"  Always guessing '{common}' would be right for {k / n:.1%}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    with open(state_path(config), encoding="utf-8") as f:
        state = json.load(f)
    rows = read_rows(ROOT / "data" / f"{args.config.stem}.csv")

    passed = True
    for label, check in (
        ("Manifest", check_manifest),
        ("Ids", check_ids),
        ("Complete", check_complete),
        ("Ranges", check_ranges),
        ("Labels", check_labels),
        ("Inputs reproducible", check_inputs),
        ("Reruns", check_reruns),
    ):
        ok, detail = check(rows, config, state, args.config)
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print_classes(rows)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
