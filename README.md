# What if Earth had 2 moons?

Simulating Earth, the Moon and a hypothetical second moon with N-body gravity
([REBOUND](https://rebound.readthedocs.io/)), then training a machine learning
model to predict the outcome from the starting conditions alone.

Inspired by SPOCK (Tamayo et al., 2020), which uses ML to predict the stability
of planetary systems.

**Status:** Phase 2, dataset generation.

![Both moons orbiting Earth](figures/two_moons.gif)

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

`requirements-lock.txt` lists every installed package version on the development computer (Windows).

## Run

From the project folder (on macOS / Linux use `venv/bin/python` and `/`):

| Command | What it does |
|---|---|
| `venv\Scripts\python src\check_setup.py` | Checks the packages by simulating one simple orbit |
| `venv\Scripts\python src\check_initial_state.py` | Checks the saved NASA data (add `--online` to ask NASA again) |
| `venv\Scripts\python src\horizons.py` | Downloads the NASA data if it is not saved yet |
| `venv\Scripts\python src\simulate.py` | Simulates the real Sun, Earth and Moon for one year |
| `venv\Scripts\python src\check_events.py` | Checks collision and ejection detection |
| `venv\Scripts\python src\fetch_reference.py` | Downloads NASA's Moon positions if not saved yet |
| `venv\Scripts\python src\validate_real_system.py` | Compares the simulated Moon with NASA's |
| `venv\Scripts\python src\plot_real_system.py` | Saves charts to `figures/` |
| `venv\Scripts\python src\simulate.py configs\single_run.json` | Simulates 10 years with a second moon |
| `venv\Scripts\python src\check_second_moon.py` | Checks the second moon's setup, collisions and ejection |
| `venv\Scripts\python src\plot_single_run.py` | Saves charts of the run with a second moon |
| `venv\Scripts\python src\animate.py` | Saves the orbit GIF (takes a few minutes) |
| `venv\Scripts\python src\check_summary.py` | Checks the lightweight simulation mode and its settings |

The walkthrough is in `notebooks/01_first_simulation.ipynb`.

## Folders

| Folder | Contents |
|---|---|
| `configs/` | Starting conditions and simulation settings |
| `src/` | Reusable code |
| `notebooks/` | Exploration |
| `figures/` | Charts and animations |
| `data/` | Generated simulation results (not stored in Git) |

## Known limitations

Bodies are treated with Newtonian gravity only. Other planets, tides, Earth's equatorial bulge
and relativity are not modeled, so results should not be read as predictions
over millions of years.
