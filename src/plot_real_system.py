"""Figures of the validation run: the Moon's orbit and its position error against JPL Horizons.

Usage:
    python src/plot_real_system.py
"""

import matplotlib.pyplot as plt

from plot_style import (
    BLUE, INK, MUTED_INK, ORANGE, SURFACE, add_legend, new_chart, save, set_titles,
)
from simulate import DAY_S
from validate_real_system import compare

NASA_DOT_EVERY = 20  # outputs; 20 x 6 hours = 5 days


def plot_orbit(c):
    moon = c["with_sun"].relative("moon") / 1000  # thousand km
    nasa = c["nasa"][::NASA_DOT_EVERY] / 1000
    fig, ax = new_chart(7, 7.4)
    ax.plot(moon[:, 0], moon[:, 1], color=BLUE, linewidth=1.0, label="Our simulation")
    ax.plot(nasa[:, 0], nasa[:, 1], "o", color=ORANGE, markersize=5,
            markeredgecolor=SURFACE, markeredgewidth=1, label="NASA, every 5 days")
    ax.plot(0, 0, "o", color=INK, markersize=9)
    ax.annotate("Earth (not to scale)", (0, 0), xytext=(0, -20),
                textcoords="offset points", ha="center", color=INK)
    ax.set_aspect("equal")
    ax.set_xlabel("x (thousand km)", color=MUTED_INK)
    ax.set_ylabel("y (thousand km)", color=MUTED_INK)
    add_legend(ax, loc="upper right")
    set_titles(ax, "The Moon's path around Earth, 2026",
               "One year seen from above, on the plane of Earth's orbit")
    return fig


def plot_error(c):
    days = c["times_s"] / DAY_S
    fig, ax = new_chart(8.5, 5)
    # Skip the first point: its error is ~0 and cannot be shown on a log axis.
    for error, color, label in (
        (c["error_without_sun_km"], ORANGE, "Without the Sun"),
        (c["error_km"], BLUE, "With the Sun"),
    ):
        ax.plot(days[1:], error[1:], color=color, linewidth=2, label=label)
        ax.annotate(f"{label}\nlargest {error.max():,.0f} km", (days[-1], error[-1]),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    color=INK, fontsize=9, annotation_clip=False)
    ax.set_yscale("log")
    ax.set_ylim(1e-2, 2e5)
    ax.set_xlim(0, days[-1])
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:,.10g}")
    ax.set_xlabel("Days since 2026-01-01", color=MUTED_INK)
    ax.set_ylabel("Distance from NASA's Moon (km, log scale)", color=MUTED_INK)
    add_legend(ax, loc="lower right")
    set_titles(ax, "The Moon's orbit needs the Sun",
               "Position error of our simulation compared with NASA JPL Horizons")
    return fig


def main():
    plt.switch_backend("Agg")  # non-interactive backend
    comparison = compare()
    save(plot_orbit(comparison), "real_moon_orbit.png")
    save(plot_error(comparison), "real_moon_error.png")


if __name__ == "__main__":
    main()
