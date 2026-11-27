"""Build the data archive for Zenodo.

Run:  venv/Scripts/python src/package_data.py

Writes dist/two-moons-ml-data-v1.0.zip with the simulation files, their run records and logs,
the configurations and manifests, the derived results, docs/data_archive.md as README.md and a
SHA256SUMS file. The main CSV files are first checked against the SHA-256 checksums in their
committed manifests. Files are added in a fixed order with a fixed timestamp, so the same inputs
give a byte-identical archive.
"""

import hashlib
import json
import sys
import zipfile

from horizons import ROOT

VERSION = "1.0"
NAME = f"two-moons-ml-data-v{VERSION}"
DATA, CONFIGS, RESULTS = ROOT / "data", ROOT / "configs", ROOT / "results"
TIMESTAMP = (2026, 11, 28, 0, 0, 0)
BATCHES = ("dataset", "pilot", "pilot_strict", "pilot_shift", "pilot_2026-05-01",
           "pilot_2026-09-01", "survivors_1000yr", "twins_1m", "twins_test_1m")
MANIFESTED = ("dataset", "survivors_1000yr", "twins_1m", "twins_test_1m")
LOGS = ("dataset", "survivors_1000yr", "twins_1m", "twins_test_1m", "phase4", "phase5_test",
        "phase5_speed")
DERIVED = ("phase3_results.json", "compare_pilot.json", "survival_curve.json",
           "phase4_analysis.json")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def members():
    """(path in archive, source file) pairs, in a fixed order."""
    files = [("README.md", ROOT / "docs" / "data_archive.md")]
    for name in BATCHES:
        files.append((f"simulations/{name}.csv", DATA / f"{name}.csv"))
        files.append((f"simulations/{name}.info.json", DATA / f"{name}.info.json"))
    files.append(("simulations/single_run_long.csv", DATA / "single_run_long.csv"))
    for path in sorted(CONFIGS.iterdir()):
        files.append((f"configs/{path.name}", path))
    for name in DERIVED:
        files.append((f"results/{name}", DATA / name))
    for path in sorted((DATA / "phase4").iterdir()):
        files.append((f"results/phase4/{path.name}", path))
    for path in sorted(RESULTS.iterdir()):
        files.append((f"results/{path.name}", path))
    for name in LOGS:
        files.append((f"logs/{name}.log", DATA / f"{name}.log"))
    return files


def check_manifests():
    problems = []
    for name in MANIFESTED:
        manifest = json.loads((CONFIGS / f"{name}_manifest.json").read_text(encoding="utf-8"))
        if sha256_bytes((DATA / f"{name}.csv").read_bytes()) != manifest["data_sha256"]:
            problems.append(f"data/{name}.csv differs from its manifest")
    return problems


def main():
    files = members()
    missing = [str(src.relative_to(ROOT)) for _, src in files if not src.exists()]
    problems = [f"missing {m}" for m in missing] or check_manifests()
    for problem in problems:
        print(f"FAIL  {problem}")
    if problems:
        return 1
    target = ROOT / "dist" / f"{NAME}.zip"
    target.parent.mkdir(exist_ok=True)
    sums = []
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, source in files:
            data = source.read_bytes()
            sums.append(f"{sha256_bytes(data)}  {arcname}")
            info = zipfile.ZipInfo(f"{NAME}/{arcname}", TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        info = zipfile.ZipInfo(f"{NAME}/SHA256SUMS", TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, "\n".join(sums) + "\n")
    size = target.stat().st_size / 1e6
    print(f"PASS  {len(MANIFESTED)} data files match their manifests")
    print(f"Saved dist/{target.name}: {len(files) + 1} files, {size:.1f} MB, "
          f"SHA-256 {sha256_bytes(target.read_bytes())}")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
