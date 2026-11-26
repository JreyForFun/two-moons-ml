# Figure guide

Description, reading guide, interpretation and caveats for every figure in `figures/`. Each figure
is produced by a script and can be regenerated exactly. Terms are defined in the
[glossary](glossary.md).

Color convention: **blue** for the Moon, surviving systems or the reference simulation;
**orange** for the second moon, non-surviving systems or comparison runs.

| Figure | Phase | Script |
|---|---|---|
| [two_moons.gif](#two_moonsgif) | 1 | `src/animate.py` |
| [real_moon_orbit.png](#real_moon_orbitpng) | 1 | `src/plot_real_system.py` |
| [real_moon_error.png](#real_moon_errorpng) | 1 | `src/plot_real_system.py` |
| [two_moons_distance.png](#two_moons_distancepng) | 1 | `src/plot_single_run.py` |
| [two_moons_energy.png](#two_moons_energypng) | 1 | `src/plot_single_run.py` |
| [pilot_outcomes.png](#pilot_outcomespng) | 2 | `src/analyze_pilot.py` |
| [pilot_survival.png](#pilot_survivalpng) | 2 | `src/analyze_pilot.py` |
| [stability_map.png](#stability_mappng) | 3 | `src/plot_dataset.py` |
| [outcome_maps.png](#outcome_mapspng) | 3 | `src/plot_dataset.py` |
| [stability_map_eccentricity.png](#stability_map_eccentricitypng) | 3 | `src/plot_dataset.py` |
| [survival_by_direction.png](#survival_by_directionpng) | 3 | `src/plot_dataset.py` |
| [survival_curve_full.png](#survival_curve_fullpng) | 3 | `src/survival_curve.py` |
| [first_moon_long_term.png](#first_moon_long_termpng) | 3 | `src/long_run.py` |

---

## two_moons.gif

![Both moons orbiting Earth](../figures/two_moons.gif)

**Content.** 60 days of the Earth-centered system viewed from above the ecliptic: the Moon and a
hypothetical second moon of 0.1 lunar masses on a circular orbit at 0.4 lunar distances. Frames
are 6 hours apart; trails show the previous 5 days.

**Reading.** The second moon completes about four orbits per lunar orbit, as expected from
Kepler's third law (0.4^1.5 ≈ 0.25).

**Interpretation.** An illustration of the system studied; quantitative results are in the
figures below.

**Caveats.** Distances are to scale; body sizes are not. The frame is centered on Earth, so
Earth's motion around the Sun is not shown.

---

## real_moon_orbit.png

![The Moon's path around Earth](../figures/real_moon_orbit.png)

**Content.** The Moon's path around Earth during 2026, projected onto the ecliptic. Line:
simulation. Points: JPL Horizons positions every 5 days.

**Reading.** Every JPL point lies on the simulated path. The orbit is an ellipse (about 357,000 to
405,000 km from Earth) whose orientation and shape are slowly changed by the Sun, so successive
orbits do not overlap exactly.

**Interpretation.** The simulation reproduces the Moon's orbit at the scale of the figure.

**Caveats.** Errors of order 10 km are invisible at this scale; they are quantified in the next
figure.

---

## real_moon_error.png

![Position error with and without the Sun](../figures/real_moon_error.png)

**Content.** Distance between the simulated and JPL Moon positions over one year, with the Sun
included (blue) and omitted (orange).

**Reading.** Logarithmic vertical axis: each gridline is a factor of 10. With the Sun, the error
grows slowly to about 10 km. Without it, the error exceeds 4,000 km within weeks and peaks at
55,535 km.

**Interpretation.**
- The simulation is accurate to 10.3 km after one year (about 0.003% of the Earth-Moon distance).
- Solar perturbations dominate the error budget; the Sun cannot be omitted.
- The slow growth of the blue curve is consistent with small unmodeled effects (other planets,
  tides, oblateness) accumulating over time.

**Caveats.** One year from one start date; errors continue to grow over longer integrations.

---

## two_moons_distance.png

![Both moons' distance from Earth over 10 years](../figures/two_moons_distance.png)

**Content.** Earth distance of the Moon (blue) and the second moon (orange) over a 10-year
integration.

**Reading.** Each oscillation is one orbit; the height of each band reflects the orbit's
eccentricity, and a circular orbit would appear as a flat line.
- The Moon's band is steady at about 357,000 to 403,000 km.
- The second moon starts on a circular orbit (a thin line) and its band widens: the yearly
  distance range grows from 5,847 km in the first year to 14,726 km in the tenth.

**Interpretation.** Both moons survive, but the second moon's eccentricity is being excited by
lunar perturbations. Survival over a fixed interval does not imply an unchanging orbit, which is
why `survived` in the dataset means a lifetime of at least 100 years.

**Caveats.** A single system over 10 years; whether the growth continues or oscillates is open
(Q9 in [questions.md](questions.md)).

---

## two_moons_energy.png

![Total energy over 10 years](../figures/two_moons_energy.png)

**Content.** Relative change in the total energy of the system during the 10-year integration.

**Reading.** The vertical axis is in units of 10⁻¹⁵. Values fall on discrete levels set by
floating-point precision. No systematic drift is present.

**Interpretation.** The integration conserves energy to rounding precision.

**Caveats.** The total is dominated by Earth's heliocentric orbit, so errors confined to the moons
could be masked. The ephemeris comparison is the more sensitive test.

---

## pilot_outcomes.png

![Which pilot moons survived](../figures/pilot_outcomes.png)

**Content.** The 100 pilot moons by initial semi-major axis (logarithmic horizontal axis) and
inclination. Circles: survived 100 years. Crosses: collided or were ejected. Above 90° the orbit
is retrograde.

**Reading.**
- 17 of the 18 survivors start within 0.7 lunar distances. Beyond 1 lunar distance, 24 of 30 moons
  are ejected.
- Prograde survivors have inclinations of about 45° to 70°; retrograde survivors about 125° to
  166°, flatter than most retrograde non-survivors (concentrated between 90° and 120°).
- Few points lie near 0° because the pilot sampled inclination isotropically.

**Interpretation.** Outcomes are structured in parameter space, the pattern a surrogate model
must learn. The sparse coverage of near-planar orbits motivated the change of inclination
sampling for the full dataset.

**Caveats.** 100 moons; mass, eccentricity and orientation angles also vary but are not shown.
Stability maps from the full dataset (Phase 3) supersede this figure.

---

## pilot_survival.png

![Share of pilot moons still there over time](../figures/pilot_survival.png)

**Content.** Fraction of the 100 pilot moons not yet collided or ejected, as a function of time.

**Reading.** Each step down is one collision or ejection. Logarithmic time axis. The surviving
fraction is 88% at 1 year, 45% at 10 years and 18% at 100 years, and is still declining at the end.

**Interpretation.** Losses continue on every timescale from months to a century, so the choice of
time limit materially affects the share labeled `survived`.

**Caveats.** All runs reached either a terminal event or the 100-year limit, so this is a simple
empirical fraction; with censoring before the limit, a Kaplan-Meier estimate would be needed.
Based on isotropic inclination sampling.

---

## stability_map.png

![Survival share by semi-major axis and inclination](../figures/stability_map.png)

**Content.** Share of the 9,600 training moons surviving 100 years, binned by initial semi-major
axis (12 logarithmic bins, bottom axis in lunar distances, top axis in Hill radii) and inclination
(12 bins of 15°). Darker cells mean higher survival. Dashed line: the Moon's orbit. Dotted line:
half of Earth's Hill radius. Every cell holds 44 to 93 moons.

**Reading.**
- Inside about 0.5 lunar distances, low-inclination orbits (below 45° or above 135°) survive almost
  always (96.5%).
- A pale band around 90° runs across all distances: near-polar orbits rarely survive, even close to
  Earth.
- Beyond about 0.75 lunar distances the map is pale for prograde orbits; only near-planar
  retrograde orbits (above 135°) keep some survival beyond the Moon's orbit.

**Interpretation.** Survival is structured by three mechanisms: close encounters with the Moon
(orbits reaching its distance), Lidov–Kozai cycles for strongly inclined orbits, and the greater
stability of retrograde orbits far from Earth. This is the structure a surrogate model must learn.

**Caveats.** Mass, eccentricity and orientation angles vary within each cell and are averaged over.
The inclination distribution is uniform in degrees, so cell shares are conditional on inclination
and not affected by that choice, but overall shares are (see Q24). Split-half correlation 0.991.

---

## outcome_maps.png

![Outcome shares by semi-major axis and inclination](../figures/outcome_maps.png)

**Content.** Four panels on the axes of the stability map: shares of moons that survived, were
ejected, or collided with Earth (shared blue scale), and the number of rare outcomes (collision
with the Moon or loss of the Moon, orange scale).

**Reading.**
- Ejections dominate beyond the Moon's orbit, especially for prograde orbits.
- Collisions with Earth fill the near-polar band at all distances and the region around the Moon's
  orbit.
- Rare outcomes cluster between about 0.5 and 1.5 lunar distances, where the two moons interact
  most strongly; up to about 11 per cell.

**Interpretation.** Each outcome occupies its own region. The rare classes are concentrated near
the Moon's orbit, which matters for the Phase 4 choice between merging them and sampling that
region more densely.

**Caveats.** The rare-outcome panel shows counts, not shares, and is based on 254 training moons.

---

## stability_map_eccentricity.png

![Survival share by semi-major axis and eccentricity](../figures/stability_map_eccentricity.png)

**Content.** Survival share by semi-major axis and eccentricity. Dashed curves mark orbits that
just touch the Moon's orbit: apoapsis equal to one lunar distance (left) and periapsis equal to one
lunar distance (right). Orbits between and above the two curves cross the Moon's orbit. Dotted
curve: periapsis at the Roche limit; orbits above it were excluded from sampling, which leaves the
upper-left cells empty.

**Reading.** Survival drops sharply where the left dashed curve is crossed: once the apoapsis
reaches the Moon's orbit, survival falls from about 60–80% to near zero. Orbits that cross the
Moon's orbit survive in 3.0% of cases. Outside the Moon's orbit, survival stays low at all
eccentricities.

**Interpretation.** Close approaches to the Moon are the main destabilizing mechanism for moons
near its distance. A simple geometric quantity, whether the orbit reaches the Moon's, captures
much of the outcome.

**Caveats.** Inclination is averaged over, including the near-polar orbits that fail for a
different reason. Split-half correlation 0.977.

---

## survival_by_direction.png

![Survival by semi-major axis for prograde and retrograde moons](../figures/survival_by_direction.png)

**Content.** Share surviving 100 years in each semi-major-axis bin (in Hill radii), separately for
prograde (blue) and retrograde (orange) training moons, with 95% Wilson intervals. Vertical lines:
the 10% survival edge from rule R2 (the same bin for both directions), the Moon's orbit, and the
prograde stability limit reported for a Jupiter-mass planet (0.49 Hill radii; Domingos et al. 2006).

**Reading.**
- Up to about 0.1 Hill radii both directions survive at 65–72%.
- Both fall below 10% just inside the Moon's orbit (about 0.22 Hill radii); retrograde survival
  falls more slowly.
- Beyond the Moon's orbit, prograde survival stays near 0% while retrograde survival recovers to
  about 17% between 0.5 and 0.78 Hill radii.

**Interpretation.** The Moon sets the outer limit for prograde second moons, well inside the limit
expected from the Sun alone. Retrograde orbits survive beyond the Moon, consistent with the greater
stability of retrograde satellites. Rule R2, as defined, does not detect this because both
directions cross 10% in the same bin.

**Caveats.** The literature limit applies to a planet with no other moon and is shown for
orientation only.

---

## survival_curve_full.png

![Fraction of second moons still orbiting up to 1,000 years](../figures/survival_curve_full.png)

**Content.** Fraction of systems not yet collided or ejected, from 0.1 to 1,000 years
(logarithmic time axis). Solid blue: the 9,600 training systems up to 100 years. Dashed blue with
band: beyond 100 years, the 100-year survival multiplied by the surviving share of 500 random
survivors integrated to 1,000 years, with a 95% interval. Dotted orange: the same curve reweighted
to isotropic inclinations. Grey: the 100-system pilot.

**Reading.** The training curve falls from 58% at 10 years to 38% at 100 years and 30% at 1,000
years. The slope flattens after 100 years but does not reach zero. The reweighted curve lies below
the training curve after a few years because near-planar orbits, which survive more often, carry
less weight under isotropic sampling. The pilot curve stays close to the reweighted curve for the
first few years and falls below it after about 3 years.

**Interpretation.** Losses continue on every timescale up to 1,000 years, more slowly after
100 years (21.4% of 100-year survivors lost by 1,000 years, against 34.7% of 10-year survivors
lost by 100 years). The 100-year label is a lower bound on lifetime.

**Caveats.** Beyond 100 years the curve rests on 500 systems; its band reflects that sample only.
The pilot curve is based on 100 systems (see rule R1 in the [technical report](report.md)).

---

## first_moon_long_term.png

![Eccentricity of the first second moon over 1,000 years](../figures/first_moon_long_term.png)

**Content.** Eccentricity around Earth of the Phase 1 second moon (0.1 lunar masses, 0.4 lunar
distances, initially circular and planar) over 1,000 years, every 10 days (thin line) and as a
10-year running mean, with the Moon's 10-year mean for reference. The dotted line marks the end of
the original 10-year run.

**Reading.** The 10-year mean oscillates between 0.013 and 0.039 with no trend; the average is
0.0242 in both halves of the run. The dominant period is about 17 years. The Moon's mean
eccentricity stays near 0.052.

**Interpretation.** The growth in the distance range seen in Phase 1 (`two_moons_distance.png`)
was the rising part of a bounded oscillation, not the start of a runaway. This system appears
stable over at least 1,000 years.

**Caveats.** A single system. Osculating elements include short-period variations, which the
running mean smooths out.
