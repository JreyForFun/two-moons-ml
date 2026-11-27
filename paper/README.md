# Paper

Draft: *The Fate of a Hypothetical Second Moon of Earth: N-body Simulations and a
Machine-Learning Surrogate.*

| File | Contents |
|---|---|
| `main.tex` | Manuscript (AASTeX 6.3.1, two-column) |
| `references.bib` | Bibliography |

Figures are read from the repository's `figures/` folder. Every number in the text is printed by
`src/paper_numbers.py` or `src/analyze_pilot.py`, and `src/check_paper.py` checks citations,
references, figure files, length limits and the headline numbers against the result files.

## Building

**Overleaf (no installation):** create a blank project, upload `main.tex`, `references.bib` and a
`figures/` folder containing the PNG files referenced in the text, then compile with pdfLaTeX.
The AASTeX class (`aastex631.cls`) is included in Overleaf's TeX Live.

**Locally (TeX Live or MiKTeX):** from this folder,

```
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

If `aastex631.cls` is missing, download it from the
[AAS journals author resources](https://journals.aas.org/aastex-package-for-manuscript-preparation/).

Text in red brackets marks the dataset DOI, inserted once the data are archived.

## Status

| Section | Status |
|---|---|
| Abstract (233 words) | Final |
| Introduction, including related work | Final |
| Methods: simulation, sampling, outcomes, pilot | Edited |
| Methods: surrogate models | Edited |
| Methods: exploration (test split, decision rules R1–R4) | Edited |
| Results: validation, pilot, dataset | Edited |
| Results: stability maps, pilot gap, long-term survival | Edited |
| Results: surrogate performance, held-out test set, speed | Edited |
| Discussion | Edited |
| Conclusions | Edited |
| Author and affiliation | Done |
| Keywords (Unified Astronomy Thesaurus) | Done |
| References verified (volume, pages, DOI) | Done |
| Data DOI | Pending |

## Before submission

- Check the target venue's current author guidelines, including length, figure limits and
  disclosure requirements.
- Archive the dataset (for example on Zenodo) and insert its DOI; then
  `src/check_paper.py --final` must pass.

## Target venues

- **Research Notes of the AAS:** at most 1,500 words including references, and one figure or
  table. Requires a condensed version of this draft.
- **arXiv (astro-ph.EP):** the full draft as a preprint. First-time submitters need an endorsement.
- **Zenodo:** preprint and dataset together, with a citable DOI.
