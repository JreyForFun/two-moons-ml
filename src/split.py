"""Set aside a test set before any exploration or modeling.

Run once:  venv/Scripts/python src/split.py

20% of the moons, stratified by label (each label keeps its share), are written to
configs/split.json. Exploration and model development use only the remaining training
moons; the test moons are used once, for the final evaluation.
"""

import json
import sys
from collections import Counter

import numpy as np

from generate_dataset import read_rows
from horizons import ROOT
from make_manifest import sha256

DATASET = ROOT / "data" / "dataset.csv"
MANIFEST = ROOT / "configs" / "dataset_manifest.json"
SPLIT_FILE = ROOT / "configs" / "split.json"
SEED = 20261127
TEST_SHARE = 0.2


def make_split(rows, seed=SEED, test_share=TEST_SHARE):
    """Return sorted test ids: the same share drawn from every label."""
    rng = np.random.default_rng(seed)
    by_label = {}
    for row in sorted(rows, key=lambda r: int(r["id"])):
        by_label.setdefault(row["result_label"], []).append(int(row["id"]))
    test = []
    for label in sorted(by_label):
        ids = by_label[label]
        size = round(len(ids) * test_share)
        test.extend(int(i) for i in rng.choice(ids, size, replace=False))
    return sorted(test)


def main():
    if SPLIT_FILE.exists():
        print(f"configs/{SPLIT_FILE.name} already exists; the test set must not change.")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(DATASET) != manifest["data_sha256"]:
        raise SystemExit("data/dataset.csv does not match the manifest")
    rows = read_rows(DATASET)
    test = set(make_split(rows))
    labels = Counter(r["result_label"] for r in rows)
    test_labels = Counter(r["result_label"] for r in rows if int(r["id"]) in test)
    split = {
        "description": "Held-out test set, stratified by label. Not used until final evaluation.",
        "dataset_sha256": manifest["data_sha256"],
        "seed": SEED,
        "test_share": TEST_SHARE,
        "counts": {"train": len(rows) - len(test), "test": len(test)},
        "test_labels": dict(sorted(test_labels.items())),
        "train_labels": {k: labels[k] - test_labels[k] for k in sorted(labels)},
        "test_ids": sorted(test),
    }
    SPLIT_FILE.write_text(json.dumps(split, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in split.items() if k != "test_ids"}, indent=2))
    print(f"Saved configs/{SPLIT_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
