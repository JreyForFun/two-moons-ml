"""Pilot-study analysis: agreement between the pilot variants and the pre-registered rules.

Compares the reference run with the tolerance, displacement and start-date variants, estimates
the computing time of the full dataset, and draws the pilot figures.

Usage:
    python src/analyze_pilot.py
"""

import math
from collections import Counter

import matplotlib.pyplot as plt

from generate_dataset import read_rows
from horizons import ROOT
from labels import LABELS
from plot_style import BLUE, INK, MUTED_INK, ORANGE, SURFACE, add_legend, new_chart, save, set_titles

YEAR_DAYS = 365.25
LIMITS_YEARS = (10, 30, 100)
WORKERS = 4
BUDGET_HOURS = 9
TARGET_MOONS = 5000
RARE = 0.02
MAX_TIMEOUTS = 0.02
EXTRA_DISAGREEMENTS = 3
OTHER_DATES = ("2026-05-01", "2026-09-01")


def load(name):
    path = ROOT / "data" / f"{name}.csv"
    if not path.exists():
        raise SystemExit(f"data/{path.name} is missing. Run generate_dataset.py first.")
    return {int(row["id"]): row for row in read_rows(path)}


def label_at(row, years):
    """Label if the simulation had stopped after this many years."""
    if row["result_label"] == "error":
        return "error"
    if float(row["result_survival_days"]) >= years * YEAR_DAYS:
        return "survived"
    return row["result_label"]


def wilson(successes, n):
    """95% confidence interval for a proportion."""
    z, p = 1.96, successes / n
    middle = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return max(0.0, middle - half), min(1.0, middle + half)


def agreement(a, b, years):
    """Moons with the same label in both runs (timeouts and errors left out)."""
    skip = ("timeout", "error")
    ids = [i for i in a if i in b and label_at(a[i], years) not in skip
           and label_at(b[i], years) not in skip]
    same = sum(label_at(a[i], years) == label_at(b[i], years) for i in ids)
    return same, len(ids)


def describe(same, n):
    low, high = wilson(same, n)
    return f"{same}/{n} the same ({same / n:.1%}, 95% interval {low:.1%} to {high:.1%})"


def hours_for(rows, years, moons):
    """Estimated hours for a full dataset, scaling each run to the time limit."""
    seconds = 0.0
    for row in rows.values():
        simulated = float(row["result_survival_days"])
        share = min(1.0, years * YEAR_DAYS / simulated) if simulated > 0 else 1.0
        seconds += float(row["result_computing_s"]) * share
    return seconds / len(rows) * moons / WORKERS / 3600


def plot_outcomes(a):
    """Initial orbits of the pilot moons and their outcomes."""
    fig, ax = new_chart(8.5, 5.5)
    for title, color, marker, keep in (
        ("Survived 100 years", BLUE, "o", lambda label: label == "survived"),
        ("Did not survive", ORANGE, "X", lambda label: label not in ("survived", "timeout", "error")),
    ):
        rows = [r for r in a.values() if keep(r["result_label"])]
        ax.scatter([float(r["input_distance_lunar"]) for r in rows],
                   [float(r["input_inclination_deg"]) for r in rows],
                   s=55, color=color, marker=marker, edgecolor=SURFACE, linewidth=1,
                   label=f"{title} ({len(rows)})")
    ax.set_xscale("log")
    ticks = [0.1, 0.2, 0.5, 1, 2, 3]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.minorticks_off()
    ax.set_yticks(range(0, 181, 30))
    ax.axhline(90, color=INK, linewidth=0.8)
    for y, text in ((97, "backward"), (83, "forward")):
        ax.annotate(text, (1, y), xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", color=MUTED_INK, fontsize=9, va="center",
                    annotation_clip=False)
    ax.set_xlabel("Starting distance (1 = our Moon's, log scale)", color=MUTED_INK)
    ax.set_ylabel("Tilt (degrees)", color=MUTED_INK)
    add_legend(ax, loc="upper right")
    set_titles(ax, "Which second moons survived?", "Pilot: 100 random second moons")
    return fig


def plot_survival(a):
    """Share of pilot moons not yet collided or ejected, as a function of time."""
    rows = [r for r in a.values() if r["result_label"] not in ("timeout", "error")]
    ends = sorted(float(r["result_survival_days"]) / YEAR_DAYS for r in rows
                  if r["result_label"] != "survived")
    n = len(rows)
    years = [0.01] + [max(e, 0.01) for e in ends] + [100]
    share = [100.0] + [100 * (1 - (k + 1) / n) for k in range(len(ends))]
    share.append(share[-1])
    fig, ax = new_chart(8.5, 4.5)
    ax.step(years, share, where="post", color=BLUE, linewidth=2)
    ax.set_xscale("log")
    ticks = [0.1, 1, 10, 100]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.set_xlim(0.1, 100)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Years (log scale)", color=MUTED_INK)
    ax.set_ylabel("Still there (%)", color=MUTED_INK)
    set_titles(ax, "How long do second moons last?", f"Pilot: {n} random second moons")
    return fig


def main():
    a, b, c = load("pilot"), load("pilot_strict"), load("pilot_shift")
    n = len(a)
    print(f"RUN A: {n} moons")
    for years in LIMITS_YEARS:
        counts = Counter(label_at(r, years) for r in a.values())
        parts = [f"{label} {counts[label]}" for label in LABELS if counts[label]]
        print(f"  {years:3d} years: {', '.join(parts)}")
    baseline = Counter(label_at(r, 100) for r in a.values()).most_common(1)[0]
    print(f"  Always guessing '{baseline[0]}' would be right for {baseline[1] / n:.0%}")

    times = sorted(float(r["result_computing_s"] or 0) for r in a.values())
    print(f"  Computing time per moon: median {times[n // 2]:.1f} s, "
          f"largest {times[-1]:.1f} s, total {sum(times) / 3600:.2f} hours")

    print("\nCHAOS AND ACCURACY (100 years)")
    c_same, c_n = agreement(a, c, 100)
    b_same, b_n = agreement(a, b, 100)
    print(f"  C, 1 meter shift:      {describe(c_same, c_n)}")
    print(f"  B, stricter settings:  {describe(b_same, b_n)}")
    b_bad, c_bad = b_n - b_same, c_n - c_same
    keep = b_bad <= c_bad + EXTRA_DISAGREEMENTS
    print(f"  Rule: B differs on {b_bad}, C on {c_bad}. "
          f"{'Keep epsilon 1e-9' if keep else 'Use epsilon 1e-11'}")

    print("\nSTART DATE (100 years, compared with A)")
    for date in OTHER_DATES:
        print(f"  D, {date}: {describe(*agreement(a, load(f'pilot_{date}'), 100))}")
    first = {i: row for i, row in a.items() if i < 30}
    print(f"  C, same 30 moons: {describe(*agreement(first, c, 100))}")

    print("\nTIME LIMIT")
    chosen = None
    for years in LIMITS_YEARS:
        hours = hours_for(a if keep else b, years, TARGET_MOONS)
        fits = hours <= BUDGET_HOURS
        chosen = years if fits else chosen
        print(f"  {years:3d} years: about {hours:.1f} hours for {TARGET_MOONS:,} moons"
              f"{'' if fits else f' (more than {BUDGET_HOURS})'}")
    print(f"  Rule: {f'use {chosen} years' if chosen else 'no limit fits'}")

    for years in LIMITS_YEARS:
        counts = Counter(label_at(r, years) for r in a.values())
        rare = [label for label in LABELS[:6] if counts[label] < RARE * n]
        print(f"\nUnder {RARE:.0%} at {years} years: {', '.join(rare) or 'none'}", end="")
    timeouts = sum(r["result_label"] == "timeout" for r in a.values())
    errors = sum(r["result_label"] == "error" for r in a.values())
    print(f"\n\nTimeouts: {timeouts} ({'fine' if timeouts <= MAX_TIMEOUTS * n else 'too many'}), "
          f"errors: {errors}")

    print()
    print("ADDED AFTER SEEING THE RESULTS (not part of the rules)")
    for years in LIMITS_YEARS:
        print(f"  Chaos, {years:3d} years, C vs A: {describe(*agreement(a, c, years))}")
    for low, high in ((0, 40), (40, 90), (90, 140), (140, 180)):
        rows = [r for r in a.values() if low <= float(r["input_inclination_deg"]) < high]
        counts = Counter(r["result_label"] for r in rows)
        print(f"  Tilt {low:3d}-{high:3d}, {len(rows):2d} moons: {dict(counts.most_common())}")
    for low, high in ((0.1, 0.3), (0.3, 1), (1, 3)):
        rows = [r for r in a.values() if low <= float(r["input_distance_lunar"]) < high]
        counts = Counter(r["result_label"] for r in rows)
        print(f"  Distance {low}-{high}, {len(rows):2d} moons: {dict(counts.most_common())}")

    plt.switch_backend("Agg")  # non-interactive backend
    save(plot_outcomes(a), "pilot_outcomes.png")
    save(plot_survival(a), "pilot_survival.png")


if __name__ == "__main__":
    main()
