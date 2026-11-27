"""Validation of the integration against the JPL Horizons ephemeris of the Moon over one year.

Tolerances were fixed before the first run.

Usage:
    python src/validate_real_system.py
"""

import sys

import numpy as np

from fetch_reference import load_reference
from horizons import load_state
from simulate import DAY_S, load_config, run

REAL_PERIOD_DAYS = 27.32166  # long-term average sidereal month
MAX_ENERGY_ERROR = 1e-12
MAX_PERIOD_ERROR_DAYS = 0.1  # one year does not fully average out perturbations
MAX_PERIOD_DIFFERENCE_DAYS = 0.01  # compared with NASA over the same year
MAX_POSITION_ERROR_KM = 1000.0


def average_period_days(times_s, positions):
    """Mean orbital period, from the total angle swept."""
    angle = np.unwrap(np.arctan2(positions[:, 1], positions[:, 0]))
    trips = (angle[-1] - angle[0]) / (2 * np.pi)
    return (times_s[-1] - times_s[0]) / DAY_S / trips


def compare():
    """Run with and without the Sun and compare both with NASA."""
    state, config = load_state(), load_config()
    times, nasa = load_reference()
    with_sun = run(state, config)
    without_sun = run(state, {**config, "bodies": ["earth", "moon"]})
    for result in (with_sun, without_sun):
        if len(result.times_s) != len(times) or np.abs(result.times_s - times).max() > 1e-3:
            raise RuntimeError("simulation and NASA times do not match")
    return {
        "times_s": times,
        "nasa": nasa,
        "with_sun": with_sun,
        "error_km": np.linalg.norm(with_sun.relative("moon") - nasa, axis=1),
        "error_without_sun_km": np.linalg.norm(without_sun.relative("moon") - nasa, axis=1),
    }


def main():
    c = compare()
    result, error = c["with_sun"], c["error_km"]
    period = average_period_days(c["times_s"], result.relative("moon"))
    nasa_period = average_period_days(c["times_s"], c["nasa"])

    checks = [
        ("Survived the full year", result.outcome == "survived", result.outcome),
        ("Energy error", result.max_energy_error() < MAX_ENERGY_ERROR,
         f"{result.max_energy_error():.1e} (limit {MAX_ENERGY_ERROR:.0e})"),
        ("Average period", abs(period - REAL_PERIOD_DAYS) < MAX_PERIOD_ERROR_DAYS,
         f"{period:.4f} days (long-term real: {REAL_PERIOD_DAYS})"),
        ("Period vs NASA, same year", abs(period - nasa_period) < MAX_PERIOD_DIFFERENCE_DAYS,
         f"{nasa_period:.4f} days, difference {abs(period - nasa_period) * DAY_S:.1f} s"),
        ("Largest position error", error.max() < MAX_POSITION_ERROR_KM,
         f"{error.max():.1f} km (limit {MAX_POSITION_ERROR_KM:.0f} km)"),
    ]
    for label, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")

    print(f"Start error: {error[0]:.1e} km, average {error.mean():.1f} km, end {error[-1]:.1f} km")
    print(f"Baseline without the Sun: largest error {c['error_without_sun_km'].max():,.0f} km")
    passed = all(ok for _, ok, _ in checks)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
