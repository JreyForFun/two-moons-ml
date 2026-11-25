"""Check the random second moons and the labels.

Run:  venv/Scripts/python src/check_sampling.py
"""

import math
import sys

import numpy as np

from horizons import ROOT, load_state
from labels import LABELS, make_label
from sampling import build_case, closest_point_km, roche_limit_km, sample_settings
from simulate import build_simulation, load_config

CONFIG = ROOT / "configs" / "pilot.json"
SAMPLES = 5000


def check_ranges(state, config, samples):
    ranges = {**config["sampling"], "node_deg": [0, 360], "periapsis_deg": [0, 360],
              "true_anomaly_deg": [0, 360]}
    for name, (low, high) in ranges.items():
        values = [s[name] for s in samples]
        if min(values) < low - 1e-9 or max(values) > high + 1e-9:
            return False, f"{name}: {min(values)} to {max(values)}"
    return True, f"{len(samples)} moons inside all ranges"


def check_coverage(state, config, samples):
    """Settings that the Roche rule does not affect should be spread evenly.

    Compares with the ideal spread (Kolmogorov-Smirnov distance). For this many
    samples, more than 0.03 would be very unlikely by chance.
    """
    uniform = {
        "tilt": [(1 - math.cos(math.radians(s["inclination_deg"]))) / 2 for s in samples],
        "node": [s["node_deg"] / 360 for s in samples],
        "periapsis": [s["periapsis_deg"] / 360 for s in samples],
        "starting angle": [s["true_anomaly_deg"] / 360 for s in samples],
        "mass": [math.log(s["mass_lunar"] / 0.001) / math.log(1000) for s in samples],
    }
    worst = 0.0
    for values in uniform.values():
        values = np.sort(values)
        n = len(values)
        worst = max(worst, np.max(np.arange(1, n + 1) / n - values),
                    np.max(values - np.arange(n) / n))
    backward = np.mean([s["inclination_deg"] > 90 for s in samples])
    return worst < 0.03, f"largest deviation {worst:.3f}, {backward:.1%} backward"


def check_reproducible(state, config, samples):
    """Same moon again, in a different order, and different with another seed."""
    again = {i: sample_settings(state, config, i)[0] for i in reversed(range(50))}
    same = all(again[i] == samples[i] for i in range(50))
    other = sample_settings(state, {**config, "seed": config["seed"] + 1}, 0)[0]
    return same and other != samples[0], "independent of order, changes with the seed"


def check_roche(state, config, samples):
    limit = roche_limit_km(state)
    closest = min(closest_point_km(s) for s in samples)
    redraws = sum(sample_settings(state, config, i)[1] for i in range(len(samples)))
    ok = closest >= limit and 18000 < limit < 18800 and redraws > 0
    return ok, (f"limit {limit:,.0f} km, closest {closest:,.0f} km, "
                f"{redraws / (redraws + len(samples)):.1%} of draws rejected")


def check_orbits(state, config, samples):
    """REBOUND calculates the settings back, for forward and backward orbits."""
    names = config["bodies"]
    worst, backward = 0.0, 0
    for i in range(200):
        case, settings, _ = build_case(state, config, i)
        sim = build_simulation(case, config)
        moon2 = sim.particles[names.index("moon2")]
        earth = sim.particles[names.index("earth")]
        orbit = moon2.orbit(primary=earth)
        d = moon2 - earth
        spin = d.x * d.vy - d.y * d.vx
        tilt = settings["inclination_deg"]
        if (spin < 0) != (tilt > 90):
            return False, f"moon {i} orbits the wrong way"
        backward += tilt > 90
        worst = max(worst, abs(orbit.a / (settings["distance_lunar"] * 384400.0) - 1),
                    abs(orbit.e - settings["eccentricity"]),
                    abs(math.degrees(orbit.inc) - tilt) / 180)
    return worst < 1e-6, f"largest error {worst:.1e}, {backward} of 200 backward"


def check_shift(state, config, samples):
    normal = build_case(state, config, 3)[0]["bodies"]["moon2"]
    shifted = build_case(state, {**config, "shift_m": 1.0}, 3)[0]["bodies"]["moon2"]
    moved = shifted["position_km"][0] - normal["position_km"][0]
    others_same = (shifted["position_km"][1:] == normal["position_km"][1:]
                   and shifted["velocity_km_s"] == normal["velocity_km_s"])
    return abs(moved - 0.001) < 1e-6 and others_same, f"moved {moved * 1000:.4f} m"


def check_labels(state, config, samples):
    cases = {
        ("survived", ()): "survived",
        ("timeout", ()): "timeout",
        ("error", ()): "error",
        ("collision", ("earth", "moon2")): "hit_earth",
        ("collision", ("moon2", "earth")): "hit_earth",
        ("collision", ("moon", "moon2")): "hit_moon",
        ("collision", ("earth", "moon")): "moon_lost",
        ("collision", ("moon2", "sun")): "other",
        ("collision", ("moon", "sun")): "other",
        ("collision", ("earth", "sun")): "other",
        ("ejection", ("moon2",)): "ejected",
        ("ejection", ("moon",)): "moon_lost",
    }
    wrong = [case for case, label in cases.items() if make_label(*case) != label]
    covered = set(cases.values()) == set(LABELS)
    return not wrong and covered, f"{len(cases)} endings" if not wrong else str(wrong)


def main():
    state, config = load_state(), load_config(CONFIG)
    samples = [sample_settings(state, config, i)[0] for i in range(SAMPLES)]
    passed = True
    for label, check in (
        ("Ranges", check_ranges),
        ("Even coverage", check_coverage),
        ("Reproducible", check_reproducible),
        ("Roche rule", check_roche),
        ("Orbits, forward and backward", check_orbits),
        ("1 meter shift", check_shift),
        ("Labels", check_labels),
    ):
        ok, detail = check(state, config, samples)
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
