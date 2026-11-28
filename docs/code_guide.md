# Code guide

How the code in `src/` is organized, how data flows through it, and the conventions it follows.
Commands are listed in the [README](../README.md#reproducing-the-results); terms are defined in
the [glossary](glossary.md).

## Data flow

```text
JPL Horizons ──> horizons.py ──> configs/initial_state.json
                                        │
             sampling.py + second_moon.py (random second moon -> state vectors)
                                        │
             simulate.py (REBOUND, IAS15; collision and ejection detection)
                                        │
             generate_dataset.py ──> data/<batch>.csv ──> make_manifest.py ──> configs/<batch>_manifest.json
                                        │
             split.py ──> configs/split.json (2,400 test moons, set aside before any analysis)
                                        │
        ┌───────────────────────────────┼─────────────────────────────────┐
  exploration                    surrogate models                   test evaluation
  plot_dataset.py                train_models.py                    evaluate_test.py (runs once)
  compare_pilot.py               analyze_models.py                  analyze_test.py
  survival_curve.py              -> configs/selected_model.json     benchmark_speed.py
  -> data/phase3_results.json    -> data/phase4/                    -> results/
        └───────────────────────────────┼─────────────────────────────────┘
                                        │
             paper_numbers.py, plot_paper.py, package_paper.py ──> paper/
             package_data.py ──> dist/two-moons-ml-data-v1.0.zip (Zenodo)
```

## Modules by layer

| Layer | Modules | Role |
|---|---|---|
| Starting state | `horizons.py`, `fetch_reference.py` | Download and store the Sun, Earth and Moon states and the Moon's reference ephemeris; everything else reads the saved files |
| Simulation core | `simulate.py`, `second_moon.py`, `sampling.py`, `labels.py` | Build and run a REBOUND simulation; convert orbital elements to state vectors; draw random second moons; map outcomes to labels |
| Batch generation | `generate_dataset.py`, `make_manifest.py`, `select_survivors.py`, `select_twins.py` | Run many moons in parallel and resumably; record checksums; derive follow-up batches |
| Exploration | `split.py`, `explore.py`, `plot_dataset.py`, `compare_pilot.py`, `survival_curve.py`, `long_run.py`, `analyze_pilot.py` | Train/test split, binned shares with intervals, decision rules R1–R4, pilot analysis |
| Models | `features.py`, `models.py`, `cv.py`, `train_models.py`, `analyze_models.py` | Feature sets, model pipelines, nested cross-validation, rules P1–P6, criteria for the test evaluation |
| Evaluation | `evaluate_test.py`, `analyze_test.py`, `benchmark_speed.py`, `predict.py` | The single test evaluation, failure analysis, timing, and the prediction tool |
| Figures | `plot_style.py`, `plot_real_system.py`, `plot_single_run.py`, `animate.py`, `plot_models.py`, `plot_test.py`, `plot_paper.py`, `make_post_figures.py` | Screen figures (`figures/`), print figures (`paper/figures/`), post images (`figures/post/`) |
| Publication | `paper_numbers.py`, `package_paper.py`, `package_data.py` | Numbers quoted in the paper, compiled manuscripts, data archive |
| Checks | `check_*.py`, `validate_real_system.py` | Automated tests that print PASS or FAIL |

## Script reference

Run times are for the development machine (4 cores); the batch simulations scale with the number
of workers.

| Script | Reads | Writes | Run time |
|---|---|---|---|
| `horizons.py` | JPL Horizons (network) | `configs/initial_state.json`, `configs/state_<date>.json` | seconds |
| `fetch_reference.py` | JPL Horizons (network) | `configs/reference_moon.csv` | seconds |
| `simulate.py` | a configuration | `data/<config>.npz` | seconds |
| `validate_real_system.py` | initial state, reference ephemeris | (prints PASS or FAIL) | seconds |
| `generate_dataset.py` | a batch configuration | `data/<batch>.csv`, `.info.json`, `.log` | dataset about 5 h; survivors about 4.5 h; twins 25–40 min |
| `make_manifest.py` | `data/<batch>.csv` | `configs/<batch>_manifest.json` | seconds |
| `analyze_pilot.py` | `data/pilot*.csv` | pilot figures | seconds |
| `split.py` | dataset, manifest | `configs/split.json` (run once) | seconds |
| `plot_dataset.py` | training moons | `data/phase3_results.json`, stability maps | a few minutes |
| `compare_pilot.py` | pilot, training moons | `data/compare_pilot.json` | a few minutes |
| `select_survivors.py`, `select_twins.py` | dataset, split | follow-up batch configurations (run once) | seconds |
| `survival_curve.py` | training moons, 1,000-year survivors | `data/survival_curve.json`, figure | seconds |
| `long_run.py` | example configuration | `data/single_run_long.csv`, figure | about 7 min |
| `train_models.py` | training moons | `data/phase4/`, `configs/selected_model.json` | `compare` about 1–1.5 h; others minutes |
| `analyze_models.py` | `data/phase4/`, twins | `data/phase4_analysis.json`, criteria | minutes |
| `evaluate_test.py` | selected model, protocol, test moons | `results/phase5_test*.{json,csv}` (once) | a few minutes |
| `benchmark_speed.py` | selected model, training moons | `results/phase5_speed.json` | about 15 min |
| `analyze_test.py` | committed results, test twins | `results/phase5_analysis.json` | seconds |
| `predict.py` | dataset (first run) or cache | prints probabilities | 1–2 min on first run (fits and caches the model), then about 0.1 s |
| `plot_*.py`, `animate.py`, `make_post_figures.py` | results and data | figures | seconds to a few minutes |
| `paper_numbers.py` | results and data | (prints numbers) | seconds |
| `package_paper.py` | `paper/*.tex`, figures | `paper/<name>.pdf`, flat upload bundle `dist/<name>_upload.zip` and `dist/<name>_upload/` | under a minute |
| `package_data.py` | data, configurations, results | `dist/two-moons-ml-data-v1.0.zip` | seconds |

## Conventions

- **Units.** Simulations use km and s, with gravitational parameters GM (km³/s²) in place of
  masses, so G = 1. Second-moon inputs use lunar masses, lunar distances (384,400 km) and degrees.
- **Columns.** In batch files, `input_*` columns describe the initial conditions and may serve as
  model inputs; `result_*` columns describe the outcome and are never used as inputs.
  `features.py` and `check_models.py` enforce this.
- **Randomness.** Every moon has its own generator seeded by (batch seed, id), so a moon's
  parameters do not depend on execution order. All seeds are stored in the configuration files.
- **Test set.** Only `evaluate_test.py` loads test moons for scoring; `features.py` refuses to
  return them, and `check_evaluation.py` verifies that no other script reads them (apart from
  `check_explore.py`, which confirms the split's size and stratification).
- **Frozen files.** `results/`, `configs/split.json`, `configs/selected_model.json` and
  `configs/phase5_protocol.json` are not modified after their commits; `check_release.py`
  verifies this.
- **Outputs.** Generated data go to `data/` (not in Git), committed results to `results/`, screen
  figures to `figures/`, print figures to `paper/figures/`, release bundles to `dist/` (not in Git).
- **Resumability.** Long batches and model training save each finished unit at once; repeating the
  command continues where it stopped.
- **Docstrings.** Each script begins with a one-line summary, a short description of its inputs and
  outputs, and a `Usage:` block.

## Checks

Each `check_*.py` script prints one PASS or FAIL line per test and a final PASS or FAIL; the exit
code is non-zero on failure. Tolerances were fixed before the first run. `check_fresh_clone.py`
installs the project from GitHub in a new environment and runs the checks that need no generated
data; `check_dataset.py`, `check_models.py` and `check_evaluation.py` need the data.

## Adding a simulation batch

1. Write a configuration in `configs/` (copy `dataset.json`; set a new seed, or an `ids` list to
   re-run selected moons, and optionally `shift_m` or `duration_days`).
2. Run `generate_dataset.py` with it; the output goes to `data/<config name>.csv`. A changed
   configuration under an existing name is refused, so earlier data cannot be overwritten.
3. Run `make_manifest.py` to record its checksum, outcome counts and computing time.
