"""Shared figure style and helpers."""

import matplotlib.pyplot as plt

from horizons import ROOT

FIGURES = ROOT / "figures"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # color-blind safe pair
SURFACE, INK, MUTED_INK, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9"


def new_chart(width, height, rows=1, cols=1, **kwargs):
    """Figure and axes (one Axes, or an array for several panels) in the project style."""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height), layout="constrained", **kwargs)
    fig.set_facecolor(SURFACE)
    for ax in [axes] if rows == cols == 1 else axes.flat:
        ax.set_facecolor(SURFACE)
        ax.grid(color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", colors=MUTED_INK, length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    return fig, axes


def set_titles(ax, title, subtitle):
    ax.set_title(f"{title}\n", loc="left", color=INK, fontsize=14, fontweight="bold")
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=MUTED_INK, fontsize=10)


def add_legend(ax, **kwargs):
    ax.legend(frameon=True, facecolor=SURFACE, edgecolor=GRID, framealpha=1,
              labelcolor=INK, **kwargs)


def save(fig, name):
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / name, dpi=160)
    plt.close(fig)
    print(f"Saved figures/{name}")
