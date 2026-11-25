"""Check that the packages work by simulating one simple orbit.

Run:  venv/Scripts/python src/check_setup.py

A small planet goes around a star exactly once, so it should end where it
started and the total energy should not change.
"""

import math
import sys

import matplotlib
import numpy
import rebound

MAX_POSITION_ERROR = 1e-12  # in units of the orbit's semi-major axis
MAX_ENERGY_ERROR = 1e-13  # relative


def relative_position(sim):
    """Position of the planet as seen from the star."""
    star, planet = sim.particles[0], sim.particles[1]
    return (planet.x - star.x, planet.y - star.y, planet.z - star.z)


def run_test_orbit():
    """Simulate one full orbit. Return (position error, relative energy error)."""
    sim = rebound.Simulation()  # units: G = 1
    sim.integrator = "ias15"
    sim.add(m=1.0)  # star
    sim.add(m=1e-3, a=1.0, e=0.1)  # planet on a slightly stretched orbit
    sim.move_to_com()

    start = relative_position(sim)
    start_energy = sim.energy()
    sim.integrate(sim.particles[1].P)  # P = one orbital period

    position_error = math.dist(start, relative_position(sim))
    energy_error = abs((sim.energy() - start_energy) / start_energy)
    return position_error, energy_error


def main():
    print("Python    ", sys.version.split()[0])
    print("REBOUND   ", rebound.__version__)
    print("NumPy     ", numpy.__version__)
    print("Matplotlib", matplotlib.__version__)

    position_error, energy_error = run_test_orbit()
    passed = position_error < MAX_POSITION_ERROR and energy_error < MAX_ENERGY_ERROR
    print(f"Position error after one orbit: {position_error:.2e}")
    print(f"Relative energy error:          {energy_error:.2e}")
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
