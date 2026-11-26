"""Choose random training moons to re-simulate with a 1 m nudge ("chaos twins").

Run once:  venv/Scripts/python src/select_twins.py
Then:      venv/Scripts/python src/generate_dataset.py configs/twins_1m.json

The twin of a moon is the same moon displaced by 1 m along x. Comparing each twin's outcome
with the original measures how much of the outcome is decided by chaos. Twin labels are a
reference only; they are never used to train models.
"""

import json
import sys

import numpy as np

from explore import load_dataset
from horizons import ROOT

SOURCE = ROOT / "configs" / "dataset.json"
OUTPUT = ROOT / "configs" / "twins_1m.json"
SEED = 20261130
COUNT = 1500
SHIFT_M = 1.0


def main():
    if OUTPUT.exists():
        print(f"configs/{OUTPUT.name} already exists.")
        return 1
    train = load_dataset("train")
    rng = np.random.default_rng(SEED)
    ids = sorted(int(i) for i in rng.choice(train["id"].to_numpy(), COUNT, replace=False))
    config = json.loads(SOURCE.read_text(encoding="utf-8"))
    config.update({
        "description": f"Chaos twins: {COUNT} random training moons of the dataset displaced by "
                       f"{SHIFT_M:g} m (selection seed {SEED})",
        "shift_m": SHIFT_M,
        "count": COUNT,
        "ids": ids,
    })
    OUTPUT.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(train):,} training moons, {COUNT} chosen. Saved configs/{OUTPUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
