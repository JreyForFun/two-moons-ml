"""Dataset loading and binned outcome shares with uncertainties.

Exploration uses only the training moons (configs/split.json). Bins and decision rules were fixed
before the analysis (docs/report.md, Phase 3).
"""

import json
from functools import cache

import numpy as np
import pandas as pd

from analyze_pilot import wilson
from horizons import ROOT, load_state
from make_manifest import sha256
from paper_numbers import hill_radius_km
from second_moon import LUNAR_DISTANCE_KM

DATASET = ROOT / "data" / "dataset.csv"
MANIFEST = ROOT / "configs" / "dataset_manifest.json"
SPLIT_FILE = ROOT / "configs" / "split.json"
YEAR_DAYS = 365.25
OUTCOMES = ("survived", "ejected", "hit_earth", "hit_moon", "moon_lost")
MIN_CELL = 20  # cells with fewer moons are not shown
BOOTSTRAP_SEED = 20261128
BOOTSTRAP_SAMPLES = 1000

BINS = {
    "input_distance_lunar": np.geomspace(0.1, 3.0, 13),
    "input_inclination_deg": np.linspace(0.0, 180.0, 13),
    "input_eccentricity": np.linspace(0.0, 0.8, 9),
    "input_mass_lunar": np.geomspace(0.001, 1.0, 7),
}


@cache
def hill_km():
    return hill_radius_km(load_state())[0]


def load_dataset(part="train"):
    """Dataset rows for "train", "test" or "all", with derived columns.

    Refuses to load a CSV that differs from the one recorded in the manifest.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(DATASET) != manifest["data_sha256"]:
        raise ValueError("data/dataset.csv does not match configs/dataset_manifest.json")
    df = pd.read_csv(DATASET, keep_default_na=False,
                     na_values={"result_survival_days": [""], "result_computing_s": [""]})
    test = set(json.loads(SPLIT_FILE.read_text(encoding="utf-8"))["test_ids"])
    in_test = df["id"].isin(test)
    if part == "train":
        df = df[~in_test]
    elif part == "test":
        df = df[in_test]
    elif part != "all":
        raise ValueError(f"unknown part: {part}")
    df = df.sort_values("id").reset_index(drop=True)

    a_km = df["input_distance_lunar"] * LUNAR_DISTANCE_KM
    df["periapsis_km"] = a_km * (1 - df["input_eccentricity"])
    df["apoapsis_km"] = a_km * (1 + df["input_eccentricity"])
    df["distance_hill"] = a_km / hill_km()
    df["retrograde"] = df["input_inclination_deg"] > 90
    df["survived"] = df["result_label"] == "survived"
    df["survival_years"] = df["result_survival_days"] / YEAR_DAYS
    return df


def shares_by_bin(df, column, bins=None):
    """Count and outcome shares per bin, with a Wilson interval for survival."""
    bins = BINS[column] if bins is None else bins
    # labels=False gives bin numbers; the exact edges come from `bins` (pandas rounds labels).
    groups = pd.cut(df[column], bins, include_lowest=True, labels=False)
    rows = []
    for k in range(len(bins) - 1):
        part = df[groups == k]
        n = len(part)
        row = {"low": float(bins[k]), "high": float(bins[k + 1]), "count": n}
        for outcome in OUTCOMES:
            row[outcome] = (part["result_label"] == outcome).mean() if n else np.nan
        low, high = wilson(int(part["survived"].sum()), n) if n else (np.nan, np.nan)
        row.update({"survived_low": low, "survived_high": high})
        rows.append(row)
    return pd.DataFrame(rows)


def grid_shares(df, x, y, outcome="survived", bins_x=None, bins_y=None):
    """Share of an outcome on a 2D grid. Returns (share, count); sparse cells are NaN."""
    bins_x = BINS[x] if bins_x is None else bins_x
    bins_y = BINS[y] if bins_y is None else bins_y
    ix = np.clip(np.digitize(df[x], bins_x) - 1, 0, len(bins_x) - 2)
    iy = np.clip(np.digitize(df[y], bins_y) - 1, 0, len(bins_y) - 2)
    shape = (len(bins_y) - 1, len(bins_x) - 1)
    count = np.zeros(shape)
    hits = np.zeros(shape)
    np.add.at(count, (iy, ix), 1)
    np.add.at(hits, (iy, ix), (df["result_label"] == outcome).to_numpy())
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(count >= MIN_CELL, hits / count, np.nan)
    return share, count


def isotropic_weights(df):
    """Weights that turn inclinations drawn uniformly in degrees into isotropic ones.

    Isotropic orientations have density proportional to sin(i); uniform-in-degrees has
    constant density, so the weight is proportional to sin(i). Normalized to mean 1.
    """
    w = np.sin(np.radians(df["input_inclination_deg"].to_numpy()))
    return w / w.mean()


def effective_sample_size(weights):
    """How many equally weighted samples the weighted sample is worth."""
    return float(weights.sum() ** 2 / (weights ** 2).sum())


def weighted_share(mask, weights):
    return float(np.sum(weights * np.asarray(mask)) / np.sum(weights))


def bootstrap(df, statistic, samples=BOOTSTRAP_SAMPLES, seed=BOOTSTRAP_SEED):
    """Statistic recomputed on resamples of the rows (drawn with replacement)."""
    rng = np.random.default_rng(seed)
    n = len(df)
    return np.array([statistic(df.iloc[rng.integers(0, n, n)]) for _ in range(samples)])


def survival_edge(df, bins=None):
    """Outer survival edge in Hill radii (rule R2).

    Survival shares are computed in the fixed semi-major-axis bins. Starting from the bin
    with the highest survival share, the edge is the center (geometric mean) of the first
    bin farther out whose share is below 10%. Bins with fewer than MIN_CELL moons are
    skipped. Returns inf if survival never drops below 10% inside the sampled range.
    """
    table = shares_by_bin(df, "input_distance_lunar", bins)
    table = table[table["count"] >= MIN_CELL].reset_index(drop=True)
    peak = int(table["survived"].idxmax())
    for _, row in table.iloc[peak:].iterrows():
        if row["survived"] < 0.10:
            center_lunar = np.sqrt(row["low"] * row["high"])
            return float(center_lunar * LUNAR_DISTANCE_KM / hill_km())
    return float("inf")


def split_half_agreement(df, x, y, outcome="survived"):
    """Count-weighted correlation of cell shares between even and odd ids."""
    even, odd = df[df["id"] % 2 == 0], df[df["id"] % 2 == 1]
    share_a, count_a = grid_shares(even, x, y, outcome)
    share_b, count_b = grid_shares(odd, x, y, outcome)
    keep = ~np.isnan(share_a) & ~np.isnan(share_b)
    a, b, w = share_a[keep], share_b[keep], (count_a + count_b)[keep]
    ma, mb = np.average(a, weights=w), np.average(b, weights=w)
    cov = np.average((a - ma) * (b - mb), weights=w)
    r = cov / np.sqrt(np.average((a - ma) ** 2, weights=w) * np.average((b - mb) ** 2, weights=w))
    return float(r), int(keep.sum())
