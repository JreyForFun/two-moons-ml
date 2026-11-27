"""Timing of the surrogate model against direct integration.

Model and simulation run single-threaded in one process on the same machine, on training moons
only. Writes results/phase5_speed.json.

Usage:
    python src/benchmark_speed.py
"""

import json
import platform
import statistics
import sys
import time

import numpy as np

from features import add_features, feature_columns, training_data
from generate_dataset import make_inputs
from horizons import ROOT
from labels import make_label
from models import make_model
from simulate import load_config, run_summary

PROTOCOL = ROOT / "configs" / "phase5_protocol.json"
SELECTED = ROOT / "configs" / "selected_model.json"
DATASET_CONFIG = ROOT / "configs" / "dataset.json"
MANIFEST = ROOT / "configs" / "dataset_manifest.json"
OUTPUT = ROOT / "results" / "phase5_speed.json"
LATENCY_REPEATS = 1000
BATCH = 2400


def benchmark_model(df, selected):
    cols = feature_columns(selected["feature_set"])
    started = time.perf_counter()
    model = make_model(selected["model"], seed=selected["seed"], params=selected["params"])
    model.fit(df[cols], df["y"].to_numpy())
    train_seconds = time.perf_counter() - started
    raw = df[[c for c in df.columns if c.startswith("input_")] + ["id"]]
    latencies = []
    for k in range(LATENCY_REPEATS):
        row = raw.iloc[[k % len(raw)]]
        t0 = time.perf_counter()
        model.predict_proba(add_features(row)[cols])
        latencies.append(time.perf_counter() - t0)
    batch = raw.iloc[:BATCH]
    t0 = time.perf_counter()
    model.predict_proba(add_features(batch)[cols])
    batch_seconds = time.perf_counter() - t0
    return {"training_seconds": train_seconds,
            "latency_median_s": statistics.median(latencies),
            "latency_mean_s": statistics.fmean(latencies),
            "batch_moons": BATCH, "batch_seconds": batch_seconds,
            "batch_per_moon_s": batch_seconds / BATCH}


def benchmark_simulation(df, spec):
    config = load_config(DATASET_CONFIG)
    with open(ROOT / "configs" / "initial_state.json", encoding="utf-8") as f:
        state = json.load(f)
    rng = np.random.default_rng(spec["seed"])
    ids = sorted(int(i) for i in rng.choice(df["id"].to_numpy(), spec["moons"], replace=False))
    labels = df.set_index("id")["result_label"]
    runs = []
    for moon_id in ids:
        case, _ = make_inputs(state, config, moon_id)
        t0 = time.perf_counter()
        summary = run_summary(case, config)
        seconds = time.perf_counter() - t0
        label = make_label(summary.outcome, summary.involved)
        runs.append({"id": moon_id, "seconds": seconds, "label": label,
                     "matches_dataset": label == labels[moon_id]})
        print(f"  moon {moon_id}: {seconds:6.2f} s, {label}", flush=True)
    seconds = [r["seconds"] for r in runs]
    by_label = {}
    for r in runs:
        by_label.setdefault(r["label"], []).append(r["seconds"])
    return {"moons": len(runs), "median_s": statistics.median(seconds),
            "mean_s": statistics.fmean(seconds),
            "by_outcome": {k: {"moons": len(v), "median_s": statistics.median(v),
                               "mean_s": statistics.fmean(v)} for k, v in sorted(by_label.items())},
            "all_outcomes_reproduced": all(r["matches_dataset"] for r in runs), "runs": runs}


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    df = training_data()
    print("Model benchmark", flush=True)
    model = benchmark_model(df, selected)
    print(f"  latency {model['latency_median_s'] * 1000:.2f} ms per moon, batch "
          f"{model['batch_per_moon_s'] * 1e6:.1f} microseconds per moon", flush=True)
    print("Simulation benchmark", flush=True)
    sim = benchmark_simulation(df, protocol["speed_benchmark"]["simulation"])
    reference = protocol["speed_benchmark"]["preregistered_reference_s"]
    dataset_cpu_s = manifest["computing"]["cpu_hours"] * 3600
    saving_per_prediction = sim["mean_s"] - model["latency_median_s"]
    results = {
        "machine": {"system": f"{platform.system()} {platform.release()}",
                    "processor": platform.processor(), "python": platform.python_version()},
        "model": model, "simulation": sim,
        "speedup": {
            "preregistered_median": reference / model["latency_median_s"],
            "same_machine_median": sim["median_s"] / model["latency_median_s"],
            "same_machine_mean": sim["mean_s"] / model["latency_median_s"],
            "batch_vs_mean": sim["mean_s"] / model["batch_per_moon_s"],
        },
        "time_for_12000_moons": {"model_batch_s": 12000 * model["batch_per_moon_s"],
                                 "simulation_cpu_hours": manifest["computing"]["cpu_hours"]},
        "break_even_predictions": (dataset_cpu_s + model["training_seconds"]) / saving_per_prediction,
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    s = results["speedup"]
    print(f"Simulation: median {sim['median_s']:.2f} s, mean {sim['mean_s']:.2f} s; outcomes "
          f"reproduced: {sim['all_outcomes_reproduced']}")
    print(f"Speedup: pre-registered {s['preregistered_median']:,.0f}x, same machine median "
          f"{s['same_machine_median']:,.0f}x, mean {s['same_machine_mean']:,.0f}x, batch "
          f"{s['batch_vs_mean']:,.0f}x")
    print(f"Break-even after {results['break_even_predictions']:,.0f} predictions")
    print(f"Saved results/{OUTPUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
