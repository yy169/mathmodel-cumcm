#!/usr/bin/env python3
"""Pre-freeze mechanical checks that need no judgement.

Three failures found on 2024B, none of which produced a compiler warning and
all of which needed a full manual read to surface:

  1. floats defined but never cited -- 5 of 16 on that manuscript;
  2. a number in the body whose producing script had been deleted as unused;
  3. optimality claimed as unique where an exact tie existed, because the tie
     check was applied to one subproblem and not another.

Rules written into a document get forgotten. Rules written into a gate do not.

    python scripts/check_manuscript_hygiene.py --project <cwd>
    python scripts/check_manuscript_hygiene.py --project <cwd> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The symbol table is conventionally not cross-referenced.
UNCITED_ALLOWED = {"tab:symbols", "tab:notation"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def tex_sources(project: Path) -> list[Path]:
    paper = project / "paper"
    if not paper.is_dir():
        return []
    return [p for p in paper.glob("*.tex") if not re.search(r"_pre_|_backup|_old", p.name)]


def check_float_citations(project: Path) -> list[dict]:
    """Every \\label must be reached by at least one \\ref.

    The reverse direction (every \\ref resolves) is what LaTeX already warns
    about; this one it never mentions.
    """
    out = []
    for tex in tex_sources(project):
        body = read(tex)
        labels = set(re.findall(r"\\label\{([^}]+)\}", body))
        refs = set(re.findall(r"\\(?:ref|autoref|eqref)\{([^}]+)\}", body))
        # Equations are routinely labelled for local reuse without being cited.
        floats = {la for la in labels if la.split(":")[0] in {"fig", "tab"}}
        unused = sorted(floats - refs - UNCITED_ALLOWED)
        for la in unused:
            out.append(
                {
                    "check": "float-uncited",
                    "severity": "error",
                    "file": tex.name,
                    "detail": f"{la} 有 \\label 但正文从未 \\ref",
                }
            )
    return out


def _result_values(project: Path) -> dict[int, set[float]]:
    """Every number in results/ and state/, pre-rounded to each precision.

    Substring matching cannot work here: the manuscript rounds (0.0451) and the
    result files do not (0.04506442017268496). The question is not whether the
    printed token appears verbatim but whether any recorded value rounds to it.
    """
    by_precision: dict[int, set[float]] = {d: set() for d in range(1, 7)}
    for folder in ("results", "state"):
        d = project / folder
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if f.suffix.lower() not in {".json", ".csv"}:
                continue
            if f.stat().st_size > 40_000_000:
                continue
            for token in re.findall(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", read(f)):
                try:
                    value = float(token)
                except ValueError:
                    continue
                for prec in by_precision:
                    by_precision[prec].add(round(value, prec))
                    # The manuscript often prints a magnitude whose sign lives
                    # in the surrounding prose ("下边界 $A=-2.2513$" recorded as
                    # -2.251291798606495), so match on absolute value too.
                    by_precision[prec].add(round(abs(value), prec))
    return by_precision


def check_number_provenance(project: Path) -> list[dict]:
    """Every computed decimal in the body should round from a recorded value.

    **Known limit.** Only decimals with four or more fractional digits are
    checked. A results directory holds thousands of numbers, so at two or three
    decimals some recorded value rounds to almost any token by coincidence and
    the check passes vacuously. Short decimals -- parameter increments such as
    "再增加0.25元" being the common case -- therefore cannot be traced this way
    and still need a human to ask where the number came from.

    Reporting this limit matters: a check that quietly covers less than it seems
    to is worse than no check, because the clean run reads as assurance.
    """
    by_precision = _result_values(project)
    if not any(by_precision.values()):
        return []

    out = []
    for tex in tex_sources(project):
        body = re.sub(r"%.*", "", read(tex))
        for token in sorted(set(re.findall(r"(?<![\d.])\d+\.\d{4,}(?![\d])", body))):
            decimals = len(token.split(".", 1)[1])
            if decimals > 6:
                continue
            try:
                value = float(token)
            except ValueError:
                continue
            if value in by_precision.get(decimals, set()):
                continue
            out.append(
                {
                    "check": "number-untraced",
                    "severity": "warning",
                    "file": tex.name,
                    "detail": (
                        f"{token} 在 results/ 与 state/ 中找不到能舍入到它的值；"
                        f"确认其计算是否已被删除"
                    ),
                }
            )
    return out


def check_tie_consistency(project: Path) -> list[dict]:
    """If any subproblem records an exact-tie count, all optima must."""
    summary = project / "results" / "authoritative_summary.json"
    if not summary.is_file():
        return []
    try:
        data = json.loads(read(summary))
    except json.JSONDecodeError:
        return [{"check": "tie-consistency", "severity": "error",
                 "file": summary.name, "detail": "authoritative_summary.json 无法解析"}]

    reporting: list[str] = []
    silent: list[str] = []

    # A node *asserts* optimality when it holds a best/optimal entry. The tie
    # information lives beside that entry, not inside it -- treating the entry
    # itself as a separate claim reports the parent's own tie fields as missing.
    ASSERTS = ("best_policy", "authoritative_best", "best_strategy", "optimal_policy")
    TIE_KEYS = ("tie", "unique_global_optimum", "number_of_ties")

    def has_tie_info(node: dict) -> bool:
        if any(any(t in k for t in TIE_KEYS) for k in node):
            return True
        # The tie fields may sit inside the asserted optimum rather than beside
        # it, e.g. authoritative_best.unique_global_optimum.
        for key in ASSERTS:
            child = node.get(key)
            if isinstance(child, dict) and any(
                any(t in k for t in TIE_KEYS) for k in child
            ):
                return True
        return False

    # A per-case optimum is usually a list under one of these keys, so each
    # element is its own claim. Keying only on the container silently skips
    # them: the list path ends in ".best" but the elements' paths do not.
    CLAIM_LISTS = ("best", "best_policies", "optima", "optimal")

    def walk(node, path="", parent_key=""):
        if isinstance(node, dict):
            asserts_here = (
                any(k in node for k in ASSERTS) or parent_key in CLAIM_LISTS
            )
            if asserts_here:
                (reporting if has_tie_info(node) else silent).append(path or "root")
            for k, v in node.items():
                # Do not descend into the asserted optimum itself; its parent
                # already carries the claim and the tie fields.
                if asserts_here and k in ASSERTS:
                    continue
                walk(v, f"{path}.{k}" if path else k, k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", parent_key)

    walk(data)
    if reporting and silent:
        return [
            {
                "check": "tie-consistency",
                "severity": "error",
                "file": summary.name,
                "detail": (
                    f"{len(reporting)} 处最优结论记录了并列检查，{len(silent)} 处没有："
                    f"{', '.join(silent[:4])}{' …' if len(silent) > 4 else ''}"
                ),
            }
        ]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    project = args.project.expanduser().resolve()
    if not project.is_dir():
        print(f"ERROR: no such project {project}", file=sys.stderr)
        return 2

    findings = (
        check_float_citations(project)
        + check_tie_consistency(project)
        + check_number_provenance(project)
    )

    if args.json:
        print(json.dumps({"project": str(project), "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        errors = [f for f in findings if f["severity"] == "error"]
        warnings = [f for f in findings if f["severity"] != "error"]
        for f in errors + warnings:
            tag = "ERROR  " if f["severity"] == "error" else "warning"
            print(f"  {tag} [{f['check']}] {f['file']}: {f['detail']}")
        if not findings:
            print("  ok      浮动体引用、并列一致性、数字溯源均通过")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
