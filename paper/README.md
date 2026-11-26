# Paper

Draft: *The Fate of a Hypothetical Second Moon of Earth: N-body Simulations and a
Machine-Learning Surrogate.*

| File | Contents |
|---|---|
| `main.tex` | Manuscript (AASTeX 6.3.1, two-column) |
| `references.bib` | Bibliography |

Figures are read from the repository's `figures/` folder. Every number in the text is printed by
`src/paper_numbers.py` or `src/analyze_pilot.py`.

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

Text in red brackets marks content that depends on later phases.

## Status

| Section | Status |
|---|---|
| Abstract | Drafted (Phases 1–4); test-set scores and speedup pending |
| Introduction | Drafted |
| Methods: simulation, sampling, outcomes, pilot | Drafted |
| Methods: surrogate models | Drafted |
| Methods: exploration (test split, decision rules R1–R4) | Drafted |
| Results: validation, pilot, dataset | Drafted |
| Results: stability maps, pilot gap, long-term survival | Drafted |
| Results: surrogate performance | Drafted (cross-validated); test-set scores pending (Phase 5) |
| Discussion | Drafted (Phases 1–4) |
| Conclusions | Pending |
| Author and affiliation | Done |
| Data DOI | Pending |

## Before submission

- Confirm the volume and pages of `Domingos2006` on ADS.
- Add Unified Astronomy Thesaurus identifiers to the keywords.
- Check the target venue's current author guidelines, including length, figure limits and
  disclosure requirements.
- Archive the dataset (for example on Zenodo) and insert its DOI.

## Target venues

- **Research Notes of the AAS:** at most 1,500 words including references, and one figure or
  table. Requires a condensed version of this draft.
- **arXiv (astro-ph.EP):** the full draft as a preprint. First-time submitters need an endorsement.
- **Zenodo:** preprint and dataset together, with a citable DOI.
