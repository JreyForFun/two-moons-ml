# Questions and answers

Every question raised so far, both the ones asked during the project and the ones worth
asking, with the answer and the evidence behind it. Updated after every step.

**Status:** ✅ answered · 🔶 partly answered · ⏳ open (the phase that should answer it)

See also: [report.md](report.md) for the full story, [figures.md](figures.md) for the charts.

---

## Asked during the project

**Q1. Before approving a step, how can I see it or run it?** ✅
Every step has a script. The table in `README.md` lists each command and what it does. Check
scripts print PASS or FAIL. Charts and animations are saved to `figures/`. Calculations are kept
in code files, not one-off commands, so they can be rerun.

**Q2. When will the `notebooks/` folder have a file?** ✅
At the end of Phase 1: `notebooks/01_first_simulation.ipynb`. Notebooks show results. The reusable
code lives in `src/`. Notebook 02 comes in Phase 3.

**Q3. How much computing should the dataset use?** ✅
One overnight run (8 to 10 hours) was the budget. The pilot showed 12,000 moons would fit. The run
took 5.2 hours.

**Q4. Should backward orbits be included?** ✅
Yes. Tilts from 0 to 180 degrees; over 90 means the moon orbits opposite to our Moon.

**Q5. Is there a phase where everything gets written up?** ✅
Phase 6 condenses everything into the README and final post. These documents are written as we go
so nothing is reconstructed from memory: `docs/report.md`, this file, and `docs/figures.md`.

---

## Phase 1: can we trust the simulation?

**Q6. Is the simulation realistic?** ✅
For the real system, yes. Our Moon stayed within 10.3 km of NASA's for a year, about 0.003% of
its distance. Evidence: `src/validate_real_system.py`, `figures/real_moon_error.png`.

**Q7. Why include the Sun if the question is about Earth's moons?** ✅
Without the Sun, the Moon's position was off by up to 55,535 km after a year, over 5,000 times
worse. The Sun's pull also decides how far out a moon can stay bound to Earth.

**Q8. Why this integrator (IAS15)?** ✅
It adjusts its time step automatically, which matters when a moon swings close to Earth or the
Moon. Its error is near computer rounding. The pilot confirmed it: stricter settings changed fewer
outcomes than a 1 meter nudge.

**Q9. How do we know rounding errors aren't building up?** ✅
Gravity alone conserves energy, so any change in total energy comes from the calculation. The
change stayed at about 10⁻¹⁵, pure rounding. This is a weak check on the moons, because Earth's
orbit around the Sun dominates the total. The comparison with NASA is stronger. Evidence:
`figures/two_moons_energy.png`.

**Q10. Are results reproducible?** ✅
Yes, on this computer, bit for bit. Fixed seeds, saved configs, the saved NASA data and a full
package list (`requirements-lock.txt`) make reruns identical. `check_dataset.py` reran 20 random
moons and got exactly the same results. A different computer or library version might differ in
the last digits, and chaos can grow that into different outcomes for some moons.

**Q11. What counts as "ejected"?** ✅
Farther than 4.5 million km from Earth *and* moving fast enough to escape. That is about 3 times
the distance where Earth's gravity stops dominating over the Sun's (the Hill radius, about
1.5 million km).

**Q12. What is the Roche limit and why does it matter?** ✅
Closer than about 18,365 km, Earth's tides would tear a Moon-like body apart. We don't simulate
breaking apart, so orbits that come that close are redrawn instead.

**Q13. Does "survived" mean "stable"?** ✅
No. The first second moon survived 10 years, but its orbit was stretching (its distance range grew
2.5 times). In the dataset, "survived" means "lasted at least 100 years". Statisticians call this
*censored* data. Evidence: `figures/two_moons_distance.png`.

**Q14. Does the stretching of the first moon's orbit keep growing, or swing back?** ⏳ Phase 3
Ten years was too short to tell. A longer run of that one moon would answer it.

**Q15. What does the simulation leave out?** ✅
Tides, Earth's equatorial bulge, relativity and the other planets. The 10.3 km error over a year
shows these are small for our Moon over short times. They could matter over thousands of years,
or for moons very close to Earth (where the bulge matters).

---

## Phase 2: building the dataset

**Q16. How long must a moon survive to count as stable?** ✅
100 years: the longest of 10, 30 or 100 years that fit the computing budget, by a rule set before
the pilot. Survival keeps falling with time (45% at 10 years, 28% at 30, 18% at 100 in the pilot),
so the choice matters.

**Q17. Do stricter integrator settings change the outcomes?** ✅
Rarely. 6 of 100 changed, fewer than the 12 changed by a 1 meter nudge. Those differences are
chaos, not inaccuracy, so the default is kept.

**Q18. How chaotic are the outcomes?** ✅
Moving a moon by 1 meter changed 12 of 100 outcomes after 100 years (9 after 10 years). In
chaotic systems, tiny differences grow until they change the result.

**Q19. What is the best accuracy a model could reach?** 🔶
The 88% agreement under a 1 meter nudge is a guide, not a hard ceiling. If outcomes are partly
random, the best possible model predicts the most likely outcome and can score somewhat above 88%.
We will compare our model's accuracy with it in Phase 5.

**Q20. Does the starting date matter?** 🔶
No clear effect: other dates agreed on 27 and 26 of 30 moons, vs 28 of 30 for the 1 meter nudge.
But 30 moons is a small test, so this is stated as a limitation.

**Q21. Why draw mass and distance log-uniformly?** ✅
They span large ranges (mass 0.001 to 1, a factor of 1,000). With plain uniform sampling, almost
every moon would be heavy and far. Log-uniform gives each factor of 10 equal coverage.

**Q22. Why change the tilt sampling after the pilot?** ✅
Uniform in cos(tilt) makes every direction in space equally likely, but then nearly flat orbits
are rare (7 of 100 had tilt under 40 degrees). Spreading tilt evenly in degrees covers them better.
The cost is that flat orbits are over-represented compared with random directions.

**Q23. Why use a new seed for the full dataset?** ✅
The pilot moons were used to make decisions. Reusing them in the final data would let those
decisions quietly fit them. A new seed gives fresh moons.

**Q24. What is data leakage, and how do we prevent it?** ✅
Leakage is when the model sees information it wouldn't have in real use, for example survival time,
which reveals the outcome. Columns named `input_*` may be model inputs; `result_*` must never be.
The starting position and velocity are saved too, as an alternative set of inputs.

**Q25. Are the classes balanced?** ✅
No. Survived 38%, ejected 32%, hit Earth 27%, hit the Moon 1.4%, real Moon lost 1.2%. A model can
look accurate while never predicting the rare ones. Phase 4 will decide whether to merge them or
sample more of their region, and will report per-class results.

**Q26. What is a fair baseline?** ✅
Always guessing the most common class: "survived", right 38.0% of the time. Any model must clearly
beat that. A simple model, like a Random Forest, comes next.

**Q27. Can the dataset be trusted?** ✅
`check_dataset.py` passed: no repeated or missing ids; all values in range; every input rebuilt
exactly from the seed; labels match outcomes; 20 random moons simulated again gave identical
results. The manifest's SHA-256 confirms the file hasn't changed.

**Q28. Does 38% survival mean a random second moon has a 38% chance?** ✅
No. The percentage depends on our choices: the ranges (such as 0.1 to 3 lunar distances) and how
we spread the samples. It describes our dataset, not nature.

**Q29. Why did the first speed estimate say 11 hours when the run took 5.2?** ✅
It came from the first few dozen moons, while the laptop was on battery and slowing its processor.
A small early sample is not a fair estimate.

**Q30. Why did 38% survive in the full dataset but only 18% in the pilot?** ⏳ Phase 3
The pilot's 95% interval was about 12% to 27%, so the gap is not chance. The likely cause is the
tilt sampling change: in the pilot, flat backward orbits (tilt 140 to 180) survived most often
(5 of 11), and the full dataset has more of them. To be tested with the full data.

---

## For later phases

**Q31. Which distances and tilts are safe?** ⏳ Phase 3
The pilot hints that close moons survive more often: 9 of 32 under 0.3 lunar distances, against 1
of 30 beyond 1 lunar distance. The stability maps will show it with 12,000 moons.

**Q32. Do backward orbits survive more often than forward ones?** ⏳ Phase 3
In the pilot, flat backward orbits did best (5 of 11). For moons of planets, backward orbits are
known to stay stable farther out. We will check whether our data shows this.

**Q33. Does the second moon's mass matter?** ⏳ Phase 3

**Q34. How do we know the model isn't just memorizing?** ⏳ Phase 4
By testing it on moons it never saw during training (a held-out test set), and comparing the
training and test scores.

**Q35. Which inputs are better: orbital elements or position and velocity?** ⏳ Phase 4

**Q36. How much faster is the model than the simulation?** ⏳ Phase 5
The simulation takes a median of 1.5 s per moon and up to 104 s.

**Q37. Where does the model fail, and why?** ⏳ Phase 5
Expected: near the boundary between outcomes, where chaos makes even the simulation unpredictable.
