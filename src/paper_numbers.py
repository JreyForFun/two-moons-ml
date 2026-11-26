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
    phase4()


def phase4():
    """Phase 4 numbers, read from data/phase4/ and data/phase4_analysis.json."""
    folder = ROOT / "data" / "phase4"
    analysis_path = ROOT / "data" / "phase4_analysis.json"
    if not (folder / "decisions.json").exists() or not analysis_path.exists():
        print("\nPHASE 4: run train_models.py and analyze_models.py first")
        return
    decisions = json.loads((folder / "decisions.json").read_text(encoding="utf-8"))
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    fs = decisions["P1"]["chosen"]

    def run(key):
        return json.loads((folder / f"{key}.json").read_text(encoding="utf-8"))

    print(f"\nPHASE 4 (training moons, out-of-fold)")
    for key, name in (("majority", "Majority class"), ("physics_rule", "Physics rule"),
                      (f"logistic_{fs}", "Logistic regression"),
                      (f"random_forest_{fs}", "Random Forest"), (f"xgboost_{fs}", "XGBoost"),
                      (f"mlp_{fs}", "MLP")):
        r = run(key)
        m, spread = r["metrics"], r["fold_spread"]["macro_f1"]
        print(f"  {name:20s} macro-F1 {m['macro_f1']:.3f} (folds {spread[0]:.3f} +/- {spread[1]:.3f}), "
              f"balanced acc {m['balanced_accuracy']:.3f}, accuracy {m['accuracy']:.3f}, "
              f"log loss {m['log_loss']:.3f}, {r['seconds'] / 60:.1f} min")
    for name, g in decisions["P1"]["gains_over_F1"].items():
        print(f"  P1 {name} minus F1: {g['mean']:+.4f} ({g['interval'][0]:+.4f} to {g['interval'][1]:+.4f}); "
              f"chosen {fs}")
    for name, g in decisions["P2"]["gaps"].items():
        print(f"  P2 {decisions['P2']['highest']} minus {name}: {g['mean']:+.4f} "
              f"({g['interval'][0]:+.4f} to {g['interval'][1]:+.4f}); selected {decisions['P2']['selected']}")
    p3, p6 = decisions["P3"], decisions["P6"]
    print(f"  P3 balanced-accuracy gain over physics rule {p3['mean']:+.4f} "
          f"({p3['interval'][0]:+.4f} to {p3['interval'][1]:+.4f})")
    print(f"  P6 ECE {p6['ece']:.4f}; calibrated: {p6['calibrated']}")
    m, iso = analysis["metrics"], analysis["metrics_isotropic"]
    print(f"  Selected: recall {[round(v, 3) for v in m['recall']]}, precision "
          f"{[round(v, 3) for v in m['precision']]}")
    print(f"  Selected binary: AUC {m['survived_auc']:.3f}, accuracy {m['survived_accuracy']:.3f}, "
          f"ECE {m['survived_ece']:.4f}; 4-class Brier {m['brier']:.3f}")
    print(f"  Isotropic-weighted: macro-F1 {iso['macro_f1']:.3f}, accuracy {iso['accuracy']:.3f}, "
          f"AUC {iso['survived_auc']:.3f}")
    c, p5, p4 = analysis["chaos"], analysis["P5"], analysis["P4"]
    print(f"  Chaos twins {c['moons']}: agreement {c['agreement']:.3f} {c['agreement_interval']}, "
          f"binary {c['binary_agreement']:.3f}")
    print(f"  P5 error chaotic {p5['error_chaotic']:.3f} ({p5['chaotic_moons']}), stable "
          f"{p5['error_stable']:.3f}, interval {p5['difference_interval']}")
    print(f"  P4 rare recall {p4['recall']:.3f} {p4['interval']}, sub {p4['sub_recall']}")
    first, last = analysis["learning_curve"][0], analysis["learning_curve"][-1]
    print(f"  Learning curve {first['moons']:.0f} -> {last['moons']:.0f} moons: macro-F1 "
          f"{first['macro_f1'][0]:.3f} -> {last['macro_f1'][0]:.3f}, rare recall "
          f"{first['rare_recall'][0]:.3f} -> {last['rare_recall'][0]:.3f}")
    print("  Importance: " + ", ".join(f"{g} {v[0]:.3f}" for g, v in sorted(
        analysis["importance"].items(), key=lambda kv: -kv[1][0])))
    life = run(f"lifetime_{decisions['P2']['selected']}_{fs}")
    print(f"  Lifetime: macro-F1 {life['metrics']['macro_f1']:.3f}, accuracy "
          f"{life['metrics']['accuracy']:.3f}, within one bin {life['within_one_bin']:.3f}; "
          f"shares {decisions['lifetime_shares']}")
    selected = json.loads((ROOT / "configs" / "selected_model.json").read_text(encoding="utf-8"))
    print(f"  Final settings {selected['params']}; Phase 5 C1 interval "
          f"{selected['phase5_criteria']['C1_generalization']['interval']}")


if __name__ == "__main__":
    main()
