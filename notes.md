# Lab notes

Running notes: key numbers, checks, notable moments and figure picks for the paper and
project write-up.

The structured record lives in `docs/`: [technical report](docs/report.md),
[design decisions and open questions](docs/questions.md), [figure guide](docs/figures.md) and
[glossary](docs/glossary.md).

## Key numbers

- Simulated Moon vs NASA over one year: at most 10.3 km off (average 5.6 km), about
  0.003% of the Earth-Moon distance.
- Same run without the Sun: up to 55,535 km off.
- First second moon (0.1 lunar masses at 0.4 of the Moon's distance): survived 10 years,
  staying 146,072 to 162,087 km from Earth. Computing time 4.1 s.
- That second moon's distance range grew from 5,847 km (first year) to 14,726 km (last year),
  about 2.5 times (`src/plot_single_run.py`).

- Full dataset: 12,000 simulated second moons, up to 100 years each. 20.8 CPU-hours,
  5.2 hours on a laptop with 4 workers. Median 1.5 s per moon, longest 104 s.
- Outcomes: survived 38.0%, ejected 32.0%, hit Earth 27.4%, hit the Moon 1.4%,
  real Moon lost 1.2%. No timeouts or errors.

- Phase 3: 9,600 training moons explored, 2,400 test moons held out. 500 survivors re-run to
  1,000 years (17.9 CPU-hours, 4.5 hours); 393 survived. Total simulations after Phase 3: 12,865.
- Close, low-tilt orbits: 96.5% survive. Close near-polar orbits: 0.7% survive, 99.1% hit Earth.
- Beyond the Moon's orbit: prograde 0.3% survive, retrograde 11.4%.
- Heaviest second moons knock out the real Moon in 7.4% of systems.
- 21.4% of 100-year survivors are lost by 1,000 years; ~30% of moons would last 1,000 years.

- Phase 4: Random Forest predicts the outcome with 85.0% accuracy (macro-F1 0.723) out-of-fold,
  vs 79.5% for a 2-variable physics rule and 37.9% for always guessing "survived".
- Survival probabilities calibrated (ECE 0.019); survived-or-not ROC AUC 0.985, accuracy 93.8%.
- Chaos twins: a 1 m nudge leaves 92.3% of outcomes unchanged; the model is right 89.5% of the
  time on those stable systems and wrong 53.4% of the time on chaotic ones.
- Lifetime class predicted with 76.7% accuracy, 98.6% within one class.
- Total simulations after Phase 4: 14,365 (12,360 distinct random second moons).

- Phase 5 (held-out test, 2,400 moons, evaluated once): 85.1% accuracy, macro-F1 0.711
  (cross-validated 85.0%, 0.723); physics rule 78.9%; all pre-registered criteria met.
- Survival ROC AUC 0.988, ECE 0.019; most confident half of predictions 98.2% correct.
- Speed: 111 ms per prediction vs 2.67 s median simulation (24x); 133 µs per moon in batches
  (about 80,000x vs mean simulation); 12,000 moons in 1.6 s vs 20.8 CPU-hours; break-even
  after about 7,000 predictions.
- Total simulations after Phase 5 (final): 15,065 (12,360 distinct random second moons).

## Checks passed

Reproduce with `src/check_setup.py` and `src/check_initial_state.py --online`.

- 2026-11-25, REBOUND 5.2.3 with IAS15: a two-body test orbit returned to its start
  after one period (position error 3.0e-15 in units of the orbit's semi-major axis,
  relative energy error 4.3e-16).

- 2026-11-25, JPL starting states (2026-01-01 00:00 TDB): saved values match a
  separate direct Horizons request in km to within 3e-8 km. Against astropy's lower-precision built-in
  ephemeris, Earth-Moon differs by 6.9 km and Earth-Sun by 3.0 km.
- Starting Earth-Moon distance 361,026 km. Instantaneous two-body orbit: semi-major
  axis 384,469 km, eccentricity 0.0629, inclination 5.06 deg, period 27.292 days.
- GM values are DE440. They differ slightly from the Horizons page headers (largest
  relative difference 1.1e-8, for the Moon).

- 2026-11-25, step 3 (`src/validate_real_system.py`, limits set before the first run):
  average period 27.2734 days, 0.6 s from NASA over the same year; max relative energy
  error 1.0e-15. Total energy is dominated by the Earth-Sun orbit, so it is a weak check
  on the Moon's orbit alone. The NASA comparison is the stronger test.
- 2026-11-25, step 3 (`src/check_events.py`): a Moon dropped from rest hits Earth at 4.384
  days (exact formula: 4.384), and one thrown outward at 3 km/s is labeled ejected.

- 2026-11-25, step 4 (`src/check_second_moon.py`, limits set before the first run): orbit
  matches its settings to 7.9e-14; a second moon of 1e-12 lunar masses shifts the Moon by at
  most 59.2 mm in 10 years; reruns are bit-for-bit identical on this computer; collisions with
  Earth and the Moon, and an ejection, are labeled correctly.

## Pilot (2026-11-25, `src/analyze_pilot.py`, rules set before the runs)

- 100 random second moons, up to 100 years: hit Earth 42, ejected 38, survived 18,
  hit the Moon 1, real Moon lost 1. No timeouts or errors. Median 1.2 s per moon.
- Survived: 45 after 10 years, 28 after 30, 18 after 100. It keeps falling.
- Moving a moon by 1 meter changed 12 of 100 outcomes at 100 years (9 at 10 years).
  Stricter integrator settings changed 6, so the default (1e-9) is kept.
- The plan called the 88% agreement a ceiling for ML. That is not quite right: if outcomes are
  partly random, the best possible model can score somewhat above 88%. Treat it as a guide.
- Other start dates agreed on 27/30 and 26/30; the 1 meter shift on 28/30 of the same moons. Not
  clearly different, but 30 moons is a small test.
- Time limit rule: 100 years fits (about 2.4 hours for 5,000 moons).
- Added after seeing results: only 7 of 100 moons had a tilt under 40 degrees, so near-flat
  orbits are thinly covered by the uniform cos(tilt) sampling.

## Full dataset (2026-11-26, `configs/dataset.json`)

- 12,000 moons, seed 20261126 (not the pilot's), tilt spread evenly in degrees, 100-year limit,
  default integrator settings, one start date. Started 10:38, finished 15:50, never restarted.
- `src/check_dataset.py` passed: no repeated or missing ids, all inputs in range and rebuilt
  exactly from the seed, labels match outcomes, and 20 random moons rerun gave identical results.
- `configs/dataset_manifest.json` holds the CSV's SHA-256 (37add84e...), counts and versions.
- Survived 38% here vs 18% in the pilot (95% interval about 12% to 27%). Explained in Phase 3:
  tilt sampling, the pilot's particular moons and outcome noise (see Phase 3 below).
- Hit the Moon (1.4%) and real Moon lost (1.2%) are under the 2% rule set in the plan:
  merge them or sample more of their region. Decide in Phase 4.
- Survivors are censored: "survived" means at least 100 years, not forever.

## Phase 3 (2026-11-26, `src/plot_dataset.py`, rules R1–R4 set before the analysis)

- Test set frozen first (`configs/split.json`) so exploration cannot leak into model evaluation.
- R1 not met: reweighting explains only part of the pilot gap (29.7% vs pilot 12–27%). Reruns of
  pilot moons were identical; the rest is the pilot's unlucky draws and noise (2.1 sigma).
- R2 not shown as defined (same 10% edge for both directions), but retrograde moons clearly
  survive beyond the Moon's orbit while prograde ones do not (descriptive).
- R3: mass matters (−11.4 points, heaviest vs lightest). R4: losses slow but do not stop.
- First moon over 1,000 years: eccentricity cycles (~17 years), no growth.
- Maps agree between independent halves of the data (r = 0.99).

## Phase 4 (2026-11-26 to 27, `src/train_models.py`, rules P1–P6 set before training)

- Test set still untouched; everything is out-of-fold on 9,600 training moons, nested CV.
- P1: orbital elements beat position/velocity by 0.086 macro-F1; physics features add +0.006.
- P2: Random Forest selected (0.723); XGBoost 0.715, logistic 0.658, neural net 0.653.
- P3: beats the physics rule by +0.116 balanced accuracy. P6: no calibration needed.
- P4: Moon-interaction recall 30.3% (just above the 30% line). P5: errors sit on chaotic moons.
- Learning curve nearly flat (0.700 -> 0.723 with 10x data): chaos, not data, is the limit.
- Shuffled-label test: 0.235 vs 0.662 macro-F1, so no leakage.

## Phase 5 (2026-11-27 to 28, `src/evaluate_test.py`, criteria fixed in Phase 4)

- Protocol frozen and tagged (`phase5-evaluated-model`) before the test set was opened; the
  script verified the criteria and split were unchanged and refuses a second run.
- C1 met by 0.003 (0.711 vs floor 0.708); C1b (added before opening for test-set noise) met.
- C2 (beats physics rule by +0.115), C3 (ECE 0.019) met; C4 rare recall 27%.
- T5: test errors 53.8% on chaotic moons vs 11.3% on stable ones; errors near the Moon's orbit.
- predict.py and a model card make the model usable.

## Phase 6 (2026-11-28, release and final paper)

- Fresh clone from GitHub installs and passes every data-free check; full regeneration is about
  44 CPU-hours (11 hours with 4 workers).
- Related work checked: closest are moon packing around an Earth-mass planet (Satyal et al. 2022)
  and ML maps of stable orbits (Pinheiro et al. 2025); no study of a second moon of the real
  Earth-Moon system found.
- Paper: abstract 288 -> 240 words, UAT keywords, all references verified, compiled locally
  (8 pages, 5 print-size figures, no overfull lines); paper/main.pdf in the repository.
- Notebooks re-executed from fresh kernels: all 33 text outputs identical to the committed ones.
- Data archive on Zenodo: doi:10.5281/zenodo.24607389 (83 files, 7.2 MB, CC BY 4.0).

## Story moments

- Moving a moon by just 1 meter changed the outcome of 12 out of 100 moons. Chaos limits
  what any model can predict.

- The full run's first speed reading promised 11 hours. It took 5.2. The laptop was on battery
  at the start, and the first few dozen moons were not a fair sample.

- The stability map has a dead band at 90° tilt: even very close moons crash into Earth when
  their orbits are near-polar (Lidov–Kozai). Tilt matters as much as distance.

- A pre-registered rule was not met (R1). Instead of changing the rule, the gap was investigated and
  explained step by step, which is the honest version of the story.

- A pandas quirk (rounded bin labels) was caught by an automated check before any result used it.

- Rule R2 measured the wrong feature: both directions lose survival at the Moon's orbit, and the
  retrograde advantage only appears farther out. Choosing what to measure is the hard part of
  pre-registration.

- A depth-3 decision tree given only two numbers (apoapsis and |cos i|) rediscovered the whole
  Phase 3 stability map on its own and reached 79.5% accuracy.

- The model's mistakes are mostly on moons whose fate flips with a 1 meter nudge: it fails
  where the universe itself is unpredictable.

- The test-set score landed 0.003 above the pass line. Spotting beforehand that the line was
  too strict for a 2,400-moon test, and adding C1b before opening it, kept the result honest.

- Cross-validation said 85.0% accuracy; the never-seen test moons gave 85.1%.

- Leaving out the Sun made the Moon's position thousands of times worse (55,535 km vs
  10.3 km). "Just Earth and two moons" would not have been a fair simulation.

- The first two-moon run "survived", but plotting it showed the second moon's orbit stretching.
  The outcome label alone would have hidden that.

## Best figures

- For the post: `figures/post/slide1.png` to `slide5.png` (carousel, also `carousel.pdf`),
  `figures/post/cover.png`, `figures/two_moons.mp4` (video of the orbits).
- `figures/stability_map.png`: the headline figure (where second moons survive).
- `figures/survival_by_direction.png`: beyond the Moon, survivors are almost all retrograde.
- `figures/outcome_maps.png`: what happens instead, region by region.
- `figures/first_moon_long_term.png`: 1,000 years of the first second moon.
- `figures/predicted_map.png`: the model reproduces the stability map from starting values alone.
- `figures/model_comparison.png`: models vs baselines vs the chaos reference.
- `figures/chaos_profile.png`: where a 1 m nudge changes the outcome.
- `figures/speedup.png`: model vs simulation, 24x to 80,000x faster.
- `figures/test_vs_cv.png`: test set confirms cross-validation.
- `figures/coverage_accuracy.png`: confident predictions are almost always right.
- `figures/pilot_outcomes.png`, `figures/pilot_survival.png`: pilot results.
- `figures/two_moons.gif`: 60 days of both moons.
- `figures/two_moons_distance.png`: the second moon's orbit stretching over 10 years.
- `figures/real_moon_error.png`: with vs without the Sun.
- `figures/real_moon_orbit.png`: one year of the Moon's path, with NASA's positions.

## Method decisions

- Starting positions: NASA JPL Horizons, fixed date 2026-01-01, saved to `configs/`.
- Ejected means farther than 4.5 million km from Earth (about 3 Hill radii) and not bound
  to it, checked at every output (6 hours in Phase 1, 24 hours in the dataset). Collisions are
  checked along the path of every step.
- The second moon has the Moon's density. Its settings describe an orbit around Earth alone;
  inclination is measured from the ecliptic. Distance unit: 384,400 km.
- The Sun is included because it limits how far from Earth a moon can stay bound.
- Integrator: IAS15, which adapts its time step during close encounters.
- Before adding a second moon, the real Sun-Earth-Moon system is checked against known values.

## Phase 2 answers

- How long counts as stable? 100 years (the longest limit that fit the time budget).
- Stricter integrator settings? Changed fewer outcomes than a 1 meter shift, so the default is kept.
- Start date? No clear effect in the pilot (30 moons per date), so one date is used.

## Phase 3 answers

- 38% vs 18%: tilt sampling (−8.2 points), the pilot's particular moons (−4.3), noise (−7.4).
- Safe orbits: close and low-tilt; near-polar and Moon-crossing orbits fail.
- Backward orbits: same outer 10% survival edge, but almost all survivors beyond the Moon (11.4% vs 0.3%).
- Orbit stretching: a bounded ~17-year cycle.

## Phase 4 answers

- Rare outcomes merged into "Moon interaction"; recall 30%; targeted sampling not needed.
- Orbital elements plus physics features; vectors are much worse.
- 85.0% accuracy vs 38% baseline; chaos reference 92.3%.

## Phase 5 answers

- Test macro-F1 0.711, inside 0.708–0.737 (just); difference from CV within noise.
- 24x faster per prediction, about 80,000x in batches; break-even after about 7,000 predictions.
- Wrong mostly near the Moon's orbit, on chaotic moons (T5 met).

## For Phase 6

- Done: paper finishing (keywords, references, abstract, compiled PDF), notebook re-execution,
  fresh-clone test. Remaining: condensed RNAAS version, data archive and DOI, final README,
  LinkedIn post material.

## Limitations to state in a paper

- Newtonian gravity only: no tides, no Earth equatorial bulge, no relativity. Other
  planets are left out too.
- "Survived" means survived 100 years, not stable forever; about a fifth of 100-year
  survivors are lost by 1,000 years.
- One start date (tested with 30 moons); class shares depend on the sampling design.
- The R2 criterion missed survival beyond the Moon; recommend a beyond-one-lunar-distance test.
- Lidov–Kozai is inferred from outcome patterns, not traced in individual orbits.
