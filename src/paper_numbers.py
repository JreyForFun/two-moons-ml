"""Print the derived numbers quoted in the paper, so each can be traced to code.

Run:  venv/Scripts/python src/paper_numbers.py
"""

import json
import math

import numpy as np

from analyze_pilot import agreement, label_at, load, wilson
from horizons import ROOT, load_state
from sampling import roche_limit_km
from second_moon import LUNAR_DISTANCE_KM


def hill_radius_km(state):
    """Earth's Hill radius from the saved starting state, r_H = a (m / 3M)^(1/3)."""
    bodies = state["bodies"]
    sun, earth, moon = bodies["sun"], bodies["earth"], bodies["moon"]
    a = np.linalg.norm(np.array(earth["position_km"]) - np.array(sun["position_km"]))
    m = earth["gm_km3_s2"] + moon["gm_km3_s2"]
    return a * (m / (3 * sun["gm_km3_s2"])) ** (1 / 3), a


def main():
    state = load_state()
    config = json.loads((ROOT / "configs" / "dataset.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "configs" / "dataset_manifest.json").read_text(encoding="utf-8"))

    r_hill, a_sun = hill_radius_km(state)
    low, high = config["sampling"]["distance_lunar"]
    print("GEOMETRY")
    print(f"  Earth-Sun distance at epoch      {a_sun:,.0f} km")
    print(f"  Earth Hill radius                {r_hill:,.0f} km")
    print(f"  Semi-major axis range            {low * LUNAR_DISTANCE_KM:,.0f} to "
          f"{high * LUNAR_DISTANCE_KM:,.0f} km")
    print(f"                                   {low * LUNAR_DISTANCE_KM / r_hill:.3f} to "
          f"{high * LUNAR_DISTANCE_KM / r_hill:.3f} Hill radii")
    print(f"  Half a Hill radius               {r_hill / 2:,.0f} km = "
          f"{r_hill / 2 / LUNAR_DISTANCE_KM:.2f} lunar distances")
    print(f"  Moon's distance                  {LUNAR_DISTANCE_KM / r_hill:.3f} Hill radii")
    print(f"  Ejection threshold               {config['ejection_distance_km'] / r_hill:.2f} Hill radii")
    print(f"  Roche limit                      {roche_limit_km(state):,.0f} km")

    print("\nFULL DATASET")
    n = manifest["rows"]
    for label, count in manifest["labels"].items():
        if count:
            lo, hi = wilson(count, n)
            print(f"  {label:10s} {count:6,d}  {count / n:6.1%}  (95% {lo:.1%} to {hi:.1%})")

    print("\nPILOT")
    a, b, c = load("pilot"), load("pilot_strict"), load("pilot_shift")
    for years in (10, 30, 100):
        alive = sum(label_at(r, years) == "survived" for r in a.values())
        lo, hi = wilson(alive, len(a))
        print(f"  Survived {years:3d} years            {alive}/{len(a)}  (95% {lo:.0%} to {hi:.0%})")
    for name, other in (("1 m displacement", c), ("tolerance 1e-11", b)):
        same, total = agreement(a, other, 100)
        lo, hi = wilson(same, total)
        print(f"  Agreement, {name:17s} {same}/{total}  (95% {lo:.0%} to {hi:.0%})")
    flat = sum(float(r["input_inclination_deg"]) < 40 for r in a.values())
    print(f"  Inclination below 40 degrees     {flat}/{len(a)}")
    expected = (1 - math.cos(math.radians(40))) / 2
    print(f"  Expected under isotropic         {expected:.1%}; uniform in degrees {40 / 180:.1%}")


if __name__ == "__main__":
    main()
