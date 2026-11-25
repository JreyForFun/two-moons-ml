"""Draw charts of the simulated Moon and its difference from NASA's Moon.

Run:  venv/Scripts/python src/plot_real_system.py
"""

import matplotlib

matplotlib.use("Agg")  # save files without opening a window
import matplotlib.pyplot as plt

from horizons import ROOT
from simulate import DAY_S
from validate_real_system import compare

FIGURES = ROOT / "figures"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # checked for color-blind readers
SURFACE, INK, MUTED_INK, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9"
NASA_DOT_EVERY = 20  # outputs; 20 x 6 hours = 5 days


def new_chart(width, height):
    fig, ax = plt.subplots(figsize=(width, height), layout="constrained")
    fig.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", colors=MUTED_INK, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


def set_titles(ax, title, subtitle):
    ax.set_title(f"{title}\n", loc="left", color=INK, fontsize=14, fontweight="bold")
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=MUTED_INK, fontsize=10)


def save(fig, name):
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"Saved {path}")


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
    ax.legend(loc="upper right", frameon=True, facecolor=SURFACE, edgecolor=GRID,
              framealpha=1, labelcolor=INK)
    set_titles(ax, "The Moon's path around Earth, 2026",
               "One year seen from above, on the plane of Earth's orbit")
    save(fig, "real_moon_orbit.png")


def plot_error(c):
    days = c["times_s"] / DAY_S
    fig, ax = new_chart(8.5, 5)
    # The first point is skipped: its error is almost zero, which a log axis
    # cannot show usefully.
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
    ax.legend(loc="lower right", frameon=True, facecolor=SURFACE, edgecolor=GRID,
              framealpha=1, labelcolor=INK)
    set_titles(ax, "The Moon's orbit needs the Sun",
               "Position error of our simulation compared with NASA JPL Horizons")
    save(fig, "real_moon_error.png")


def main():
    comparison = compare()
    plot_orbit(comparison)
    plot_error(comparison)


if __name__ == "__main__":
    main()
