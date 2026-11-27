"""Manifest of a finished dataset: SHA-256 checksum, outcome counts, computing time and
package versions.

The CSV is not stored in Git; the committed manifest identifies the exact file from which the
results were produced.

Usage:
    python src/make_manifest.py configs/dataset.json
"""

import argparse
import hashlib
import json
import platform
import re
import statistics
import sys
from collections import Counter
from datetime import date
from importlib import metadata
from pathlib import Path

from generate_dataset import fingerprint, read_rows, state_path
from horizons import ROOT
from labels import LABELS
from simulate import load_config

PACKAGES = ("rebound", "astroquery", "astropy", "numpy", "matplotlib", "pillow", "jupyter",
            "pandas")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def read_log(path):
    """Start, finish and workers from the progress log, if it was kept."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    found = {
        "started": re.findall(r"^started (.+)$", text, re.M),
        "finished": re.findall(r"^finished (\S+ \S+)", text, re.M),
        "workers": re.findall(r"(\d+) workers$", text, re.M),
    }
    return {
        "started": found["started"][0] if found["started"] else None,
        "finished": found["finished"][-1] if found["finished"] else None,
        "workers": int(found["workers"][0]) if found["workers"] else None,
        "times_started": len(found["started"]),  # > 1 if the batch was resumed
    }


def build_manifest(config_path):
    config = load_config(config_path)
    csv_path = ROOT / "data" / f"{config_path.stem}.csv"
    rows = read_rows(csv_path)
    with open(state_path(config), encoding="utf-8") as f:
        state = json.load(f)

    labels = Counter(row["result_label"] for row in rows)
    seconds = [float(row["result_computing_s"]) for row in rows if row["result_computing_s"]]
    return {
        "description": config.get("description", ""),
        "created": date.today().isoformat(),
        "data_file": relative(csv_path),
        "data_sha256": sha256(csv_path),
        "data_bytes": csv_path.stat().st_size,
        "rows": len(rows),
        "config_file": relative(config_path),
        "config_sha256": sha256(config_path),
        "state_file": relative(state_path(config)),
        "state_sha256": sha256(state_path(config)),
        "fingerprint": fingerprint(config, state),
        "labels": {label: labels[label] for label in LABELS},
        "censored_note": "survived = still there at the time limit (lasted at least that long)",
        "computing": {
            "cpu_hours": round(sum(seconds) / 3600, 2),
            "median_s_per_moon": round(statistics.median(seconds), 3),
            "largest_s": round(max(seconds), 3),
            **read_log(csv_path.with_suffix(".log")),
        },
        "environment": {
            "python": platform.python_version(),
            "system": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "packages": {name: metadata.version(name) for name in PACKAGES},
            "full_list": "requirements-lock.txt",
            "full_list_sha256": sha256(ROOT / "requirements-lock.txt"),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    manifest = build_manifest(args.config)
    path = ROOT / "configs" / f"{args.config.stem}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2))
    print(f"Saved configs/{path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
