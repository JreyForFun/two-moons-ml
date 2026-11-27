"""Investigation of the survival gap between the pilot and the full dataset (rule R1).

Two tests:
1. Reproducibility: pilot moons are integrated again with the final code; identical results
   exclude a code or configuration change between the pilot and the dataset.
2. Expected survivors: for each pilot moon, the survival share of its nearest training
   neighbours (in scaled mass, semi-major axis, eccentricity and inclination). An expected count
   near the observed 18 attributes the gap to the pilot's draws; a count near the training share
   indicates different outcomes for similar inputs.

Writes data/compare_pilot.json.

Usage:
    python src/compare_pilot.py
"""

import json
import multiprocessing
import sys

import numpy as np

import explore
from analyze_pilot import load
from generate_dataset import simulate_one
from horizons import ROOT, load_state
from simulate import load_config

RESULTS = ROOT / "data" / "compare_pilot.json"
RERUN = 20
NEIGHBOURS = 50
KEYS = ("result_label", "result_outcome", "result_involved", "result_survival_days")


def scaled(columns):
    """Inputs scaled to 0..1 over their sampling ranges (log for mass and distance)."""
    m, a, e, i = (np.asarray(c, dtype=float) for c in columns)
    return np.column_stack([np.log10(m / 0.001) / 3, np.log10(a / 0.1) / np.log10(30),
                            e / 0.8, i / 180])


def rerun_pilot(pilot):
    config = load_config(ROOT / "configs" / "pilot.json")
    tasks = [(i, load_state(), config) for i in range(RERUN)]
    with multiprocessing.get_context("spawn").Pool(4) as pool:
        again = pool.map(simulate_one, tasks)
    different = [row["id"] for row in again
                 if any(str(row.get(k, "")) != pilot[row["id"]][k] for k in KEYS)]
    return different


def expected_survivors(pilot, train):
    names = ("input_mass_lunar", "input_distance_lunar", "input_eccentricity",
             "input_inclination_deg")
    reference = scaled([train[n] for n in names])
    alive = train["survived"].to_numpy()
    probabilities = []
    for row in pilot.values():
        point = scaled([[float(row[n])] for n in names])
        nearest = np.argsort(((reference - point) ** 2).sum(axis=1))[:NEIGHBOURS]
        probabilities.append(alive[nearest].mean())
    p = np.array(probabilities)
    return p.sum(), np.sqrt((p * (1 - p)).sum())


def main():
    pilot = load("pilot")
    train = explore.load_dataset("train")
    observed = sum(row["result_label"] == "survived" for row in pilot.values())

    different = rerun_pilot(pilot)
    print(f"1. Re-simulated pilot moons 0-{RERUN - 1} with the current code: "
          f"{RERUN - len(different)}/{RERUN} identical" + (f", differ: {different}" if different else ""))

    expected, spread = expected_survivors(pilot, train)
    print(f"2. Observed pilot survivors: {observed}/100")
    print(f"   Expected from the {NEIGHBOURS} nearest training moons of each pilot moon: "
          f"{expected:.1f} (outcome noise alone: +/- {1.96 * spread:.1f} at 95%)")
    gap = observed - expected
    print(f"   Observed minus expected: {gap:+.1f} = {gap / spread:+.1f} standard deviations "
          f"({'within' if abs(gap) <= 1.96 * spread else 'outside'} the outcome-noise range)")
    results = {"rerun": RERUN, "rerun_identical": RERUN - len(different), "observed": observed,
               "expected": float(expected), "spread": float(spread),
               "gap_sigma": float(gap / spread), "neighbours": NEIGHBOURS}
    RESULTS.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Saved data/{RESULTS.name}")
    return 0 if not different else 1


if __name__ == "__main__":
    sys.exit(main())
