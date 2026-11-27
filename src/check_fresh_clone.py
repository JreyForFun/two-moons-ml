"""Install and test the project from a fresh clone of the GitHub repository.

Run:  venv/Scripts/python src/check_fresh_clone.py      (about 10 minutes; needs internet)

Clones the published repository into a temporary folder, creates a new virtual environment,
installs requirements.txt and runs the checks that need no generated data. Also reports how much
computing a full regeneration of the data would take. The temporary folder is removed afterwards.
"""

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from horizons import ROOT

DATA_FREE_CHECKS = ("check_setup", "check_initial_state", "check_events", "validate_real_system",
                    "check_second_moon", "check_summary", "check_sampling", "check_generate")


def run(command, cwd, timeout=1800):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def regeneration_cpu_hours():
    """Simulation CPU-hours behind every result, from the manifests and the speed benchmark."""
    parts = {}
    for name in ("dataset", "survivors_1000yr", "twins_1m", "twins_test_1m"):
        manifest = json.loads((ROOT / "configs" / f"{name}_manifest.json").read_text(encoding="utf-8"))
        parts[name] = manifest["computing"]["cpu_hours"]
    pilot_seconds = 0.0
    for path in (ROOT / "data").glob("pilot*.csv"):
        with open(path, encoding="utf-8", newline="") as f:
            pilot_seconds += sum(float(r["result_computing_s"] or 0) for r in csv.DictReader(f))
    parts["pilot runs"] = pilot_seconds / 3600
    speed = json.loads((ROOT / "results" / "phase5_speed.json").read_text(encoding="utf-8"))
    parts["speed benchmark"] = sum(r["seconds"] for r in speed["simulation"]["runs"]) / 3600
    return parts


def main():
    url = run(["git", "remote", "get-url", "origin"], ROOT).stdout.strip()
    base_python = getattr(sys, "_base_executable", sys.executable)
    folder = Path(tempfile.mkdtemp(prefix="two-moons-clone-"))
    repo = folder / "repo"
    passed = True
    try:
        clone = run(["git", "clone", "--depth", "1", url, str(repo)], folder)
        print(f"{'PASS' if clone.returncode == 0 else 'FAIL'}  Clone {url}", flush=True)
        if clone.returncode:
            return 1
        venv = run([base_python, "-m", "venv", "venv"], repo)
        python = repo / "venv" / "Scripts" / "python.exe"
        if not python.exists():
            python = repo / "venv" / "bin" / "python"
        install = run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], repo, 3600)
        ok = venv.returncode == 0 and install.returncode == 0
        passed &= ok
        print(f"{'PASS' if ok else 'FAIL'}  New virtual environment and requirements.txt installed"
              + ("" if ok else f": {install.stderr[-300:]}"), flush=True)
        for check in DATA_FREE_CHECKS:
            result = run([str(python), f"src/{check}.py"], repo)
            ok = result.returncode == 0 and result.stdout.strip().endswith("PASS")
            passed &= ok
            print(f"{'PASS' if ok else 'FAIL'}  {check}", flush=True)
        result = run([str(python), "src/predict.py", "--mass", "0.1", "--distance", "0.4",
                      "--eccentricity", "0", "--inclination", "0"], repo)
        message = (result.stdout + result.stderr).strip()
        ok = result.returncode != 0 and "not stored in Git" in message
        passed &= ok
        print(f"{'PASS' if ok else 'FAIL'}  predict.py without data explains how to obtain it", flush=True)
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    parts = regeneration_cpu_hours()
    print("Simulation CPU-hours for a full regeneration: "
          + ", ".join(f"{k} {v:.2f}" for k, v in parts.items())
          + f"; total {sum(parts.values()):.1f}")
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
