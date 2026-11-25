"""Save NASA's real Moon positions (as seen from Earth) to compare against.

Run once:  venv/Scripts/python src/fetch_reference.py

Only used for checking. The simulation never reads this file.
"""

import argparse
import csv

import numpy as np

from horizons import ROOT, load_state
from simulate import DAY_S, load_config, output_times

REFERENCE_FILE = ROOT / "configs" / "reference_moon.csv"


def fetch():
    """Return (times in seconds since the start, positions in km)."""
    import astropy.units as u
    from astropy.time import Time
    from astroquery.jplhorizons import Horizons

    config = load_config()
    start_jd = load_state()["epoch_jd_tdb"]
    start = Time(start_jd, format="jd", scale="tdb")
    stop = Time(start_jd + config["duration_days"], format="jd", scale="tdb")
    query = Horizons(
        id="301",
        location="500@399",  # center of the Earth
        epochs={"start": start.iso[:16], "stop": stop.iso[:16],
                "step": f"{config['output_interval_hours']}h"},
    )
    table = query.vectors(refplane="ecliptic", aberrations="geometric", cache=False)
    times = (np.array(table["datetime_jd"], dtype=float) - start_jd) * DAY_S
    expected = output_times(config)
    if len(times) != len(expected) or np.abs(times - expected).max() > 1.0:
        raise RuntimeError("Horizons returned different times than requested")
    positions = np.column_stack([
        (np.array(table[c], dtype=float) * table[c].unit).to_value(u.km)
        for c in ("x", "y", "z")
    ])
    return expected, positions


def load_reference():
    """Read the saved positions. Does not use the internet."""
    data = np.loadtxt(REFERENCE_FILE, delimiter=",", skiprows=1)
    return data[:, 0], data[:, 1:4]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace the saved file")
    args = parser.parse_args()
    if REFERENCE_FILE.exists() and not args.force:
        print(f"{REFERENCE_FILE.name} already exists. Use --force to replace it.")
        return

    times, positions = fetch()
    with open(REFERENCE_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["time_s", "x_km", "y_km", "z_km"])
        for t, p in zip(times, positions):
            writer.writerow([f"{t:.0f}", *(f"{value:.6f}" for value in p)])
    print(f"Saved {len(times)} positions to {REFERENCE_FILE}")


if __name__ == "__main__":
    main()
