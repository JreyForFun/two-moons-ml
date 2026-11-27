# Two moons for Earth: simulation data, version 1.0

Data for *The Fate of a Hypothetical Second Moon of Earth: N-body Simulations and a
Machine-Learning Surrogate* (J. R. I. Quizon). Code, documentation and the paper:
<https://github.com/JreyForFun/two-moons-ml> (release v1.0.0). License: CC BY 4.0.

Each simulation integrates the Sun, Earth, Moon and one hypothetical second moon with REBOUND
(IAS15 integrator), starting from JPL Horizons states at 2026-01-01 00:00 TDB (DE440, barycentric
ecliptic frame), for up to 100 years (1,000 years where stated), and stops at the first collision
or ejection. Every file can be regenerated with the code; regenerated files contain the same
moons, outcomes and survival times, but rows appear in completion order and computing times
differ, so their checksums differ from the archived ones.

## Contents

| Path | Rows | Contents |
|---|---:|---|
| `simulations/dataset.csv` | 12,000 | Main dataset: random second moons, 100 years (seed 20261126) |
| `simulations/pilot.csv` | 100 | Pilot reference run, isotropic inclinations, 100 years |
| `simulations/pilot_strict.csv` | 100 | Pilot with integrator tolerance 1e-11 |
| `simulations/pilot_shift.csv` | 100 | Pilot with each second moon displaced by 1 m |
| `simulations/pilot_2026-05-01.csv`, `pilot_2026-09-01.csv` | 30 each | First 30 pilot moons from two other start dates |
| `simulations/survivors_1000yr.csv` | 500 | Random training survivors of the dataset, integrated again to 1,000 years |
| `simulations/twins_1m.csv` | 1,500 | Random training moons of the dataset, displaced by 1 m along x |
| `simulations/twins_test_1m.csv` | 600 | Random test moons of the dataset, displaced by 1 m along x |
| `simulations/single_run_long.csv` | 36,526 | Orbital elements of one second moon (0.1 lunar masses, circular, in the ecliptic, 0.4 lunar distances) and the Moon every 10 days for 1,000 years |
| `simulations/*.info.json` | | Settings and code fingerprint of each batch run |
| `configs/` | | Configuration files, starting states, the train/test split and the manifests (SHA-256, outcome counts, computing time, package versions) |
| `results/` | | Derived results: exploration (Phase 3), model comparison with out-of-fold predictions (Phase 4), the single test-set evaluation and its analysis (Phase 5) |
| `logs/` | | Run logs with start and finish times |
| `SHA256SUMS` | | Checksums of every file in the archive |

The survivor and twin files use the main dataset's seed (20261126), so their `id` values denote
the same second moons as in `dataset.csv`. The pilot files use their own seed (20261125), and their
`id` values denote the same moons across the five pilot files only. `configs/split.json` lists the
2,400 test moons of the main dataset, held out before any analysis.

## Columns of the simulation files

| Column | Unit | Meaning |
|---|---|---|
| `id` | | Index of the second moon; its random generator is seeded by the dataset seed and this index |
| `input_mass_lunar` | lunar masses | Mass of the second moon |
| `input_distance_lunar` | lunar distances (384,400 km) | Initial geocentric semi-major axis |
| `input_eccentricity` | | Initial eccentricity |
| `input_inclination_deg` | degrees | Inclination to the ecliptic; above 90 is retrograde |
| `input_node_deg` | degrees | Longitude of the ascending node |
| `input_periapsis_deg` | degrees | Argument of periapsis |
| `input_true_anomaly_deg` | degrees | Initial true anomaly |
| `input_x_km`, `input_y_km`, `input_z_km` | km | Initial geocentric position of the second moon (ecliptic frame) |
| `input_vx_km_s`, `input_vy_km_s`, `input_vz_km_s` | km/s | Initial geocentric velocity of the second moon |
| `result_label` | | `survived`, `hit_earth`, `hit_moon`, `ejected` or `moon_lost` (the Moon collided with Earth or was ejected) |
| `result_outcome` | | Raw outcome: `survived`, `collision` or `ejection` |
| `result_involved` | | Bodies involved in the event, joined by `+` (empty for survivors) |
| `result_survival_days` | days | Time of the event; for survivors the full duration (36,525 days for 100 years), a lower bound on the lifetime |
| `result_computing_s` | s | Computing time of the run on one core |
| `result_error` | | Error message, if any (empty in all files) |
| `sampling_redraws` | | Number of rejected draws before this one (periapsis inside the Roche limit) |

An ejection is recorded when a body is more than 4.5 million km from Earth on an unbound
geocentric orbit. Collisions use the bodies' physical radii; the second moon has the Moon's density.

`single_run_long.csv`: `years`; the Moon's geocentric osculating semi-major axis (`moon_a_km`),
eccentricity (`moon_e`) and inclination to the ecliptic (`moon_inc_deg`); and the same for the
second moon (`moon2_a_km`, `moon2_e`, `moon2_inc_deg`).

## Model results

`results/phase4/*_oof.csv` hold out-of-fold predictions from nested 5-fold cross-validation on the
9,600 training moons: `id`, the true class `y` and class probabilities `p0` to `p3`, in the class
order `survived`, `ejected`, `hit_earth`, `moon_interaction` (`hit_moon` and `moon_lost`
combined). `results/phase5_test_predictions.csv` holds the predictions of the selected Random
Forest for the 2,400 test moons, from the single evaluation recorded in `results/phase5_test.json`.

## Citation

Cite the paper and this dataset (see `CITATION.cff` in the code repository).
