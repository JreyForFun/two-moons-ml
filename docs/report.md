# Project report

The full story of the project, phase by phase: what we built, what we found, what changed
and why. It is updated after every step.

- Questions and answers: [questions.md](questions.md)
- Every figure explained: [figures.md](figures.md)
- Short material for the final post: [../notes.md](../notes.md)

**Status (2026-11-26):** Phase 2 finished. Next: Phase 3, exploration and stability maps.

## Simulation count

| Date | Run | Simulations | CPU-hours | Running total of random second moons |
|---|---|---:|---:|---:|
| 2026-11-25 | Phase 1: real system (with and without the Sun), one 10-year second moon, 60-day animation | 4 | under 0.01 | 0 |
| 2026-11-25 | Pilot A: 100 random moons, 100 years | 100 | 0.19 | 100 |
| 2026-11-25 | Pilot B: same moons, stricter integrator | 100 | 0.25 | 200 |
| 2026-11-25 | Pilot C: same moons, shifted 1 meter | 100 | 0.17 | 300 |
| 2026-11-25 | Pilot D: first 30 moons, two other start dates | 60 | 0.10 | 360 |
| 2026-11-26 | Full dataset: 12,000 new moons, 100 years | 12,000 | 20.77 | **12,360** |

Not counted: the short simulations inside the automatic checks, and the 20 moons that
`check_dataset.py` reran.

---

## Phase 1: setup and first simulation (2026-11-25)

**Goal:** a gravity simulation we can trust, and a first look at Earth with two moons.

### What we built

| Step | What | Commit |
|---|---|---|
| 1 | Python environment, folders, README, notes | `dce062a` |
| 2 | Real starting positions from NASA JPL Horizons, plus checks | `5b7f607`, `bd50501` |
| 3 | Simulate the real Sun, Earth and Moon and compare with NASA | `0abd341` |
| 4 | Add a second moon; detect collisions and ejections | `3d90f24` |
| 5 | Animation, charts and `notebooks/01_first_simulation.ipynb` | `003af3d` |

### Key ideas

- **N-body simulation.** Every body pulls on every other body with gravity. There is no formula
  for the motion of three or more bodies, so the computer moves them forward in small time steps.
  We use the REBOUND library.
- **State vector.** A body's position and velocity at one moment. With the masses, that is all
  the simulation needs. We took real ones from NASA for 2026-01-01.
- **Integrator.** The method that takes the time steps. We use IAS15, which picks its own step
  size: small steps during close encounters, larger ones otherwise. It is accurate to about the
  limit of computer rounding.
- **Orbital elements.** Another way to describe an orbit: size (semi-major axis), shape
  (eccentricity), tilt (inclination), two more angles that turn the orbit in space, and where the
  moon starts on it. We describe the second moon this way, because the numbers mean something.

### Results

- **Validation:** our simulated Moon stayed within **10.3 km** of NASA's Moon for a full year
  (average 5.6 km, about 0.003% of the Earth-Moon distance). Its average orbit period was off by
  0.6 seconds.
- **The Sun matters:** without it, the error grew to **55,535 km**.
- **First second moon** (0.1 lunar masses, 0.4 lunar distances, circular, flat): survived 10
  years, staying 146,072 to 162,087 km from Earth. Its yearly distance range grew from 5,847 km to
  14,726 km, about 2.5 times. Its orbit was stretching.
- **Checks:** energy stayed constant to rounding noise; reruns were identical to the last bit; a
  dropped Moon hit Earth at the time the exact formula predicts (4.384 days).

### What we learned

- Test the simulator on something known before trying something unknown.
- The Sun cannot be left out, even for "just Earth and two moons".
- **"Survived" is not "stable."** The first moon survived, but its orbit was changing. A label
  alone hides that.

### What changed along the way

- A chart was first titled "both moons kept their distance". After looking at it closely, we saw
  the second moon's band widening, so the title now says the orbit is stretching.
- The energy chart showed rounding steps as a jagged line. It now uses dots.
- The animation took too long to make, because each frame recalculated the layout. It is now
  calculated once, and the simulation uses 1-hour steps for smoother motion.

---

## Phase 2: dataset generation (2026-11-25 to 2026-11-26)

**Goal:** thousands of random second moons, each simulated and labeled with what happened.
This becomes the training data for the ML model.

### Decisions made before starting

- **Computing budget:** one overnight run (8 to 10 hours).
- **Orbits:** both forward (same direction as our Moon) and backward (tilt over 90 degrees).
- **Pilot first:** 100 moons to set the remaining choices, with decision rules written down
  *before* seeing the results, so the results could not bend the rules.

### What we built

| Step | What | Commit |
|---|---|---|
| 2.1 | Lightweight simulation mode (keeps only the ending), accuracy and time-limit settings, full package list | `11c3c96` |
| 2.2 | Random second moons (`src/sampling.py`) and outcome labels (`src/labels.py`) | `67c89c0` |
| 2.3 | Batch runner with 4 workers, safe to stop and resume (`src/generate_dataset.py`) | `dd3862e` |
| 2.4 | Pilot runs and their analysis (`src/analyze_pilot.py`) | `dd3862e`, `3f685b1` |
| 2.5 | Even-in-degrees tilt option, full dataset config, the full run, manifest | `8000c85`, `ed0f1d6` |
| 2.6 | Dataset checks (`src/check_dataset.py`) and these documents | `ed0f1d6` |

### How a random moon is made

| Setting | Range | How it is drawn |
|---|---|---|
| Mass | 0.001 to 1 lunar masses | log-uniform (each factor of 10 equally likely) |
| Distance (semi-major axis) | 0.1 to 3 lunar distances | log-uniform |
| Eccentricity | 0 to 0.8 | uniform |
| Tilt | 0 to 180 degrees | pilot: uniform in cos(tilt); full dataset: uniform in degrees |
| Other angles, starting point | 0 to 360 degrees | uniform |

- **Roche limit:** a moon closer to Earth than about 18,365 km would be torn apart by tides. Orbits
  that come closer are redrawn, and the redraws are counted.
- **Seeds:** each moon has its own random generator made from (seed, id), so moon 57 is always the
  same moon, in whatever order the moons finish.

### Labels

| Label | Meaning |
|---|---|
| `survived` | Still orbiting at the time limit (100 years). Lasted *at least* that long. |
| `hit_earth` | The second moon crashed into Earth |
| `hit_moon` | The second moon crashed into our Moon |
| `ejected` | The second moon escaped: farther than 4.5 million km and not bound to Earth |
| `moon_lost` | Our real Moon was the one ejected or crashed |
| `other`, `timeout`, `error` | Anything else; the run took too long; the run failed. None happened. |

The raw outcome is saved too, so labels can be redefined without simulating again.

### Pilot: design

The same 100 moons, simulated with one change at a time:

| Run | Change | Question |
|---|---|---|
| A | None | What outcomes, and how long does it take? |
| B | Stricter integrator (epsilon 1e-11 instead of 1e-9) | Are results limited by accuracy? |
| C | Second moon moved by 1 meter | How chaotic is this? |
| D | Two other start dates (30 moons each) | Does the date matter? |

### Pilot: results

- **Outcomes (run A, 100 years):** hit Earth 42, ejected 38, survived 18, hit the Moon 1, real Moon
  lost 1. No timeouts or errors. Median 1.2 s per moon.
- **Survival keeps falling:** 45 survived 10 years, 28 survived 30, 18 survived 100.
- **Chaos:** moving a moon by 1 meter changed **12 of 100** outcomes (9 at 10 years).
- **Accuracy:** stricter settings changed 6, fewer than chaos alone, so the default is accurate
  enough.
- **Start date:** 27 and 26 of 30 agreed, compared with 28 of 30 for the 1 meter shift. No clear
  effect, but 30 moons is a small test.
- **Time:** 100 years would take about 2.4 hours for 5,000 moons, within the budget.

### Pilot: decisions (by the rules set beforehand)

| Rule | Result | Decision |
|---|---|---|
| Accuracy | B differed on 6, C on 12 | Keep the default integrator setting |
| Start date | Not clearly different from chaos | One start date |
| Time limit | 100 years fits | 100 years |
| Timeouts over 2% | 0 timeouts | No change |
| Rare classes under 2% | hit_moon, moon_lost | Decide in Phase 4 |

### Pilot: changes made after seeing the results

These were not covered by the rules, so they were proposed and approved separately.

1. **Tilt sampling:** only 7 of 100 pilot moons had a tilt under 40 degrees, so nearly flat
   orbits were thinly covered. The full dataset spreads tilt evenly in degrees. Cost: flat orbits
   are now over-represented compared with random directions in space.
2. **Number of moons:** 100 years ran faster than feared, so the target rose from 5,000 to
   **12,000** moons.
3. **New seed:** the full dataset uses seed 20261126, not the pilot's, so the moons used to make
   decisions are not reused in the final data.
4. **Wording:** the plan called 88% agreement under a 1 meter shift a "ceiling" for any model.
   That is too strong; a model can score somewhat higher. It is now treated as a guide.

### Full dataset: results

- **12,000 moons**, finished in **5.2 hours** with 4 workers (20.8 CPU-hours). Median 1.5 s per
  moon, longest 104 s. Never restarted.

| Outcome | Moons | Share |
|---|---:|---:|
| Survived 100 years | 4,554 | 38.0% |
| Ejected | 3,841 | 32.0% |
| Hit Earth | 3,288 | 27.4% |
| Hit the Moon | 171 | 1.4% |
| Real Moon lost | 146 | 1.2% |

- **Checks passed** (`src/check_dataset.py`): no repeated or missing ids; all inputs in range;
  every input rebuilt exactly from the seed; labels match outcomes; 20 random moons simulated again
  gave identical results.
- **Manifest:** `configs/dataset_manifest.json` stores the CSV's SHA-256 fingerprint, counts,
  computing time and package versions. The CSV itself is not in Git.

### What we learned

- **Chaos is real and measurable.** About 1 in 8 outcomes flips with a 1 meter nudge. No model can
  be perfect.
- **Most random second moons don't last.** In the pilot only 18% survived 100 years.
- **The data depends on how we sample.** With tilt spread evenly in degrees, 38% survived. These
  percentages describe our sampling choices, not "the chance a random moon survives".
- **Write the rules before the results.** It kept decisions honest and quick.
- **Automatic checks catch real bugs.** A change to the tilt code silently changed every pilot
  moon; `check_sampling.py` caught it before the full run.

### What changed along the way

- Outputs every 24 hours instead of 6, to make long runs faster. Collisions are still detected
  between outputs.
- The first speed reading of the full run promised 11 hours. It took 5.2. The laptop was on battery
  at the start, and the first few dozen moons were not a fair sample.

---

## Method summary (how a paper would describe it)

> We integrate the Sun, Earth, Moon and a hypothetical second moon with REBOUND's IAS15
> integrator, starting from JPL Horizons state vectors (DE440, 2026-01-01 TDB). The setup
> reproduces the Moon's ephemeris to within 10.3 km over one year. Second-moon parameters are
> drawn log-uniformly in mass (10⁻³ to 1 lunar masses) and semi-major axis (0.1 to 3 lunar
> distances), uniformly in eccentricity (0 to 0.8), inclination (0 to 180 degrees) and the
> remaining angles, rejecting orbits with pericenter inside the Roche limit. Each system is
> integrated for up to 100 years and labeled by its first terminal event (collision or
> ejection); systems surviving to the limit are right-censored. A pilot study showed that a
> 1 m perturbation changes 12% of outcomes, larger than the effect of tightening the integrator
> tolerance (6%). The final dataset contains 12,000 systems.

## Limitations

- Newtonian gravity only: no tides, no Earth bulge, no relativity, no other planets.
- "Survived" means survived 100 years, not stable forever.
- One start date (no clear effect in a 30-moon test).
- Class shares depend on the sampling ranges and distributions chosen.
