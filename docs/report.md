# Technical report

A record of the project, phase by phase: methods, results, decisions and revisions. Terms are
defined in the [glossary](glossary.md); figures are described in the [figure guide](figures.md);
design decisions and open questions are collected in [questions.md](questions.md).

**Status (2026-11-28):** complete (release v1.0.0). The paper and its Research Notes version are
in [`paper/`](../paper/README.md); a plain-language summary is in [summary.md](summary.md).

## Key findings

Evidence strength:
- **Verified:** an automated check or a direct measurement.
- **Rule met** or **rule not met:** a pre-registered criterion, reported either way.
- **Descriptive:** a pattern identified after inspecting the data.

Model scores are confirmed on the held-out test set (Phase 5) unless marked cross-validated.

| # | Finding | Key numbers | Evidence | Figure |
|---|---|---|---|---|
| 1 | The simulation reproduces the real Moon, and the Sun is essential | 10.3 km error after one year; 55,535 km without the Sun | Verified | [real_moon_error](figures.md#real_moon_errorpng) |
| 2 | Most random second moons do not last; the share depends on the sampling design | 38.0% survive 100 years (29.7% with isotropic inclinations); 32.0% ejected; 27.4% hit Earth | Verified | [stability_map](figures.md#stability_mappng) |
| 3 | Chaos limits predictability, mainly near the Moon's orbit | A 1 m nudge changes 7.7% of outcomes (20.3% at 0.55–0.97 lunar distances, none inside 0.31) | Verified (1,500 twins) | [chaos_profile](figures.md#chaos_profilepng) |
| 4 | Survival is concentrated on close orbits near the ecliptic plane, prograde or retrograde | 96.5% survive inside 0.5 lunar distances below 45° or above 135° inclination; 3.0% of Moon-crossing orbits survive | Descriptive (maps reproducible, r = 0.99) | [stability_map_eccentricity](figures.md#stability_map_eccentricitypng) |
| 5 | Near-polar orbits are driven into Earth, consistent with Lidov–Kozai cycles | 99.1% of close near-polar moons collide with Earth | Descriptive; mechanism inferred | [outcome_maps](figures.md#outcome_mapspng) |
| 6 | The Moon, not the Sun, sets the outer limit; beyond it, survivors are almost all retrograde | Both directions drop below 10% survival at 0.22 Hill radii; beyond the Moon 11.4% retrograde vs 0.3% prograde survive | R2 not met (edge); difference descriptive | [survival_by_direction](figures.md#survival_by_directionpng) |
| 7 | Heavier second moons survive less, partly by destabilizing the Moon | 30.9% vs 42.3% survival (heaviest vs lightest bin); Moon lost in 7.4% vs 0% | R3 met | — |
| 8 | Losses continue beyond 100 years, more slowly | 21.4% of 100-year survivors lost by 1,000 years; about 30% of systems would last 1,000 years | R4 not met (no levelling off) | [survival_curve_full](figures.md#survival_curve_fullpng) |
| 9 | The pilot-versus-dataset survival gap is explained without a code change | 37.9% → 29.7% (sampling) → 25.4% (pilot draws) → 18% (noise, 2.1σ) | R1 not met; investigated | — |
| 10 | A two-variable physics rule already captures the main structure | Depth-3 tree on apoapsis and \|cos *i*\|: 79.5% accuracy | Verified (cross-validated) | — |
| 11 | Orbital elements are far better model inputs than state vectors | Macro-F1 lower by 0.086 for vectors; physics features add 0.006 | Rule P1 met | — |
| 12 | A Random Forest predicts the outcome from the starting conditions alone, and generalizes | Test: 85.1% accuracy, macro-F1 0.711 (cross-validated 85.0%, 0.723); physics rule 78.9%, majority 38.0% | Rules P2, P3 met; criteria C1, C1b, C2 met on test | [test_vs_cv](figures.md#test_vs_cvpng) |
| 13 | Its survival probabilities are trustworthy | Test ECE 0.019 (every class ≤ 0.030); ROC AUC 0.988 | Rule P6 and criterion C3 met | [test_calibration](figures.md#test_calibrationpng) |
| 14 | Its errors concentrate on chaotic systems near the Moon's orbit; more data would help little | Test error 53.8% on chaotic vs 11.3% on stable systems; macro-F1 0.700 → 0.723 with 10× data (cross-validated) | Rules P5 and T5 met; learning curve | [error_map](figures.md#error_mappng) |
| 15 | The model relies on the same physics: distance and inclination | Importance 0.31 (distance), 0.24 (inclination), 0.075 (mass) | Descriptive | [feature_importance](figures.md#feature_importancepng) |
| 16 | Collisions with the Moon remain hard to predict | `moon_interaction` recall 27.0% on test (30.3% cross-validated; collisions with the Moon 14.6%) | Rule P4 met narrowly; C4 reported | [test_confusion](figures.md#test_confusionpng) |
| 17 | The starting conditions also predict roughly when a system fails | Lifetime class on test: 76.9% accuracy, 98.4% within one class | Descriptive | [lifetime_confusion](figures.md#lifetime_confusionpng) |
| 18 | A stable-looking second moon can oscillate without growing | Phase 1 moon: eccentricity cycles (~17 years), bounded over 1,000 years | Descriptive (one system) | [first_moon_long_term](figures.md#first_moon_long_termpng) |
| 19 | The surrogate is far faster than simulation | 111 ms vs 2.67 s median (24×); about 80,000× in batches; repays its training data after about 7,000 predictions | Verified (same-machine benchmark) | [speedup](figures.md#speeduppng) |
| 20 | Its confidence tells when to trust it | Most confident 50% of test predictions: 98.2% correct | Descriptive (test set) | [coverage_accuracy](figures.md#coverage_accuracypng) |

## Simulation log

| Date | Run | Simulations | CPU-hours | Cumulative random second moons |
|---|---|---:|---:|---:|
| 2026-11-25 | Phase 1: real system (with and without the Sun), one 10-year second moon, 60-day animation | 4 | < 0.01 | 0 |
| 2026-11-25 | Pilot A: 100 random moons, 100 years | 100 | 0.19 | 100 |
| 2026-11-25 | Pilot B: same moons, integrator tolerance 10⁻¹¹ | 100 | 0.25 | 200 |
| 2026-11-25 | Pilot C: same moons, second moon displaced by 1 m | 100 | 0.17 | 300 |
| 2026-11-25 | Pilot D: first 30 moons at two other start dates | 60 | 0.10 | 360 |
| 2026-11-26 | Full dataset: 12,000 new moons, 100 years | 12,000 | 20.77 | 12,360 |
| 2026-11-26 | Phase 3: the Phase 1 second moon for 1,000 years | 1 | 0.01 | 12,360 |
| 2026-11-26 | Phase 3: 500 training survivors re-integrated to 1,000 years | 500 | 17.94 | 12,360 |
| 2026-11-26 | Phase 4: chaos twins, 1,500 training moons displaced by 1 m | 1,500 | 2.66 | 12,360 |
| 2026-11-27 | Phase 5: speed benchmark, 100 training moons in one process | 100 | 0.30 | 12,360 |
| 2026-11-28 | Phase 5: test chaos twins, 600 test moons displaced by 1 m | 600 | 1.58 | **12,360** |

Short simulations inside the automated checks and verification reruns (20 dataset moons, 20 pilot
moons) are not counted. The re-integrated survivors, the chaos twins and the benchmark runs are
existing dataset moons, so the cumulative count of distinct random second moons is unchanged.

**Total:** 15,065 simulations, of 12,360 distinct random second moons (plus the 4 Phase 1 runs
and the single 1,000-year run of the Phase 1 system).

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

## Phase 3: exploration and stability maps (2026-11-26)

**Objective:** locate each outcome in parameter space before any modeling, and answer the open
questions on the pilot gap, orbit direction, mass, long-term survival and the first second moon.

### Work

| Step | Content | Commit |
|---|---|---|
| 3.1 | Held-out test split (`src/split.py`), exploration helpers (`src/explore.py`) and checks | `ccb9bbc` |
| 3.2 | Chosen-id batches; 500 random survivors integrated to 1,000 years | `a7dcde4` |
| 3.3 | Decision rules R1–R3, stability maps (`src/plot_dataset.py`), pilot investigation (`src/compare_pilot.py`) | `dbce1fe` |
| 3.4 | The Phase 1 second moon over 1,000 years (`src/long_run.py`) | `661d80f` |
| 3.5 | Rule R4 and survival to 1,000 years (`src/survival_curve.py`) | `3aad1cf` |
| 3.6 | `notebooks/02_dataset_exploration.ipynb` and documentation | `e6996df` |

### Method

- **Held-out test set.** Before any exploration, 2,400 moons (20%, stratified by label, seed
  20261127) were set aside in `configs/split.json`. All Phase 3 analyses use the remaining 9,600
  training moons, so patterns found here cannot leak into the evaluation of the Phase 4 models.
- **Fixed binning:** semi-major axis in 12 logarithmic bins from 0.1 to 3 lunar distances,
  inclination in 12 bins of 15°, eccentricity in 8 bins of 0.1, mass in 6 logarithmic bins. Map
  cells with fewer than 20 moons are not shown; in practice every cell holds 44 to 93.
- **Uncertainty:** Wilson intervals for shares; bootstrap intervals (1,000 resamples) for edges and
  differences.
- **Robustness:** each map is rebuilt from even and odd ids separately and the two are compared.
- **Pre-registered rules**, fixed in the Phase 3 plan before the analysis:

| Rule | Question | Criterion |
|---|---|---|
| R1 | Does the change of inclination sampling explain the pilot gap (18% vs 38%)? | Isotropically reweighted survival inside the pilot's 95% interval (12% to 27%) |
| R2 | Do retrograde orbits survive farther out? | Bootstrap interval of (retrograde − prograde) outer 10% survival edge above 0 |
| R3 | Does mass matter? | Bootstrap interval of (heaviest − lightest mass bin) survival excludes 0 |
| R4 | Does survival level off after 100 years? | Loss from 100 to 1,000 years below half the loss from 10 to 100 years |

The survival edge in R2 was clarified before the analysis as the *outer* edge: the first bin
beyond the bin of highest survival whose survival share falls below 10%. The overall
prograde/retrograde split (35% vs 41%) had been seen while planning, so R2 tests a
distance-resolved quantity instead.

### Results

**Stability map.** Survival is high for moons inside about half the Moon's distance on low
inclinations: 96.5% of moons below 0.5 lunar distances with inclinations under 45° or over 135°
survive. Beyond about 0.75 lunar distances almost nothing prograde survives. The maps are
reproducible: split-half correlations of 0.991 (semi-major axis × inclination, 141 cells) and
0.977 (semi-major axis × eccentricity, 93 cells).

**Near-polar orbits.** Close moons on near-polar orbits (inclination 75° to 105°, inside 0.5 lunar
distances) almost never survive: 0.7% survive and 99.1% collide with Earth. This is consistent
with Lidov–Kozai cycles driven by the Moon and the Sun, which convert inclination into
eccentricity until the periapsis reaches Earth.

**Crossing the Moon's orbit.** Moons whose orbits cross the Moon's survive in 3.0% of cases
(60.5% ejected, 31.2% hit Earth). Moons entirely inside the Moon's orbit survive in 62.0%.
Survival falls steadily with eccentricity, from 47.1% (e < 0.1) to 24.0% (e 0.7–0.8).

**R1, pilot gap: not explained by the rule.** Reweighting the training moons to isotropic
inclinations (effective sample size 7,786) lowers survival from 37.9% to 29.7%, just above the
pilot's interval. Following the rule, other causes were investigated:
1. Re-simulating pilot moons 0–19 with the current code reproduced all 20 exactly, ruling out a
   code or setting change.
2. The survival share of the 50 nearest training moons of each pilot moon predicts 25.4 pilot
   survivors (95% range from outcome noise ±6.8); 18 were observed, 2.1 standard deviations lower.

| Step | Survival | Change |
|---|---:|---:|
| Full dataset as sampled (training moons) | 37.9% | |
| Reweighted to isotropic inclinations | 29.7% | −8.2 |
| Expected for the pilot's specific 100 moons | 25.4% | −4.3 |
| Observed in the pilot | 18.0% | −7.4 |

The gap is therefore attributed to the change of inclination sampling, the particular draws of a
100-moon pilot, and outcome noise at the 2σ level, with no evidence of a systematic difference.
The isotropically reweighted outcome shares are: survived 29.7%, ejected 30.7%, hit Earth 37.6%,
hit the Moon 0.9%, Moon lost 1.1%.

**R2, outer edge by direction: not shown.** Both directions fall below 10% survival in the same
bin, centered at 0.218 Hill radii (0.84 lunar distances, just inside the Moon's orbit); the
bootstrap interval of the difference is 0.000 to 0.071. The edge is set by the Moon rather than by
the Hill radius. *Descriptively*, retrograde moons recover beyond the Moon's orbit: for semi-major
axes above 1 lunar distance, 11.4% of retrograde moons survive against 0.3% of prograde moons,
reaching about 17% between 0.5 and 0.78 Hill radii. This agrees qualitatively with the greater
stability of retrograde satellites found for planets.

**R3, mass: matters.** Survival in the heaviest mass bin (0.32–1 lunar masses) is 11.4 points lower
than in the lightest (0.001–0.003): 30.9% versus 42.3%, bootstrap interval −14.4 to −8.3 points.
Heavy second moons more often destabilize the Moon itself (`moon_lost` 7.4% versus 0.0%) and
collide with Earth (30.2% versus 24.8%).

**R4, survival beyond 100 years: does not level off.** 500 randomly chosen training survivors were
integrated again from the start to 1,000 years (`configs/survivors_1000yr.json`, 17.9 CPU-hours).
All 500 were still present at 100 years, exactly as in their original runs, and none timed out.
Of the systems alive at 10 years, 34.7% were lost by 100 years; of the 100-year survivors, 21.4%
(95% interval 18.0% to 25.2%) were lost by 1,000 years (69 collided with Earth, 33 were ejected,
4 collided with the Moon, and in 1 the Moon was lost). The rule required less than 17.4%. Losses
slow down but continue: an estimated 29.8% of training systems would still be orbiting after
1,000 years. The label `survived` is therefore a lower bound on lifetime.

**The first second moon over 1,000 years (Q9).** The Phase 1 system (0.1 lunar masses, 0.4 lunar
distances) survives 1,000 years. Its eccentricity oscillates with a dominant period of about 17
years; the 10-year mean stays between 0.013 and 0.039, with the same average (0.0242) in both
halves of the run, and the osculating eccentricity never exceeds 0.055. The semi-major axis stays
within 153,580 to 154,973 km. The growth seen over the first 10 years was part of this bounded
oscillation.

### Reading the decision rules

Each rule states a claim, the quantity that measures it and a pass criterion, all fixed before the
analysis, so the outcome of the data cannot shape the criterion. A rule that is *not met* means the
evidence did not reach the criterion; it does not show the claim to be false.

- **R3** was met: the interval of the mass difference lies entirely below zero.
- **R1 and R4** are near misses with quantified partial effects: the inclination change explains
  about 8 of the 20 points of the pilot gap, and 21.4% of 100-year survivors are lost by 1,000
  years against the 17.4% required for levelling off.
- **R2** is not shown by its criterion: the bootstrap interval of the edge difference includes
  zero. The criterion measured where survival first drops below 10%, which the Moon fixes for both
  directions, and did not capture the recovery of retrograde survival beyond the Moon's orbit. That
  difference (11.4% versus 0.3% beyond one lunar distance) was identified after inspecting the data
  and is reported as descriptive.

Findings based on a met criterion carry more weight than descriptive ones, which are hypotheses
for future tests rather than confirmed results.

### Findings

- Three regions dominate: close, low-inclination orbits survive; near-polar orbits are driven into
  Earth; orbits reaching the Moon's are ejected or collide.
- The Moon, not the Hill radius, sets the outer limit for prograde second moons. Beyond the Moon's
  orbit, survivors are almost all retrograde (11.4% versus 0.3%).
- Heavier second moons survive less often, partly because they destabilize the Moon.
- The pilot-to-dataset difference is accounted for by sampling design, small-sample variation and
  outcome noise.
- About a fifth of 100-year survivors are lost by 1,000 years; `survived` is a lower bound.

### Revisions

- A bug in `shares_by_bin` (bin edges taken from pandas' rounded interval labels) was caught by
  `src/check_explore.py` before any results were produced.

---

## Phase 4: surrogate models (2026-11-26 to 2026-11-27)

**Objective:** models that predict the outcome of a system, and its probability, from the starting
parameters alone, evaluated without touching the held-out test set.

### Work

| Step | Content | Commit |
|---|---|---|
| 4.1 | Settings (`configs/models.json`), feature sets (`src/features.py`), model pipelines (`src/models.py`), cross-validation and metrics (`src/cv.py`), checks (`src/check_models.py`) | `8e1c904` |
| 4.2 | Chaos twins: 1,500 training systems re-simulated with a 1 m displacement (`src/select_twins.py`) | `8e1c904`, `601590f` |
| 4.3 | Resumable training runner (`src/train_models.py`); baselines and rule P1 | `bce5e69` |
| 4.4 | Nested model comparison (rules P2, P3, P6), final settings, lifetime task | `975d7fb` |
| 4.5 | Analysis (`src/analyze_models.py`): chaos reference, rules P4 and P5, learning curve, importance, Phase 5 criteria | `975d7fb` |
| 4.6 | Figures (`src/plot_models.py`) | `975d7fb` |
| 4.7 | `notebooks/03_models.ipynb` and documentation | `84b34cd` |

### Method

- **Target:** four classes, `survived`, `ejected`, `hit_earth` and `moon_interaction` (collision
  with the Moon or loss of the Moon, merged: 254 training systems). P(survived) also gives a
  binary survival prediction.
- **Features** (inputs only):
  - F1, orbital elements: log mass, log semi-major axis, eccentricity, cos *i*, sine and cosine
    of the three orientation angles;
  - F2, Earth-relative state vector and log mass;
  - F3, F1 plus periapsis, apoapsis, a flag for orbits crossing the Moon's, |cos *i*|, the
    Lidov–Kozai quantity √(1−e²) cos *i*, and the starting angle to the Moon.
- **Models:**
  - baselines: majority class, and a physics rule (a decision tree of depth at most 3 on apoapsis
    and |cos *i*| only);
  - candidates: logistic regression, Random Forest, XGBoost, multilayer perceptron.

  Every model is a scikit-learn pipeline, so preprocessing is fitted inside each training fold.
- **Validation:**
  - stratified 5-fold cross-validation on the 9,600 training systems;
  - hyperparameters chosen by a randomized search (25 candidates, inner 3-fold) inside each
    outer training part (nested cross-validation);
  - every system receives one out-of-fold (OOF) prediction, and comparisons use paired bootstrap
    intervals (1,000 resamples) over these.
- **Metrics:**
  - primary: macro-F1;
  - also balanced accuracy, accuracy, per-class precision and recall, log loss and Brier score;
  - for survival: ROC AUC, accuracy and expected calibration error (ECE).
- **Chaos reference:** the share of the 1,500 twin pairs with identical outcomes.
- **Checks** (`src/check_models.py`):
  - only input columns enter the features, and no test system is loaded;
  - derived features match hand calculations;
  - folds are stratified, and runs are reproducible;
  - a Random Forest trained on shuffled labels scores at chance (macro-F1 0.235 versus 0.662 on
    real labels in the same quick check), ruling out leakage.
- **Pre-registered rules**, fixed before any model was trained:

| Rule | Question | Criterion |
|---|---|---|
| P1 | Feature set | F2 or F3 replaces F1 if the interval of its macro-F1 gain (Random Forest, default settings) lies above 0 |
| P2 | Model | Highest macro-F1, unless a simpler model's gap interval includes 0 (logistic < Random Forest < XGBoost < MLP) |
| P3 | Beats the physics rule | Interval of the balanced-accuracy gain above 0 |
| P4 | Rare class | Targeted sampling recommended if `moon_interaction` recall is below 30% |
| P5 | Errors and chaos | Error rate on twin-disagreeing systems exceeds that on twin-agreeing systems (interval above 0) |
| P6 | Calibration | If ECE of P(survived) exceeds 0.05, an isotonic-calibrated version is kept if it lowers log loss |

### Results

**Baselines.** Always predicting `survived` gives macro-F1 0.138 (accuracy 37.9%). The physics
rule reaches macro-F1 0.597 and accuracy 79.5%. Fitted on all training systems, it reads:
orbits with apoapsis below 0.875 lunar distances survive unless |cos *i*| ≤ 0.42 (inclination
roughly 65° to 115°), in which case they collide with Earth; orbits reaching farther are ejected,
or collide with Earth when near-polar and within 1.9 lunar distances. It never predicts
`moon_interaction`.

**P1, feature set: F3.** State vectors are clearly worse than orbital elements (macro-F1 −0.086,
interval −0.099 to −0.073). The physics features add +0.006 (interval +0.0001 to +0.014), a small
gain just above zero.

**P2 and P3, model comparison (nested cross-validation on F3):**

| Model | Macro-F1 | Balanced accuracy | Accuracy | Log loss | Fold macro-F1 (mean ± SD) |
|---|---:|---:|---:|---:|---:|
| Majority class | 0.138 | 0.250 | 0.379 | — | — |
| Physics rule | 0.597 | 0.603 | 0.795 | 0.599 | 0.597 ± 0.006 |
| Logistic regression | 0.658 | 0.694 | 0.780 | 0.608 | 0.652 ± 0.012 |
| **Random Forest** | **0.723** | **0.719** | **0.850** | 0.405 | 0.723 ± 0.026 |
| XGBoost | 0.715 | 0.714 | 0.850 | 0.401 | 0.715 ± 0.012 |
| Multilayer perceptron | 0.653 | 0.650 | 0.835 | 0.428 | 0.652 ± 0.007 |

The Random Forest has the highest macro-F1; its gain over logistic regression is +0.065 (interval
+0.050 to +0.080), so P2 selects it. It beats the physics rule by +0.116 in balanced accuracy
(interval +0.103 to +0.132; P3 met). Per class, recall is 91.9% (survived), 86.7% (ejected),
78.7% (hit Earth) and 30.3% (Moon interaction). As a survival classifier it reaches 93.8%
accuracy and a ROC AUC of 0.985. With isotropic weights, macro-F1 is 0.712 and accuracy 84.6%.

**P6, calibration: no change needed.** The ECE of P(survived) is 0.019, below the 0.05 limit.

**P4, rare class: targeted sampling not triggered (near miss).** The `moon_interaction` recall
is 30.3% (Wilson interval 25.0% to 36.2%), just above the 30% criterion. Losses of the Moon are
recognized in 48.7% of cases, collisions with the Moon in 14.6%; 46% of all
`moon_interaction` systems (117 of 254) are predicted as ejections.

**Chaos reference and P5: errors concentrate on chaotic systems.** A 1 m displacement leaves the
outcome unchanged in 92.3% of the 1,500 twin pairs (interval 90.8% to 93.5%; 98.4% for survival
alone). Chaos peaks near the Moon's orbit (20.3% of outcomes change between 0.55 and 0.97
lunar distances, 17.2% between 0.97 and 1.70) and is absent inside 0.31 lunar distances
(none of 498 pairs changed). The model errs on 53.4% of the 116 chaotic
systems and on 10.5% of the stable ones (difference interval +0.34 to +0.52; P5 met). On stable
systems its accuracy is 89.5%, close to the 92.3% reproducibility of the simulation.

**What the model learned.** Grouped permutation importance (drop in macro-F1):
- distance 0.308;
- inclination 0.236;
- mass 0.075;
- orientation and phase 0.003;
- eccentricity alone 0.002, since periapsis and apoapsis in the distance group already carry it.

The out-of-fold predicted survival probability reproduces the simulated stability map, with the
largest cell difference 0.13, at region edges.

**Learning curve.** From 768 to 7,680 training systems per fold, macro-F1 rises only from 0.700
to 0.723, and the `moon_interaction` recall stays near 29–30%. Additional simulations would
improve the model little; the outcomes' chaotic component is the main limit.

**Lifetime classes (secondary task).** With training shares of 10.8% (lost within 1 year),
31.1% (1–10 years), 20.2% (10–100 years) and 37.9% (survived), the Random Forest predicts the
lifetime class with macro-F1 0.728 and accuracy 76.7% (majority 37.9%); 98.6% of predictions are
correct or one class off.

**Selected model for Phase 5.** One randomized search on all training systems gave
`min_samples_leaf` 5, `max_features` 0.5, `max_depth` 20 and `class_weight`
`balanced_subsample` (`configs/selected_model.json`). The Phase 5 criteria were fixed before the
test set is opened:
- C1: test macro-F1 inside the cross-validated interval 0.708 to 0.737;
- C2: beats the physics rule in balanced accuracy;
- C3: ECE of P(survived) at most 0.05;
- C4: `moon_interaction` recall reported;
- the speedup over simulation is measured.

### Reading the decision rules

- P1, P2, P3, P5 were met.
- P6 required no action.
- P4 was met by a narrow margin: the recall interval (25% to 36%) straddles the criterion, so the
  conclusion that targeted sampling is unnecessary is supported mainly by the flat learning curve
  rather than by the recall alone.

### Findings

- A Random Forest predicts the outcome of a second moon with 85% accuracy (macro-F1 0.72) and
  well-calibrated probabilities, clearly better than a physics rule.
- On systems whose outcome is reproducible under a 1 m nudge, it is right about 9 times in 10.
  Most remaining errors are on chaotic systems.
- The model relies on the same quantities as the physics: distance relative to the Moon and
  inclination relative to 90°.
- More simulations would help little; collisions with the Moon remain hard to predict.
- The starting conditions also predict roughly when a system fails.

### Revisions

- The reported Brier score is the four-class score; the label in `src/paper_numbers.py` was
  corrected before any document quoted it.
- The cross-validated scores are slightly optimistic because the feature set was chosen on the
  same training data. The Phase 5 test evaluation confirmed that this optimism is small (test
  macro-F1 0.711 against 0.723 cross-validated).

---

## Phase 5: evaluation on the held-out test set (2026-11-27 to 2026-11-28)

**Objective:** a single, verifiable evaluation of the selected model on the 2,400 test systems held
out since Phase 3, a fair speed comparison with direct simulation, and an analysis of failures.

### Work

| Step | Content | Commit |
|---|---|---|
| 5.1 | Protocol (`configs/phase5_protocol.json`), evaluation script (`src/evaluate_test.py`), checks (`src/check_evaluation.py`) | `5a93769` |
| 5.2 | Dry run on a training holdout | `5a93769` |
| 5.3 | The single test evaluation (from tag `phase5-evaluated-model`) | `d4f404c` |
| 5.4 | Speed benchmark (`src/benchmark_speed.py`) | `0ad5d7d`, `69cefc4` |
| 5.5 | Test chaos twins and failure analysis (`src/analyze_test.py`) | `0ad5d7d`, `69cefc4` |
| 5.6 | Figures (`src/plot_test.py`) | `6245f8f` |
| 5.7 | Prediction tool (`src/predict.py`) and model card (`docs/model_card.md`) | `69cefc4`, `7e2612f` |
| 5.8 | `notebooks/04_evaluation.ipynb` and documentation | `7e2612f` |

### Protocol

- **Criteria** fixed at the end of Phase 4 (`configs/selected_model.json`, commit `975d7fb`):
  - C1: test macro-F1 inside 0.708–0.737;
  - C2: balanced-accuracy gain over the physics rule with an interval above 0;
  - C3: ECE of P(survived) at most 0.05;
  - C4: `moon_interaction` recall reported with a Wilson interval.
- **Amendment before opening the test set (C1b).** The C1 interval reflects the uncertainty of
  the score on 9,600 systems; on 2,400 test systems the score scatters about twice as widely, so a
  perfectly generalizing model would miss C1 about one time in three. C1 is kept unchanged. C1b
  additionally requires the 95% interval of (test − cross-validated macro-F1) to include 0, with
  both samples bootstrapped independently.
- **All descriptive analyses** fixed in `configs/phase5_protocol.json` before opening: seed
  variability, per-class calibration, isotropic weighting, lifetime classes, error map,
  coverage–accuracy curve, test chaos twins with rule T5. The consequence of each possible verdict
  was also fixed, and model switching ruled out.
- **Safeguards.** `src/evaluate_test.py` is the only analysis script that loads the test set. It
  runs only if:
  - the Git tree is clean;
  - the criteria are unchanged since `975d7fb` and the split since `ccb9bbc`;
  - the dataset matches its manifest;
  - no results exist yet.

  It records the commit and file checksums with the results and refuses a second run (verified).
  A dry run on a training holdout exercised the full pipeline first.
- **Final models:** the selected Random Forest (final settings, seed 20261201), the physics rule
  and the majority class, trained on all 9,600 training systems.

### Results

**Criteria.**

| Criterion | Result | Verdict |
|---|---|---|
| C1 | Test macro-F1 0.711 (interval 0.683–0.738) inside 0.708–0.737 | Met |
| C1b | Difference from cross-validation −0.012 (interval −0.045 to +0.018) | Met |
| C2 | Balanced-accuracy gain over the physics rule +0.115 (interval +0.088 to +0.144) | Met |
| C3 | ECE of P(survived) 0.019 | Met |
| C4 | `moon_interaction` recall 27.0% (Wilson interval 17.6% to 39.0%, 63 systems) | Reported |

**Test performance.**

| Model | Macro-F1 | Accuracy | Balanced accuracy |
|---|---:|---:|---:|
| Random Forest | 0.711 | 0.851 (0.837–0.865) | 0.712 |
| Physics rule | 0.591 | 0.789 | 0.597 |
| Majority class | 0.138 | 0.380 | 0.250 |

Every test metric agrees with its cross-validated value:
- accuracy 0.851 versus 0.850;
- survival ROC AUC 0.988 versus 0.985;
- survival accuracy 94.1% versus 93.8%;
- log loss 0.400 versus 0.405;
- ECE 0.019 versus 0.019.

Per-class recall on test is 92% (survived), 87% (ejected), 79% (hit Earth) and 27% (Moon
interaction). Per-class calibration errors are all at most 0.030. Five other seeds give test
macro-F1 of 0.709–0.716. With isotropic weights, macro-F1 is 0.687 and accuracy 84.0%. The lifetime
class is predicted with 76.9% accuracy (macro-F1 0.732), and 98.4% of predictions are within one
class.

**Failure analysis.** 600 random test systems were re-simulated with a 1 m displacement after the
evaluation was committed:
- 91.3% of outcomes are unchanged (97.8% for survival alone);
- **rule T5 is met:** the model errs on 53.8% of the 52 chaotic systems and on 11.3% of the
  others (difference interval +0.28 to +0.56);
- the test error map places the failures near the Moon's orbit, with error rates of 26–45%
  between 0.55 and 1.7 lunar distances (highest, 45%, at 0.55–0.97 lunar distances and 120°–150°),
  while close-in systems are almost never misclassified;
- ranked by confidence, the most confident 50% of test predictions are 98.2% correct and the most
  confident 80% are 91.8% correct.

**Speed** (single process, same machine, plugged in):

| | Seconds per system |
|---|---:|
| Simulation, mean (100 training systems) | 10.72 |
| Simulation, median | 2.67 |
| Model, one prediction (median of 1,000) | 0.111 |
| Model, per system in a batch of 2,400 | 0.000133 |

- Survivors take a median of 19.7 s to simulate, failures 0.1–1.1 s.
- The model is 24 times faster than the median simulation and 97 times faster than the mean for
  single predictions, and about 80,000 times faster than the mean in batches.
- All 12,000 systems would be classified in 1.6 s, against 20.8 CPU-hours of simulation.
- Counting the training data and 44 s of model training, the surrogate repays its cost after
  about 7,000 predictions.
- The pre-registered comparison, against the 1.456 s median recorded with four parallel workers
  during dataset generation, gives a factor of 13.
- All 100 re-simulated benchmark systems reproduced their dataset outcomes.

**Prediction tool and model card.** `src/predict.py` returns outcome and lifetime probabilities for
any second moon, warns outside the training ranges and inside the Roche limit, and reproduces the
evaluated predictions exactly. `docs/model_card.md` summarizes intended use, performance, speed,
limits and failure modes.

### Reading the decision rules

All pre-registered criteria (C1–C3) and rule T5 were met. C1 was met by a margin of 0.003; the
amendment C1b, fixed before opening, confirms that the test score is consistent with the
cross-validated estimate within test-set noise. The near-identical test and cross-validated scores
indicate that the selection optimism noted in Phase 4 is small.

### Findings

- The surrogate generalizes: on systems never used for any decision, it reaches 85.1% accuracy,
  matching cross-validation, and beats the physics rule.
- Its probabilities are calibrated on new systems, and its confidence identifies the predictions to
  trust: half of the test set is predicted with 98% accuracy.
- Its failures sit where the dynamics are chaotic, near the Moon's orbit.
- It is 24 to 80,000 times faster than direct simulation, depending on use, and repays its training
  data after about 7,000 predictions.

### Revisions

- The planned size of the committed predictions file (about 150 KB) was underestimated; including
  the input columns needed for the failure analysis, it is 1.2 MB.
- Speedups are quoted to two significant figures; the timing ratios are not more precise.

---

## Phase 6: release, final paper and archive (2026-11-28)

**Objective:** a repository that can be installed, understood and reproduced by others, a
submission-ready paper, and an archived release. Results are frozen: no file under `results/` and
none of `configs/split.json`, `configs/selected_model.json` or `configs/phase5_protocol.json`
changes, and the test evaluation is not repeated.

### Work

| Step | Content | Commit |
|---|---|---|
| 6.1 | Release checklist as code (`src/check_release.py`): frozen results, links, imports, run-table coverage, documented figures, wording, headline numbers across documents | `f14b7aa` |
| 6.2 | Fresh-clone test (`src/check_fresh_clone.py`); README section on reproducing everything | `47fca00`, `494d5d4` |
| 6.3 | All four notebooks re-executed from fresh kernels; every text output identical to the committed version | `22b3d5a` |
| 6.4 | Paper: references verified, related work, keywords, abstract, editing pass; paper check (`src/check_paper.py`) | `494d5d4` |
| 6.5 | Print-size paper figures (`src/plot_paper.py`); compilation and upload bundle (`src/package_paper.py`); `paper/main.pdf` | `22b3d5a` |
| 6.6 | Research Notes version (`paper/rnaas.tex`, `paper/rnaas.pdf`) and its checks | `5d07f8d` |
| 6.7 | Data archive (`src/package_data.py`, `docs/data_archive.md`), `CITATION.cff` 1.0.0, `.zenodo.json` | `2f9a38f` |
| 6.8 | README as landing page, plain-language summary (`docs/summary.md`), `CHANGELOG.md`, final status lines | `1f2484a` |
| 6.9 | Post images (`src/make_post_figures.py`, `figures/post/`) and the animation as video (`figures/two_moons.mp4`; `imageio-ffmpeg` pinned) | `a4aec08` |
| 6.10 | Dataset DOI cited in both papers, README, CITATION.cff and `.zenodo.json`; tag v1.0.0 | `02067b5` |
| 6.11 | Pre-release audit: figure order, introduction, limitation wording, metadata | `f8b9f3f` |
| 6.12 | Code documentation: docstrings and comments in `src/` rewritten; code guide (`docs/code_guide.md`) | this step |

### Reproducibility

The fresh-clone test clones the public repository into a temporary folder, creates a new virtual
environment, installs `requirements.txt` and runs the eight checks that need no generated data;
all pass, and `src/predict.py` explains how to obtain the data when it is missing. Regenerating
every result requires about 44 CPU-hours of simulation (dataset 20.8, 1,000-year survivors 17.9,
chaos twins 2.7 and 1.6, pilot runs 0.7, speed benchmark 0.3). Regenerated data files reproduce
the archived inputs, outcomes and survival times, but not their checksums, because rows are
written in completion order and include each run's computing time.

### Paper

- All references were checked against the publisher records (volume, pages, DOI); DOIs were
  added for Domingos et al. (2006) and Shen & Tremaine (2008), and pandas was added to the
  software citations.
- Related work added: N-body moon packing around an Earth-mass planet (Satyal et al. 2022), the
  first machine-learned stability classifier (Tamayo et al. 2016), instability-time prediction
  with a Bayesian neural network (Cranmer et al. 2021) and gradient-boosted maps of stable orbits
  around planets (Pinheiro et al. 2025). No prior study of a second moon of the present
  Earth–Moon system was found, so the novelty statement is qualified ("to our knowledge").
- Keywords carry Unified Astronomy Thesaurus identifiers (1089, 2212, 436, 1857, 1858).
- The abstract was shortened from 288 to 240 words (limit 250). It now quotes the chaos limit
  from the 1,500 chaos twins (about 8%) rather than the 100-system pilot (12%).
- Wording corrections: survival is "concentrated on close orbits near the ecliptic plane,
  prograde or retrograde" rather than "requires a close, low-inclination orbit"; the 0.003%
  validation error refers to the maximum, not the mean; the survivor simulation time is a median.
- `src/check_paper.py` checks citations, labels, figure files, balanced environments, the
  abstract length, placeholders and 32 headline numbers recomputed from the committed result files
  and manifests. After archiving, the dataset DOI replaced the last placeholder; the `--final`
  mode, which allows none, passes.
- Figures are drawn at print size (one column, 3.4 inches; the stability map 6.0 inches) as vector
  PDFs with text of 6 to 8 pt. The survival figure now shows the training systems, the extension
  to 1,000 years, the isotropic reweighting and the pilot, replacing the pilot-only figure; figures
  comparing test and cross-validated scores and model and simulation time were added.
- The paper is compiled with Tectonic 0.17.0 (archive verified against its published SHA-256)
  into 8 pages without undefined references or overfull lines; each page was inspected.
  `src/package_paper.py` also writes an upload bundle including the generated `.bbl` file, which
  arXiv requires because it does not run BibTeX.
- A condensed version for Research Notes of the AAS (`paper/rnaas.tex`) follows the journal's
  current preparation guidelines: 1,500 words including title, headers, captions and references
  (150 reserved for the abstract), a single figure or table that fits on one page, and the first
  person singular for single-author notes. It has a 139-word abstract, about 1,250 words in
  total (counted from the source and, independently, from the compiled PDF) and one two-panel
  figure: the stability map and the test-versus-cross-validation comparison. Its headline
  numbers are checked against the result files like those of the full paper.

### Archive

`src/package_data.py` builds the data archive for Zenodo: the 14,960 simulated systems in nine
batch files, the 1,000-year run of the first second moon, the run records, configurations and
manifests, the derived results (including all out-of-fold predictions and the test-set results)
and the run logs, with a data description ([data_archive.md](data_archive.md)) and a `SHA256SUMS`
file; 83 files, 7.2 MB. The four main data files are checked against the checksums in their
committed manifests before packaging, and the archive is byte-identical when rebuilt. The data
are released under CC BY 4.0 and the code under the MIT license. The archive is deposited on
Zenodo as doi:10.5281/zenodo.24607389; the uploaded file was confirmed byte-identical to the rebuilt archive, and
the paper cites the dataset in its references (`Quizon2026data`).

### Pre-release audit

Before the release, every document was checked again for stale statements and the paper was
reread in full. Changes:

- The figures of the full paper were not numbered in the order of first citation (the survival
  figure was cited in the pilot section before the stability map); the early citation was removed,
  and `src/check_paper.py` now checks the order of figures and tables.
- The introduction's list of contributions now includes the single held-out evaluation and the
  speed measurement; the pilot's reference run is labeled (A).
- The limitation on omitted physics no longer cites the one-year validation as evidence for 100
  years; it states that the effects are expected to remain minor for most orbits.
- `.zenodo.json` uses the lowercase license identifier (`mit`) shown in Zenodo's documentation.
- The model card, notes, paper README and glossary were brought up to date (data on Zenodo, word
  counts, the DOI entry).

### Code documentation

The docstrings and comments of all 52 scripts and modules in `src/` were rewritten in a uniform
style: a one-line summary, a short description of inputs and outputs, and a `Usage:` block;
inline comments are limited to units, sources and non-obvious reasons. Explanations of the
workflow, run times and conventions moved to a separate code guide
([code_guide.md](code_guide.md)). The change is limited to documentation: for every file, the
syntax tree with comments and docstrings removed is identical before and after, and all checks
pass.

### Communication material

`src/make_post_figures.py` draws five 1080 x 1350 pixel slides and a 1200 x 627 cover that restate
the main results in plain language (the question, the stability map, chaos, test accuracy, speed),
with numbers read from the same result files as the paper, and converts the orbit animation to an
H.264 video. `imageio-ffmpeg` 0.8.1, which bundles ffmpeg, was added to the pinned requirements;
the newest release (0.8.2, published the day before) was not used.

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
> systems. A stratified 20% test set is held out before exploration. On the remaining 9,600
> systems, survival is concentrated on close, low-inclination orbits; near-polar orbits collide
> with Earth, consistent with Lidov–Kozai cycles, and orbits reaching the Moon's are ejected or
> collide. Of 500 random 100-year survivors integrated to 1,000 years, 21.4% are lost. Under
> nested cross-validation, a Random Forest on orbital elements and physics features predicts
> the four-class outcome with macro-F1 0.723 and accuracy 85.0% (physics-rule baseline 0.597
> and 79.5%), with calibrated survival probabilities (ECE 0.019). A 1 m perturbation leaves
> 92.3% of outcomes unchanged, and model errors concentrate on the chaotic systems. On the
> 2,400 held-out systems, evaluated once under criteria fixed in advance, the model reaches
> 85.1% accuracy (macro-F1 0.711) with calibrated probabilities, and is 24 times faster than
> the median simulation per prediction and about 80,000 times faster in batches.

## Limitations

- Newtonian point-mass gravity with finite-radius collisions: no tides, no Earth oblateness, no
  general relativity, no other planets.
- `survived` means surviving 100 years, not long-term stability; about a fifth of 100-year
  survivors are lost by 1,000 years.
- A single start date, supported by a 30-moon test.
- Class shares depend on the chosen parameter ranges and distributions.
- The R2 criterion (outer 10% survival edge) did not capture survival beyond the Moon's orbit. A
  criterion based on survival beyond one lunar distance is recommended for future tests of the
  prograde-retrograde difference.
- The Lidov–Kozai mechanism is inferred from outcome patterns; individual orbits were not traced.
- Survival between 100 and 1,000 years rests on a sample of 500 systems.
- The feature set was chosen on the training data; the held-out test scores, close to the
  cross-validated ones, indicate that the resulting optimism is small.
- Collisions with the Moon are rarely predicted (recall 14.6% within the merged class).
- Speed was measured on one laptop; absolute times depend on hardware, ratios less so.
