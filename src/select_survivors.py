"""Choose random training survivors to integrate for 1,000 years.

Run once:  venv/Scripts/python src/select_survivors.py
Then:      venv/Scripts/python src/generate_dataset.py configs/survivors_1000yr.json

The new config is the dataset config with a longer duration and an "ids" list, so the same
moons are integrated again from the start. Their first 100 years repeat the original runs.
"""

import json
import sys

import numpy as np

from explore import load_dataset
from horizons import ROOT

SOURCE = ROOT / "configs" / "dataset.json"
OUTPUT = ROOT / "configs" / "survivors_1000yr.json"
SEED = 20261129
COUNT = 500
YEARS = 1000
MAX_SECONDS = 1800  # the slowest survivor needs about 10 x 104 s


def main():
    if OUTPUT.exists():
        print(f"configs/{OUTPUT.name} already exists.")
        return 1
    train = load_dataset("train")
    survivors = train.loc[train["survived"], "id"].to_numpy()
    rng = np.random.default_rng(SEED)
    ids = sorted(int(i) for i in rng.choice(survivors, COUNT, replace=False))
    config = json.loads(SOURCE.read_text(encoding="utf-8"))
    config.update({
        "description": f"{COUNT} random training survivors of the dataset, integrated for "
                       f"{YEARS:,} years (selection seed {SEED})",
        "duration_days": YEARS * 36525 // 100,
        "max_seconds": MAX_SECONDS,
        "count": COUNT,
        "ids": ids,
    })
    OUTPUT.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(survivors):,} training survivors, {COUNT} chosen. Saved configs/{OUTPUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
