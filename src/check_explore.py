"""Checks of the train/test split and the exploration helpers.

Usage:
    python src/check_explore.py
"""

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import explore
from sampling import closest_point_km
from second_moon import LUNAR_DISTANCE_KM


def check_split():
    split = json.loads(explore.SPLIT_FILE.read_text(encoding="utf-8"))
    everything = explore.load_dataset("all")
    train, test = explore.load_dataset("train"), explore.load_dataset("test")
    disjoint = not set(train["id"]) & set(test["id"])
    complete = set(train["id"]) | set(test["id"]) == set(everything["id"])
    labels, test_labels = Counter(everything["result_label"]), Counter(test["result_label"])
    stratified = all(abs(test_labels[k] - 0.2 * n) <= 1 for k, n in labels.items())
    ok = disjoint and complete and stratified and len(test) == len(split["test_ids"]) == 2400
    return ok, f"{len(train):,} train, {len(test):,} test, same label mix in both"


def check_refuses_changed_data():
    original = explore.DATASET
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder) / "dataset.csv"
        shutil.copy(original, copy)
        with open(copy, "a", encoding="utf-8") as f:
            f.write("\n")
        explore.DATASET = copy
        try:
            explore.load_dataset()
            refused = False
        except ValueError:
            refused = True
        finally:
            explore.DATASET = original
    return refused, "a CSV that differs from the manifest is refused"


def check_derived(df):
    worst = 0.0
    for _, row in df.head(500).iterrows():
        settings = {"distance_lunar": row["input_distance_lunar"],
                    "eccentricity": row["input_eccentricity"]}
        worst = max(worst, abs(row["periapsis_km"] - closest_point_km(settings)))
    retro_ok = (df["retrograde"] == (df["input_inclination_deg"] > 90)).all()
    hill = (df["distance_hill"] * explore.hill_km()
            / (df["input_distance_lunar"] * LUNAR_DISTANCE_KM) - 1).abs().max()
    return worst < 1e-6 and retro_ok and hill < 1e-12, f"periapsis off by at most {worst:.1e} km"


def check_bins(df):
    for column in explore.BINS:
        table = explore.shares_by_bin(df, column)
        if table["count"].sum() != len(df):
            return False, f"{column}: counts add to {table['count'].sum()}"
        filled = table[table["count"] > 0]
        if not np.allclose(filled[list(explore.OUTCOMES)].sum(axis=1), 1):
            return False, f"{column}: shares do not add to 1"
    _, count = explore.grid_shares(df, "input_distance_lunar", "input_inclination_deg")
    return count.sum() == len(df), f"{len(explore.BINS)} binnings and the grid add up"


def check_weights():
    """Reweighting uniform-in-degrees tilts must reproduce isotropic statistics."""
    rng = np.random.default_rng(1)
    fake = pd.DataFrame({"input_inclination_deg": rng.uniform(0, 180, 20000)})
    w = explore.isotropic_weights(fake)
    below = explore.weighted_share(fake["input_inclination_deg"] < 40, w)
    expected = (1 - np.cos(np.radians(40))) / 2
    ess = explore.effective_sample_size(w)
    ok = abs(below - expected) < 0.005 and abs(w.mean() - 1) < 1e-12 and ess < len(fake)
    return ok, f"{below:.1%} below 40 degrees (isotropic {expected:.1%}), effective size {ess:,.0f}"


def check_edge():
    """Synthetic data with a known edge, plus the no-edge case."""
    rng = np.random.default_rng(2)
    bins = explore.BINS["input_distance_lunar"]
    cutoff = bins[8]  # survival drops exactly at a bin boundary
    distance = np.exp(rng.uniform(np.log(0.1), np.log(3.0), 6000))
    alive = np.where(distance < cutoff, rng.random(6000) < 0.6, rng.random(6000) < 0.02)
    fake = pd.DataFrame({"input_distance_lunar": distance,
                         "result_label": np.where(alive, "survived", "ejected"),
                         "survived": alive})
    edge = explore.survival_edge(fake) * explore.hill_km() / LUNAR_DISTANCE_KM
    expected = np.sqrt(bins[8] * bins[9])  # center of the first bin beyond the cutoff
    stays = fake.assign(survived=True, result_label="survived")
    ok = abs(edge - expected) < 1e-9 and explore.survival_edge(stays) == float("inf")
    return ok, f"edge found at {edge:.2f} lunar distances, none when all survive"


def check_split_half():
    rng = np.random.default_rng(3)
    n = 20000
    fake = pd.DataFrame({
        "id": np.arange(n),
        "input_distance_lunar": np.exp(rng.uniform(np.log(0.1), np.log(3.0), n)),
        "input_inclination_deg": rng.uniform(0, 180, n),
    })
    p = np.clip(1.2 - fake["input_distance_lunar"] / 2, 0, 1)
    fake["result_label"] = np.where(rng.random(n) < p, "survived", "ejected")
    r, cells = explore.split_half_agreement(fake, "input_distance_lunar", "input_inclination_deg")
    return r > 0.9, f"correlation {r:.3f} over {cells} cells for a known pattern"


def main():
    df = explore.load_dataset("train")
    passed = True
    for label, check in (
        ("Split", check_split),
        ("Changed data refused", check_refuses_changed_data),
        ("Derived columns", lambda: check_derived(df)),
        ("Bins", lambda: check_bins(df)),
        ("Isotropic weights", check_weights),
        ("Survival edge", check_edge),
        ("Split-half agreement", check_split_half),
    ):
        ok, detail = check()
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
