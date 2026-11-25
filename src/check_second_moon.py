"""Check that the second moon is set up and simulated correctly.

Run:  venv/Scripts/python src/check_second_moon.py

The limits below were chosen before the first run.
"""

import copy
import math
import sys

import numpy as np

from horizons import ROOT, load_state
from second_moon import add_second_moon
from simulate import DAY_S, build_simulation, load_config, run

CONFIG = ROOT / "configs" / "single_run.json"
MAX_ELEMENT_ERROR = 1e-9  # relative for size, absolute (radians) for the rest
MAX_MOON_SHIFT_KM = 0.001  # 1 meter


def with_settings(config, **changes):
    """Copy of config with some second-moon settings replaced."""
    config = copy.deepcopy(config)
    config["second_moon"].update(changes)
    return config


def check_orbit_matches_settings(state, config):
    """Let REBOUND calculate the orbit back from our position and velocity."""
    settings = {"mass_lunar": 0.3, "distance_lunar": 0.6, "eccentricity": 0.25,
                "inclination_deg": 20.0, "node_deg": 40.0, "periapsis_deg": 70.0,
                "true_anomaly_deg": 110.0}
    sim = build_simulation(add_second_moon(state, settings), config)
    names = config["bodies"]
    moon2 = sim.particles[names.index("moon2")]
    orbit = moon2.orbit(primary=sim.particles[names.index("earth")])
    errors = [abs(orbit.a / (0.6 * 384400.0) - 1), abs(orbit.e - 0.25)]
    for angle, name in ((orbit.inc, "inclination_deg"), (orbit.Omega, "node_deg"),
                        (orbit.omega, "periapsis_deg"), (orbit.f, "true_anomaly_deg")):
        difference = angle - math.radians(settings[name])
        errors.append(abs(math.remainder(difference, 2 * math.pi)))
    return max(errors) < MAX_ELEMENT_ERROR, f"largest error {max(errors):.1e}"


def check_tiny_moon_changes_nothing(state, config):
    tiny = run(state, with_settings(config, mass_lunar=1e-12))
    none = run(state, {**config, "bodies": ["sun", "earth", "moon"]})
    if len(tiny.times_s) != len(none.times_s):
        return False, f"run ended early: {tiny.outcome} {tiny.involved}"
    shift = np.linalg.norm(tiny.relative("moon") - none.relative("moon"), axis=1).max()
    return shift < MAX_MOON_SHIFT_KM, f"Moon moved at most {shift * 1e6:.3g} mm in 10 years"


def check_reruns_identical(state, config):
    first, second = run(state, config), run(state, config)
    same = (np.array_equal(first.positions_km, second.positions_km)
            and first.outcome == second.outcome and first.involved == second.involved)
    return same, f"{len(first.times_s)} outputs compared exactly"


def check_hits_earth(state, config):
    """A very stretched orbit whose closest point is inside Earth."""
    result = run(state, with_settings(config, eccentricity=0.97, true_anomaly_deg=180.0))
    ok = result.outcome == "collision" and result.involved == ("earth", "moon2")
    return ok, describe(result)


def check_hits_moon(state, config):
    """Start 10,000 km from the Moon with the same velocity, so it falls in."""
    state = add_second_moon(state, config["second_moon"])
    moon, moon2 = state["bodies"]["moon"], state["bodies"]["moon2"]
    moon2["position_km"] = [moon["position_km"][0] + 10000.0, *moon["position_km"][1:]]
    moon2["velocity_km_s"] = list(moon["velocity_km_s"])
    config = {key: value for key, value in config.items() if key != "second_moon"}
    result = run(state, config)
    ok = result.outcome == "collision" and result.involved == ("moon", "moon2")
    return ok, describe(result)


def check_ejected(state, config):
    """Start outside Earth's Hill sphere, where the Sun wins."""
    result = run(state, with_settings(config, distance_lunar=6.0))
    ok = result.outcome == "ejection" and result.involved == ("moon2",)
    return ok, describe(result)


def describe(result):
    return f"{result.outcome} {result.involved} after {result.end_time_s / DAY_S:.2f} days"


def main():
    state, config = load_state(), load_config(CONFIG)
    checks = [
        ("Orbit matches its settings", check_orbit_matches_settings),
        ("Near-zero mass changes nothing", check_tiny_moon_changes_nothing),
        ("Reruns are identical", check_reruns_identical),
        ("Hits Earth", check_hits_earth),
        ("Hits the Moon", check_hits_moon),
        ("Ejected", check_ejected),
    ]
    passed = True
    for label, check in checks:
        ok, detail = check(state, config)
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
