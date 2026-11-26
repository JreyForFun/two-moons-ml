"""Model inputs (feature sets F1-F3) and targets for the training moons.

Every feature is computed from `input_*` columns and the fixed starting state only, never from
`result_*` columns. Only training moons are loaded; a test id raises an error.
"""

import json
from functools import cache

import numpy as np

from explore import SPLIT_FILE, load_dataset
from horizons import ROOT, load_state

CONFIG = ROOT / "configs" / "models.json"
INPUT_VECTORS = ("input_x_km", "input_y_km", "input_z_km",
                 "input_vx_km_s", "input_vy_km_s", "input_vz_km_s")


@cache
def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def moon_direction():
    """Unit vector from Earth to the Moon at the common starting epoch."""
    bodies = load_state()["bodies"]
    d = np.array(bodies["moon"]["position_km"]) - np.array(bodies["earth"]["position_km"])
    return d / np.linalg.norm(d)


def add_features(df):
    """Return a copy of df with every feature column used by F1-F3."""
    out = df.copy()
    a = out["input_distance_lunar"]
    e = out["input_eccentricity"]
    inc = np.radians(out["input_inclination_deg"])
    out["log_mass"] = np.log10(out["input_mass_lunar"])
    out["log_a"] = np.log10(a)
    out["e"] = e
    out["cos_i"] = np.cos(inc)
    for name, column in (("node", "input_node_deg"), ("peri", "input_periapsis_deg"),
                         ("anom", "input_true_anomaly_deg")):
        angle = np.radians(out[column])
        out[f"sin_{name}"] = np.sin(angle)
        out[f"cos_{name}"] = np.cos(angle)
    for column in INPUT_VECTORS:
        out[column.removeprefix("input_")] = out[column]
    out["periapsis_lunar"] = a * (1 - e)
    out["apoapsis_lunar"] = a * (1 + e)
    out["crosses_moon"] = ((out["periapsis_lunar"] < 1) & (out["apoapsis_lunar"] > 1)).astype(float)
    out["abs_cos_i"] = np.abs(out["cos_i"])
    out["kozai"] = np.sqrt(1 - e ** 2) * out["cos_i"]
    position = out[list(INPUT_VECTORS[:3])].to_numpy()
    out["cos_moon_angle"] = position @ moon_direction() / np.linalg.norm(position, axis=1)
    return out


def add_targets(df):
    """Integer targets: `y` (4 outcome classes) and `y_lifetime` (4 lifetime classes)."""
    cfg = config()
    out = df.copy()
    merged = out["result_label"].replace(cfg["merge"])
    codes = {name: k for k, name in enumerate(cfg["classes"])}
    unknown = set(merged) - set(codes)
    if unknown:
        raise ValueError(f"labels without a class: {unknown}")
    out["y"] = merged.map(codes).astype(int)
    years = out["result_survival_days"] / 365.25
    low, high = cfg["lifetime_edges_years"]
    out["y_lifetime"] = np.select(
        [out["result_label"] == "survived", years < low, years < high], [3, 0, 1], default=2)
    return out


def training_data():
    """Training moons with features and targets. Refuses to return any test moon."""
    df = load_dataset("train")
    test = set(json.loads(SPLIT_FILE.read_text(encoding="utf-8"))["test_ids"])
    if test & set(df["id"]):
        raise RuntimeError("test moons found in the training data")
    return add_targets(add_features(df))


def feature_columns(name):
    return list(config()["feature_sets"][name])


def check_inputs_only():
    """Feature names must not refer to result columns or targets."""
    names = {c for cols in config()["feature_sets"].values() for c in cols}
    return sorted(n for n in names if n.startswith("result_") or n in ("y", "y_lifetime"))
