# Paper

*The Fate of a Hypothetical Second Moon of Earth: N-body Simulations and a Machine-Learning
Surrogate.* Final text.

| File | Contents |
|---|---|
| `main.tex` | Manuscript (AASTeX 6.3.1, two-column) |
| `references.bib` | Bibliography |
| `main.pdf` | Compiled manuscript |
| `rnaas.tex`, `rnaas.pdf` | Condensed version for Research Notes of the AAS |
| `figures/` | Print-size figures (PDF), drawn by `src/plot_paper.py` |

Figures are read from `paper/figures/`. Every number in the text is printed by
`src/paper_numbers.py` or `src/analyze_pilot.py`, and `src/check_paper.py` checks citations,
references, figure files, length limits and the headline numbers against the result files.

## Building

**Tectonic (used for `main.pdf`):** `venv/Scripts/python src/package_paper.py` compiles the
paper with [Tectonic](https://tectonic-typesetting.github.io/) 0.17.0 from `tools/tectonic/`
(or `tectonic` on the PATH), fails on undefined references and overfull lines, copies the PDF to
`paper/main.pdf` and writes `dist/main_upload.zip` (source, bibliography, `.bbl` and figures)
for Overleaf, arXiv or a journal.

**Overleaf (no installation):** create a blank project, upload the contents of `dist/main_upload.zip`
(or `main.tex`, `references.bib` and the `figures/` folder), then compile with pdfLaTeX.
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

The dataset is cited as `Quizon2026data` (Zenodo).

## Status

| Section | Status |
|---|---|
| Abstract (240 words) | Final |
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
| Research Notes version (1,245 words, abstract 139 words, one figure) | Done |
| Data DOI (10.5281/zenodo.24607389) | Done |

## Before submission

- Check the target venue's current author guidelines, including length, figure limits and
  disclosure requirements.
- Run `src/check_paper.py --final` (no placeholders allowed) and rebuild with
  `src/package_paper.py` after any change.

## Target venues

- **Research Notes of the AAS:** `rnaas.tex`. The journal's limits (1,500 words including title,
  headers, captions and references, with 150 words reserved for the abstract; one figure or
  table, which must fit on one page) are checked by `src/check_paper.py`; the editorial office's
  word count is final. Single-author notes are written in the first person singular. AAS
  prefers AASTeX 7; the note uses AASTeX 6.3.1 with its `RNAAS` option, which is still accepted
  and is the version available to the local build. Build with
  `venv/Scripts/python src/package_paper.py rnaas`.
- **arXiv (astro-ph.EP):** the full draft as a preprint. First-time submitters need an endorsement.
- **Zenodo:** preprint and dataset together, with a citable DOI.
