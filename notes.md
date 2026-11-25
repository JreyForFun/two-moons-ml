# Project notes

Material for the final LinkedIn post and a possible paper.

## Key numbers

_None yet. Planned: number of simulations, model accuracy, speedup of ML vs. simulation._

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

## Story moments

_None yet._

## Best figures

_None yet._

## Method decisions

- Starting positions: NASA JPL Horizons, fixed date 2026-01-01, saved to `configs/`.
- The Sun is included because it limits how far from Earth a moon can stay bound.
- Integrator: IAS15, which adapts its time step during close encounters.
- Before adding a second moon, the real Sun-Earth-Moon system is checked against known values.

## Limitations to state in a paper

- Newtonian gravity only: no tides, no Earth equatorial bulge, no relativity.
- "Stable" will mean "survived to the chosen time limit", not stable forever.
