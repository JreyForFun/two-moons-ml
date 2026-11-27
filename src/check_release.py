"""Release checklist: frozen results, documentation integrity and consistent numbers.

Run:  venv/Scripts/python src/check_release.py
"""

import ast
import json
import re
import subprocess
import sys

from horizons import ROOT

FROZEN = {  # file: commit in which its final content was committed
    "results/phase5_test.json": "d4f404c",
    "results/phase5_test_predictions.csv": "d4f404c",
    "results/phase5_speed.json": "69cefc4",
    "results/phase5_analysis.json": "69cefc4",
    "configs/selected_model.json": "975d7fb",
    "configs/phase5_protocol.json": "5a93769",
    "configs/split.json": "ccb9bbc",
    "configs/dataset_manifest.json": "ed0f1d6",
}
DOCS = ["README.md", "notes.md", "docs/report.md", "docs/questions.md", "docs/figures.md",
        "docs/glossary.md", "docs/model_card.md", "paper/README.md"]
STALE = [r"(?i)phase 5 next", r"(?i)results so far", r"(?i)checked in phase 5",
         r"(?i)until the phase 5", r"(?i)await the phase 5", r"(?i)\bso far:"]
BANNED_VARIANTS = ["81,000", "80,521", "7,100 predictions", "7,055 predictions"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def tracked(pattern):
    return [ROOT / p for p in git("ls-files", pattern).stdout.split()]


def check_frozen():
    changed = [f for f, commit in FROZEN.items()
               if git("diff", "--quiet", commit, "--", f).returncode != 0]
    return not changed, f"{len(FROZEN)} frozen files unchanged" if not changed else f"changed: {changed}"


def anchors(path):
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            out.add(re.sub(r"[^\w\- ]", "", m.group(1).strip().lower()).replace(" ", "-"))
    return out


def check_links():
    bad = []
    for path in tracked("*.md"):
        for target in re.findall(r"\]\(([^)\s]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not dest.exists() or (anchor and dest.suffix == ".md" and anchor not in anchors(dest)):
                bad.append(f"{path.relative_to(ROOT)} -> {target}")
    return not bad, "all Markdown links and anchors resolve" if not bad else "; ".join(bad[:5])


def check_imports():
    unused = []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update({(a.asname or a.name).split(".")[0]: 1 for a in node.names})
            elif isinstance(node, ast.ImportFrom):
                names.update({a.asname or a.name: 1 for a in node.names})
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        used |= {n.value.id for n in ast.walk(tree)
                 if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
        unused += [f"{path.name}:{n}" for n in names if n not in used]
    return not unused, "no unused imports" if not unused else ", ".join(unused)


def check_readme_coverage():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [p.name for p in (ROOT / "src").glob("*.py")
               if f"src\\{p.name}" not in readme and f"src/{p.name}" not in readme]
    return not missing, "every script and module is in the README" if not missing else str(missing)


def check_figures_documented():
    guide = (ROOT / "docs" / "figures.md").read_text(encoding="utf-8")
    missing = [p.name for p in (ROOT / "figures").iterdir()
               if p.is_file() and p.name not in guide]
    return not missing, "every figure in figures/ is in the figure guide" if not missing else str(missing)


def check_wording():
    problems = []
    for name in DOCS:
        text = (ROOT / name).read_text(encoding="utf-8")
        problems += [f"{name}: {p}" for p in STALE if re.search(p, text)]
        problems += [f"{name}: {v}" for v in BANNED_VARIANTS if v in text]
    pattern = re.compile(r"\bAI\b|claude|assistant", re.I)
    allowed = {"paper/main.tex", "paper/rnaas.tex"}
    for path in tracked("*"):
        rel = path.relative_to(ROOT).as_posix()
        if rel in allowed or rel == "src/check_release.py" or rel.startswith("results/") or rel.endswith((".png", ".gif", ".mp4", ".pdf",
                                                                        ".ipynb", ".bib")) \
                or rel == "requirements-lock.txt":
            continue
        if path.is_file() and pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            problems.append(f"{rel}: assistant or AI wording")
    for rel in allowed:
        path = ROOT / rel
        if path.exists():
            hits = [line for line in path.read_text(encoding="utf-8").splitlines() if pattern.search(line)]
            if any("AI assistant" not in line for line in hits) or len(hits) > 2:
                problems.append(f"{rel}: AI wording outside the disclosure sentence")
    return not problems, "no stale phrases or wording issues" if not problems else "; ".join(problems[:6])


def check_numbers():
    """Headline numbers from the result files appear, identically, where they are quoted."""
    test = json.loads((ROOT / "results" / "phase5_test.json").read_text(encoding="utf-8"))
    analysis = json.loads((ROOT / "results" / "phase5_analysis.json").read_text(encoding="utf-8"))
    speed = json.loads((ROOT / "results" / "phase5_speed.json").read_text(encoding="utf-8"))
    m = test["metrics"]["selected"]
    expected = {
        "test accuracy": f"{m['accuracy'] * 100:.1f}%",
        "test macro-F1": f"{m['macro_f1']:.3f}",
        "test ECE": f"{test['criteria']['C3']['ece']:.3f}",
        "test twin agreement": f"{analysis['T5']['agreement'] * 100:.1f}%",
        "single-prediction speedup": f"{speed['speedup']['same_machine_median']:.0f} times",
        "batch speedup": f"about {round(speed['speedup']['batch_vs_mean'], -4):,.0f}",
        "break-even": f"about {round(speed['break_even_predictions'], -3):,.0f} predictions",
    }
    where = {"README.md": ["test accuracy", "single-prediction speedup", "batch speedup", "break-even"],
             "docs/report.md": list(expected), "docs/model_card.md": ["test macro-F1", "test ECE"],
             "paper/main.tex": ["test macro-F1", "test twin agreement"]}
    missing = []
    for name, keys in where.items():
        text = (ROOT / name).read_text(encoding="utf-8").replace("\\%", "%")
        missing += [f"{name}: {k} ({expected[k]})" for k in keys if expected[k] not in text]
    return not missing, (f"{len(expected)} headline numbers consistent across 4 documents"
                         if not missing else "; ".join(missing))


def main():
    passed = True
    for label, check in (("Frozen results", check_frozen), ("Links", check_links),
                         ("Imports", check_imports), ("README coverage", check_readme_coverage),
                         ("Figures documented", check_figures_documented),
                         ("Wording", check_wording), ("Headline numbers", check_numbers)):
        ok, detail = check()
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
