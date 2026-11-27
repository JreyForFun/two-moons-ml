"""N-body integration of the Sun, Earth, Moon and an optional second moon with REBOUND (IAS15).

Units are km and s, with gravitational parameters GM in place of masses (G = 1).

Usage:
    python src/simulate.py [configs/real_system.json]
"""

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rebound

from horizons import ROOT, load_state
from second_moon import add_second_moon

DEFAULT_CONFIG = ROOT / "configs" / "real_system.json"
DAY_S = 86400.0


@dataclass
class Result:
    """One finished run. Arrays stop at the moment the run ended."""

    bodies: list  # names, in the same order as the position array
    times_s: np.ndarray  # (n,)
    positions_km: np.ndarray  # (n, bodies, 3)
    energy: np.ndarray  # (n,)
    outcome: str  # "survived", "collision", "ejection" or "timeout"
    involved: tuple  # names of the bodies that collided or were ejected
    end_time_s: float

    def relative(self, body, center="earth"):
        """Positions of body as seen from center, shape (n, 3)."""
        b, c = self.bodies.index(body), self.bodies.index(center)
        return self.positions_km[:, b] - self.positions_km[:, c]

    def max_energy_error(self):
        return float(np.max(np.abs((self.energy - self.energy[0]) / self.energy[0])))


@dataclass
class Summary:
    """Outcome of a run, without the trajectory."""

    outcome: str
    involved: tuple
    end_time_s: float  # simulated time
    computing_s: float  # wall-clock seconds


def load_config(path=DEFAULT_CONFIG):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def output_times(config):
    """Output times in seconds, including 0 and the end."""
    steps = config["duration_days"] * 24 / config["output_interval_hours"]
    if abs(steps - round(steps)) > 1e-9:
        raise ValueError("duration must be a whole number of output intervals")
    return np.arange(round(steps) + 1) * config["output_interval_hours"] * 3600.0


def build_simulation(state, config):
    """Create the REBOUND simulation from starting states."""
    sim = rebound.Simulation()
    sim.G = 1.0
    sim.integrator = config["integrator"]
    if "epsilon" in config:  # IAS15 accuracy; REBOUND's default is 1e-9
        sim.integrator.epsilon = config["epsilon"]
    sim.dt = 3600.0  # first guess only: IAS15 chooses its own steps
    for name in config["bodies"]:
        body = state["bodies"][name]
        x, y, z = body["position_km"]
        vx, vy, vz = body["velocity_km_s"]
        sim.add(m=body["gm_km3_s2"], r=body["radius_km"],
                x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
    sim.move_to_com()
    return sim


def find_ejected(sim, config):
    """Name of a moon that is far from Earth and not bound to it, or None.

    Only checked at output times. The Sun and Earth are never counted.
    """
    names = config["bodies"]
    earth = sim.particles[names.index("earth")]
    for i, name in enumerate(names):
        if name in ("sun", "earth"):
            continue
        moon = sim.particles[i]
        d = moon - earth
        distance = math.sqrt(d.x**2 + d.y**2 + d.z**2)
        speed_squared = d.vx**2 + d.vy**2 + d.vz**2
        orbit_energy = speed_squared / 2 - (earth.m + moon.m) / distance
        if distance > config["ejection_distance_km"] and orbit_energy > 0:
            return name
    return None


def _simulate(state, config):
    """Advance one simulation, yielding (sim, outcome, involved) at every output.

    The outcome is None until the last output of the run.
    """
    if "moon2" in config["bodies"] and "second_moon" in config:
        state = add_second_moon(state, config["second_moon"])
    names = list(config["bodies"])
    sim = build_simulation(state, config)
    collided = []

    def on_collision(sim_pointer, collision):
        if not collided:
            collided.append((names[collision.p1], names[collision.p2]))
        sim_pointer.contents.stop()
        return 0  # keep both particles

    # "line" checks the path during each step, so fast bodies cannot jump
    # through each other between steps.
    sim.collision = "line"
    sim.collision_resolve = on_collision

    started = time.perf_counter()
    max_seconds = config.get("max_seconds", math.inf)
    outputs = output_times(config)
    for i, t in enumerate(outputs):
        sim.integrate(t)
        if collided:
            yield sim, "collision", tuple(sorted(collided[0]))
            return
        ejected = find_ejected(sim, config)
        if ejected:
            yield sim, "ejection", (ejected,)
            return
        if i == len(outputs) - 1:
            yield sim, "survived", ()
            return
        if time.perf_counter() - started > max_seconds:
            yield sim, "timeout", ()
            return
        yield sim, None, ()


def run(state, config):
    """Run one simulation and keep the whole trajectory."""
    times, positions, energy = [], [], []
    for sim, outcome, involved in _simulate(state, config):
        times.append(sim.t)
        positions.append([[p.x, p.y, p.z] for p in sim.particles])
        energy.append(sim.energy())
    return Result(list(config["bodies"]), np.array(times), np.array(positions),
                  np.array(energy), outcome, involved, times[-1])


def run_summary(state, config):
    """Run one simulation and return only its outcome (no trajectory)."""
    started = time.perf_counter()
    for sim, outcome, involved in _simulate(state, config):
        pass
    return Summary(outcome, involved, float(sim.t), time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", nargs="?", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    started = time.perf_counter()
    result = run(load_state(), load_config(args.config))
    seconds = time.perf_counter() - started
    print(f"Outcome: {result.outcome} {' + '.join(result.involved)}".rstrip())
    print(f"Simulated: {result.end_time_s / DAY_S:.2f} days, {len(result.times_s)} outputs")
    for name in result.bodies:
        if name not in ("sun", "earth"):
            distance = np.linalg.norm(result.relative(name), axis=1)
            print(f"Distance from Earth, {name}: "
                  f"{distance.min():,.0f} to {distance.max():,.0f} km")
    print(f"Max relative energy error: {result.max_energy_error():.1e}")
    print(f"Computing time: {seconds:.1f} s")

    output = ROOT / "data" / f"{args.config.stem}.npz"
    output.parent.mkdir(exist_ok=True)
    np.savez_compressed(output, bodies=result.bodies, times_s=result.times_s,
                        positions_km=result.positions_km, energy=result.energy,
                        outcome=result.outcome, involved=result.involved,
                        end_time_s=result.end_time_s)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
