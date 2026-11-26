"""Draw random second moons.

Every moon has its own random generator made from (seed, id), so moon 57 is the
same no matter which other moons are drawn or in which order.
"""

import math

import numpy as np

from second_moon import LUNAR_DISTANCE_KM, add_second_moon

ROCHE_FACTOR = 2.44  # fluid body
MAX_DRAWS = 10000


def roche_limit_km(state):
    """Closer to Earth than this, a moon with our Moon's density is torn apart."""
    earth, moon = state["bodies"]["earth"], state["bodies"]["moon"]
    mass_ratio = earth["gm_km3_s2"] / moon["gm_km3_s2"]
    return ROCHE_FACTOR * moon["radius_km"] * mass_ratio ** (1 / 3)


def _log_uniform(rng, low, high):
    return float(math.exp(rng.uniform(math.log(low), math.log(high))))


def _draw_tilt(rng, ranges):
    """Tilt in degrees.

    "isotropic" (the default, used by the pilot): uniform in cos(tilt), so every
    direction in space is equally likely. Few orbits are then nearly flat.
    "uniform_degrees": every tilt angle is equally likely, which covers flat
    orbits better but over-represents them compared with random directions.
    """
    low, high = ranges["inclination_deg"]
    rule = ranges.get("tilt_distribution", "isotropic")
    if rule == "uniform_degrees":
        return float(rng.uniform(low, high))
    if rule == "isotropic":
        cos_tilt = rng.uniform(math.cos(math.radians(high)), math.cos(math.radians(low)))
        return math.degrees(math.acos(cos_tilt))
    raise ValueError(f"unknown tilt_distribution: {rule}")


def _draw(rng, ranges):
    # The tilt is drawn first. Changing this order would change every moon,
    # including those already simulated in the pilot.
    tilt = _draw_tilt(rng, ranges)
    return {
        "mass_lunar": _log_uniform(rng, *ranges["mass_lunar"]),
        "distance_lunar": _log_uniform(rng, *ranges["distance_lunar"]),
        "eccentricity": float(rng.uniform(*ranges["eccentricity"])),
        "inclination_deg": tilt,
        "node_deg": float(rng.uniform(0, 360)),
        "periapsis_deg": float(rng.uniform(0, 360)),
        "true_anomaly_deg": float(rng.uniform(0, 360)),
    }


def closest_point_km(settings):
    return settings["distance_lunar"] * LUNAR_DISTANCE_KM * (1 - settings["eccentricity"])


def sample_settings(state, config, moon_id):
    """Return (settings, redraws). Orbits that go inside the Roche limit are redrawn."""
    rng = np.random.default_rng([config["seed"], moon_id])
    limit = roche_limit_km(state)
    for redraws in range(MAX_DRAWS):
        settings = _draw(rng, config["sampling"])
        if closest_point_km(settings) >= limit:
            return settings, redraws
    raise RuntimeError("no valid moon found; check the sampling ranges")


def build_case(state, config, moon_id):
    """Return (state with moon2, settings, redraws) for one random moon.

    The optional config key "shift_m" moves moon2 by that many meters along x.
    It is used to measure how sensitive the outcomes are.
    """
    settings, redraws = sample_settings(state, config, moon_id)
    case = add_second_moon(state, settings)
    case["bodies"]["moon2"]["position_km"][0] += config.get("shift_m", 0.0) / 1000
    return case, settings, redraws
