"""Phase 3: apply rules R1-R3 to the training moons and draw the stability maps.

Run:  venv/Scripts/python src/plot_dataset.py

Prints the rule results and saves data/phase3_results.json and figures to figures/.
Rules and binning were fixed before the analysis (docs/report.md, Phase 3).
"""

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

import explore
from horizons import ROOT
from plot_style import (BLUE, GRID, INK, MUTED_INK, ORANGE, SURFACE, add_legend, new_chart,
                        save, set_titles)
from sampling import roche_limit_km
from horizons import load_state
from second_moon import LUNAR_DISTANCE_KM

RESULTS = ROOT / "data" / "phase3_results.json"
PILOT_INTERVAL = (0.12, 0.27)  # 95% Wilson interval of pilot survival (18/100)
PROGRADE_GUIDE_HILL = 0.49  # Domingos et al. (2006), Jupiter-mass planet, circular orbits
RETROGRADE_GUIDE_HILL = 0.93

# Sequential ramps: blue steps 100-700 of the reference palette; a one-hue orange ramp for
# the second sequential context (counts of rare outcomes).
SHARE_CMAP = LinearSegmentedColormap.from_list("share", [
    "#cce3fd", "#9dc8f7", "#6aabf1", "#338ced", "#2370cd", "#1757ac", "#0e3d7e"])
COUNT_CMAP = LinearSegmentedColormap.from_list("count", [
    "#fde4d6", "#f9b994", "#f48f58", "#eb6834", "#c4501f", "#8f3a15"])
for cmap in (SHARE_CMAP, COUNT_CMAP):
    cmap.set_bad(SURFACE)

A_COL, I_COL, E_COL, M_COL = ("input_distance_lunar", "input_inclination_deg",
                              "input_eccentricity", "input_mass_lunar")


def lunar_to_hill(x):
    return np.asarray(x) * LUNAR_DISTANCE_KM / explore.hill_km()


def hill_to_lunar(h):
    return np.asarray(h) * explore.hill_km() / LUNAR_DISTANCE_KM


def interval(values):
    return [float(np.quantile(values, 0.025, method="lower")),
            float(np.quantile(values, 0.975, method="higher"))]


# ---------------------------------------------------------------- rules

def rule_r1(df):
    """Survival share after reweighting to isotropic inclinations."""
    w = explore.isotropic_weights(df)
    shares = {o: explore.weighted_share(df["result_label"] == o, w) for o in explore.OUTCOMES}
    survived = shares["survived"]
    explained = PILOT_INTERVAL[0] <= survived <= PILOT_INTERVAL[1]
    return {"unweighted_survived": float(df["survived"].mean()),
            "reweighted": shares, "effective_sample_size": explore.effective_sample_size(w),
            "pilot_interval": PILOT_INTERVAL, "explained": explained}


def rule_r2(df):
    """Outer survival edge, retrograde minus prograde, with a bootstrap interval."""
    def edges(part):
        return (explore.survival_edge(part[~part["retrograde"]]),
                explore.survival_edge(part[part["retrograde"]]))

    pro, retro = edges(df)
    diffs = explore.bootstrap(df, lambda part: np.subtract(*edges(part)[::-1]))
    low, high = interval(diffs)
    return {"prograde_edge_hill": pro, "retrograde_edge_hill": retro,
            "difference_interval": [low, high], "share_positive": float(np.mean(diffs > 0)),
            "retrograde_farther": low > 0}


def rule_r3(df):
    """Survival in the highest minus the lowest mass bin."""
    bins = explore.BINS[M_COL]

    def difference(part):
        low = part[part[M_COL] < bins[1]]["survived"].mean()
        high = part[part[M_COL] >= bins[-2]]["survived"].mean()
        return high - low

    diffs = explore.bootstrap(df, difference)
    low, high = interval(diffs)
    return {"difference": float(difference(df)), "difference_interval": [low, high],
            "mass_matters": not low <= 0 <= high,
            "table": explore.shares_by_bin(df, M_COL)[
                ["low", "high", "count", "survived", "survived_low", "survived_high"]
            ].to_dict(orient="records")}


def robustness(df):
    return {name: dict(zip(("correlation", "cells"), explore.split_half_agreement(df, x, y)))
            for name, (x, y) in {"distance_x_tilt": (A_COL, I_COL),
                                 "distance_x_eccentricity": (A_COL, E_COL)}.items()}


# ---------------------------------------------------------------- figures

def distance_axis(ax, label=True):
    ax.set_xscale("log")
    ticks = [0.1, 0.2, 0.5, 1, 2, 3]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.minorticks_off()
    ax.set_xlim(explore.BINS[A_COL][0], explore.BINS[A_COL][-1])
    if label:
        ax.set_xlabel("Semi-major axis (lunar distances, log scale)", color=MUTED_INK)


def hill_top_axis(ax):
    top = ax.secondary_xaxis("top", functions=(lunar_to_hill, hill_to_lunar))
    top.set_xticks([0.05, 0.1, 0.2, 0.5], ["0.05", "0.1", "0.2", "0.5"])
    top.minorticks_off()
    top.tick_params(colors=MUTED_INK, length=0)
    top.spines["top"].set_visible(False)
    top.set_xlabel("Hill radii", color=MUTED_INK, fontsize=9)
    return top


def guide_lines(ax, tilt=True):
    half_hill = hill_to_lunar(0.5)
    ax.axvline(1.0, color=INK, linewidth=1, linestyle="--")
    ax.axvline(half_hill, color=INK, linewidth=1, linestyle=":")
    if tilt:
        ax.axhline(90, color=INK, linewidth=0.8)


def map_titles(fig, ax, title, subtitle):
    """Title above the figure; subtitle placed by matplotlib above the top Hill-radius axis."""
    fig.suptitle(title, x=0.02, ha="left", color=INK, fontsize=14, fontweight="bold")
    ax.set_title(subtitle, loc="left", color=MUTED_INK, fontsize=10)


def line_legend(fig, entries):
    handles = [Line2D([], [], color=INK, linewidth=1.2, linestyle=style, label=label)
               for style, label in entries]
    fig.legend(handles=handles, loc="outside lower center", ncols=len(handles), frameon=False,
               labelcolor=INK, fontsize=9)


def colorbar(fig, mesh, ax, label):
    bar = fig.colorbar(mesh, ax=ax, shrink=0.8, pad=0.03)
    bar.set_label(label, color=MUTED_INK)
    bar.ax.tick_params(colors=MUTED_INK, length=0)
    bar.outline.set_visible(False)


def draw_map(ax, df, y, outcome="survived", cmap=SHARE_CMAP, values=None, vmax=1.0):
    share, count = explore.grid_shares(df, A_COL, y, outcome)
    data = share if values is None else values(df, y, count)
    mesh = ax.pcolormesh(explore.BINS[A_COL], explore.BINS[y], data, cmap=cmap,
                         vmin=0, vmax=vmax, edgecolors=SURFACE, linewidth=1.5)
    ax.grid(False)
    return mesh, count


def stability_map(df):
    fig, ax = new_chart(8.5, 6.2)
    mesh, count = draw_map(ax, df, I_COL)
    distance_axis(ax)
    hill_top_axis(ax)
    ax.set_yticks(range(0, 181, 30))
    ax.set_ylabel("Inclination (degrees)", color=MUTED_INK)
    guide_lines(ax)
    for yy, text in ((97, "retrograde"), (83, "prograde")):
        ax.annotate(text, (1, yy), xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", color=MUTED_INK, fontsize=9, va="center",
                    annotation_clip=False)
    colorbar(fig, mesh, ax, "Share surviving 100 years")
    line_legend(fig, (("--", "Moon's orbit"), (":", "Half of Earth's Hill radius")))
    filled = count[count >= explore.MIN_CELL]
    map_titles(fig, ax, "Which second moons survive 100 years?",
               f"{len(df):,} training moons in {filled.size} cells "
               f"({int(filled.min())} to {int(filled.max())} moons each)")
    return fig


def outcome_maps(df):
    fig, axes = new_chart(11, 8.2, rows=2, cols=2, sharex=True, sharey=True)
    panels = (("survived", "Survived 100 years"), ("ejected", "Ejected"),
              ("hit_earth", "Collided with Earth"))
    mesh = None
    for ax, (outcome, title) in zip(axes.flat, panels):
        mesh, _ = draw_map(ax, df, I_COL, outcome)
        ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")

    def rare_counts(part, y, count):
        rare = part[part["result_label"].isin(["hit_moon", "moon_lost"])]
        _, rare_count = explore.grid_shares(rare.assign(result_label="x"), A_COL, y, "x")
        return np.where(count >= explore.MIN_CELL, rare_count, np.nan)

    rare_ax = axes[1, 1]
    rare_mesh, _ = draw_map(rare_ax, df, I_COL, cmap=COUNT_CMAP, values=rare_counts, vmax=None)
    rare_ax.set_title("Collided with the Moon, or Moon lost (count)", loc="left", color=INK,
                      fontsize=11, fontweight="bold")
    for ax in axes.flat:
        distance_axis(ax, label=ax in axes[1])
        ax.set_yticks(range(0, 181, 45))
        guide_lines(ax)
    for ax in axes[:, 0]:
        ax.set_ylabel("Inclination (degrees)", color=MUTED_INK)
    for target, m, label in ((axes[:, 1], mesh, "Share of moons"),
                             ([rare_ax], rare_mesh, "Moons")):
        bar = fig.colorbar(m, ax=list(np.atleast_1d(target)) if m is rare_mesh else axes[0, :],
                           shrink=0.85)
        bar.set_label(label, color=MUTED_INK)
        bar.ax.tick_params(colors=MUTED_INK, length=0)
        bar.outline.set_visible(False)
    fig.suptitle("What happens to second moons, by orbit", x=0.02, ha="left", color=INK,
                 fontsize=14, fontweight="bold")
    return fig


def eccentricity_map(df):
    fig, ax = new_chart(8.5, 6.0)
    mesh, count = draw_map(ax, df, E_COL)
    distance_axis(ax)
    hill_top_axis(ax)
    ax.set_ylabel("Eccentricity", color=MUTED_INK)
    a = np.geomspace(0.1, 3, 400)
    roche = roche_limit_km(load_state()) / LUNAR_DISTANCE_KM
    inner, outer = a[a < 1], a[a > 1]
    ax.plot(inner, 1 / inner - 1, color=INK, linewidth=1.5, linestyle="--")  # apoapsis = Moon
    ax.plot(outer, 1 - 1 / outer, color=INK, linewidth=1.5, linestyle="--")  # periapsis = Moon
    ax.plot(a, 1 - roche / a, color=INK, linewidth=1.5, linestyle=":")
    ax.annotate("orbits crossing\nthe Moon's orbit", (1.0, 0.70), ha="center", fontsize=9,
                color=INK, bbox={"boxstyle": "round,pad=0.3", "fc": SURFACE, "ec": GRID})
    ax.set_ylim(0, 0.8)
    colorbar(fig, mesh, ax, "Share surviving 100 years")
    line_legend(fig, (("--", "Orbit touches the Moon's orbit"),
                      (":", "Periapsis at the Roche limit (closer orbits excluded)")))
    map_titles(fig, ax, "Orbits that cross the Moon's rarely survive",
               f"{len(df):,} training moons; blank cells hold fewer than {explore.MIN_CELL}")
    return fig


def direction_plot(df, r2):
    fig, ax = new_chart(8.5, 5.0)
    for retro, color, name in ((False, BLUE, "Prograde"), (True, ORANGE, "Retrograde")):
        table = explore.shares_by_bin(df[df["retrograde"] == retro], A_COL)
        centers = lunar_to_hill(np.sqrt(table["low"] * table["high"]))
        ax.fill_between(centers, table["survived_low"] * 100, table["survived_high"] * 100,
                        color=color, alpha=0.18, linewidth=0)
        ax.plot(centers, table["survived"] * 100, color=color, linewidth=2, marker="o",
                markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label=f"{name} ({len(table) and int(table['count'].sum()):,} moons)")
    pro, retro_edge = r2["prograde_edge_hill"], r2["retrograde_edge_hill"]
    if pro == retro_edge:
        ax.axvline(pro, color=INK, linewidth=1.2, linestyle="--")
        ax.annotate("10% survival edge,\nboth directions", (pro, 96), xytext=(-4, 0),
                    textcoords="offset points", ha="right", va="top", fontsize=8, color=INK)
    else:
        for edge, color in ((pro, BLUE), (retro_edge, ORANGE)):
            if np.isfinite(edge):
                ax.axvline(edge, color=color, linewidth=1.5, linestyle="--")
    moon_hill = float(lunar_to_hill(1.0))
    ax.axvline(moon_hill, color=INK, linewidth=1, linestyle="-")
    ax.annotate("Moon", (moon_hill, 96), xytext=(4, 0), textcoords="offset points",
                va="top", fontsize=8, color=INK)
    ax.axvline(PROGRADE_GUIDE_HILL, color=MUTED_INK, linewidth=1, linestyle=":")
    ax.annotate("prograde stability limit\nfor a Jupiter-mass planet", (PROGRADE_GUIDE_HILL, 55),
                xytext=(-4, 0), textcoords="offset points", ha="right", va="top",
                fontsize=8, color=MUTED_INK)
    ax.set_xscale("log")
    ticks = [0.03, 0.05, 0.1, 0.2, 0.5, 0.8]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.minorticks_off()
    ax.set_ylim(0, 100)
    ax.set_xlabel("Semi-major axis (Hill radii, log scale)", color=MUTED_INK)
    ax.set_ylabel("Surviving 100 years (%)", color=MUTED_INK)
    add_legend(ax, loc="lower left")
    set_titles(ax, "Beyond the Moon, only retrograde second moons survive",
               "Training moons by semi-major axis bin; bands are 95% Wilson intervals")
    return fig


def main():
    df = explore.load_dataset("train")
    results = {"moons": len(df), "r1": rule_r1(df), "r2": rule_r2(df), "r3": rule_r3(df),
               "robustness": robustness(df),
               "direction": {name: {"moons": int(len(part)), "survived": float(part["survived"].mean())}
                             for name, part in (("prograde", df[~df["retrograde"]]),
                                                ("retrograde", df[df["retrograde"]]))},
               "eccentricity_table": explore.shares_by_bin(df, E_COL)[
                   ["low", "high", "count", "survived", "survived_low", "survived_high"]
               ].to_dict(orient="records")}
    RESULTS.write_text(json.dumps(results, indent=2, default=float) + "\n", encoding="utf-8")

    r1, r2, r3 = results["r1"], results["r2"], results["r3"]
    print(f"TRAINING MOONS: {len(df):,}")
    print("\nR1  Pilot vs full dataset")
    print(f"    Survival as sampled: {r1['unweighted_survived']:.1%}; reweighted to isotropic "
          f"inclinations: {r1['reweighted']['survived']:.1%} "
          f"(effective sample size {r1['effective_sample_size']:,.0f})")
    print(f"    Pilot interval 12% to 27%: {'explained' if r1['explained'] else 'NOT explained'}")
    print("    Reweighted shares: " + ", ".join(f"{k} {v:.1%}" for k, v in r1["reweighted"].items()))
    print("\nR2  Outer survival edge (Hill radii)")
    print(f"    Prograde {r2['prograde_edge_hill']:.3f}, retrograde {r2['retrograde_edge_hill']:.3f}")
    print(f"    Difference 95% interval {r2['difference_interval'][0]:.3f} to "
          f"{r2['difference_interval'][1]:.3f} ({r2['share_positive']:.1%} of resamples > 0): "
          f"{'retrograde farther' if r2['retrograde_farther'] else 'not shown'}")
    print("\nR3  Mass (highest minus lowest bin)")
    print(f"    Difference {r3['difference']:+.1%}, 95% interval {r3['difference_interval'][0]:+.1%} "
          f"to {r3['difference_interval'][1]:+.1%}: {'mass matters' if r3['mass_matters'] else 'no clear effect'}")
    for row in r3["table"]:
        print(f"    {row['low']:.4f}-{row['high']:.4f}: {row['count']:5d} moons, survived "
              f"{row['survived']:.1%} ({row['survived_low']:.1%} to {row['survived_high']:.1%})")
    print("\nDESCRIPTIVE")
    for name, d in results["direction"].items():
        print(f"    {name}: {d['moons']:,} moons, survived {d['survived']:.1%}")
    for row in results["eccentricity_table"]:
        print(f"    e {row['low']:.1f}-{row['high']:.1f}: {row['count']:5d} moons, survived {row['survived']:.1%}")
    for name, r in results["robustness"].items():
        print(f"    Split-half agreement, {name}: r = {r['correlation']:.3f} over {r['cells']} cells")

    plt.switch_backend("Agg")
    save(stability_map(df), "stability_map.png")
    save(outcome_maps(df), "outcome_maps.png")
    save(eccentricity_map(df), "stability_map_eccentricity.png")
    save(direction_plot(df, r2), "survival_by_direction.png")
    print(f"Saved data/{RESULTS.name}")


if __name__ == "__main__":
    main()
