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
  1,000 years (17.9 CPU-hours, 4.5 hours); 393 survived. Total simulations so far: 12,865.
- Close, low-tilt orbits: 96.5% survive. Close near-polar orbits: 0.7% survive, 99.1% hit Earth.
- Beyond the Moon's orbit: prograde 0.3% survive, retrograde 11.4%.
- Heaviest second moons knock out the real Moon in 7.4% of systems.
- 21.4% of 100-year survivors are lost by 1,000 years; ~30% of moons would last 1,000 years.

_Planned: model accuracy, speedup of ML vs. simulation._

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
- Survived 38% here vs 18% in the pilot (95% interval about 12% to 27%). The tilt sampling
  changed between them, giving more nearly flat orbits. Whether that explains it is a Phase 3 question.
- Hit the Moon (1.4%) and real Moon lost (1.2%) are under the 2% rule set in the plan:
  merge them or sample more of their region. Decide in Phase 4.
- Survivors are censored: "survived" means at least 100 years, not forever.

## Phase 3 (2026-11-26, `src/plot_dataset.py`, rules R1–R4 set before the analysis)

- Test set frozen first (`configs/split.json`) so exploration cannot leak into model evaluation.
- R1 failed: reweighting explains only part of the pilot gap (29.7% vs pilot 12–27%). Reruns of
  pilot moons were identical; the rest is the pilot's unlucky draws and noise (2.1 sigma).
- R2 not shown as defined (same 10% edge for both directions), but retrograde moons clearly
  survive beyond the Moon's orbit while prograde ones do not (descriptive).
- R3: mass matters (−11.4 points, heaviest vs lightest). R4: losses slow but do not stop.
- First moon over 1,000 years: eccentricity cycles (~17 years), no growth.
- Maps agree between independent halves of the data (r = 0.99).

## Story moments

- Moving a moon by just 1 meter changed the outcome of 12 out of 100 moons. Chaos limits
  what any model can predict.

- The full run's first speed reading promised 11 hours. It took 5.2. The laptop was on battery
  at the start, and the first few dozen moons were not a fair sample.

- The stability map has a dead band at 90° tilt: even very close moons crash into Earth when
  their orbits are near-polar (Lidov–Kozai). Tilt matters as much as distance.

- A pre-registered rule failed (R1). Instead of changing the rule, the gap was investigated and
  explained step by step, which is the honest version of the story.

- A pandas quirk (rounded bin labels) was caught by an automated check before any result used it.

- Leaving out the Sun made the Moon's position thousands of times worse (55,535 km vs
  10.3 km). "Just Earth and two moons" would not have been a fair simulation.

- The first two-moon run "survived", but plotting it showed the second moon's orbit stretching.
  The outcome label alone would have hidden that.

## Best figures

- `figures/stability_map.png`: the headline figure (where second moons survive).
- `figures/survival_by_direction.png`: only retrograde moons survive beyond the Moon.
- `figures/outcome_maps.png`: what happens instead, region by region.
- `figures/first_moon_long_term.png`: 1,000 years of the first second moon.
- `figures/pilot_outcomes.png`, `figures/pilot_survival.png`: pilot results.
- `figures/two_moons.gif`: 60 days of both moons.
- `figures/two_moons_distance.png`: the second moon's orbit stretching over 10 years.
- `figures/real_moon_error.png`: with vs without the Sun.
- `figures/real_moon_orbit.png`: one year of the Moon's path, with NASA's positions.

## Method decisions

- Starting positions: NASA JPL Horizons, fixed date 2026-01-01, saved to `configs/`.
- Ejected means farther than 4.5 million km from Earth (about 3 Hill radii) and not bound
  to it, checked every 6 hours. Collisions are checked along the path of every step.
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
- Backward orbits: same inner edge, but only they survive beyond the Moon.
- Orbit stretching: a bounded ~17-year cycle.

## Questions for Phase 4

- Merge the two rare outcomes or sample their region (near the Moon's orbit) more densely?
- Orbital elements, state vectors, or derived features (periapsis, apoapsis vs the Moon, tilt vs 90°)?
- How far above the 38% majority baseline can a model get, given 12% chaos?

## Limitations to state in a paper

- Newtonian gravity only: no tides, no Earth equatorial bulge, no relativity. Other
  planets are left out too.
- "Stable" will mean "survived to the chosen time limit", not stable forever.
