# Design decisions and open questions

The questions behind each design choice, with the answer and the supporting evidence. Open
questions name the phase expected to answer them. Terms are defined in the
[glossary](glossary.md); the full record is in the [technical report](report.md).

Status: **Answered**, **Partly answered**, or **Open (phase)**.

## Contents

- [Simulation validity](#simulation-validity) (Q1–Q11)
- [Dataset design](#dataset-design) (Q12–Q27)
- [Exploration](#exploration-phase-3) (Q28–Q31)
- [Modeling and evaluation](#modeling-and-evaluation-phases-45) (Q32–Q35)

---

## Simulation validity

**Q1. Is the simulation realistic?** *Answered.*
For the real system, yes: the simulated Moon stays within 10.3 km of the JPL ephemeris over one
year, about 0.003% of its distance.
Evidence: `src/validate_real_system.py`, [real_moon_error.png](figures.md#real_moon_errorpng).

**Q2. Why include the Sun in a question about Earth's moons?** *Answered.*
Without it, the Moon's position error after one year reaches 55,535 km, over 5,000 times larger.
The Sun's tidal pull also sets the outer limit for bound satellites (the Hill radius).

**Q3. Why IAS15?** *Answered.*
It adapts its step size during close encounters and keeps errors near machine precision. In the
pilot, tightening its tolerance changed fewer outcomes (6 of 100) than a 1 m displacement (12 of
100), so the default tolerance is not the limiting factor.

**Q4. Is numerical error accumulating?** *Answered.*
The relative energy error stays around 10⁻¹⁵ with no drift over 10 years. Because Earth's
heliocentric orbit dominates the total energy, this is a weak test of the moons themselves; the
ephemeris comparison (Q1) is the stronger test.
Evidence: [two_moons_energy.png](figures.md#two_moons_energypng).

**Q5. Are the results reproducible?** *Answered.*
On the same machine and software, bit for bit: fixed seeds, saved configurations, stored JPL
data and a full package list (`requirements-lock.txt`). Re-simulating 20 random moons from the
final dataset gave identical results. Different hardware or library versions may differ in the
last digits, which chaos can amplify into different outcomes for some moons.

**Q6. How is ejection defined?** *Answered.*
Distance from Earth above 4.5 million km together with positive Earth-relative orbital energy.
The threshold is about three times Earth's Hill radius (≈ 1.5 million km).

**Q7. Why exclude orbits that pass inside the Roche limit?** *Answered.*
Inside about 18,365 km, a Moon-density body would be tidally disrupted, which the simulation does
not model. Such orbits are redrawn and the number of redraws is recorded.

**Q8. Does surviving the time limit mean the orbit is stable?** *Answered.*
No. The first second moon survived 10 years while its distance range grew by a factor of 2.5.
`survived` is therefore treated as right-censored: a lifetime of at least 100 years.
Evidence: [two_moons_distance.png](figures.md#two_moons_distancepng).

**Q9. Does the eccentricity growth of the first second moon continue or oscillate?** *Open (Phase 3).*
Ten years is too short to tell. A longer integration of the same system would answer it.

**Q10. What physics is omitted, and when would it matter?** *Answered.*
Tides, Earth's oblateness, general relativity and the other planets. The 10.3 km validation error
shows these are small for the Moon over a year. They can matter over thousands of years, and
oblateness matters most for satellites close to Earth.

**Q11. What computing budget and orbit directions does the dataset cover?** *Answered.*
One overnight run (8 to 10 hours, 4 workers), covering both prograde and retrograde orbits
(inclination 0° to 180°). The final run took 5.2 hours.

---

## Dataset design

**Q12. How long must a moon survive to be labeled stable?** *Answered.*
100 years: the longest candidate limit (10, 30 or 100 years) that fit the computing budget, by a
pre-registered rule. Survival keeps declining with time (45%, 28% and 18% at 10, 30 and 100 years
in the pilot), so the limit materially affects the labels.

**Q13. Do outcomes depend on integrator tolerance?** *Answered.*
Rarely: 6 of 100 outcomes changed at tolerance 10⁻¹¹, fewer than the 12 changed by a 1 m
displacement. The differences are attributed to chaos rather than numerical inaccuracy.

**Q14. How chaotic are the outcomes?** *Answered.*
A 1 m displacement changed 12 of 100 outcomes after 100 years and 9 of 100 after 10 years.

**Q15. What accuracy can a model be expected to reach?** *Partly answered.*
The 88% agreement under a 1 m displacement is an indicative bound, not a strict ceiling: when
outcomes are partly random, an optimal predictor can exceed the agreement between two noisy
realizations. Model accuracy will be compared against it in Phase 5.

**Q16. Does the start date matter?** *Partly answered.*
No clear effect: agreement of 27/30 and 26/30 at two other dates, versus 28/30 for a 1 m
displacement. The sample is small, so this is listed as a limitation.

**Q17. Why log-uniform sampling for mass and semi-major axis?** *Answered.*
Both span large ranges (mass over a factor of 1,000). Uniform sampling would concentrate almost all
moons at the high end; log-uniform sampling covers each factor of 10 equally.

**Q18. Why was the inclination sampling changed after the pilot?** *Answered.*
Isotropic sampling (uniform in cos *i*) makes near-planar orbits rare: only 7 of 100 pilot moons had
inclinations below 40°. Sampling uniformly in degrees covers them better, at the cost of
over-representing them relative to random orientations.

**Q19. Why does the final dataset use a different seed from the pilot?** *Answered.*
Pilot moons informed the design decisions. Using new moons keeps the final data independent of
those decisions.

**Q20. How is data leakage prevented?** *Answered.*
Columns are prefixed `input_` (candidate features: orbital elements and the equivalent
Earth-relative state vector) or `result_` (label, raw outcome, survival time, computing time).
`result_` columns are never used as features.

**Q21. Are the classes balanced?** *Answered.*
No: `survived` 38.0%, `ejected` 32.0%, `hit_earth` 27.4%, `hit_moon` 1.4%, `moon_lost` 1.2%. Phase 4
will decide between merging the rare classes and targeted sampling, and will report per-class
metrics.

**Q22. What is the baseline to beat?** *Answered.*
The majority-class baseline (always `survived`) scores 38.0% accuracy. A Random Forest will be
the first learned baseline.

**Q23. Can the dataset be trusted?** *Answered.*
`src/check_dataset.py` passes: no duplicate or missing ids, all parameters in range, all inputs
regenerated exactly from the seed, labels consistent with outcomes, and 20 random moons
re-simulated identically. The manifest's SHA-256 confirms the file is unchanged.

**Q24. Does 38% survival mean a random second moon has a 38% chance of surviving?** *Answered.*
No. The share depends on the chosen parameter ranges and distributions. It describes the dataset,
not an astrophysical probability.

**Q25. Why did the early runtime estimate (11 hours) exceed the actual runtime (5.2 hours)?** *Answered.*
It was based on the first few dozen moons, computed while the machine was on battery power with
reduced processor speed. Small early samples give unreliable estimates.

**Q26. Why are both orbital elements and state vectors stored?** *Answered.*
They describe the same starting orbit in two forms. Comparing models trained on each (Phase 4)
shows which representation is easier to learn from.

**Q27. Why did 38% survive in the full dataset but only 18% in the pilot?** *Open (Phase 3).*
The pilot's 95% interval (about 12% to 27%) excludes 38%, so sampling noise is an unlikely
explanation. The leading hypothesis is the change in inclination sampling: in the pilot,
near-planar retrograde orbits (140° to 180°) survived most often (5 of 11), and the full dataset
contains proportionally more of them.

---

## Exploration (Phase 3)

**Q28. Which semi-major axes and inclinations allow survival?** *Open (Phase 3).*
The pilot suggests that close-in moons survive more often: 9 of 32 below 0.3 lunar distances,
against 1 of 30 beyond 1 lunar distance. Stability maps of the full dataset will test this.

**Q29. Are retrograde orbits more stable than prograde ones?** *Open (Phase 3).*
Studies of satellites around planets find that retrograde orbits remain stable to larger
distances than prograde ones. The pilot is consistent with this (5 of 11 near-planar retrograde
orbits survived), and the full dataset will test it.

**Q30. Does the second moon's mass matter?** *Open (Phase 3).*

**Q31. How are survival times distributed, and does survival level off?** *Open (Phase 3).*
In the pilot, the surviving fraction is still falling at 100 years.

---

## Modeling and evaluation (Phases 4–5)

**Q32. How is memorization detected?** *Open (Phase 4).*
By evaluating on a held-out test set never used for training and comparing training and test
scores.

**Q33. Which input representation works better: orbital elements or state vectors?** *Open (Phase 4).*

**Q34. How much faster is the surrogate than the simulation?** *Open (Phase 5).*
Reference: the simulation takes a median of 1.5 s per moon and up to 104 s.

**Q35. Where does the model fail?** *Open (Phase 5).*
Expected near boundaries between outcome regions, where chaos makes even the simulation
unpredictable (Q14).
