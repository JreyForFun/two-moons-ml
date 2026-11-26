"""Phase 4 figures.

Run after analyze_models.py:  venv/Scripts/python src/plot_models.py
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

import cv
import explore
from analyze_models import RESULTS
from features import config, training_data
from plot_dataset import SHARE_CMAP, distance_axis, guide_lines
from plot_style import BLUE, INK, MUTED_INK, ORANGE, SURFACE, new_chart, save, set_titles
from train_models import OUT, load_decisions

NAMES = {"majority": "Majority class", "physics_rule": "Physics rule", "logistic": "Logistic regression",
         "random_forest": "Random Forest", "xgboost": "XGBoost", "mlp": "Neural network (MLP)"}
LABELS = {"survived": "Survived", "ejected": "Ejected", "hit_earth": "Hit Earth",
          "moon_interaction": "Moon interaction"}
LIFETIME = ["< 1 yr", "1–10 yr", "10–100 yr", "≥ 100 yr"]
DIVERGING = LinearSegmentedColormap.from_list("diff", ["#1b64be", "#84b9f3", "#efefef",
                                                       "#f4a582", "#c4501f"])


def load_run(key):
    result = json.loads((OUT / f"{key}.json").read_text(encoding="utf-8"))
    return result, pd.read_csv(OUT / f"{key}_oof.csv")


def bootstrap_interval(y, prob, statistic, seed=1):
    rng = np.random.default_rng(seed)
    values = [statistic(y[i], prob[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(1000))]
    return cv.interval(np.array(values))


def accuracy(y, prob):
    return float((prob.argmax(axis=1) == y).mean())


def model_comparison(analysis, fs):
    decisions = load_decisions()
    keys = [("majority", "majority"), ("physics_rule", "physics_rule")] + [
        (n, f"{n}_{fs}") for n in config()["simplicity_order"]]
    selected = decisions["P2"]["selected"]
    fig, axes = new_chart(11, 4.6, cols=2, sharey=True)
    for ax, (statistic, title) in zip(axes, ((cv.macro_f1, "Macro-F1"), (accuracy, "Accuracy"))):
        for row, (name, key) in enumerate(keys):
            result, oof = load_run(key)
            y, prob = oof["y"].to_numpy(), oof.filter(like="p").to_numpy()
            value = statistic(y, prob)
            low, high = bootstrap_interval(y, prob, statistic)
            color = ORANGE if name == selected else BLUE
            ax.plot([low, high], [row, row], color=color, linewidth=2)
            ax.plot(value, row, "o", color=color, markersize=8, markeredgecolor=SURFACE,
                    markeredgewidth=1.5)
            ax.annotate(f"{value:.3f}", (high, row), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=INK)
        if statistic is accuracy:
            ref = analysis["chaos"]["agreement"]
            ax.axvline(ref, color=INK, linewidth=1, linestyle="--")
            ax.annotate(f"chaos reference {ref:.3f}\n(twin agreement)", (ref, 0.5),
                        xytext=(-4, 0), textcoords="offset points", ha="right", va="center",
                        fontsize=8, color=INK)
        ax.set_xlim(0, 1.05)
        ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
        ax.set_xlabel("Out-of-fold score (95% bootstrap interval)", color=MUTED_INK)
    axes[0].set_yticks(range(len(keys)), [NAMES[n] for n, _ in keys])
    axes[0].invert_yaxis()
    fig.suptitle("Surrogate models against baselines", x=0.02, ha="left", color=INK, fontsize=14,
                 fontweight="bold")
    return fig


def confusion(y, pred, labels, title, subtitle):
    k = len(labels)
    counts = np.zeros((k, k), dtype=int)
    np.add.at(counts, (y, pred), 1)
    share = counts / counts.sum(axis=1, keepdims=True)
    fig, ax = new_chart(6.8, 5.8)
    ax.imshow(share, cmap=SHARE_CMAP, vmin=0, vmax=1)
    ax.grid(False)
    for i in range(k):
        for j in range(k):
            ax.text(j, i, f"{share[i, j]:.0%}\n{counts[i, j]:,}", ha="center", va="center",
                    fontsize=9, color=SURFACE if share[i, j] > 0.55 else INK)
    ax.set_xticks(range(k), labels, rotation=20)
    ax.set_yticks(range(k), labels)
    ax.set_xlabel("Predicted", color=MUTED_INK)
    ax.set_ylabel("Simulated", color=MUTED_INK)
    set_titles(ax, title, subtitle)
    return fig


def importance_plot(analysis):
    items = sorted(analysis["importance"].items(), key=lambda kv: kv[1][0])
    fig, ax = new_chart(8, 4.2)
    names = [g.replace("_", " ").capitalize() for g, _ in items]
    means = [v[0] for _, v in items]
    sds = [v[1] for _, v in items]
    ax.barh(names, means, xerr=sds, color=BLUE, height=0.55, error_kw={"ecolor": INK, "lw": 1})
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_xlabel("Drop in macro-F1 when the group is shuffled (mean ± SD over 5 folds)",
                  color=MUTED_INK)
    set_titles(ax, "What the model relies on", "Grouped permutation importance, out-of-fold")
    return fig


def predicted_map(df, oof):
    merged = df.merge(oof[["id", "p0"]], on="id")
    bins_x, bins_y = explore.BINS["input_distance_lunar"], explore.BINS["input_inclination_deg"]
    ix = np.clip(np.digitize(merged["input_distance_lunar"], bins_x) - 1, 0, len(bins_x) - 2)
    iy = np.clip(np.digitize(merged["input_inclination_deg"], bins_y) - 1, 0, len(bins_y) - 2)
    shape = (len(bins_y) - 1, len(bins_x) - 1)
    count, sim, pred = np.zeros(shape), np.zeros(shape), np.zeros(shape)
    np.add.at(count, (iy, ix), 1)
    np.add.at(sim, (iy, ix), merged["survived"].to_numpy())
    np.add.at(pred, (iy, ix), merged["p0"].to_numpy())
    sim, pred = sim / count, pred / count
    fig, axes = new_chart(15, 5.0, cols=3, sharey=True)
    for ax, data, title, cmap, lims in (
            (axes[0], sim, "Simulated survival share", SHARE_CMAP, (0, 1)),
            (axes[1], pred, "Predicted P(survived), out-of-fold", SHARE_CMAP, (0, 1)),
            (axes[2], pred - sim, "Predicted minus simulated", DIVERGING, (-0.3, 0.3))):
        mesh = ax.pcolormesh(bins_x, bins_y, data, cmap=cmap, vmin=lims[0], vmax=lims[1],
                             edgecolors=SURFACE, linewidth=1.2)
        ax.grid(False)
        distance_axis(ax)
        guide_lines(ax)
        ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
        bar = fig.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02)
        bar.ax.tick_params(colors=MUTED_INK, length=0)
        bar.outline.set_visible(False)
    axes[0].set_yticks(range(0, 181, 30))
    axes[0].set_ylabel("Inclination (degrees)", color=MUTED_INK)
    fig.suptitle("The surrogate reproduces the stability map", x=0.02, ha="left", color=INK,
                 fontsize=14, fontweight="bold")
    return fig, float(np.nanmax(np.abs(pred - sim)))


def calibration_plot(y, prob, ece):
    alive = (y == 0).astype(float)
    p = prob[:, 0]
    edges = np.linspace(0, 1, 11)
    index = np.clip(np.digitize(p, edges) - 1, 0, 9)
    fig, ax = new_chart(6, 5.6)
    ax.plot([0, 1], [0, 1], color=MUTED_INK, linewidth=1, linestyle="--")
    xs, ys, ns = [], [], []
    for b in range(10):
        mask = index == b
        if mask.sum() >= 20:
            xs.append(p[mask].mean())
            ys.append(alive[mask].mean())
            ns.append(int(mask.sum()))
    ax.plot(xs, ys, color=BLUE, linewidth=2, marker="o", markersize=8, markeredgecolor=SURFACE,
            markeredgewidth=1.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted P(survived), 10 bins", color=MUTED_INK)
    ax.set_ylabel("Observed share surviving", color=MUTED_INK)
    set_titles(ax, "Are the survival probabilities honest?",
               f"Out-of-fold, {len(y):,} training moons; ECE {ece:.3f}")
    return fig


def learning_curve_plot(analysis):
    curve = analysis["learning_curve"]
    moons = [c["moons"] for c in curve]
    fig, axes = new_chart(11, 4.4, cols=2)
    for ax, key, title, color in ((axes[0], "macro_f1", "Macro-F1", BLUE),
                                  (axes[1], "rare_recall", "Moon-interaction recall", ORANGE)):
        mean = np.array([c[key][0] for c in curve])
        sd = np.array([c[key][1] for c in curve])
        ax.fill_between(moons, mean - sd, mean + sd, color=color, alpha=0.18, linewidth=0)
        ax.plot(moons, mean, color=color, linewidth=2, marker="o", markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.set_xscale("log")
        ax.set_xticks(moons, [f"{m:,.0f}" for m in moons])
        ax.minorticks_off()
        ax.set_ylim(0, 1)
        ax.set_xlabel("Training moons per fold (log scale)", color=MUTED_INK)
        ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
    fig.suptitle("Would more simulations help?", x=0.02, ha="left", color=INK, fontsize=14,
                 fontweight="bold")
    return fig


def chaos_profile(analysis):
    chaos = analysis["chaos"]
    fig, axes = new_chart(11, 4.4, cols=2, sharey=True)
    for ax, key, label, log in ((axes[0], "by_distance", "Semi-major axis (lunar distances, log scale)", True),
                                (axes[1], "by_inclination", "Inclination (degrees)", False)):
        rows = chaos[key]
        centers = [np.sqrt(r["low"] * r["high"]) if log else (r["low"] + r["high"]) / 2 for r in rows]
        share = np.array([r["changed"] for r in rows]) * 100
        low = np.array([r["interval"][0] for r in rows]) * 100
        high = np.array([r["interval"][1] for r in rows]) * 100
        ax.fill_between(centers, low, high, color=ORANGE, alpha=0.18, linewidth=0)
        ax.plot(centers, share, color=ORANGE, linewidth=2, marker="o", markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        if log:
            ax.set_xscale("log")
            ticks = [0.1, 0.2, 0.5, 1, 2, 3]
            ax.set_xticks(ticks, [str(t) for t in ticks])
            ax.minorticks_off()
            ax.axvline(1.0, color=INK, linewidth=1, linestyle="--")
        else:
            ax.set_xticks(range(0, 181, 30))
            ax.axvline(90, color=INK, linewidth=0.8)
        ax.set_xlabel(label, color=MUTED_INK)
    axes[0].set_ylabel("Outcome changed by a 1 m nudge (%)", color=MUTED_INK)
    axes[0].set_ylim(0, None)
    fig.suptitle(f"Where outcomes are chaotic ({chaos['moons']:,} twin pairs)", x=0.02, ha="left",
                 color=INK, fontsize=14, fontweight="bold")
    return fig


def main():
    plt.switch_backend("Agg")
    analysis = json.loads(RESULTS.read_text(encoding="utf-8"))
    sel = analysis["selected"]
    key = f"{sel['model']}_{sel['feature_set']}" + ("_calibrated" if sel["calibrated"] else "")
    result, oof = load_run(key)
    y, prob = oof["y"].to_numpy(), oof.filter(like="p").to_numpy()
    df = training_data()
    save(model_comparison(analysis, sel["feature_set"]), "model_comparison.png")
    save(confusion(y, prob.argmax(axis=1), [LABELS[c] for c in config()["classes"]],
                   f"Where the {NAMES[sel['model']]} is right and wrong",
                   "Out-of-fold predictions, rows sum to 100%"), "confusion_matrix_cv.png")
    save(importance_plot(analysis), "feature_importance.png")
    fig, worst = predicted_map(df, oof)
    save(fig, "predicted_map.png")
    print(f"  Largest map-cell difference: {worst:.3f}")
    save(calibration_plot(y, prob, result["metrics"]["survived_ece"]), "calibration.png")
    save(learning_curve_plot(analysis), "learning_curve.png")
    save(chaos_profile(analysis), "chaos_profile.png")
    lifetime, life_oof = load_run(f"lifetime_{sel['model']}_{sel['feature_set']}")
    ly, lprob = life_oof["y"].to_numpy(), life_oof.filter(like="p").to_numpy()
    save(confusion(ly, lprob.argmax(axis=1), LIFETIME, "Predicting when a second moon is lost",
                   f"Lifetime classes, out-of-fold; within one class: {lifetime['within_one_bin']:.0%}"),
         "lifetime_confusion.png")


if __name__ == "__main__":
    main()
