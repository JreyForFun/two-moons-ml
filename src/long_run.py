"""Follow the Phase 1 second moon for 1,000 years and record its orbit around Earth.

Run:  venv/Scripts/python src/long_run.py          (about 7 minutes)
      venv/Scripts/python src/long_run.py --plot   (redraw the figure from saved data)

Saves data/single_run_long.csv (osculating elements every 10 days) and
figures/first_moon_long_term.png.
"""

import argparse
import csv
import math
import time

import matplotlib.pyplot as plt
import numpy as np

from horizons import ROOT, load_state
from plot_style import BLUE, INK, MUTED_INK, ORANGE, new_chart, save, set_titles
from simulate import DAY_S, _simulate, load_config

CONFIG = ROOT / "configs" / "single_run_long.json"
OUTPUT = ROOT / "data" / "single_run_long.csv"
YEAR_DAYS = 365.25
FIELDS = ("years", "moon_a_km", "moon_e", "moon_inc_deg", "moon2_a_km", "moon2_e", "moon2_inc_deg")


def simulate():
    config = load_config(CONFIG)
    names = config["bodies"]
    started = time.perf_counter()
    rows, outcome = [], None
    for sim, outcome, _ in _simulate(load_state(), config):
        earth = sim.particles[names.index("earth")]
        row = {"years": sim.t / DAY_S / YEAR_DAYS}
        for name in ("moon", "moon2"):
            orbit = sim.particles[names.index(name)].orbit(primary=earth)
            row.update({f"{name}_a_km": orbit.a, f"{name}_e": orbit.e,
                        f"{name}_inc_deg": math.degrees(orbit.inc)})
        rows.append(row)
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Outcome: {outcome} after {rows[-1]['years']:.1f} years, "
          f"{time.perf_counter() - started:.0f} s. Saved data/{OUTPUT.name}")


def load():
    with open(OUTPUT, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in FIELDS}


def running_mean(values, window):
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="valid")


def summarize(data):
    years, e = data["years"], data["moon2_e"]
    for start, end in ((0, 10), (90, 100), (490, 500), (990, 1000)):
        part = e[(years >= start) & (years <= end)]
        print(f"  Years {start:4d}-{end:4d}: second moon e mean {part.mean():.4f}, "
              f"max {part.max():.4f}")
    print(f"  Largest e over 1,000 years: {e.max():.4f} at year {years[e.argmax()]:.0f}")
    print(f"  Semi-major axis range: {data['moon2_a_km'].min():,.0f} to "
          f"{data['moon2_a_km'].max():,.0f} km")


def plot(data):
    years = data["years"]
    window = round(10 * YEAR_DAYS / 10)  # 10 years of 10-day outputs
    fig, ax = new_chart(8.5, 4.6)
    ax.plot(years, data["moon2_e"], color=ORANGE, linewidth=0.4, alpha=0.45)
    ax.plot(years[window - 1:], running_mean(data["moon2_e"], window), color=ORANGE,
            linewidth=2, label="Second moon (10-year mean)")
    ax.plot(years[window - 1:], running_mean(data["moon_e"], window), color=BLUE,
            linewidth=2, label="Moon (10-year mean)")
    ax.axvline(10, color=INK, linewidth=0.8, linestyle=":")
    ax.annotate("end of the\nPhase 1 run", (10, 0.98), xycoords=("data", "axes fraction"),
                xytext=(4, 0), textcoords="offset points", va="top", fontsize=8, color=INK)
    ax.set_xlim(0, years[-1])
    ax.set_ylim(0, None)
    ax.set_xlabel("Years since 2026-01-01", color=MUTED_INK)
    ax.set_ylabel("Eccentricity", color=MUTED_INK)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncols=2,
               frameon=False, labelcolor=INK)
    set_titles(ax, "The first second moon's orbit oscillates but does not grow",
               "Eccentricity around Earth over 1,000 years: every 10 days (thin line) "
               "and 10-year mean")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plot", action="store_true", help="only redraw from saved data")
    if not parser.parse_args().plot:
        simulate()
    data = load()
    summarize(data)
    plt.switch_backend("Agg")
    save(plot(data), "first_moon_long_term.png")


if __name__ == "__main__":
    main()
