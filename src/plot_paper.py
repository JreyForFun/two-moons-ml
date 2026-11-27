"""Print-size figures for the manuscripts (paper/figures/).

Figures are drawn at journal column (3.4 in) or page width as vector PDFs, without titles (the
captions carry them) and with text of 6.5 to 8 pt. Includes the two-panel figure of the Research
Notes version. The screen figures in figures/ are not changed.

Usage:
    python src/plot_paper.py [--preview]    (--preview also writes PNGs to tools/build/previews/)
"""

import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

import cv
import explore
from analyze_pilot import load as load_pilot
from horizons import ROOT
from plot_dataset import (I_COL, colorbar, distance_axis, draw_map, guide_lines,
                          hill_top_axis)
from plot_style import BLUE, GRID, INK, MUTED_INK, ORANGE
from plot_test import accuracy, boot, load as load_test, probs, survived_auc
from simulate import DAY_S
from survival_curve import YEARS, alive_share, band, curves, load_extended
from validate_real_system import compare

OUT = ROOT / "paper" / "figures"
PREVIEW = ROOT / "tools" / "build" / "previews"
COLUMN = 3.4  # inches; AASTeX two-column width
PAGE = 6.0    # inches; printed at 0.85 of the text width
PRINT_STYLE = {"font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
               "legend.fontsize": 6.5, "pdf.fonttype": 42, "axes.labelcolor": MUTED_INK,
               "savefig.facecolor": "white", "figure.facecolor": "white"}


def chart(width, height, rows=1, cols=1, **kwargs):
    """Print-style axes: white background, light grid, no frame."""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height), layout="constrained", **kwargs)
    for ax in np.atleast_1d(axes).flat:
        ax.set_facecolor("white")
        ax.grid(color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", colors=MUTED_INK, length=0, pad=2)
        for spine in ax.spines.values():
            spine.set_visible(False)
    return fig, axes


def legend(ax, **kwargs):
    ax.legend(frameon=True, facecolor="white", edgecolor=GRID, framealpha=1, labelcolor=INK,
              borderpad=0.4, handlelength=1.8, **kwargs)


def below(fig, ax):
    """Legend in two columns under the axes, so it covers no data."""
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncols=2,
               frameon=False, labelcolor=INK, handlelength=1.8, columnspacing=1.2)


def validation():
    c = compare()
    days = c["times_s"] / DAY_S
    fig, ax = chart(COLUMN, 2.1)
    for error, color, label in ((c["error_without_sun_km"], ORANGE, "Without the Sun"),
                                (c["error_km"], BLUE, "With the Sun")):
        ax.plot(days[1:], error[1:], color=color, linewidth=1.2,
                label=f"{label} (largest {error.max():,.0f} km)" if error.max() >= 100
                else f"{label} (largest {error.max():.1f} km)")
    ax.set_yscale("log")
    ax.set_ylim(1e-2, 2e5)
    ax.set_xlim(0, days[-1])
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:,.10g}")
    ax.set_xlabel("Days since 2026-01-01")
    ax.set_ylabel("Position error (km)")
    legend(ax, loc="lower right")
    return fig


def map_panel(fig, ax):
    """Survival share by semi-major axis and inclination; returns the line-style handles."""
    df = explore.load_dataset("train")
    mesh, _ = draw_map(ax, df, I_COL)
    distance_axis(ax)
    top = hill_top_axis(ax)
    top.set_xlabel("Hill radii", color=MUTED_INK, fontsize=7.5)
    ax.set_yticks(range(0, 181, 30))
    ax.set_ylabel("Inclination (degrees)")
    guide_lines(ax)
    for yy, text in ((97, "retrograde"), (83, "prograde")):
        ax.annotate(text, (1, yy), xycoords=("axes fraction", "data"), xytext=(4, 0),
                    textcoords="offset points", color=MUTED_INK, fontsize=6.5, va="center",
                    annotation_clip=False)
    colorbar(fig, mesh, ax, "Share surviving 100 years")
    return [Line2D([], [], color=INK, linewidth=1, linestyle=style, label=label)
            for style, label in (("--", "Moon's orbit"), (":", "Half of Earth's Hill radius"))]


def stability_map():
    fig, ax = chart(PAGE, 3.3)
    handles = map_panel(fig, ax)
    fig.legend(handles=handles, loc="outside lower center", ncols=2, frameon=False,
               labelcolor=INK, fontsize=7)
    return fig


def survival():
    train = explore.load_dataset("train")
    ext, _ = load_extended()
    fig, ax = chart(COLUMN, 2.6)
    main_curve = curves(train, ext) * 100
    early = YEARS <= 100
    t, low, high = band(train, ext)
    ax.fill_between(t, low * 100, high * 100, color=BLUE, alpha=0.18, linewidth=0)
    ax.plot(YEARS[early], main_curve[early], color=BLUE, linewidth=1.2,
            label=f"Training ({len(train):,})")
    ax.plot(YEARS[~early], main_curve[~early], color=BLUE, linewidth=1.2, linestyle="--",
            label=f"{len(ext)} survivors to 1,000 yr")
    ax.plot(YEARS, curves(train, ext, weighted=True) * 100, color=ORANGE, linewidth=1.2,
            linestyle=":", label="Isotropic reweighting")
    pilot = np.array([float(r["result_survival_days"]) / explore.YEAR_DAYS
                      for r in load_pilot("pilot").values()])
    ax.plot(YEARS[early], [alive_share(pilot, x) * 100 for x in YEARS[early]], color=MUTED_INK,
            linewidth=0.9, label="Pilot (100, isotropic)")
    ax.axvline(100, color=MUTED_INK, linewidth=0.6, linestyle=":")
    ax.set_xscale("log")
    ticks = [0.1, 1, 10, 100, 1000]
    ax.set_xticks(ticks, [f"{x:g}" for x in ticks])
    ax.minorticks_off()
    ax.set_xlim(0.1, 1000)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Years since the start")
    ax.set_ylabel("Systems with the second moon (%)")
    below(fig, ax)
    return fig


def scores_panel(ax):
    """Cross-validated and test scores with bootstrap intervals."""
    test, _, _, frame = load_test()
    oof = pd.read_csv(ROOT / "data" / "phase4" / "random_forest_F3_oof.csv")
    sets = ((-0.14, oof["y"].to_numpy(), oof.filter(like="p").to_numpy(), BLUE,
             "Cross-validated (9,600 training)"),
            (0.14, frame["y"].to_numpy(), probs(frame, "selected"), ORANGE,
             "Held-out test (2,400)"))
    rows = (("Macro-F1", cv.macro_f1), ("Accuracy", accuracy),
            ("Balanced accuracy", cv.balanced_accuracy), ("Survival ROC AUC", survived_auc))
    low, high = test["criteria"]["C1"]["interval"]
    ax.axvspan(low, high, ymin=0.77, ymax=0.98, color=BLUE, alpha=0.22, linewidth=0)
    for r, (name, stat) in enumerate(rows):
        for offset, y, prob, color, label in sets:
            value, (lo, hi) = stat(y, prob), boot(y, prob, stat)
            ax.plot([lo, hi], [r + offset] * 2, color=color, linewidth=1.2)
            ax.plot(value, r + offset, "o", color=color, markersize=4.5, markeredgecolor="white",
                    markeredgewidth=0.8, label=label if r == 0 else None)
            ax.annotate(f"{value:.3f}", (hi, r + offset), xytext=(3, 0), textcoords="offset points",
                        va="center", fontsize=6, color=INK)
    ax.set_yticks(range(len(rows)), [name for name, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0.6, 1.03)
    ax.set_xlabel("Score with 95% bootstrap interval")


def test_vs_cv():
    fig, ax = chart(COLUMN, 2.2)
    scores_panel(ax)
    below(fig, ax)
    return fig


def rnaas_figure():
    """One two-panel figure for the Research Note: (a) stability map, (b) test versus CV."""
    fig, (top, bottom) = chart(PAGE, 5.4, rows=2, height_ratios=[3.2, 2.0])
    handles = map_panel(fig, top)
    top.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncols=2,
               frameon=False, labelcolor=INK, fontsize=7)
    scores_panel(bottom)
    bottom.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncols=2, frameon=False,
                  labelcolor=INK, fontsize=7)
    for ax, letter in ((top, "a"), (bottom, "b")):
        ax.text(-0.09, 1.02, f"({letter})", transform=ax.transAxes, fontsize=8.5,
                fontweight="bold", color=INK, va="bottom")
    return fig


def speed():
    _, _, timing, _ = load_test()
    sim, model = timing["simulation"], timing["model"]
    bars = (("Simulation, mean", sim["mean_s"], BLUE), ("Simulation, median", sim["median_s"], BLUE),
            ("Model, one system", model["latency_median_s"], ORANGE),
            ("Model, batch (per system)", model["batch_per_moon_s"], ORANGE))
    fig, ax = chart(COLUMN, 1.55)
    values = [b[1] for b in bars]
    ax.barh([b[0] for b in bars], values, color=[b[2] for b in bars], height=0.6)
    ax.set_xscale("log")
    ax.invert_yaxis()
    for r, value in enumerate(values):
        text = f"{value:.2f} s" if value >= 0.1 else (f"{value * 1000:.1f} ms" if value >= 1e-3
                                                     else f"{value * 1e6:.0f} µs")
        ax.annotate(text, (value, r), xytext=(3, 0), textcoords="offset points", va="center",
                    fontsize=6.5, color=INK)
    ax.set_xlim(min(values) / 3, max(values) * 30)
    ax.set_xlabel("Seconds per system (log scale)")
    return fig


FIGURES = {"paper_validation": validation, "paper_stability_map": stability_map,
           "paper_survival": survival, "paper_test_vs_cv": test_vs_cv, "paper_speed": speed,
           "rnaas_figure": rnaas_figure}


def main():
    plt.switch_backend("Agg")
    preview = "--preview" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(PRINT_STYLE):
        for name, draw in FIGURES.items():
            fig = draw()
            fig.savefig(OUT / f"{name}.pdf")
            if preview:
                PREVIEW.mkdir(parents=True, exist_ok=True)
                fig.savefig(PREVIEW / f"{name}.png", dpi=300)
            plt.close(fig)
            print(f"Saved paper/figures/{name}.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
