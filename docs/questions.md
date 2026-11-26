# Design decisions and open questions

The questions behind each design choice, with the answer and the supporting evidence. Open
questions name the phase expected to answer them. Terms are defined in the
[glossary](glossary.md); the full record is in the [technical report](report.md).

Status: **Answered**, **Partly answered**, or **Open (phase)**.

## Contents

- [Simulation validity](#simulation-validity) (Q1–Q11)
- [Dataset design](#dataset-design) (Q12–Q27)
- [Exploration](#exploration-phase-3) (Q28–Q31, Q36–Q38, Q41)
- [Modeling and evaluation](#modeling-and-evaluation-phases-45) (Q32–Q35, Q39–Q40)

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

**Q9. Does the eccentricity growth of the first second moon continue or oscillate?** *Answered.*
It oscillates. Over 1,000 years the system survives; the eccentricity cycles with a dominant period
of about 17 years, its 10-year mean stays between 0.013 and 0.039, and the average is the same
(0.0242) in both halves of the run. The growth over the first 10 years was the rising part of
this cycle.
Evidence: `src/long_run.py`, [first_moon_long_term.png](figures.md#first_moon_long_termpng).

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

**Q27. Why did 38% survive in the full dataset but only 18% in the pilot?** *Answered.*
Mostly sampling design, plus a small and unlucky pilot. Reweighting the training moons to the
pilot's isotropic inclinations lowers survival from 37.9% to 29.7%, just outside the pilot's 95%
interval, so the pre-registered rule R1 was not met and other causes were investigated.
Re-simulating 20 pilot moons with the final code reproduced them exactly (no code change). The 50
nearest training moons of each pilot moon predict 25.4 survivors against the observed 18,
2.1 standard deviations of outcome noise. The gap divides into −8.2 points (inclination sampling),
−4.3 (the pilot's particular moons) and −7.4 (outcome noise).
Evidence: `src/plot_dataset.py`, `src/compare_pilot.py`, [technical report](report.md), Phase 3.

---

## Exploration (Phase 3)

**Q28. Which semi-major axes and inclinations allow survival?** *Answered.*
Close, low-inclination orbits: 96.5% of moons inside 0.5 lunar distances with inclinations below
45° or above 135° survive 100 years. Near-polar orbits fail at every distance (Q37), and orbits
reaching the Moon's orbit rarely survive (3.0%). Beyond about 0.75 lunar distances only
retrograde orbits survive (Q29). The maps reproduce across independent halves of the data
(correlation 0.991).
Evidence: [stability_map.png](figures.md#stability_mappng),
[stability_map_eccentricity.png](figures.md#stability_map_eccentricitypng).

**Q29. Are retrograde orbits more stable than prograde ones?** *Partly answered.*
Not at the outer survival edge: by rule R2, both directions fall below 10% survival in the same bin, just
inside the Moon's orbit (0.22 Hill radii). Beyond the Moon's orbit, yes (descriptive): 11.4% of
retrograde moons survive against 0.3% of prograde moons, up to about 17% between 0.5 and 0.78 Hill
radii. Overall, retrograde moons survive 41.2% and prograde 34.8%; since all parameters were drawn
independently, this comparison is not confounded.
Evidence: [survival_by_direction.png](figures.md#survival_by_directionpng).

**Q30. Does the second moon's mass matter?** *Answered.*
Yes (rule R3): survival is 42.3% in the lightest mass bin (0.001–0.003 lunar masses) and 30.9% in
the heaviest (0.32–1), a difference of −11.4 points (95% interval −14.4 to −8.3). The heaviest
second moons destabilize the Moon itself in 7.4% of systems, against none for the lightest.

**Q31. How are survival times distributed, and does survival level off?** *Answered.*
Losses occur on every timescale and slow down without stopping (rule R4 not met). 34.7% of
systems alive at 10 years are lost by 100 years; 21.4% (95% interval 18.0% to 25.2%) of 100-year
survivors are lost by 1,000 years, based on 500 random survivors integrated further. About 29.8%
of training systems would survive 1,000 years.
Evidence: `src/survival_curve.py`, [survival_curve_full.png](figures.md#survival_curve_fullpng).

**Q36. Why does the Moon, not the Hill radius, set the outer limit?** *Answered.*
The Moon orbits at 0.26 Hill radii, well inside the roughly 0.5 Hill radii where solar tides alone
would destabilize a prograde satellite. Second moons whose orbits approach the Moon's suffer close
encounters that eject them or send them into Earth, so survival collapses near the Moon's distance
before the solar limit is reached.

**Q37. Why do close near-polar orbits almost never survive?** *Answered (mechanism inferred).*
Inside 0.5 lunar distances, 99.1% of moons with inclinations between 75° and 105° collide with
Earth. This matches Lidov–Kozai cycles: a perturber orbiting near the ecliptic (the Moon and the
Sun) slowly exchanges a satellite's inclination for eccentricity, until the periapsis reaches
Earth's surface. The mechanism is inferred from the pattern; individual orbits were not traced.

**Q38. Is "survived 100 years" a reliable label?** *Answered.*
It is a reproducible but censored label: all 500 extended survivors repeated their first 100
years exactly, but about a fifth were lost by 1,000 years. Models trained on it predict survival
for 100 years, not long-term stability.

**Q41. What does it mean when a pre-registered rule is not met?** *Answered.*
The evidence did not reach the criterion fixed before the analysis; the claim is not shown false.
Of the four Phase 3 rules, R3 (mass) was met; R1 (pilot gap) and R4 (levelling off) were near
misses with quantified partial effects; R2 (outer edge) was not shown because its criterion
measured where survival first drops, which the Moon fixes for both directions. The
prograde-retrograde difference beyond the Moon's orbit is a descriptive finding, recommended as a
pre-registered test in future work.
Evidence: [technical report](report.md), Phase 3, "Reading the decision rules"; glossary entries
"Criterion met / not met" and "Descriptive (post-hoc) finding".

---

## Modeling and evaluation (Phases 4–5)

**Q32. How is memorization detected?** *Open (Phase 4).*
By evaluating on a held-out test set never used for training and comparing training and test
scores. The test set (2,400 moons, stratified) was frozen before exploration in `configs/split.json`.

**Q33. Which input representation works better: orbital elements or state vectors?** *Open (Phase 4).*

**Q34. How much faster is the surrogate than the simulation?** *Open (Phase 5).*
Reference: the simulation takes a median of 1.5 s per moon and up to 104 s.

**Q35. Where does the model fail?** *Open (Phase 5).*
Expected near boundaries between outcome regions, where chaos makes even the simulation
unpredictable (Q14).

**Q39. Should the two rare outcomes be merged or sampled more densely?** *Open (Phase 4).*
Collisions with the Moon (1.4%) and loss of the Moon (1.2%) are concentrated between about 0.5
and 1.5 lunar distances ([outcome_maps.png](figures.md#outcome_mapspng)), so targeted sampling of
that region is feasible.

**Q40. Do derived geometric features help?** *Open (Phase 4).*
Periapsis, apoapsis relative to the Moon's orbit and inclination relative to 90° separate the
outcome regions in Phase 3 and are candidate features.
