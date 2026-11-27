"""Survival to 1,000 years and rule R4 (does survival level off after 100 years?).

The surviving fraction after t years is the share of training moons lasting at least t years for
t <= 100, and S(100) times the share of the 500 extended survivors lasting at least t years for
t > 100. The extended survivors are a random sample of training survivors, so the product is
unbiased. Writes data/survival_curve.json and figures/survival_curve_full.png.

Usage:
    python src/survival_curve.py
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import explore
from analyze_pilot import load as load_pilot, wilson
from horizons import ROOT
from plot_style import BLUE, MUTED_INK, ORANGE, add_legend, new_chart, save, set_titles

EXTENDED = ROOT / "data" / "survivors_1000yr.csv"
CONFIG = ROOT / "configs" / "survivors_1000yr.json"
RESULTS = ROOT / "data" / "survival_curve.json"
YEARS = np.geomspace(0.1, 1000, 400)


def alive_share(years, t, weights=None):
    alive = np.asarray(years) >= t * (1 - 1e-12)
    return float(np.average(alive, weights=weights))


def load_extended():
    ids = json.loads(CONFIG.read_text(encoding="utf-8"))["ids"]
    ext = pd.read_csv(EXTENDED, keep_default_na=False,
                      na_values={"result_survival_days": [""]})
    ext = ext.sort_values("id").reset_index(drop=True)
    ext["survival_years"] = ext["result_survival_days"] / explore.YEAR_DAYS
    return ext, ids


def rule_r4(train, ext):
    """Loss per factor of 10 in time: 10 to 100 years vs 100 to 1,000 years."""
    years = train["survival_years"].to_numpy()
    s10, s100 = alive_share(years, 10), alive_share(years, 100)
    known = ext[ext["result_label"] != "timeout"]
    kept = int((known["survival_years"] >= 1000 * (1 - 1e-12)).sum())
    n = len(known)
    loss_early = 1 - s100 / s10
    loss_late = 1 - kept / n
    low, high = wilson(n - kept, n)
    return {"alive_10": s10, "alive_100": s100, "loss_10_100": loss_early,
            "extended_known": n, "extended_alive_1000": kept, "loss_100_1000": loss_late,
            "loss_100_1000_interval": [low, high],
            "timeouts": int((ext["result_label"] == "timeout").sum()),
            "levels_off": loss_late < loss_early / 2,
            "alive_1000": s100 * kept / n,
            "labels_after_100": ext["result_label"].value_counts().to_dict()}


def curves(train, ext, weighted=False):
    w_train = explore.isotropic_weights(train) if weighted else None
    w_ext = None
    if weighted:
        w_ext = np.sin(np.radians(ext["input_inclination_deg"].to_numpy()))
    years_train = train["survival_years"].to_numpy()
    years_ext = ext["survival_years"].to_numpy()
    s100 = alive_share(years_train, 100, w_train)
    out = []
    for t in YEARS:
        if t <= 100:
            out.append(alive_share(years_train, t, w_train))
        else:
            out.append(s100 * alive_share(years_ext, t, w_ext))
    return np.array(out)


def band(train, ext):
    """95% band for t > 100 from the Wilson interval of the conditional share."""
    s100 = alive_share(train["survival_years"], 100)
    years_ext = ext["survival_years"].to_numpy()
    t = YEARS[YEARS > 100]
    lows, highs = [], []
    for value in t:
        kept = int((years_ext >= value * (1 - 1e-12)).sum())
        low, high = wilson(kept, len(years_ext))
        lows.append(s100 * low)
        highs.append(s100 * high)
    return t, np.array(lows), np.array(highs)


def plot(train, ext, r4):
    fig, ax = new_chart(8.5, 5.0)
    main_curve = curves(train, ext) * 100
    early = YEARS <= 100
    ax.plot(YEARS[early], main_curve[early], color=BLUE, linewidth=2,
            label=f"Training moons ({len(train):,})")
    t, low, high = band(train, ext)
    ax.fill_between(t, low * 100, high * 100, color=BLUE, alpha=0.18, linewidth=0)
    ax.plot(YEARS[~early], main_curve[~early], color=BLUE, linewidth=2, linestyle="--",
            label=f"Extended: {len(ext)} random survivors to 1,000 years")
    ax.plot(YEARS, curves(train, ext, weighted=True) * 100, color=ORANGE, linewidth=2,
            linestyle=":", label="Reweighted to isotropic inclinations")
    pilot = np.array([float(r["result_survival_days"]) / explore.YEAR_DAYS
                      for r in load_pilot("pilot").values()])
    ax.plot(YEARS[early], [alive_share(pilot, x) * 100 for x in YEARS[early]],
            color=MUTED_INK, linewidth=1.5, label="Pilot (100 moons, isotropic)")
    ax.axvline(100, color=MUTED_INK, linewidth=0.8, linestyle=":")
    ax.set_xscale("log")
    ticks = [0.1, 1, 10, 100, 1000]
    ax.set_xticks(ticks, [str(x) for x in ticks])
    ax.minorticks_off()
    ax.set_xlim(0.1, 1000)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Years (log scale)", color=MUTED_INK)
    ax.set_ylabel("Still orbiting (%)", color=MUTED_INK)
    add_legend(ax, loc="lower left")
    set_titles(ax, "Losses slow down but continue past 100 years" if not r4["levels_off"]
               else "Survival levels off after 100 years",
               "Fraction of second moons not yet collided or ejected; band: 95% interval")
    return fig


def main():
    train = explore.load_dataset("train")
    ext, ids = load_extended()
    original = train.set_index("id").loc[ids]
    consistent = (len(ext) == len(ids)
                  and (ext["survival_years"] >= 100 * (1 - 1e-12)).all()
                  and (original["result_label"] == "survived").all())
    r4 = rule_r4(train, ext)
    r4["reproducible_first_100_years"] = bool(consistent)
    RESULTS.write_text(json.dumps(r4, indent=2) + "\n", encoding="utf-8")

    print(f"Extended survivors: {len(ext)}; all still present at 100 years: {consistent}")
    print(f"Timeouts: {r4['timeouts']}; endings after 100 years: {r4['labels_after_100']}")
    print("\nR4  Does survival level off?")
    print(f"    Alive at 10 years {r4['alive_10']:.1%}, at 100 years {r4['alive_100']:.1%}: "
          f"lost {r4['loss_10_100']:.1%} from 10 to 100 years")
    lo, hi = r4["loss_100_1000_interval"]
    print(f"    Of {r4['extended_known']} survivors, {r4['extended_alive_1000']} reached 1,000 years: "
          f"lost {r4['loss_100_1000']:.1%} ({lo:.1%} to {hi:.1%}) from 100 to 1,000 years")
    print(f"    Rule: levels off if under {r4['loss_10_100'] / 2:.1%}: "
          f"{'levels off' if r4['levels_off'] else 'does not level off'}")
    print(f"    Estimated alive at 1,000 years: {r4['alive_1000']:.1%} of training moons")
    plt.switch_backend("Agg")
    save(plot(train, ext, r4), "survival_curve_full.png")
    print(f"Saved data/{RESULTS.name}")


if __name__ == "__main__":
    main()
