"""Get Sun, Earth and Moon starting states from NASA JPL Horizons.

Run once from the project root:  venv/Scripts/python src/horizons.py
Another start date:              venv/Scripts/python src/horizons.py --date 2026-05-01
The result is saved to configs/initial_state.json. Everything else reads that
file, so reruns need no internet and always start from identical numbers.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "configs" / "initial_state.json"

EPOCH_TDB = "2026-01-01 00:00:00"
CENTER = "500@0"  # Solar System barycenter (the center of mass)

# GM (gravity strength) is used instead of mass because GM is measured far more
# precisely than G or the mass alone. GM: JPL DE440 (Park et al., 2021).
# Radii are for collision detection: IAU nominal Sun, mean Earth and Moon.
BODIES = {
    "sun": {"horizons_id": "10", "gm_km3_s2": 132712440041.279419, "radius_km": 695700.0},
    "earth": {"horizons_id": "399", "gm_km3_s2": 398600.435507, "radius_km": 6371.0084},
    "moon": {"horizons_id": "301", "gm_km3_s2": 4902.800118, "radius_km": 1737.4},
}


def fetch_state(epoch_tdb=EPOCH_TDB):
    """Download the state vectors and return them as a JSON-ready dictionary."""
    # Imported here so that loading the saved file needs no astroquery/internet.
    import astropy.units as u
    import astroquery
    from astropy.time import Time
    from astroquery.jplhorizons import Horizons

    epoch_jd = Time(epoch_tdb, scale="tdb").jd
    bodies = {}
    for name, info in BODIES.items():
        query = Horizons(id=info["horizons_id"], location=CENTER, epochs=epoch_jd)
        table = query.vectors(refplane="ecliptic", aberrations="geometric", cache=False)
        if len(table) != 1:
            raise RuntimeError(f"Expected 1 row for {name}, got {len(table)}")
        row = table[0]
        if abs(float(row["datetime_jd"]) - epoch_jd) > 1e-9:
            raise RuntimeError(f"Wrong epoch returned for {name}")
        bodies[name] = {
            **info,
            "horizons_name": str(row["targetname"]),
            "position_km": [
                float((row[c] * table[c].unit).to_value(u.km)) for c in ("x", "y", "z")
            ],
            "velocity_km_s": [
                float((row[c] * table[c].unit).to_value(u.km / u.s))
                for c in ("vx", "vy", "vz")
            ],
            "query_url": query.uri,
        }

    return {
        "source": "NASA JPL Horizons via astroquery",
        "astroquery_version": astroquery.__version__,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "epoch_tdb": epoch_tdb,
        "epoch_jd_tdb": float(epoch_jd),
        "center": "Solar System barycenter",
        "frame": "ICRF axes rotated to the J2000 ecliptic",
        "aberrations": "geometric (true positions, no light-time correction)",
        "units": {"position": "km", "velocity": "km/s", "gm": "km^3/s^2", "radius": "km"},
        "gm_source": "JPL DE440 (Park et al., 2021)",
        "bodies": bodies,
    }


def load_state(path=STATE_FILE):
    """Read the saved state. Does not use the internet."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace the saved file")
    parser.add_argument("--date", help="start date like 2026-05-01, saved to its own file")
    args = parser.parse_args()

    path = ROOT / "configs" / f"state_{args.date}.json" if args.date else STATE_FILE
    if path.exists() and not args.force:
        print(f"{path.name} already exists. Use --force to replace it.")
        return

    state = fetch_state(f"{args.date} 00:00:00" if args.date else EPOCH_TDB)
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    print(f"Saved configs/{path.name}")


if __name__ == "__main__":
    main()
