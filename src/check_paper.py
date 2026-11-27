"""Checks of the manuscripts: structure, venue limits and headline numbers.

Verifies citations against the bibliography (every entry cited), labels against references,
figure and table numbering against first citation, figure files, balanced braces and
environments, abstract length and placeholders, and a curated list of headline numbers
recomputed from the committed results and manifests. For the Research Notes version it also
checks the journal limits (1,500 words including references, one figure or table).

Usage:
    python src/check_paper.py [--final]    (--final also rejects any remaining placeholder)
"""

import json
import re
import sys

from analyze_pilot import wilson
from horizons import ROOT

PAPER = ROOT / "paper"
BIB = PAPER / "references.bib"
FIGURE_DIRS = (ROOT / "figures", PAPER / "figures")
LIMITS = {"main.tex": {"abstract": 250},
          "rnaas.tex": {"abstract": 150, "total_words": 1500, "floats": 1}}
ALLOWED_PLACEHOLDERS = {"Zenodo DOI"}


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def words(tex):
    """Approximate word count of LaTeX text: math counts as one word, commands are dropped."""
    text = re.sub(r"\$[^$]*\$", " X ", tex)
    text = re.sub(r"\\(cite[pt]?|ref|label|url)\*?(\[[^\]]*\])*\{[^}]*\}", " X ", text)
    text = text.replace("~", " ").replace("\\%", "%")
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    text = re.sub(r"[{}\[\]]", " ", text)
    return sum(1 for w in text.split() if re.search(r"[A-Za-z0-9]", w))


def section(tex, begin, end):
    match = re.search(re.escape(begin) + r"(.*?)" + re.escape(end), tex, re.S)
    return match.group(1) if match else ""


def bib_entries():
    text = BIB.read_text(encoding="utf-8")
    entries = {}
    for match in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", text, re.S):
        entries[match.group(1).strip()] = match.group(2)
    return entries


def cited_keys(tex):
    keys = set()
    for group in re.findall(r"\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex):
        keys |= {k.strip() for k in group.split(",") if k.strip()}
    return keys


def check_structure(name, tex, entries):
    problems = []
    cited = cited_keys(tex)
    problems += [f"unknown citation {k}" for k in sorted(cited - set(entries))]
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    refs = set(re.findall(r"\\ref\{([^}]+)\}", tex))
    problems += [f"undefined reference {r}" for r in sorted(refs - labels)]
    problems += [f"figure or table never referenced: {l}" for l in sorted(labels - refs)
                 if l.startswith(("fig:", "tab:"))]
    for kind in ("fig:", "tab:"):
        floats = [m.group(1) for m in re.finditer(
            r"\\begin\{(?:figure|table)\*?\}.*?\\label\{([^}]+)\}", tex, re.S)
            if m.group(1).startswith(kind)]
        text = re.sub(r"\\begin\{(figure|table)\*?\}.*?\\end\{(figure|table)\*?\}", "", tex,
                      flags=re.S)
        order = list(dict.fromkeys(r for r in re.findall(r"\\ref\{([^}]+)\}", text)
                                   if r.startswith(kind)))
        if order != [f for f in floats if f in order]:
            problems.append(f"{kind[:-1]} numbering differs from first-citation order: "
                            f"placed {floats}, first cited {order}")
    for fig in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        if not any((d / fig).exists() for d in FIGURE_DIRS):
            problems.append(f"missing figure {fig}")
    body = tex.replace("\\{", "").replace("\\}", "")
    if body.count("{") != body.count("}"):
        problems.append(f"unbalanced braces ({body.count('{')} open, {body.count('}')} close)")
    begins = re.findall(r"\\begin\{([^}]+)\}", tex)
    ends = re.findall(r"\\end\{([^}]+)\}", tex)
    for env in sorted(set(begins) | set(ends)):
        if begins.count(env) != ends.count(env):
            problems.append(f"unbalanced environment {env}")
    return problems, cited


def check_limits(name, tex, cited, entries, final):
    problems, notes = [], []
    limits = LIMITS[name]
    abstract = words(section(tex, "\\begin{abstract}", "\\end{abstract}"))
    notes.append(f"abstract {abstract} words (limit {limits['abstract']})")
    if abstract > limits["abstract"]:
        problems.append(f"abstract has {abstract} words, limit {limits['abstract']}")
    for placeholder in re.findall(r"\\pending\{([^}]*)\}", tex):
        if final or placeholder not in ALLOWED_PLACEHOLDERS:
            problems.append(f"placeholder left: {placeholder}")
    if "total_words" in limits:
        body = section(tex, "\\begin{document}", "\\end{document}")
        body = re.sub(r"\\(title|author|affiliation)\{[^}]*\}", " ", body)
        reference_words = sum(words(re.sub(r"\b(doi|volume|pages|number|year)\s*=.*", "",
                                           entries[k])) for k in cited if k in entries)
        total = words(body) + reference_words
        notes.append(f"{total} words with references (limit {limits['total_words']})")
        if total > limits["total_words"]:
            problems.append(f"{total} words including references, limit {limits['total_words']}")
        floats = len(re.findall(r"\\begin\{(figure|table)\*?\}", tex))
        if floats > limits["floats"]:
            problems.append(f"{floats} figures or tables, limit {limits['floats']}")
    return problems, notes


def expected_numbers():
    """Headline numbers as they must be printed, recomputed from committed files."""
    test, speed = load("results/phase5_test.json"), load("results/phase5_speed.json")
    analysis, manifest = load("results/phase5_analysis.json"), load("configs/dataset_manifest.json")
    survivors = load("configs/survivors_1000yr_manifest.json")
    m, phys = test["metrics"]["selected"], test["metrics"]["physics_rule"]
    c = test["criteria"]
    t5 = analysis["T5"]
    pct = lambda x: f"{x * 100:.1f}%"
    n = manifest["rows"]
    expected = {
        "test accuracy": pct(m["accuracy"]),
        "test macro-F1": f"macro-F1 of {m['macro_f1']:.3f}",
        "abstract macro-F1": f"macro-F1 {m['macro_f1']:.2f}",
        "physics rule accuracy": pct(phys["accuracy"]),
        "physics rule macro-F1": f"{phys['macro_f1']:.3f}",
        "majority accuracy": pct(test["metrics"]["majority"]["accuracy"]),
        "C1 interval": f"{c['C1']['interval'][0]:.3f}--{c['C1']['interval'][1]:.3f}",
        "C1b difference": f"${c['C1b']['difference']:.3f}$",
        "C2 gain": f"{c['C2']['gain']:.3f}",
        "test ECE": f"{c['C3']['ece']:.3f}",
        "survival ROC AUC": f"{m['survived_auc']:.3f}",
        "rare-class recall": f"{round(c['C4']['recall'] * c['C4']['moons'])} of {c['C4']['moons']}",
        "seed range": "{:.3f} and {:.3f}".format(*test["seed_luck"]["spread"]),
        "lifetime accuracy": pct(test["lifetime"]["accuracy"]),
        "test twin agreement": pct(t5["agreement"]),
        "error on chaotic test systems": pct(t5["error_chaotic"]),
        "error on other test systems": pct(t5["error_stable"]),
        "most confident half": pct(next(r["accuracy"] for r in analysis["coverage_accuracy"]
                                        if abs(r["coverage"] - 0.5) < 1e-9)),
        "cross-validated macro-F1": f"{analysis['cv_vs_test']['macro_f1']['cv']:.3f}",
        "single-prediction speedup": f"{speed['speedup']['same_machine_median']:.0f} times",
        "batch speedup": f"about {round(speed['speedup']['batch_vs_mean'], -4):,.0f} times",
        "batch time per system": f"{speed['model']['batch_per_moon_s'] * 1e6:.0f}~$\\mu$s",
        "break-even": f"about {round(speed['break_even_predictions'], -3):,.0f} predictions",
        "dataset CPU-hours": f"{manifest['computing']['cpu_hours']:.1f}",
        "survivors kept to 1,000 years": f"{survivors['labels']['survived']} survived",
    }
    for label, count in manifest["labels"].items():
        if count:
            lo, hi = wilson(count, n)
            expected[f"{label} share"] = f"{count:,} & {pct(count / n)} ({lo * 100:.1f}--{hi * 100:.1f})"
    lost = survivors["rows"] - survivors["labels"]["survived"]
    lo, hi = wilson(lost, survivors["rows"])
    expected["lost 100 to 1,000 years"] = f"{pct(lost / survivors['rows'])} (95%"
    expected["lost 100 to 1,000 years interval"] = f"{lo * 100:.1f}--{hi * 100:.1f}%"
    return expected


RNAAS_NUMBERS = ("test accuracy", "test macro-F1", "physics rule accuracy", "physics rule macro-F1",
                 "C1 interval", "survival ROC AUC", "error on chaotic test systems",
                 "error on other test systems", "most confident half", "single-prediction speedup",
                 "batch speedup", "batch time per system")


def check_numbers(name, tex):
    text = re.sub(r"\s+", " ", tex.replace("\\%", "%"))
    expected = expected_numbers()
    if name == "rnaas.tex":
        expected = {k: v for k, v in expected.items() if k in RNAAS_NUMBERS}
        expected["single-prediction speedup"] = expected["single-prediction speedup"].replace(
            " times", " times and")
    missing = [f"{k} ({v})" for k, v in expected.items() if v not in text]
    return missing, len(expected)


def main():
    final = "--final" in sys.argv
    entries = bib_entries()
    passed = True
    all_cited = set()
    for name in LIMITS:
        path = PAPER / name
        if not path.exists():
            print(f"SKIP  {name}: not written yet")
            continue
        tex = strip_comments(path.read_text(encoding="utf-8"))
        problems, cited = check_structure(name, tex, entries)
        all_cited |= cited
        ok = not problems
        print(f"{'PASS' if ok else 'FAIL'}  {name} structure: "
              + (f"{len(cited)} citations, labels, figures and environments consistent" if ok
                 else "; ".join(problems)))
        passed &= ok
        problems, notes = check_limits(name, tex, cited, entries, final)
        ok = not problems
        print(f"{'PASS' if ok else 'FAIL'}  {name} limits: " + ("; ".join(problems) if problems
                                                              else ", ".join(notes)))
        passed &= ok
        missing, total = check_numbers(name, tex)
        ok = not missing
        print(f"{'PASS' if ok else 'FAIL'}  {name} headline numbers: "
              + (f"{total} numbers match the result files" if ok else "; ".join(missing)))
        passed &= ok
    unused = sorted(set(entries) - all_cited)
    ok = not unused
    print(f"{'PASS' if ok else 'FAIL'}  Bibliography: "
          + (f"all {len(entries)} entries cited" if ok else "uncited: " + ", ".join(unused)))
    passed &= ok
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
