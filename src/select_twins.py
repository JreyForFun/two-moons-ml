"""Choose moons to re-simulate with a 1 m nudge ("chaos twins").

Run once:  venv/Scripts/python src/select_twins.py           1,500 training moons (Phase 4)
           venv/Scripts/python src/select_twins.py --test    600 test moons (Phase 5, only after
                                                            the test evaluation is committed)
Then:      venv/Scripts/python src/generate_dataset.py configs/twins_1m.json
           venv/Scripts/python src/generate_dataset.py configs/twins_test_1m.json

The twin of a moon is the same moon displaced by 1 m along x. Comparing each twin's outcome
with the original measures how much of the outcome is decided by chaos. Twin labels are a
reference only; they are never used to train models.
"""

import argparse
import json
import sys

import numpy as np

from explore import SPLIT_FILE, load_dataset
from horizons import ROOT

SOURCE = ROOT / "configs" / "dataset.json"
SHIFT_M = 1.0
SETS = {
    "train": {"output": ROOT / "configs" / "twins_1m.json", "seed": 20261130, "count": 1500},
    "test": {"output": ROOT / "configs" / "twins_test_1m.json", "seed": 20261205, "count": 600},
}


def candidate_ids(part):
    if part == "train":
        return load_dataset("train")["id"].to_numpy()
    if not (ROOT / "results" / "phase5_test.json").exists():
        raise SystemExit("The test evaluation must be committed before test moons are re-simulated.")
    # Test ids come from the split file only; no test results are read here.
    return np.array(sorted(json.loads(SPLIT_FILE.read_text(encoding="utf-8"))["test_ids"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", action="store_true", help="choose test moons (Phase 5)")
    part = "test" if parser.parse_args().test else "train"
    spec = SETS[part]
    if spec["output"].exists():
        print(f"configs/{spec['output'].name} already exists.")
        return 1
    pool = candidate_ids(part)
    rng = np.random.default_rng(spec["seed"])
    ids = sorted(int(i) for i in rng.choice(pool, spec["count"], replace=False))
    config = json.loads(SOURCE.read_text(encoding="utf-8"))
    config.update({
        "description": f"Chaos twins: {spec['count']} random {part} moons of the dataset displaced "
                       f"by {SHIFT_M:g} m (selection seed {spec['seed']})",
        "shift_m": SHIFT_M,
        "count": spec["count"],
        "ids": ids,
    })
    spec["output"].write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(pool):,} {part} moons, {spec['count']} chosen. Saved configs/{spec['output'].name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
