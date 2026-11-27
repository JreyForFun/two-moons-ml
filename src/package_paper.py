"""Compilation of a manuscript with Tectonic and its upload bundle.

Compiles paper/<name>.tex, fails on undefined references or citations and on lines overfull by
more than 1 pt, copies the PDF to paper/<name>.pdf, and writes dist/<name>_upload.zip with the
source, bibliography, generated .bbl (arXiv does not run BibTeX) and the figures used. Tectonic
is taken from tools/tectonic/ or the PATH.

Usage:
    python src/package_paper.py [rnaas]
"""

import re
import shutil
import subprocess
import sys
import zipfile

from horizons import ROOT

PAPER = ROOT / "paper"
BUILD = ROOT / "tools" / "build"
DIST = ROOT / "dist"
FIGURE_DIRS = (PAPER / "figures", ROOT / "figures")


def tectonic():
    local = ROOT / "tools" / "tectonic" / "tectonic.exe"
    found = local if local.exists() else shutil.which("tectonic")
    if not found:
        raise SystemExit("Tectonic not found: see 'Building' in paper/README.md")
    return str(found)


def compile_tex(name):
    BUILD.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([tectonic(), "--keep-logs", "--keep-intermediates", "--outdir",
                             str(BUILD), f"{name}.tex"], cwd=PAPER, capture_output=True,
                            text=True)
    log = (BUILD / f"{name}.log").read_text(encoding="utf-8", errors="ignore")
    problems = []
    if result.returncode:
        problems.append(f"Tectonic failed: {result.stderr[-500:]}")
    problems += sorted(set(re.findall(r"(?:Reference|Citation) `[^']+' (?:on page \d+ )?undefined",
                                      log)))
    for width in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log):
        if float(width) > 1.0:
            problems.append(f"overfull line, {width} pt too wide")
    return problems


def bundle(name):
    tex = (PAPER / f"{name}.tex").read_text(encoding="utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    DIST.mkdir(exist_ok=True)
    target = DIST / f"{name}_upload.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(PAPER / f"{name}.tex", f"{name}.tex")
        z.write(PAPER / "references.bib", "references.bib")
        z.write(BUILD / f"{name}.bbl", f"{name}.bbl")
        for fig in figures:
            source = next(d / fig for d in FIGURE_DIRS if (d / fig).exists())
            z.write(source, f"figures/{fig}")
    return target, len(figures)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "main"
    problems = compile_tex(name)
    for problem in problems:
        print(f"FAIL  {problem}")
    if problems:
        return 1
    shutil.copyfile(BUILD / f"{name}.pdf", PAPER / f"{name}.pdf")
    target, figures = bundle(name)
    print(f"Saved paper/{name}.pdf and dist/{target.name} ({figures} figures)")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
