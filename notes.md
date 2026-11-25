# Project notes

Material for the final LinkedIn post and a possible paper.

## Key numbers

- Simulated Moon vs NASA over one year: at most 10.3 km off (average 5.6 km), about
  0.003% of the Earth-Moon distance.
- Same run without the Sun: up to 55,535 km off.

_Planned: number of simulations, model accuracy, speedup of ML vs. simulation._

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

## Story moments

- Leaving out the Sun made the Moon's position thousands of times worse (55,535 km vs
  10.3 km). "Just Earth and two moons" would not have been a fair simulation.

## Best figures

- `figures/real_moon_error.png`: with vs without the Sun.
- `figures/real_moon_orbit.png`: one year of the Moon's path, with NASA's positions.

## Method decisions

- Starting positions: NASA JPL Horizons, fixed date 2026-01-01, saved to `configs/`.
- Ejected means farther than 4.5 million km from Earth (about 3 Hill radii) and not bound
  to it, checked every 6 hours. Collisions are checked along the path of every step.
- The Sun is included because it limits how far from Earth a moon can stay bound.
- Integrator: IAS15, which adapts its time step during close encounters.
- Before adding a second moon, the real Sun-Earth-Moon system is checked against known values.

## Limitations to state in a paper

- Newtonian gravity only: no tides, no Earth equatorial bulge, no relativity. Other
  planets are left out too.
- "Stable" will mean "survived to the chosen time limit", not stable forever.
