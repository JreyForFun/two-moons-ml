"""Animation of the Moon and a second moon orbiting Earth (figures/two_moons.gif).

Usage:
    python src/animate.py
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from horizons import ROOT, load_state
from plot_single_run import MOONS
from plot_style import FIGURES, GRID, INK, MUTED_INK, SURFACE, add_legend, new_chart, set_titles
from simulate import DAY_S, load_config, run

CONFIG = ROOT / "configs" / "single_run.json"
DAYS = 60
STEP_HOURS = 1
STEPS_PER_FRAME = 6  # 6 h per frame
TAIL_STEPS = 120  # 5-day trail
FRAMES_PER_SECOND = 20


def make_animation(result):
    """One frame every 6 hours, seen from above the plane of Earth's orbit."""
    fig, ax = new_chart(6.4, 7)
    ax.set_aspect("equal")
    ax.set_xlim(-430, 430)
    ax.set_ylim(-430, 430)
    ax.set_xlabel("x (thousand km)", color=MUTED_INK)
    ax.set_ylabel("y (thousand km)", color=MUTED_INK)
    ax.plot(0, 0, "o", color=INK, markersize=12)
    ax.annotate("Earth", (0, 0), xytext=(0, -24), textcoords="offset points",
                ha="center", color=INK)

    paths, tails, dots = [], [], []
    for (name, label, color), size in zip(MOONS, (9, 6)):
        path = result.relative(name)[:, :2] / 1000
        paths.append(path)
        ax.plot(path[:, 0], path[:, 1], color=GRID, linewidth=0.8, zorder=1)
        tails.append(ax.plot([], [], color=color, linewidth=2)[0])
        dots.append(ax.plot([], [], "o", color=color, markersize=size, label=label,
                            markeredgecolor=SURFACE)[0])
    add_legend(ax, loc="upper right")
    day_text = ax.text(0.02, 0.97, "", transform=ax.transAxes, color=INK, va="top",
                       fontsize=12)
    set_titles(ax, "Earth with two moons",
               "Distances to scale, bodies not to scale. Second moon: 0.1 lunar masses")

    fig.canvas.draw()  # fix the layout once, not per frame
    fig.set_layout_engine("none")

    def draw(frame):
        step = frame * STEPS_PER_FRAME
        first = max(0, step - TAIL_STEPS)
        for path, tail, dot in zip(paths, tails, dots):
            tail.set_data(path[first:step + 1, 0], path[first:step + 1, 1])
            dot.set_data(path[step:step + 1, 0], path[step:step + 1, 1])
        day_text.set_text(f"Day {result.times_s[step] / DAY_S:.0f}")
        return tails + dots + [day_text]

    frames = (len(result.times_s) - 1) // STEPS_PER_FRAME + 1
    return FuncAnimation(fig, draw, frames=frames, blit=False), fig


def main():
    plt.switch_backend("Agg")  # non-interactive backend
    config = {**load_config(CONFIG), "duration_days": DAYS,
              "output_interval_hours": STEP_HOURS}
    result = run(load_state(), config)
    animation, fig = make_animation(result)
    FIGURES.mkdir(exist_ok=True)
    animation.save(FIGURES / "two_moons.gif", writer=PillowWriter(fps=FRAMES_PER_SECOND),
                   dpi=100)
    plt.close(fig)
    print("Saved figures/two_moons.gif")


if __name__ == "__main__":
    main()
