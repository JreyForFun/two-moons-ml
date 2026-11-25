# What if Earth had 2 moons?

Simulating Earth, the Moon and a hypothetical second moon with N-body gravity
([REBOUND](https://rebound.readthedocs.io/)), then training a machine learning
model to predict the outcome from the starting conditions alone.

Inspired by SPOCK (Tamayo et al., 2020), which uses ML to predict the stability
of planetary systems.

**Status:** Phase 1, setup and first simulation.

## Setup

Requires Python 3.14 (the version used for development).

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

## Folders

| Folder | Contents |
|---|---|
| `configs/` | Starting conditions and simulation settings |
| `src/` | Reusable code |
| `notebooks/` | Exploration |
| `figures/` | Charts and animations |
| `data/` | Generated simulation results (not stored in Git) |

## Known limitations

Bodies are treated with Newtonian gravity only. Tides, Earth's equatorial bulge
and relativity are not modeled, so results should not be read as predictions
over millions of years.
