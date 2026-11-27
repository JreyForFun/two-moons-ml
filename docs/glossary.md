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

**Lidov-Kozai effect.** A satellite whose orbit is strongly inclined to the orbit of a distant
perturber (here the Moon and the Sun, both near the ecliptic) exchanges inclination for
eccentricity in slow cycles. Above about 39° of relative inclination, the eccentricity can grow
until the periapsis reaches the planet's surface.

**Osculating elements.** The orbital elements of the two-body orbit a body would follow if all
perturbations stopped at that instant. Under perturbations they change continuously.

## Chaos and statistics

**Chaos (sensitive dependence on initial conditions).** In a chaotic system, tiny differences in
the starting state grow over time until they change the outcome. This sets a limit on how well any
method, including a perfect simulation with imperfect inputs, can predict long-term outcomes.

**Pilot study.** A small preliminary run used to choose settings for the main experiment.

**Pre-registered rules.** Decision criteria written down before seeing the data, so that results
cannot influence the choice of criteria.

**Criterion met / not met.** A pre-registered rule is *met* when the evidence reaches its pass
criterion. *Not met* means the evidence fell short; it does not show the claim to be false. A
near miss, where the result lies just outside the criterion, often indicates a partial effect.

**Deciding with an interval.** A rule about a difference is met when the 95% interval of that
difference excludes zero: in nearly all resamples the difference has the same sign. An interval
that includes zero means the data are compatible with no difference.

**Descriptive (post-hoc) finding.** A pattern noticed after inspecting the data rather than tested
by a pre-registered rule. It may be real, but it carries less weight, because the comparison was
chosen after seeing the result; it is a hypothesis for a future test.

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

**Conditional survival.** The share of systems alive at time *t*₂ among those alive at *t*₁. The
overall survival to *t*₂ is the survival to *t*₁ multiplied by this share.

**Stability map (heat map).** A grid over two starting parameters in which each cell is colored by
the share of systems in it that survived.

**Importance weighting.** Giving each sample a weight equal to the ratio of a target distribution
to the distribution it was drawn from, so weighted statistics describe the target distribution
without new samples.

**Effective sample size.** The number of equally weighted samples that would carry the same
statistical information as a weighted sample: (Σw)² / Σw².

**Bootstrap.** Estimating the uncertainty of a statistic by recomputing it on many resamples of the
data drawn with replacement.

**Split-half agreement.** Building the same result from two disjoint halves of the data and
measuring how closely they agree; high agreement shows a pattern is not sampling noise.

**Nearest-neighbour estimate.** Predicting a quantity for a point from the values at the most
similar points in a reference set (here, the survival share of the 50 most similar training moons).

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
so its score on that part estimates performance on new cases. A *stratified* split keeps the
share of every label the same in both parts. Here the test set was fixed before any exploration,
so patterns seen while exploring cannot shape the model in ways that inflate its test score.

**Overfitting.** When a model memorizes its training data instead of learning general patterns.
It shows as a high training score with a much lower test score.

**Cross-validation.** Splitting the training data into *k* parts (folds), training on *k* − 1 and
scoring on the remaining part, in turn. *Stratified* folds keep every class's share the same in
each fold.

**Out-of-fold (OOF) prediction.** The prediction for a training moon made by the cross-validation
model that did not see it. Every moon gets exactly one, so OOF predictions can be scored and
compared like predictions on new data.

**Nested cross-validation.** Hyperparameters are chosen by an inner cross-validation inside each
outer training part, so the outer scores are never tuned on the data they measure.

**Hyperparameter.** A model setting chosen before training (for example tree depth), as opposed
to the parameters the model learns from data.

**Precision, recall and F1.** For one class: precision is the share of predictions of that class
that are correct; recall is the share of that class that is found; F1 is their harmonic mean.

**Macro-F1.** The F1 score averaged over classes with equal weight, so a rare class counts as much
as a common one.

**Balanced accuracy.** The recall averaged over classes; equal to accuracy when classes are
balanced, and robust to imbalance otherwise.

**Log loss and Brier score.** Scores for predicted probabilities. Both reward confident correct
predictions and penalize confident wrong ones; lower is better.

**Calibration and ECE.** A model is calibrated if events predicted with probability *p* occur a
fraction *p* of the time. The expected calibration error (ECE) is the average gap between predicted
probability and observed frequency, weighted over probability bins.

**ROC AUC.** For a yes/no outcome, the probability that a randomly chosen positive case receives a
higher predicted probability than a randomly chosen negative case (0.5 is chance, 1 is perfect).

**Class weights.** Weighting training examples inversely to their class frequency, so the model
does not ignore rare classes.

**Logistic regression.** A linear model of the log-odds of each class; a simple, interpretable
baseline.

**Random Forest.** An average of many decision trees, each trained on a random resample of the data
and random subsets of the features.

**Gradient boosting (XGBoost).** A sequence of small decision trees, each fitted to correct the
errors of the previous ones.

**Multilayer perceptron (MLP).** A small feed-forward neural network; it needs standardized inputs.

**Circular encoding.** Representing an angle by its sine and cosine, so 359° and 1° are close.

**Paired bootstrap.** Comparing two models by resampling the same moons for both and recomputing the
difference in a score; the spread of the differences gives its uncertainty while removing
moon-to-moon variation common to both models.

**Permutation importance.** The drop in a score when one input (or a *group* of related inputs) is
randomly shuffled. Grouping related inputs prevents them from hiding each other's importance.

**Label-permutation test.** Training on randomly shuffled labels. A leak-free pipeline then scores
at chance level; a high score would reveal leakage.

**Learning curve.** A score as a function of the number of training examples; a curve that is still
rising indicates that more data would help.

**Chaos twins.** Pairs of simulations of the same system, one displaced by 1 m. The share of pairs
with different outcomes measures how much of the outcome is decided by chaos.

**Selection optimism.** Any choice made with the same data that measures performance can make the
measured score slightly too favorable; an untouched test set removes this bias.

**Held-out evaluation.** Scoring a model once on data that played no part in any choice: not in
training, tuning, feature selection or model selection. It gives the unbiased estimate of
performance on new cases.

**Provenance.** The record of exactly which code, data and settings produced a result, here the
Git commit, file checksums and time stored with the test results.

**Amendment before unblinding.** A change to the evaluation criteria made before the held-out data
are opened, documented with its reason. Changes made after seeing the data are not legitimate.

**Latency and throughput.** Latency is the time for a single prediction; throughput is the number
of predictions per unit time when many are made together. Batch prediction is usually much faster
per case.

**Break-even point.** The number of predictions after which a surrogate model has saved more
computing time than its training data cost to generate.

**Coverage-accuracy curve.** Accuracy on the most confident predictions, as a function of the
share of cases kept (the coverage). It shows how much accuracy improves if the model may abstain
on its least confident cases.

**Model card.** A short standard document describing a model's intended use, training data,
performance, limitations and known failure modes.

**Seed variability.** The spread of results caused only by the random seed of a stochastic model,
such as a Random Forest. Fixing the primary seed in advance and reporting the spread over other
seeds separates real effects from luck.
