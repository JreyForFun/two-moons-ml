"""Images and video for a social-media post about the project.

Run:  venv/Scripts/python src/make_post_figures.py      (needs the generated data in data/)

Saves to figures/post/: five carousel slides (1080 x 1350 px PNG, and all five in carousel.pdf)
and a 1200 x 627 px cover image; and figures/two_moons.mp4, the orbit animation as an H.264
video. Numbers come from the same result files as the paper.
"""

import json
import sys

import imageio_ffmpeg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

import explore
from horizons import ROOT
from plot_dataset import I_COL, distance_axis, draw_map
from plot_style import BLUE, FIGURES, GRID, INK, MUTED_INK, ORANGE

POST = FIGURES / "post"
SLIDE = (7.2, 9.0)   # inches at 150 dpi = 1080 x 1350 px
COVER = (8.0, 4.18)  # inches at 150 dpi = 1200 x 627 px
DPI = 150
LINK = "github.com/JreyForFun/two-moons-ml"
STYLE = {"font.size": 13, "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
         "axes.labelcolor": MUTED_INK, "figure.facecolor": "white", "savefig.facecolor": "white"}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def slide(number, title, subtitle, footer_link=True):
    """Blank slide with a title block and a footer."""
    fig = plt.figure(figsize=SLIDE)
    fig.text(0.07, 0.94, title, fontsize=25, fontweight="bold", color=INK, va="top")
    fig.text(0.07, 0.835, subtitle, fontsize=14, color=MUTED_INK, va="top", linespacing=1.4)
    if footer_link:
        fig.text(0.07, 0.03, LINK, fontsize=11, color=MUTED_INK)
    fig.text(0.93, 0.03, f"{number} / 5", fontsize=11, color=MUTED_INK, ha="right")
    return fig


def plain(ax):
    ax.set_facecolor("white")
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", colors=MUTED_INK, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def orbits(ax, days=60):
    """Geocentric paths of the Moon and the second moon from the Phase 1 run."""
    run = np.load(ROOT / "data" / "single_run.npz")
    bodies = list(run["bodies"])
    keep = run["times_s"] <= days * 86400
    earth = run["positions_km"][keep, bodies.index("earth")]
    for name, color, size, label, offset, align in (
            ("moon", BLUE, 16, "Moon", (12, 8), "left"),
            ("moon2", ORANGE, 11, "Second moon", (-12, -16), "right")):
        path = (run["positions_km"][keep, bodies.index(name)] - earth) / 1000
        ax.plot(path[:, 0], path[:, 1], color=color, linewidth=1.6, alpha=0.55)
        ax.plot(path[-1, 0], path[-1, 1], "o", color=color, markersize=size,
                markeredgecolor="white", markeredgewidth=2)
        ax.annotate(label, (path[-1, 0], path[-1, 1]), xytext=offset, textcoords="offset points",
                    fontsize=14, color=INK, ha=align)
    ax.plot(0, 0, "o", color=INK, markersize=26)
    ax.annotate("Earth", (0, 0), xytext=(0, -30), textcoords="offset points", ha="center",
                fontsize=14, color=INK)
    ax.set_aspect("equal")
    ax.set_xlim(-430, 430)
    ax.set_ylim(-430, 430)
    ax.axis("off")


def slide_question():
    fig = slide(1, "What if Earth had\ntwo moons?",
                "12,000 simulated second moons, real NASA starting data,\n"
                "and a machine-learning model that predicts their fate.")
    orbits(fig.add_axes([0.08, 0.1, 0.84, 0.66]))
    return fig


def slide_map():
    fig = slide(2, "Where a second moon\nsurvives 100 years",
                "Share surviving, by distance from Earth and tilt of the orbit\n"
                "(9,600 simulated moons)")
    ax = plain(fig.add_axes([0.15, 0.17, 0.72, 0.6]))
    mesh, _ = draw_map(ax, explore.load_dataset("train"), I_COL)
    distance_axis(ax, label=False)
    ax.set_xlabel("Distance from Earth (Moon distances)")
    ax.set_yticks([7.5, 90, 172.5], ["flat", "on its\nside", "flat,\nbackwards"])
    ax.axvline(1.0, color=INK, linewidth=1.5, linestyle="--")
    ax.annotate("Moon's orbit", (1.0, 183), xytext=(4, 0), textcoords="offset points",
                fontsize=12, color=INK, annotation_clip=False)
    bar = fig.colorbar(mesh, ax=ax, orientation="horizontal", fraction=0.04, pad=0.14)
    bar.set_label("Share surviving (dark = most survive)", color=MUTED_INK)
    bar.ax.tick_params(colors=MUTED_INK, length=0)
    bar.outline.set_visible(False)
    bar.set_ticks([0, 0.5, 1], labels=["0%", "50%", "100%"])
    return fig


def slide_chaos():
    chaos = load("data/phase4_analysis.json")["chaos"]
    rows = chaos["by_distance"]
    fig = slide(3, "Chaos: a 1-meter nudge\nchanges the outcome",
                f"Moving a second moon by 1 m at the start changes its fate\n"
                f"in {100 - chaos['agreement'] * 100:.0f}% of cases, mostly near the Moon's orbit")
    ax = plain(fig.add_axes([0.15, 0.13, 0.78, 0.6]))
    centers = [np.sqrt(r["low"] * r["high"]) for r in rows]
    share = np.array([r["changed"] for r in rows]) * 100
    low = np.array([r["interval"][0] for r in rows]) * 100
    high = np.array([r["interval"][1] for r in rows]) * 100
    ax.fill_between(centers, low, high, color=ORANGE, alpha=0.2, linewidth=0)
    ax.plot(centers, share, color=ORANGE, linewidth=3, marker="o", markersize=10,
            markeredgecolor="white", markeredgewidth=2)
    ax.set_xscale("log")
    ticks = [0.1, 0.2, 0.5, 1, 2, 3]
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.axvline(1.0, color=INK, linewidth=1.5, linestyle="--")
    ax.annotate("Moon's orbit", (1.0, ax.get_ylim()[1]), xytext=(5, -16),
                textcoords="offset points", fontsize=12, color=INK)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_xlabel("Distance from Earth (Moon distances)")
    ax.set_ylabel("Outcomes changed by the nudge")
    return fig


def slide_accuracy():
    test = load("results/phase5_test.json")["metrics"]
    bars = (("Always guess\n\"survives\"", test["majority"]["accuracy"], GRID),
            ("Simple physics\nrule", test["physics_rule"]["accuracy"], "#a9a8a2"),
            ("Machine-learning\nmodel", test["selected"]["accuracy"], BLUE))
    fig = slide(4, "A model predicts the fate\nof unseen moons",
                "Share of correct predictions for 2,400 moons the model\n"
                "never saw, tested once at the very end")
    ax = plain(fig.add_axes([0.1, 0.13, 0.82, 0.6]))
    ax.grid(axis="x", visible=False)
    x = np.arange(len(bars))
    ax.bar(x, [b[1] * 100 for b in bars], color=[b[2] for b in bars], width=0.6)
    for i, (_, value, _) in enumerate(bars):
        ax.annotate(f"{value * 100:.1f}%", (i, value * 100), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=18, fontweight="bold",
                    color=INK)
    ax.set_xticks(x, [b[0] for b in bars], fontsize=13, color=INK)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    return fig


def slide_speed():
    speed = load("results/phase5_speed.json")
    sim, model, s = speed["simulation"], speed["model"], speed["speedup"]
    fig = slide(5, f"About {round(s['batch_vs_mean'], -4):,.0f} times faster\nthan simulating",
                f"Time per moon. One prediction is {s['same_machine_median']:.0f} times faster than\n"
                "a typical simulation; many moons at once, far faster still",
                footer_link=False)
    ax = plain(fig.add_axes([0.36, 0.2, 0.56, 0.5]))
    rows = (("Simulation,\ntypical moon", sim["median_s"], MUTED_INK, f"{sim['median_s']:.1f} s"),
            ("Model,\none moon", model["latency_median_s"], BLUE,
             f"{model['latency_median_s']:.2f} s"),
            ("Model,\nmany moons", model["batch_per_moon_s"], BLUE,
             f"{model['batch_per_moon_s'] * 1e6:.0f} µs"))
    y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.55)
    ax.set_xscale("log")
    ax.invert_yaxis()
    ax.set_yticks(y, [r[0] for r in rows], fontsize=13, color=INK)
    for i, row in enumerate(rows):
        ax.annotate(row[3], (row[1], i), xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=16, fontweight="bold", color=INK)
    ax.set_xlim(3e-5, 200)
    ax.set_xticks([1e-4, 1e-2, 1], ["0.0001 s", "0.01 s", "1 s"])
    ax.grid(axis="y", visible=False)
    fig.text(0.07, 0.07, "Code, data and paper: " + LINK, fontsize=12.5, color=INK,
             fontweight="bold")
    return fig


def cover():
    fig = plt.figure(figsize=COVER)
    fig.text(0.05, 0.8, "What if Earth had\ntwo moons?", fontsize=26, fontweight="bold",
             color=INK, va="top")
    fig.text(0.05, 0.42, "12,000 N-body simulations\nand a machine-learning surrogate\n"
             "that predicts each moon's fate", fontsize=13, color=MUTED_INK, va="top",
             linespacing=1.4)
    fig.text(0.05, 0.08, LINK, fontsize=10, color=MUTED_INK)
    orbits(fig.add_axes([0.52, 0.04, 0.46, 0.92]))
    return fig


def make_video():
    """The orbit GIF as an H.264 MP4 at the same frame rate."""
    gif = Image.open(FIGURES / "two_moons.gif")
    fps = 1000 / gif.info["duration"]
    frames = []
    for k in range(gif.n_frames):
        gif.seek(k)
        frames.append(np.asarray(gif.convert("RGB")))
    height, width = frames[0].shape[:2]
    writer = imageio_ffmpeg.write_frames(str(FIGURES / "two_moons.mp4"), (width, height), fps=fps,
                                         codec="libx264", pix_fmt_out="yuv420p", quality=8,
                                         macro_block_size=2)
    writer.send(None)
    for frame in frames:
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    return len(frames), fps


def main():
    plt.switch_backend("Agg")
    POST.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE), PdfPages(POST / "carousel.pdf") as pdf:
        for k, draw in enumerate((slide_question, slide_map, slide_chaos, slide_accuracy,
                                  slide_speed), start=1):
            fig = draw()
            fig.savefig(POST / f"slide{k}.png", dpi=DPI)
            pdf.savefig(fig)
            plt.close(fig)
            print(f"Saved figures/post/slide{k}.png")
        fig = cover()
        fig.savefig(POST / "cover.png", dpi=DPI)
        plt.close(fig)
    print("Saved figures/post/carousel.pdf and figures/post/cover.png")
    frames, fps = make_video()
    print(f"Saved figures/two_moons.mp4 ({frames} frames at {fps:.0f} fps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
