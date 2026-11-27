"""Prediction of the fate of a second moon with the evaluated surrogate model.

Arguments: mass in lunar masses, semi-major axis in lunar distances (384,400 km), eccentricity,
inclination to the ecliptic in degrees (above 90 is retrograde) and, optionally, the longitude of
the ascending node, argument of periapsis and true anomaly in degrees (default 0).

The model is the Random Forest evaluated on the held-out test set, trained on the 9,600 training
moons, so its reported performance applies. Fitted models are cached in data/phase5/ and rebuilt
deterministically when missing.

Usage:
    python src/predict.py --mass 0.1 --distance 0.4 --eccentricity 0.1 --inclination 20
"""

import argparse
import json
import sys

import joblib
import numpy as np
import pandas as pd

from explore import DATASET
from features import add_features, config, feature_columns, training_data
from horizons import ROOT, load_state
from make_manifest import sha256
from models import make_model
from sampling import roche_limit_km
from second_moon import LUNAR_DISTANCE_KM, add_second_moon

SELECTED = ROOT / "configs" / "selected_model.json"
CACHE = ROOT / "data" / "phase5" / "predict_models.joblib"
RANGES = {"mass_lunar": (0.001, 1.0), "distance_lunar": (0.1, 3.0), "eccentricity": (0.0, 0.8),
          "inclination_deg": (0.0, 180.0)}
LIFETIME = ("lost within 1 year", "lost within 1-10 years", "lost within 10-100 years",
            "survives 100 years")


def load_models():
    """Outcome and lifetime models, fitted exactly as in the Phase 5 evaluation."""
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    fingerprint = sha256(SELECTED)
    if CACHE.exists():
        cached = joblib.load(CACHE)
        if cached["selected_sha256"] == fingerprint:
            return cached
    if not DATASET.exists():
        raise SystemExit(
            "The model is trained from data/dataset.csv, which is not stored in Git. Download the "
            "data archive (see 'Data and reproducibility' in the README) into data/, or regenerate "
            "it with: python src/generate_dataset.py configs/dataset.json")
    train = training_data()
    cols = feature_columns(selected["feature_set"])
    models = {}
    for target in ("y", "y_lifetime"):
        model = make_model(selected["model"], seed=selected["seed"], params=selected["params"])
        models[target] = model.fit(train[cols], train[target].to_numpy())
    cached = {"selected_sha256": fingerprint, "columns": cols, "outcome": models["y"],
              "lifetime": models["y_lifetime"]}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(cached, CACHE)
    return cached


def predict_frame(frame):
    """Probabilities for rows that contain the dataset's input_* columns."""
    models = load_models()
    X = add_features(frame)[models["columns"]]
    out = pd.DataFrame(index=frame.index)
    for k, name in enumerate(config()["classes"]):
        out[f"p_{name}"] = models["outcome"].predict_proba(X)[:, k]
    for k, name in enumerate(LIFETIME):
        out[f"p_life_{k}"] = models["lifetime"].predict_proba(X)[:, k]
    return out


def describe(settings):
    """Input row (as in the dataset) for one second moon, plus warnings."""
    warnings = []
    for key, (low, high) in RANGES.items():
        if not low <= settings[key] <= high:
            warnings.append(f"{key} = {settings[key]} is outside the training range {low} to {high}")
    state = load_state()
    periapsis_km = settings["distance_lunar"] * LUNAR_DISTANCE_KM * (1 - settings["eccentricity"])
    if periapsis_km < roche_limit_km(state):
        warnings.append(f"periapsis {periapsis_km:,.0f} km is inside the Roche limit; such orbits "
                        "were excluded from the training data")
    case = add_second_moon(state, settings)
    earth, moon2 = case["bodies"]["earth"], case["bodies"]["moon2"]
    position = np.array(moon2["position_km"]) - np.array(earth["position_km"])
    velocity = np.array(moon2["velocity_km_s"]) - np.array(earth["velocity_km_s"])
    row = {f"input_{k}": v for k, v in settings.items()}
    for name, value in zip(("x_km", "y_km", "z_km"), position):
        row[f"input_{name}"] = value
    for name, value in zip(("vx_km_s", "vy_km_s", "vz_km_s"), velocity):
        row[f"input_{name}"] = value
    return pd.DataFrame([row]), warnings


def predict(mass_lunar, distance_lunar, eccentricity, inclination_deg, node_deg=0.0,
            periapsis_deg=0.0, true_anomaly_deg=0.0):
    """Outcome and lifetime probabilities for one second moon, with any warnings."""
    settings = {"mass_lunar": mass_lunar, "distance_lunar": distance_lunar,
                "eccentricity": eccentricity, "inclination_deg": inclination_deg,
                "node_deg": node_deg, "periapsis_deg": periapsis_deg,
                "true_anomaly_deg": true_anomaly_deg}
    row, warnings = describe(settings)
    probs = predict_frame(row).iloc[0]
    outcome = {name: float(probs[f"p_{name}"]) for name in config()["classes"]}
    lifetime = {name: float(probs[f"p_life_{k}"]) for k, name in enumerate(LIFETIME)}
    return {"outcome": outcome, "lifetime": lifetime, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mass", type=float, required=True, help="lunar masses")
    parser.add_argument("--distance", type=float, required=True, help="semi-major axis, lunar distances")
    parser.add_argument("--eccentricity", type=float, required=True)
    parser.add_argument("--inclination", type=float, required=True, help="degrees from the ecliptic")
    parser.add_argument("--node", type=float, default=0.0, help="degrees")
    parser.add_argument("--periapsis", type=float, default=0.0, help="degrees")
    parser.add_argument("--anomaly", type=float, default=0.0, help="starting angle, degrees")
    a = parser.parse_args()
    result = predict(a.mass, a.distance, a.eccentricity, a.inclination, a.node, a.periapsis,
                     a.anomaly)
    for warning in result["warnings"]:
        print(f"Warning: {warning}")
    print("Outcome within 100 years:")
    for name, p in sorted(result["outcome"].items(), key=lambda kv: -kv[1]):
        print(f"  {name:18s} {p:6.1%}")
    print("Lifetime:")
    for name, p in result["lifetime"].items():
        print(f"  {name:26s} {p:6.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
