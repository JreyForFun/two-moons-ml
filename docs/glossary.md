# Glossary

Short definitions of the physics, statistics and machine learning terms used in this project.
Other documents link here instead of repeating them.

## Orbital mechanics

**N-body simulation.** A numerical calculation of how several bodies move under their mutual
gravity. Two bodies have an exact solution (Kepler orbits); three or more generally do not, so the
motion is advanced in small time steps. This project uses [REBOUND](https://rebound.readthedocs.io/).

**State vector.** A body's position and velocity at a given instant. Together with the masses,
state vectors fully determine the future motion under Newtonian gravity.

**Ephemeris.** A table of a body's position over time. NASA JPL Horizons provides high-precision
ephemerides based on the DE440 planetary model.

**Integrator.** The algorithm that advances the simulation in time. IAS15, used here, adapts its
step size automatically and keeps errors near machine precision (about 10⁻¹⁶ relative), which
matters during close encounters.

**Orbital elements.** Six numbers that describe an orbit in a more intuitive way than a state vector:

| Element | Meaning |
|---|---|
| Semi-major axis *a* | Size of the orbit: the average of the closest and farthest distance |
| Eccentricity *e* | Shape: 0 is a circle; values toward 1 are increasingly elongated |
| Inclination *i* | Tilt of the orbit relative to a reference plane (here the ecliptic) |
| Longitude of the ascending node Ω | Direction in which the orbit crosses the reference plane upward |
| Argument of periapsis ω | Orientation of the closest point within the orbital plane |
| True anomaly ν | Position of the body along the orbit at the starting time |

**Ecliptic.** The plane of Earth's orbit around the Sun. All inclinations in this project are
measured from it. The Moon's orbit is inclined about 5° to it.

**Prograde / retrograde.** A prograde orbit runs in the same direction as the Moon's
(inclination below 90°); a retrograde orbit runs the opposite way (above 90°).

**Periapsis / apoapsis.** The closest and farthest points of an orbit. Periapsis distance is
*a*(1 − *e*).

**Kepler's third law.** The orbital period grows with the semi-major axis to the power 3/2. A
moon at 0.4 lunar distances therefore orbits about four times faster than the Moon.

**Hill radius.** The distance within which a planet's gravity dominates over the Sun's tides.
For Earth it is about 1.5 million km. Satellites far beyond roughly half the Hill radius are
generally not stable over long times.

**Roche limit.** The distance inside which a planet's tides would tear apart a fluid satellite
held together by its own gravity. For a body with the Moon's density orbiting Earth it is about
18,365 km (2.44 × lunar radius × (Earth mass / Moon mass)^(1/3)).

**Ejection.** Here: the second moon is more than 4.5 million km from Earth (about three Hill
radii) and has positive orbital energy relative to Earth, meaning it is no longer bound.

**Energy conservation.** In a system with gravity alone, total energy is constant. Any change in
the computed total energy measures numerical error.

## Chaos and statistics

**Chaos (sensitive dependence on initial conditions).** In a chaotic system, tiny differences in
the starting state grow over time until they change the outcome. This sets a limit on how well any
method, including a perfect simulation with imperfect inputs, can predict long-term outcomes.

**Pilot study.** A small preliminary run used to choose settings for the main experiment.

**Pre-registered rules.** Decision criteria written down before seeing the data, so that results
cannot influence the choice of criteria.

**Log-uniform distribution.** Values whose logarithm is uniformly distributed, so that each
factor of 10 is equally represented. Used for quantities spanning several orders of magnitude.

**Isotropic sampling.** Drawing orientations so every direction in space is equally likely. For
inclination this means uniform in cos *i*, which makes nearly flat orbits (*i* near 0° or 180°) rare.

**Random seed.** The starting number of a pseudo-random generator. The same seed reproduces the
same sequence of random numbers, which makes the dataset reproducible.

**Wilson score interval.** A confidence interval for a proportion that behaves well for small
samples and proportions near 0 or 1.

**Right-censoring.** When an event (here: collision or ejection) has not happened by the end of
observation, only a lower bound on its time is known. Moons labeled `survived` are right-censored
at 100 years.

**Kaplan-Meier curve.** The standard estimate of the fraction of a population surviving past each
time, accounting for censored observations.

**SHA-256.** A cryptographic fingerprint of a file. Any change to the file, even one character,
produces a completely different value.

## Machine learning

**Surrogate model.** A fast model trained to imitate a slow calculation, here the N-body simulation.

**Features and labels.** Features are the inputs a model sees (the second moon's starting
parameters); labels are the outputs it learns to predict (the outcome).

**Class imbalance.** When some labels are much rarer than others. A model can reach high overall
accuracy while never predicting the rare classes, so per-class metrics are needed.

**Majority-class baseline.** The accuracy obtained by always predicting the most common label.
Any useful model must clearly exceed it.

**Data leakage.** When a model is given information that would not be available at prediction
time, such as the survival time, which reveals the outcome. It produces unrealistically good scores.

**Train / test split.** Holding back part of the data that the model never sees during training,
so its score on that part estimates performance on new cases.

**Overfitting.** When a model memorizes its training data instead of learning general patterns.
It shows as a high training score with a much lower test score.
