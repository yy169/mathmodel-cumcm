from __future__ import annotations

import argparse
from pathlib import Path

from audit_common import as_bool, read_csv, resolve_project_path, write_json


ALLOWED_DECISIONS = {"KEEP", "REDESIGN", "DELETE"}


def check_figure_audit(
    project: Path, registry: Path | None = None, verbose: bool = False
) -> dict:
    registry = registry or project / "reports" / "figure_audit.csv"
    if not registry.exists():
        return {
            "checker": "figure_audit",
            "project": str(project),
            "registry": str(registry),
            "registry_status": "BLOCKED",
            "summary": {"figure_evidence_pass": None},
            "issues": [{"severity": "BLOCKED", "code": "MISSING_FIGURE_AUDIT"}],
        }

    rows = read_csv(registry)
    issues: list[dict] = []
    checked: list[dict] = []
    for row_number, row in enumerate(rows, start=2):
        figure_id = row.get("figure_id", f"row_{row_number}").strip()
        decision = row.get("decision", "").strip().upper()
        included = as_bool(row.get("included_in_manuscript", "false"))
        row_issues: list[str] = []

        if decision not in ALLOWED_DECISIONS:
            row_issues.append("INVALID_DECISION")
        if decision == "REDESIGN":
            row_issues.append("FIGURE_STILL_REQUIRES_REDESIGN")
        if decision == "KEEP":
            for field in ("evidence_question", "source_artifacts", "generation_script", "final_width"):
                if not row.get(field, "").strip():
                    row_issues.append(f"KEEP_WITHOUT_{field.upper()}")
            if not included:
                row_issues.append("KEEP_NOT_INCLUDED")
            if not as_bool(row.get("readability_pass", "false")):
                row_issues.append("FINAL_SIZE_READABILITY_NOT_PASSED")
            if not as_bool(row.get("grayscale_pass", "false")):
                row_issues.append("GRAYSCALE_NOT_PASSED")
            if row.get("table_overlap", "").strip().lower() in {"high", "duplicate", "full"}:
                row_issues.append("HIGH_TABLE_OVERLAP")
            for field in ("source_artifacts", "generation_script"):
                for raw in [x.strip() for x in row.get(field, "").split(";") if x.strip()]:
                    path = resolve_project_path(project, raw)
                    if path is not None and not path.exists():
                        row_issues.append(f"MISSING_{field.upper()}_PATH")
        if decision == "DELETE":
            if included:
                row_issues.append("DELETED_FIGURE_STILL_INCLUDED")
            if not row.get("decision_reason", "").strip():
                row_issues.append("DELETE_WITHOUT_REASON")

        for code in row_issues:
            issues.append(
                {"severity": "FAIL", "code": code, "figure_id": figure_id, "row": row_number}
            )
        checked.append(
            {
                "figure_id": figure_id,
                "decision": decision,
                "included_in_manuscript": included,
                "row_issues": row_issues,
            }
        )

    figure_evidence_pass = bool(rows) and all(not row["row_issues"] for row in checked)
    payload = {
        "checker": "figure_audit",
        "project": str(project),
        "registry": str(registry),
        "registry_status": "PASS",
        "summary": {
            "figure_count": len(rows),
            "kept": sum(row["decision"] == "KEEP" for row in checked),
            "deleted": sum(row["decision"] == "DELETE" for row in checked),
            "redesign": sum(row["decision"] == "REDESIGN" for row in checked),
            "figure_evidence_pass": figure_evidence_pass,
        },
        "issues": issues,
    }
    if verbose:
        payload["figures"] = checked
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_figure_audit(args.project.resolve(), args.registry, args.verbose)
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
