"""Check the saved NASA starting data.

Run:            venv/Scripts/python src/check_initial_state.py
With internet:  venv/Scripts/python src/check_initial_state.py --online

The normal run compares the saved data with astropy's built-in (less precise)
ephemeris. --online also asks Horizons again, directly in km.
"""

import argparse
import math
import sys
import urllib.request

import astropy.units as u
import numpy as np
from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
from astropy.time import Time
from astropy.utils import iers

from horizons import load_state

AU_KM = 149597870.7
OBLIQUITY = math.radians(84381.448 / 3600)  # J2000 ecliptic tilt
MAX_ASTROPY_DIFFERENCE_KM = 100.0
MAX_ONLINE_DIFFERENCE_KM = 1e-6


def relative_state(state, body, center):
    """Position (km) and velocity (km/s) of body as seen from center."""
    b, c = state["bodies"][body], state["bodies"][center]
    position = np.array(b["position_km"]) - np.array(c["position_km"])
    velocity = np.array(b["velocity_km_s"]) - np.array(c["velocity_km_s"])
    return position, velocity


def moon_orbit(state):
    """Moon's two-body orbit at this instant, ignoring the Sun."""
    r, v = relative_state(state, "moon", "earth")
    mu = state["bodies"]["earth"]["gm_km3_s2"] + state["bodies"]["moon"]["gm_km3_s2"]
    distance = np.linalg.norm(r)
    a = 1 / (2 / distance - v @ v / mu)
    h = np.cross(r, v)
    e = np.linalg.norm(np.cross(v, h) / mu - r / distance)
    return {
        "distance_km": distance,
        "semi_major_axis_km": a,
        "eccentricity": e,
        "inclination_deg": math.degrees(math.acos(h[2] / np.linalg.norm(h))),
        "period_days": 2 * math.pi * math.sqrt(a**3 / mu) / 86400,
    }


def astropy_differences(state):
    """Distance in km between the saved positions and astropy's positions."""
    iers.conf.auto_download = False
    epoch = Time(state["epoch_jd_tdb"], format="jd", scale="tdb")
    cos, sin = math.cos(OBLIQUITY), math.sin(OBLIQUITY)
    to_ecliptic = np.array([[1, 0, 0], [0, cos, sin], [0, -sin, cos]])
    with solar_system_ephemeris.set("builtin"):
        pos = {
            name: to_ecliptic @ get_body_barycentric(name, epoch).xyz.to_value(u.km)
            for name in ("sun", "earth", "moon")
        }
    pairs = {"Earth-Moon": ("moon", "earth"), "Earth-Sun": ("earth", "sun")}
    return {
        label: float(np.linalg.norm(pos[b] - pos[c] - relative_state(state, b, c)[0]))
        for label, (b, c) in pairs.items()
    }


def online_difference(body):
    """Largest position difference (km) from a fresh Horizons request in km."""
    url = body["query_url"].replace("OUT_UNITS=AU-D", "OUT_UNITS=KM-S")
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode()
    row = text.split("$$SOE")[1].split("$$EOE")[0].strip().split(",")
    fresh = np.array([float(value) for value in row[2:5]])
    return float(np.abs(fresh - np.array(body["position_km"])).max())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--online", action="store_true", help="also ask Horizons again")
    args = parser.parse_args()

    state = load_state()
    print(f"Date: {state['epoch_tdb']} TDB")
    sun_distance = np.linalg.norm(relative_state(state, "earth", "sun")[0])
    print(f"Earth-Sun distance: {sun_distance / AU_KM:.4f} AU")

    orbit = moon_orbit(state)
    print(f"Earth-Moon distance: {orbit['distance_km']:,.0f} km")
    print("Moon's orbit at this instant:")
    print(f"  Semi-major axis: {orbit['semi_major_axis_km']:,.0f} km")
    print(f"  Eccentricity:    {orbit['eccentricity']:.4f}")
    print(f"  Inclination:     {orbit['inclination_deg']:.2f} deg")
    print(f"  Period:          {orbit['period_days']:.3f} days")

    passed = True
    print("Difference from astropy:")
    for label, difference in astropy_differences(state).items():
        passed &= difference < MAX_ASTROPY_DIFFERENCE_KM
        print(f"  {label}: {difference:.1f} km")

    if args.online:
        print("Difference from a new Horizons request:")
        for name, body in state["bodies"].items():
            difference = online_difference(body)
            passed &= difference < MAX_ONLINE_DIFFERENCE_KM
            print(f"  {name}: {difference:.1e} km")

    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
