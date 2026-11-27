# Model card: second-moon outcome predictor

A Random Forest that predicts what happens to a hypothetical second moon of Earth within 100 years,
from its starting orbit alone, without running an N-body simulation. Terms are defined in the
[glossary](glossary.md); the full record is in the [technical report](report.md).

## Model

| | |
|---|---|
| Type | Random Forest classifier (scikit-learn 1.9.1), 500 trees |
| Settings | `max_depth` 20, `min_samples_leaf` 5, `max_features` 0.5, `class_weight` `balanced_subsample`, seed 20261201 |
| Selection | Nested cross-validation among logistic regression, Random Forest, XGBoost and a multilayer perceptron, with pre-registered rules (Phase 4) |
| Version | Git tag `phase5-evaluated-model` (commit `5a93769`); settings in `configs/selected_model.json` |
| Use | `src/predict.py` (command line or Python function) |

## Intended use

Exploring which hypothetical second moons of the present-day Earth–Moon–Sun system survive,
collide or escape, and roughly when, much faster than direct integration. Suitable for scanning
parameter space, teaching and generating hypotheses. **Not** a substitute for simulation when an
individual outcome matters: near the Moon's orbit, outcomes are partly decided by chaos.

## Inputs and valid ranges

| Input | Range in training data |
|---|---|
| Mass | 0.001 to 1 lunar masses |
| Semi-major axis | 0.1 to 3 lunar distances (38,440 to 1,153,200 km) |
| Eccentricity | 0 to 0.8 |
| Inclination to the ecliptic | 0° to 180° (above 90° retrograde) |
| Node, argument of periapsis, starting angle | 0° to 360° |

- Orbits with periapsis inside the Roche limit (18,365 km) were excluded.
- All systems start from the real Sun, Earth and Moon on 2026-01-01 TDB (JPL Horizons, DE440).
- `src/predict.py` warns when an input lies outside these ranges.

## Outputs

- Probabilities of four outcomes within 100 years: `survived`, `ejected`, `hit_earth`, and
  `moon_interaction` (the second moon collides with the Moon, or the Moon is lost).
- From a second model with the same settings, probabilities of four lifetime classes: lost within
  1 year, 1–10 years, 10–100 years, or surviving 100 years.

## Training data

9,600 simulated systems (REBOUND, IAS15), with parameters drawn log-uniformly in mass and
semi-major axis and uniformly in the other elements, inclination uniform in degrees. A further
2,400 systems were held out and used once for the evaluation below.

## Performance

| Metric | Cross-validated (training) | Held-out test (2,400 systems) |
|---|---:|---:|
| Accuracy | 85.0% | 85.1% (83.7–86.5%) |
| Macro-F1 | 0.723 | 0.711 (0.683–0.738) |
| Balanced accuracy | 0.719 | 0.712 |
| Survival ROC AUC | 0.985 | 0.988 |
| Survival accuracy | 93.8% | 94.1% |
| ECE of P(survived) | 0.019 | 0.019 |
| Lifetime class accuracy | 76.7% | 76.9% |

- **Per-class recall on test:** survived 92%, ejected 87%, hit Earth 79%, `moon_interaction` 27%.
- **Baselines on test:** a two-variable physics rule reaches 78.9% accuracy, and always predicting
  `survived` reaches 38.0%.
- **Pre-registered criteria:** all four passed on the test set (see the technical report, Phase 5).
- **Confidence:** the 50% most confident test predictions are 98.2% correct.

## Speed

Measured single-threaded on the development laptop:
- **One prediction:** 111 ms.
- **In batches:** 133 µs per system.
- **Simulation:** median 2.7 s, mean 10.7 s per system. Survivors take about 20 s, because they run
  the full 100 years.

The model is about 24 times faster than the median simulation for single predictions, and about
80,000 times faster than the mean simulation in batches. It repays the 20.8 CPU-hours of training
simulations after about 7,000 predictions.

## Limits of predictability

A 1 m change in the starting position changes the outcome of 7.7% (training) to 8.7% (test) of
systems. Chaos peaks near the Moon's orbit. On systems whose outcome is reproducible under such a
change, the model is about 89% accurate; on the others it is wrong about half the time. No model of
the starting parameters can predict every outcome.

## Known failure modes

- **Near the Moon's orbit** (0.55–1.7 lunar distances), test error rates are 26–45% in most
  inclination bands, mostly confusions between ejection and collision with Earth.
- **Collisions with the Moon** are rarely predicted (recall about 15% in cross-validation); losses
  of the Moon are found about half the time.
- **Rare-class probabilities:** balanced class weights shift probabilities toward the rare class.
  Calibration was verified for every class on the test set (one-vs-rest ECE at most 0.03), but
  rare-class probabilities rest on few examples.
- **Under isotropic orientations** (random directions, fewer near-planar orbits), test macro-F1 is
  0.687 and accuracy 84.0%.

## Limitations

- Newtonian point-mass gravity only: no tides, Earth oblateness, relativity or other planets.
- `survived` means surviving 100 years; about a fifth of survivors are lost by 1,000 years.
- A single start date; results may differ for other configurations of the Sun and Moon.
- Outside the training ranges, predictions are extrapolations and should not be trusted.

## Provenance

- **Code and data:** <https://github.com/JreyForFun/two-moons-ml> (MIT license).
- **Test evaluation:** run once from tagged commit `5a93769`.
- **Results and predictions:** `results/phase5_test.json` and `results/phase5_test_predictions.csv`.
- **Author:** John Rey Ishiguro Quizon, STI College Legazpi.
