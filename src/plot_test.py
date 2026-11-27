"""Phase 5 figures.

Run after evaluate_test.py, benchmark_speed.py and analyze_test.py:
  venv/Scripts/python src/plot_test.py
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import cv
from features import config
from horizons import ROOT
from plot_dataset import COUNT_CMAP
from plot_models import LABELS, confusion
from plot_style import BLUE, INK, MUTED_INK, ORANGE, SURFACE, add_legend, new_chart, save, set_titles

RESULTS = ROOT / "results"
CV_OOF = ROOT / "data" / "phase4" / "random_forest_F3_oof.csv"


def load():
    test = json.loads((RESULTS / "phase5_test.json").read_text(encoding="utf-8"))
    analysis = json.loads((RESULTS / "phase5_analysis.json").read_text(encoding="utf-8"))
    speed = json.loads((RESULTS / "phase5_speed.json").read_text(encoding="utf-8"))
    frame = pd.read_csv(RESULTS / "phase5_test_predictions.csv", keep_default_na=False,
                        na_values={"result_survival_days": [""]})
    return test, analysis, speed, frame


def probs(frame, prefix):
    return frame[[f"{prefix}_p{k}" for k in range(len(config()["classes"]))]].to_numpy()


def accuracy(y, prob):
    return float((prob.argmax(axis=1) == y).mean())


def survived_auc(y, prob):
    return roc_auc_score((y == 0).astype(int), prob[:, 0])


def boot(y, prob, statistic, seed=1):
    rng = np.random.default_rng(seed)
    return cv.interval(np.array([statistic(y[i], prob[i])
                                 for i in (rng.integers(0, len(y), len(y)) for _ in range(1000))]))


def test_vs_cv(test, frame):
    oof = pd.read_csv(CV_OOF)
    oy, oprob = oof["y"].to_numpy(), oof.filter(like="p").to_numpy()
    ty, tprob = frame["y"].to_numpy(), probs(frame, "selected")
    rows = (("Macro-F1", cv.macro_f1), ("Accuracy", accuracy),
            ("Balanced accuracy", cv.balanced_accuracy), ("Survival ROC AUC", survived_auc))
    fig, ax = new_chart(8.5, 4.4)
    low, high = test["criteria"]["C1"]["interval"]
    ax.axvspan(low, high, ymin=0.78, ymax=0.97, color=BLUE, alpha=0.12, linewidth=0)
    for r, (name, stat) in enumerate(rows):
        for offset, y, prob, color, label in ((-0.12, oy, oprob, BLUE, "Cross-validated (training)"),
                                              (0.12, ty, tprob, ORANGE, "Held-out test set")):
            value, (lo, hi) = stat(y, prob), boot(y, prob, stat)
            ax.plot([lo, hi], [r + offset] * 2, color=color, linewidth=2)
            ax.plot(value, r + offset, "o", color=color, markersize=8, markeredgecolor=SURFACE,
                    markeredgewidth=1.5, label=label if r == 0 else None)
            ax.annotate(f"{value:.3f}", (hi, r + offset), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(rows)), [name for name, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0.6, 1.02)
    ax.set_xlabel("Score with 95% bootstrap interval (shaded: criterion C1)", color=MUTED_INK)
    add_legend(ax, loc="lower left")
    set_titles(ax, "The test set confirms the cross-validated scores",
               "Random Forest, 9,600 training moons (out-of-fold) vs 2,400 held-out moons")
    return fig


def calibration(test, frame):
    oof = pd.read_csv(CV_OOF)
    fig, ax = new_chart(6, 5.6)
    ax.plot([0, 1], [0, 1], color=MUTED_INK, linewidth=1, linestyle="--")
    edges = np.linspace(0, 1, 11)
    for y, p, color, label, minimum in (
            (oof["y"].to_numpy(), oof["p0"].to_numpy(), BLUE, "Cross-validated", 20),
            (frame["y"].to_numpy(), frame["selected_p0"].to_numpy(), ORANGE, "Test set", 10)):
        alive = (y == 0).astype(float)
        index = np.clip(np.digitize(p, edges) - 1, 0, 9)
        xs, ys = [], []
        for b in range(10):
            mask = index == b
            if mask.sum() >= minimum:
                xs.append(p[mask].mean())
                ys.append(alive[mask].mean())
        ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=label)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted P(survived), 10 bins", color=MUTED_INK)
    ax.set_ylabel("Observed share surviving", color=MUTED_INK)
    add_legend(ax, loc="upper left")
    set_titles(ax, "Survival probabilities stay honest on new moons",
               f"Test ECE {test['criteria']['C3']['ece']:.3f} (limit 0.05)")
    return fig


def rounded(value):
    """Two significant figures, as a timing ratio is not more precise than that."""
    return f"{float(f'{value:.2g}'):,.0f}"


def speedup(speed):
    sim, model = speed["simulation"], speed["model"]
    bars = (("Simulation, mean", sim["mean_s"], BLUE), ("Simulation, median", sim["median_s"], BLUE),
            ("Model, one moon", model["latency_median_s"], ORANGE),
            ("Model, per moon in a batch", model["batch_per_moon_s"], ORANGE))
    fig, ax = new_chart(8.5, 3.8)
    names = [b[0] for b in bars]
    values = [b[1] for b in bars]
    ax.barh(names, values, color=[b[2] for b in bars], height=0.55)
    ax.set_xscale("log")
    ax.invert_yaxis()
    for r, value in enumerate(values):
        text = f"{value:.2f} s" if value >= 0.1 else (f"{value * 1000:.1f} ms" if value >= 1e-3
                                                     else f"{value * 1e6:.0f} µs")
        ax.annotate(text, (value, r), xytext=(6, 0), textcoords="offset points", va="center",
                    fontsize=9, color=INK)
    ax.set_xlim(min(values) / 3, max(values) * 20)
    ax.set_xlabel("Seconds per moon (log scale), single process, same machine", color=MUTED_INK)
    s = speed["speedup"]
    set_titles(ax, f"The surrogate is about {rounded(s['same_machine_median'])} times faster per moon",
               f"Batch prediction: about {rounded(s['batch_vs_mean'])} times faster than the mean simulation")
    return fig


def error_map(analysis):
    em = analysis["error_map"]
    bins_a, bins_i = np.array(em["a_bins"]), np.array(em["i_bins"])
    rate = np.full((6, 6), np.nan)
    count = np.zeros((6, 6), dtype=int)
    for k, cell in enumerate(em["cells"]):
        r, c = divmod(k, 6)
        count[r, c] = cell["moons"]
        if cell["moons"] >= 20:
            rate[r, c] = cell["error_rate"]
    fig, ax = new_chart(8.5, 6.0)
    mesh = ax.pcolormesh(bins_a, bins_i, rate, cmap=COUNT_CMAP, vmin=0, vmax=0.5,
                         edgecolors=SURFACE, linewidth=1.5)
    ax.grid(False)
    for r in range(6):
        for c in range(6):
            if count[r, c]:
                x = np.sqrt(bins_a[c] * bins_a[c + 1])
                y = (bins_i[r] + bins_i[r + 1]) / 2
                value = rate[r, c]
                ax.text(x, y, f"{value:.0%}\n{count[r, c]}" if not np.isnan(value) else f"–\n{count[r, c]}",
                        ha="center", va="center", fontsize=8,
                        color=SURFACE if (not np.isnan(value) and value > 0.3) else INK)
    ax.set_xscale("log")
    ticks = [0.1, 0.2, 0.5, 1, 2, 3]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.minorticks_off()
    ax.set_yticks(range(0, 181, 30))
    ax.axvline(1.0, color=INK, linewidth=1, linestyle="--")
    ax.axhline(90, color=INK, linewidth=0.8)
    ax.set_xlabel("Semi-major axis (lunar distances, log scale)", color=MUTED_INK)
    ax.set_ylabel("Inclination (degrees)", color=MUTED_INK)
    bar = fig.colorbar(mesh, ax=ax, shrink=0.85, pad=0.03)
    bar.set_label("Test error rate", color=MUTED_INK)
    bar.ax.tick_params(colors=MUTED_INK, length=0)
    bar.outline.set_visible(False)
    set_titles(ax, "Where the model is wrong",
               "Held-out test moons; each cell shows error rate and number of moons; dashed: Moon's orbit")
    return fig


def coverage(analysis):
    points = analysis["coverage_accuracy"]
    x = [p["coverage"] * 100 for p in points]
    acc = np.array([p["accuracy"] for p in points]) * 100
    low = np.array([p["interval"][0] for p in points]) * 100
    high = np.array([p["interval"][1] for p in points]) * 100
    fig, ax = new_chart(8, 4.6)
    ax.fill_between(x, low, high, color=BLUE, alpha=0.18, linewidth=0)
    ax.plot(x, acc, color=BLUE, linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE,
            markeredgewidth=1.5)
    ref = analysis["T5"]["agreement"] * 100
    ax.axhline(ref, color=INK, linewidth=1, linestyle="--")
    ax.annotate(f"chaos reference {ref:.1f}% (test twin agreement)", (12, ref), xytext=(0, 4),
                textcoords="offset points", fontsize=8, color=INK)
    ax.set_xlim(5, 102)
    ax.set_ylim(min(80, low.min() - 2), 100.5)
    ax.set_xlabel("Share of test moons kept, most confident first (%)", color=MUTED_INK)
    ax.set_ylabel("Accuracy on kept moons (%)", color=MUTED_INK)
    set_titles(ax, "Confident predictions are almost always right",
               "Held-out test set; band: 95% Wilson interval")
    return fig


def main():
    plt.switch_backend("Agg")
    test, analysis, speed, frame = load()
    y, prob = frame["y"].to_numpy(), probs(frame, "selected")
    save(test_vs_cv(test, frame), "test_vs_cv.png")
    save(confusion(y, prob.argmax(axis=1), [LABELS[c] for c in config()["classes"]],
                   "Test set: right and wrong predictions",
                   f"{len(y):,} test moons, rows sum to 100%"), "test_confusion.png")
    save(calibration(test, frame), "test_calibration.png")
    save(speedup(speed), "speedup.png")
    save(error_map(analysis), "error_map.png")
    save(coverage(analysis), "coverage_accuracy.png")


if __name__ == "__main__":
    main()
