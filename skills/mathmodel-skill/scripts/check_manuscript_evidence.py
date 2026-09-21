from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from audit_common import as_bool, read_csv, resolve_project_path, write_json


LAYERS = (
    "problem_analysis",
    "model_formulation",
    "solver",
    "result",
    "validation",
    "interpretation",
)
ALLOWED = {"PASS", "PARTIAL", "FAIL", "BLOCKED", "NA"}


def check_manuscript_evidence(
    project: Path, registry: Path | None = None, verbose: bool = False
) -> dict:
    registry = registry or project / "reports" / "manuscript_evidence_matrix.csv"
    if not registry.exists():
        return {
            "checker": "manuscript_evidence",
            "project": str(project),
            "registry": str(registry),
            "registry_status": "BLOCKED",
            "summary": {"narrative_depth_pass": None},
            "issues": [{"severity": "BLOCKED", "code": "MISSING_MANUSCRIPT_EVIDENCE_MATRIX"}],
        }

    rows = read_csv(registry)
    issues: list[dict] = []
    checked: list[dict] = []
    counts: Counter[str] = Counter()

    for row_number, row in enumerate(rows, start=2):
        section_id = row.get("subproblem_id", f"row_{row_number}").strip()
        is_core = as_bool(row.get("is_core", "true"))
        na_reason = row.get("na_reason", "").strip()
        layer_status: dict[str, str] = {}
        row_issues: list[str] = []

        for layer in LAYERS:
            status = row.get(layer, "").strip().upper()
            layer_status[layer] = status
            counts[status] += 1
            if status not in ALLOWED:
                row_issues.append(f"INVALID_{layer.upper()}_STATUS")
            if status == "NA" and not na_reason:
                row_issues.append(f"NA_WITHOUT_REASON_{layer.upper()}")

        evidence = row.get("evidence_paths", "").strip()
        if is_core and not evidence:
            row_issues.append("CORE_ROW_WITHOUT_EVIDENCE_PATH")
        for raw in [item.strip() for item in evidence.split(";") if item.strip()]:
            path = resolve_project_path(project, raw)
            if path is not None and not path.exists():
                row_issues.append("MISSING_EVIDENCE_ARTIFACT")

        for code in row_issues:
            issues.append(
                {
                    "severity": "FAIL" if is_core else "WARNING",
                    "code": code,
                    "subproblem_id": section_id,
                    "row": row_number,
                }
            )

        checked.append(
            {
                "subproblem_id": section_id,
                "is_core": is_core,
                "layers": layer_status,
                "row_issues": row_issues,
            }
        )

    core = [row for row in checked if row["is_core"]]
    narrative_depth_pass = bool(core) and all(
        all(status in {"PASS", "NA"} for status in row["layers"].values())
        and not row["row_issues"]
        for row in core
    )
    payload = {
        "checker": "manuscript_evidence",
        "project": str(project),
        "registry": str(registry),
        "registry_status": "PASS",
        "summary": {
            "subproblem_count": len(rows),
            "core_subproblem_count": len(core),
            "layer_status_counts": dict(counts),
            "narrative_depth_pass": narrative_depth_pass,
            "incomplete_core_subproblems": [
                row["subproblem_id"]
                for row in core
                if row["row_issues"]
                or any(s not in {"PASS", "NA"} for s in row["layers"].values())
            ],
        },
        "issues": issues,
    }
    if verbose:
        payload["subproblems"] = checked
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_manuscript_evidence(
        args.project.resolve(), args.registry, verbose=args.verbose
    )
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
