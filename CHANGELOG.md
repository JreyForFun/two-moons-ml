# Changelog

## v1.0.0 (2026-11-28)

Archived on Zenodo: doi:10.5281/zenodo.24612629 (this version), doi:10.5281/zenodo.24612628 (all versions).

First release, accompanying the paper *The Fate of a Hypothetical Second Moon of Earth: N-body
Simulations and a Machine-Learning Surrogate*.

**Simulation**
- Sun, Earth and Moon from JPL Horizons (DE440, 2026-01-01 TDB) integrated with REBOUND (IAS15);
  the simulated Moon stays within 10.3 km of the ephemeris over one year.
- Second moon with collision and ejection detection; a parallel, resumable batch runner with
  per-moon random generators and SHA-256 manifests.

**Data**
- Pilot study (100 systems under five controlled variations), main dataset of 12,000 systems,
  500 survivors extended to 1,000 years, and 2,100 systems re-simulated with a 1 m displacement;
  15,065 simulations in total. Archived on Zenodo (doi:10.5281/zenodo.24607389) with a data description
  (`docs/data_archive.md`).

**Analysis**
- Stability maps and four pre-registered decision rules (R1–R4) on the 9,600 training systems,
  with a frozen test set of 2,400 systems.
- Surrogate models compared by nested cross-validation; the selected Random Forest was evaluated
  once on the test set under criteria fixed in advance: accuracy 85.1%, macro-F1 0.711, all
  criteria met (`results/`).
- Speed benchmark: 24 times faster than a median simulation per prediction, about 80,000 times
  faster in batches.
- `src/predict.py`, a command-line and importable prediction tool, with a model card.

**Paper and documentation**
- Paper (AASTeX 6.3.1) with compiled PDF and a Research Notes of the AAS version; every headline
  number checked against the result files by `src/check_paper.py`.
- Technical report, design decisions, figure guide, glossary, plain-language summary and four
  executed notebooks.
- Release checks: frozen results, links, imports, wording, cross-document numbers, and a
  fresh-clone installation test.
