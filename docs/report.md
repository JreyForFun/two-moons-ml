# Technical report

A record of the project, phase by phase: methods, results, decisions and revisions. Terms are
defined in the [glossary](glossary.md); figures are described in the [figure guide](figures.md);
design decisions and open questions are collected in [questions.md](questions.md).

**Status (2026-11-26):** Phase 2 (dataset generation) complete. Phase 3 (exploration and stability
maps) next. A manuscript draft covering Phases 1 and 2 is in [`paper/`](../paper/README.md).

## Simulation log

| Date | Run | Simulations | CPU-hours | Cumulative random second moons |
|---|---|---:|---:|---:|
| 2026-11-25 | Phase 1: real system (with and without the Sun), one 10-year second moon, 60-day animation | 4 | < 0.01 | 0 |
| 2026-11-25 | Pilot A: 100 random moons, 100 years | 100 | 0.19 | 100 |
| 2026-11-25 | Pilot B: same moons, integrator tolerance 10⁻¹¹ | 100 | 0.25 | 200 |
| 2026-11-25 | Pilot C: same moons, second moon displaced by 1 m | 100 | 0.17 | 300 |
| 2026-11-25 | Pilot D: first 30 moons at two other start dates | 60 | 0.10 | 360 |
| 2026-11-26 | Full dataset: 12,000 new moons, 100 years | 12,000 | 20.77 | **12,360** |

Short simulations inside the automated checks are not counted.

---

## Phase 1: simulation setup and validation (2026-11-25)

**Objective:** a gravity simulation validated against real data, and a first Earth system with a
second moon.

### Work

| Step | Content | Commit |
|---|---|---|
| 1 | Environment, folder layout, README | `dce062a` |
| 2 | JPL Horizons starting states and their checks | `5b7f607`, `bd50501` |
| 3 | Simulation of the real Sun-Earth-Moon system, compared with JPL | `0abd341` |
| 4 | Second moon; collision and ejection detection | `3d90f24` |
| 5 | Animation, figures, `notebooks/01_first_simulation.ipynb` | `003af3d` |

### Method

- **Bodies:** Sun, Earth and Moon, with DE440 gravitational parameters and state vectors from JPL
  Horizons at 2026-01-01 00:00 TDB (barycentric, ecliptic frame). Units: km, s.
- **Integrator:** REBOUND 5.2.3 with IAS15 at the default tolerance (ε = 10⁻⁹).
- **Second moon:** specified by orbital elements relative to Earth, converted to a state vector.
  It is given the Moon's density, so its radius scales with mass^(1/3).
- **Collisions:** detected along each integration step (REBOUND "line" detection), so fast
  encounters between output times are not missed.
- **Ejection:** distance from Earth above 4.5 million km and positive Earth-relative orbital
  energy, checked at each output.

### Results

- **Validation:** over one year, the simulated Moon stays within **10.3 km** of the JPL ephemeris
  (mean 5.6 km, about 0.003% of the Earth-Moon distance). The mean orbital period differs from JPL
  by 0.6 s.
- **Role of the Sun:** omitting it increases the error to **55,535 km**.
- **First second moon** (0.1 lunar masses, semi-major axis 0.4 lunar distances, circular, in the
  ecliptic): survives 10 years at 146,072 to 162,087 km from Earth. Its yearly distance range grows
  from 5,847 km to 14,726 km, a factor of about 2.5, showing growing eccentricity.
- **Numerical checks:** relative energy error ≈ 10⁻¹⁵; reruns are bit-for-bit identical; a Moon
  released at rest reaches Earth at 4.384 days, matching the analytic free-fall time.

### Findings

- The setup reproduces the real Moon closely enough to serve as the basis for hypothetical systems.
- The Sun is essential even for a purely Earth-centered question.
- Survival over a fixed time does not imply an unchanging orbit. The dataset therefore treats
  `survived` as a lower bound on lifetime (right-censoring).

### Revisions

- A figure initially described both moons as keeping their distance. Closer inspection showed the
  second moon's band widening, and the title was corrected.
- The energy plot was changed from a line to points, since the values take discrete rounding levels.
- The animation layout is computed once instead of per frame, and the animation uses 1-hour steps.

---

## Phase 2: dataset generation (2026-11-25 to 2026-11-26)

**Objective:** a reproducible dataset of randomly drawn second moons, each simulated and labeled
by outcome, to train a surrogate model.

### Design constraints

- **Computing budget:** a single overnight run of 8 to 10 hours on a laptop (4 worker processes).
- **Orbit directions:** both prograde and retrograde (inclination 0° to 180°).
- **Pilot study first:** remaining settings chosen by a 100-moon pilot, with decision rules fixed
  before the pilot results were seen.

### Work

| Step | Content | Commit |
|---|---|---|
| 2.1 | Lightweight simulation mode (stores only the outcome), tolerance and time-limit settings, full package list | `11c3c96` |
| 2.2 | Random second moons (`src/sampling.py`) and outcome labels (`src/labels.py`) | `67c89c0` |
| 2.3 | Resumable parallel batch runner (`src/generate_dataset.py`) | `dd3862e` |
| 2.4 | Pilot runs and analysis (`src/analyze_pilot.py`) | `dd3862e`, `3f685b1` |
| 2.5 | Inclination option, full dataset configuration, full run, manifest | `8000c85`, `ed0f1d6` |
| 2.6 | Dataset verification (`src/check_dataset.py`) and documentation | `ed0f1d6` |

### Sampling

| Parameter | Range | Distribution |
|---|---|---|
| Mass | 0.001 to 1 lunar masses | log-uniform |
| Semi-major axis | 0.1 to 3 lunar distances (38,440 to 1,153,200 km) | log-uniform |
| Eccentricity | 0 to 0.8 | uniform |
| Inclination | 0° to 180° | pilot: isotropic (uniform in cos *i*); full dataset: uniform in degrees |
| Node, periapsis, true anomaly | 0° to 360° | uniform |

- Orbits with periapsis inside the Roche limit (18,365 km) are redrawn, and the number of redraws
  is recorded.
- Each moon has its own generator seeded by (dataset seed, moon id), so a moon's parameters do not
  depend on the order in which simulations finish.

### Labels

| Label | Definition |
|---|---|
| `survived` | No collision or ejection within 100 years (right-censored) |
| `hit_earth` | Second moon collides with Earth |
| `hit_moon` | Second moon collides with the Moon |
| `ejected` | Second moon becomes unbound from Earth (see glossary) |
| `moon_lost` | The Moon, not the second moon, is ejected or collides with Earth |
| `other`, `timeout`, `error` | Any other ending; computing limit (600 s) exceeded; failed run |

The raw outcome and the bodies involved are stored alongside the label, so labels can be redefined
without new simulations. Columns are prefixed `input_` (possible model features) or `result_`
(outcomes, never used as features) to prevent data leakage.

### Pilot study

The same 100 moons were simulated under controlled variations:

| Run | Variation | Purpose |
|---|---|---|
| A | None | Outcome distribution and computing cost |
| B | Tolerance 10⁻¹¹ instead of 10⁻⁹ | Sensitivity to numerical accuracy |
| C | Second moon displaced by 1 m | Sensitivity to initial conditions (chaos) |
| D | Start dates 2026-05-01 and 2026-09-01 (30 moons each) | Dependence on the start date |

**Pre-registered rules:**
1. Keep the default tolerance if B disagrees with A on at most 3 more moons than C does.
2. Use several start dates if D disagrees with A clearly more than C does.
3. Choose the longest time limit of 10, 30 or 100 years that fits 5,000 moons in 9 hours.
4. Flag any outcome class below 2% for merging or targeted sampling.
5. Revise limits or ranges if more than 2% of runs time out.

**Results:**

- **Outcomes (A, 100 years):** hit Earth 42, ejected 38, survived 18, hit the Moon 1, Moon lost 1.
  No timeouts or errors. Median computing time 1.2 s per moon.
- **Survival over time:** 45% at 10 years, 28% at 30 years, 18% at 100 years.
- **Chaos (C):** a 1 m displacement changes **12 of 100** outcomes at 100 years
  (95% Wilson interval for agreement: 80% to 93%) and 9 of 100 at 10 years.
- **Accuracy (B):** tightening the tolerance changes 6 of 100 outcomes, fewer than the 1 m
  displacement.
- **Start date (D):** agreement 27/30 and 26/30, versus 28/30 for the 1 m displacement on the same
  moons.
- **Cost:** a 100-year limit implies about 2.4 hours for 5,000 moons.

**Decisions:**

| Rule | Observation | Decision |
|---|---|---|
| 1. Tolerance | B differs on 6, C on 12 | Default tolerance (10⁻⁹) |
| 2. Start date | No clear difference from chaos | Single start date |
| 3. Time limit | 100 years fits the budget | 100 years |
| 4. Rare classes | `hit_moon`, `moon_lost` below 2% | Deferred to Phase 4 |
| 5. Timeouts | None | No change |

**Post-hoc decisions** (outside the pre-registered rules, made after reviewing the pilot):

1. **Inclination sampling.** Only 7 of 100 pilot moons had inclinations below 40°, leaving
   near-planar orbits poorly covered. The full dataset samples inclination uniformly in degrees,
   at the cost of over-representing near-planar orbits relative to isotropic orientations.
2. **Dataset size.** The measured cost allowed **12,000** moons instead of 5,000 within the budget.
3. **Independent seed.** The full dataset uses seed 20261126 rather than the pilot's seed, so the
   moons used to make design decisions are not part of the final data.
4. **Interpretation of the chaos test.** The 88% agreement under a 1 m displacement is an
   indicative, not strict, upper bound on predictive accuracy: when outcomes are partly random,
   an optimal predictor can exceed the agreement rate between two noisy realizations.

### Full dataset

- **12,000 moons** in **5.2 hours** wall-clock with 4 workers (20.8 CPU-hours). Median 1.5 s per
  moon, maximum 104 s. The run completed without interruption.

| Outcome | Count | Share |
|---|---:|---:|
| `survived` | 4,554 | 38.0% |
| `ejected` | 3,841 | 32.0% |
| `hit_earth` | 3,288 | 27.4% |
| `hit_moon` | 171 | 1.4% |
| `moon_lost` | 146 | 1.2% |

- **Verification** (`src/check_dataset.py`): no duplicate or missing ids; all parameters within
  their ranges; every input regenerated exactly from the seed; labels consistent with raw outcomes
  and survival times; 20 randomly chosen moons re-simulated with identical results.
- **Provenance:** `configs/dataset_manifest.json` records the CSV's SHA-256, outcome counts,
  computing time and package versions. The CSV itself is regenerated from code and is not stored
  in Git.

### Findings

- **Chaos limits predictability:** about one outcome in eight changes under a 1 m displacement.
- **Most random second moons are short-lived:** under isotropic sampling, 18% survive 100 years.
- **Outcome shares depend on the sampling design:** with inclination uniform in degrees, 38%
  survive. Class shares describe this dataset, not the probability for an arbitrary moon.
- **Automated checks matter:** a change to the inclination code silently altered every pilot moon
  and was caught by `src/check_sampling.py` before the full run.

### Revisions

- Outputs were saved every 24 hours instead of 6 to reduce cost; collision detection is unaffected.
- An early runtime estimate of 11 hours, made from the first few dozen moons while the computer was
  on battery power, overstated the actual 5.2 hours.

---

## Method summary

> We integrate the Sun, Earth, Moon and a hypothetical second moon with REBOUND's IAS15
> integrator, starting from JPL Horizons state vectors (DE440, 2026-01-01 TDB). The setup
> reproduces the lunar ephemeris to within 10.3 km over one year. Second-moon parameters are
> drawn log-uniformly in mass (10⁻³ to 1 lunar masses) and semi-major axis (0.1 to 3 lunar
> distances), uniformly in eccentricity (0 to 0.8), inclination (0° to 180°) and the remaining
> angles, rejecting orbits with periapsis inside the Roche limit. Each system is integrated for up
> to 100 years and labeled by its first terminal event (collision or ejection); systems surviving
> to the limit are right-censored. A pilot study shows that a 1 m perturbation changes 12% of
> outcomes, more than tightening the integrator tolerance (6%). The final dataset contains 12,000
> systems.

## Limitations

- Newtonian point-mass gravity with finite-radius collisions: no tides, no Earth oblateness, no
  general relativity, no other planets.
- `survived` means surviving 100 years, not long-term stability.
- A single start date, supported by a 30-moon test.
- Class shares depend on the chosen parameter ranges and distributions.
