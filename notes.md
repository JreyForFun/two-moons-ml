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

## Story moments

- Moving a moon by just 1 meter changed the outcome of 12 out of 100 moons. Chaos limits
  what any model can predict.

- The full run's first speed reading promised 11 hours. It took 5.2. The laptop was on battery
  at the start, and the first few dozen moons were not a fair sample.

- Leaving out the Sun made the Moon's position thousands of times worse (55,535 km vs
  10.3 km). "Just Earth and two moons" would not have been a fair simulation.

- The first two-moon run "survived", but plotting it showed the second moon's orbit stretching.
  The outcome label alone would have hidden that.

## Best figures

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

## Questions for Phase 3

- Why did 38% survive here but 18% in the pilot? Is it the flatter orbits?
- Which distances and tilts are safe? (stability maps)
- Do backward orbits survive more often than forward ones?
- Does the orbit stretching keep growing, or swing back? (still open from Phase 1)

## Limitations to state in a paper

- Newtonian gravity only: no tides, no Earth equatorial bulge, no relativity. Other
  planets are left out too.
- "Stable" will mean "survived to the chosen time limit", not stable forever.
