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
    phase3()


def phase3():
    """Phase 3 numbers, read from the outputs of plot_dataset.py, compare_pilot.py and
    survival_curve.py (run those first)."""
    files = {name: ROOT / "data" / f"{name}.json"
             for name in ("phase3_results", "compare_pilot", "survival_curve")}
    if not all(path.exists() for path in files.values()):
        print("\nPHASE 3: run plot_dataset.py, compare_pilot.py and survival_curve.py first")
        return
    p3, cp, sc = (json.loads(path.read_text(encoding="utf-8")) for path in files.values())
    r1, r2, r3, d = p3["r1"], p3["r2"], p3["r3"], p3["descriptive"]
    print(f"\nPHASE 3 (training moons: {p3['moons']:,})")
    print(f"  R1 survival as sampled {r1['unweighted_survived']:.1%}, isotropic "
          f"{r1['reweighted']['survived']:.1%} (ESS {r1['effective_sample_size']:,.0f}); "
          f"pilot expected {cp['expected']:.1f}, observed {cp['observed']}, "
          f"{cp['gap_sigma']:+.1f} sigma; reruns identical {cp['rerun_identical']}/{cp['rerun']}")
    print("  R1 isotropic shares: " + ", ".join(f"{k} {v:.1%}" for k, v in r1["reweighted"].items()))
    print(f"  R2 edges {r2['prograde_edge_hill']:.3f} / {r2['retrograde_edge_hill']:.3f} Hill radii, "
          f"interval {r2['difference_interval'][0]:.3f} to {r2['difference_interval'][1]:.3f}")
    print(f"  R3 mass difference {r3['difference']:+.1%} "
          f"({r3['difference_interval'][0]:+.1%} to {r3['difference_interval'][1]:+.1%})")
    lo, hi = sc["loss_100_1000_interval"]
    print(f"  R4 loss 10-100 yr {sc['loss_10_100']:.1%}; 100-1,000 yr {sc['loss_100_1000']:.1%} "
          f"({lo:.1%} to {hi:.1%}); alive at 1,000 yr {sc['alive_1000']:.1%}")
    for name in ("inner_low_tilt", "inner_polar", "crossing_moon_orbit", "inside_moon_orbit",
                 "beyond_moon_prograde", "beyond_moon_retrograde"):
        print(f"  {name:24s} {d[name]['moons']:5,d} moons, survived {d[name]['survived']:.1%}, "
              f"hit Earth {d[name]['hit_earth']:.1%}, ejected {d[name]['ejected']:.1%}")
    heavy = d["mass_outcomes"]["heaviest"]
    print(f"  Heaviest mass bin: moon_lost {heavy['moon_lost']:.1%}, hit_earth {heavy['hit_earth']:.1%}")
    rb = p3["robustness"]
    print("  Split-half r: " + ", ".join(f"{k} {v['correlation']:.3f}" for k, v in rb.items()))


if __name__ == "__main__":
    main()
