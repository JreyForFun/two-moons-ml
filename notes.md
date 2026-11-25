# Project notes

Material for the final LinkedIn post and a possible paper.

## Key numbers

_None yet. Planned: number of simulations, model accuracy, speedup of ML vs. simulation._

## Checks passed

- 2026-11-25, REBOUND 5.2.3 with IAS15: a two-body test orbit returned to its start
  after one period (position error 3.0e-15 in units of the orbit's semi-major axis,
  relative energy error 4.3e-16).

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
