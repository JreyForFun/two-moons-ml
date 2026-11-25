"""Turn second-moon settings into a starting position and velocity.

Settings (see configs/single_run.json):
  mass_lunar        mass, in Moon masses
  distance_lunar    semi-major axis (average size of the orbit), in units of
                    the Moon's average distance, 384,400 km
  eccentricity      shape: 0 is a circle, closer to 1 is more stretched
  inclination_deg   tilt from the plane of Earth's orbit around the Sun
  node_deg          direction in which the tilt goes
  periapsis_deg     direction of the point closest to Earth
  true_anomaly_deg  starting angle, measured from that closest point

The orbit is the one the second moon would follow if only it and Earth existed.
The Sun and the Moon then change it during the simulation.
"""

import copy
import math

import numpy as np

LUNAR_DISTANCE_KM = 384400.0


def orbit_to_vectors(mu, a, e, inclination, node, periapsis, true_anomaly):
    """Position and velocity relative to the central body (angles in radians)."""
    if a <= 0 or not 0 <= e < 1:
        raise ValueError("need a > 0 and 0 <= eccentricity < 1")
    p = a * (1 - e**2)
    r = p / (1 + e * math.cos(true_anomaly))
    # In the flat orbit plane, with x toward the closest point:
    position = r * np.array([math.cos(true_anomaly), math.sin(true_anomaly), 0.0])
    velocity = math.sqrt(mu / p) * np.array(
        [-math.sin(true_anomaly), e + math.cos(true_anomaly), 0.0]
    )
    rotation = _rotate_z(node) @ _rotate_x(inclination) @ _rotate_z(periapsis)
    return rotation @ position, rotation @ velocity


def _rotate_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _rotate_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def add_second_moon(state, settings):
    """Return a copy of state that also contains "moon2"."""
    if settings["mass_lunar"] <= 0:
        raise ValueError("mass_lunar must be positive")
    state = copy.deepcopy(state)
    earth, moon = state["bodies"]["earth"], state["bodies"]["moon"]
    gm = settings["mass_lunar"] * moon["gm_km3_s2"]
    position, velocity = orbit_to_vectors(
        earth["gm_km3_s2"] + gm,
        settings["distance_lunar"] * LUNAR_DISTANCE_KM,
        settings["eccentricity"],
        math.radians(settings["inclination_deg"]),
        math.radians(settings["node_deg"]),
        math.radians(settings["periapsis_deg"]),
        math.radians(settings["true_anomaly_deg"]),
    )
    state["bodies"]["moon2"] = {
        "gm_km3_s2": gm,
        # Same density as the Moon, so the radius grows with the cube root of mass.
        "radius_km": moon["radius_km"] * settings["mass_lunar"] ** (1 / 3),
        "position_km": (np.array(earth["position_km"]) + position).tolist(),
        "velocity_km_s": (np.array(earth["velocity_km_s"]) + velocity).tolist(),
    }
    return state
