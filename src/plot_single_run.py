"""Figures of the 10-year example run with a second moon.

Usage:
    python src/plot_single_run.py
"""

import matplotlib.pyplot as plt
import numpy as np

from horizons import ROOT, load_state
from plot_style import BLUE, INK, MUTED_INK, ORANGE, add_legend, new_chart, save, set_titles
from simulate import DAY_S, load_config, run

CONFIG = ROOT / "configs" / "single_run.json"
DAYS_PER_YEAR = 365.25
MOONS = (("moon", "Moon", BLUE), ("moon2", "Second moon", ORANGE))


def plot_distances(result):
    """Distance of both moons from Earth over the whole run."""
    years = result.times_s / DAY_S / DAYS_PER_YEAR
    fig, ax = new_chart(8.5, 5)
    for name, label, color in MOONS:
        distance = np.linalg.norm(result.relative(name), axis=1) / 1000
        ax.plot(years, distance, color=color, linewidth=0.6, label=label)
    ax.set_xlim(0, years[-1])
    ax.set_ylim(0, 450)
    ax.set_xlabel("Years since 2026-01-01", color=MUTED_INK)
    ax.set_ylabel("Distance from Earth (thousand km)", color=MUTED_INK)
    add_legend(ax, loc="lower right")
    for line in ax.get_legend().get_lines():
        line.set_linewidth(2)
    set_titles(ax, "Both moons survived 10 years, but one orbit is stretching",
               "The second moon's band widens: its orbit is becoming less circular")
    return fig


def plot_energy(result):
    """Relative drift of the total energy, a measure of the integration error."""
    years = result.times_s / DAY_S / DAYS_PER_YEAR
    change = (result.energy - result.energy[0]) / abs(result.energy[0])
    fig, ax = new_chart(8.5, 4)
    ax.plot(years, change * 1e15, color=BLUE, linestyle="none", marker=".", markersize=2)
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.set_xlim(0, years[-1])
    ax.set_xlabel("Years since 2026-01-01", color=MUTED_INK)
    ax.set_ylabel("Relative change (× 10⁻¹⁵)", color=MUTED_INK)
    set_titles(ax, "Total energy only shows rounding noise",
               "Mostly Earth's orbit around the Sun, so a weak check on the moons themselves")
    return fig


def yearly_range_km(result, name):
    """Closest and farthest distance during the first and the last 365 days."""
    distance = np.linalg.norm(result.relative(name), axis=1)
    first = result.times_s <= 365 * DAY_S
    last = result.times_s >= result.times_s[-1] - 365 * DAY_S
    return {"first": (distance[first].min(), distance[first].max()),
            "last": (distance[last].min(), distance[last].max())}


def main():
    plt.switch_backend("Agg")  # non-interactive backend
    result = run(load_state(), load_config(CONFIG))
    for name, label, _ in MOONS:
        for year, (closest, farthest) in yearly_range_km(result, name).items():
            print(f"{label}, {year} year: {closest:,.0f} to {farthest:,.0f} km "
                  f"(spread {farthest - closest:,.0f} km)")
    save(plot_distances(result), "two_moons_distance.png")
    save(plot_energy(result), "two_moons_energy.png")


if __name__ == "__main__":
    main()
