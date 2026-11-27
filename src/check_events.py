"""Checks of collision and ejection detection and of the resulting labels.

Usage:
    python src/check_events.py
"""

import copy
import math
import sys

import numpy as np

from horizons import load_state
from simulate import DAY_S, load_config, run


def moon_with_velocity(state, radial_km_s):
    """Copy of state with the Moon moving only straight away from Earth."""
    state = copy.deepcopy(state)
    earth, moon = state["bodies"]["earth"], state["bodies"]["moon"]
    direction = np.array(moon["position_km"]) - np.array(earth["position_km"])
    direction /= np.linalg.norm(direction)
    velocity = np.array(earth["velocity_km_s"]) + radial_km_s * direction
    moon["velocity_km_s"] = velocity.tolist()
    return state


def fall_time_days(state):
    """Analytic radial free-fall time of the Moon from rest until the surfaces touch."""
    earth, moon = state["bodies"]["earth"], state["bodies"]["moon"]
    start = math.dist(earth["position_km"], moon["position_km"])
    end = earth["radius_km"] + moon["radius_km"]
    mu = earth["gm_km3_s2"] + moon["gm_km3_s2"]
    f = end / start
    shape = math.acos(math.sqrt(f)) + math.sqrt(f * (1 - f))
    return math.sqrt(start**3 / (2 * mu)) * shape / DAY_S


def main():
    state = load_state()
    config = load_config()
    two_bodies = {**config, "bodies": ["earth", "moon"]}
    passed = True

    falling = moon_with_velocity(state, 0.0)
    result = run(falling, two_bodies)
    expected = fall_time_days(falling)
    actual = result.end_time_s / DAY_S
    ok = (result.outcome == "collision" and result.involved == ("earth", "moon")
          and abs(actual - expected) < 0.05)
    passed &= ok
    print(f"Moon dropped from rest: {result.outcome} {result.involved} after "
          f"{actual:.3f} days (exact: {expected:.3f})  {'PASS' if ok else 'FAIL'}")

    result = run(moon_with_velocity(state, 3.0), config)
    ok = result.outcome == "ejection" and result.involved == ("moon",)
    passed &= ok
    print(f"Moon thrown outward at 3 km/s: {result.outcome} {result.involved} after "
          f"{result.end_time_s / DAY_S:.2f} days  {'PASS' if ok else 'FAIL'}")

    result = run(state, config)
    ok = result.outcome == "survived" and not result.involved
    passed &= ok
    print(f"Real Moon: {result.outcome}  {'PASS' if ok else 'FAIL'}")

    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
