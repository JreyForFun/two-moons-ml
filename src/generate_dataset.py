"""Simulate many random second moons and save one CSV row per moon.

Run:  venv/Scripts/python src/generate_dataset.py configs/pilot.json

Safe to stop with Ctrl+C: run the same command again and it continues. Only the
main process writes the file.

Column names: input_* may be used as ML inputs. result_* are what happened and
must never be used as inputs.
"""

import argparse
import csv
import hashlib
import json
import multiprocessing
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

from horizons import ROOT, STATE_FILE, load_state
from labels import make_label
from sampling import build_case
from simulate import DAY_S, load_config, run_summary

DEFAULT_WORKERS = 4
SETTINGS = ("mass_lunar", "distance_lunar", "eccentricity", "inclination_deg",
            "node_deg", "periapsis_deg", "true_anomaly_deg")
VECTORS = ("x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s")
COLUMNS = (
    ["id"]
    + [f"input_{name}" for name in SETTINGS]
    + [f"input_{name}" for name in VECTORS]  # starting state seen from Earth
    + ["result_label", "result_outcome", "result_involved", "result_survival_days",
       "result_computing_s", "result_error", "sampling_redraws"]
)


def state_path(config):
    """File with the starting data. Other dates use the config key "state_file"."""
    return ROOT / config["state_file"] if "state_file" in config else STATE_FILE


def fingerprint(config, state):
    """Short hash of everything that decides the results.

    "count" and "description" are left out, so a batch can be made longer.
    """
    used = {k: v for k, v in config.items() if k not in ("count", "description")}
    text = json.dumps([used, state["epoch_jd_tdb"], state["bodies"]], sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def make_inputs(state, config, moon_id):
    """Return (case, input columns) for one moon, exactly as saved in the CSV."""
    case, settings, redraws = build_case(state, config, moon_id)
    earth, moon2 = case["bodies"]["earth"], case["bodies"]["moon2"]
    vectors = np.concatenate([
        np.array(moon2["position_km"]) - np.array(earth["position_km"]),
        np.array(moon2["velocity_km_s"]) - np.array(earth["velocity_km_s"]),
    ])
    inputs = {f"input_{name}": repr(settings[name]) for name in SETTINGS}
    inputs.update({f"input_{n}": repr(float(v)) for n, v in zip(VECTORS, vectors)})
    inputs["sampling_redraws"] = redraws
    return case, inputs


def simulate_one(task):
    """Run one moon. Runs inside a worker process and never raises."""
    moon_id, state, config = task
    row = {"id": moon_id}
    try:
        case, inputs = make_inputs(state, config, moon_id)
        row.update(inputs)
        summary = run_summary(case, config)
        row.update({
            "result_label": make_label(summary.outcome, summary.involved),
            "result_outcome": summary.outcome,
            "result_involved": "+".join(summary.involved),
            "result_survival_days": repr(summary.end_time_s / DAY_S),
            "result_computing_s": f"{summary.computing_s:.3f}",
        })
    except Exception as error:  # one bad moon must not stop the batch
        row.update({"result_label": "error", "result_outcome": "error",
                    "result_error": f"{type(error).__name__}: {error}"})
    return row


def read_rows(path):
    """Finished rows. A half-written last line (after a crash) is ignored."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if rows and (None in rows[-1].values() or None in rows[-1]):
        rows.pop()
    return rows


def write_rows(path, rows):
    """Replace the file in one step, so it is never left half-written."""
    temporary = path.with_suffix(".tmp")
    with open(temporary, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, restval="", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def prepare_output(path, config, state):
    """Check that path belongs to this config. Return the ids already finished."""
    info_path = path.with_suffix(".info.json")
    code = fingerprint(config, state)
    if path.exists() or info_path.exists():
        saved = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
        if saved.get("fingerprint") != code:
            raise SystemExit(f"{path.name} was made with different settings. "
                             "Use another config name or move the old file away.")
    else:
        path.parent.mkdir(exist_ok=True)
        info = {"fingerprint": code, "config": config}
        info_path.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    rows = read_rows(path)
    write_rows(path, rows)
    return {int(row["id"]) for row in rows}


def generate(config, path, workers=DEFAULT_WORKERS, stop_after=None):
    """Simulate all missing moons and return how many were added.

    stop_after ends the batch early after that many new rows (used by the checks).
    """
    with open(state_path(config), encoding="utf-8") as f:
        state = json.load(f)
    done = prepare_output(path, config, state)
    tasks = [(i, state, config) for i in range(config["count"]) if i not in done]
    print(f"{len(done)} finished before, {len(tasks)} to do, {workers} workers", flush=True)
    if not tasks:
        return 0

    started, added, counts = time.perf_counter(), 0, Counter()
    context = multiprocessing.get_context("spawn")
    with open(path, "a", encoding="utf-8", newline="") as f, context.Pool(workers) as pool:
        writer = csv.DictWriter(f, COLUMNS, restval="", lineterminator="\n")
        for row in pool.imap_unordered(simulate_one, tasks):
            writer.writerow(row)
            f.flush()
            added += 1
            counts[row["result_label"]] += 1
            if added % max(1, min(50, len(tasks) // 10)) == 0 or added == len(tasks):
                minutes = (time.perf_counter() - started) / 60
                print(f"{added}/{len(tasks)} in {minutes:.1f} min  {dict(counts)}", flush=True)
            if added == stop_after:
                pool.terminate()
                break
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()
    output = ROOT / "data" / f"{args.config.stem}.csv"
    try:
        generate(load_config(args.config), output, args.workers)
    except KeyboardInterrupt:
        print("Stopped. Run the same command again to continue.")
        return 1
    print(f"Saved data/{output.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
