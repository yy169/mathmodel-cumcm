from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from audit_common import (
    ALLOWED_REQUIREMENT_STATUS,
    read_csv,
    resolve_project_path,
    write_json,
)


def check_requirements(
    project: Path, registry: Path | None = None, verbose: bool = False
) -> dict:
    registry = registry or project / "reports" / "requirement_registry.csv"
    if not registry.exists():
        return {
            "checker": "requirement_coverage",
            "project": str(project),
            "registry": str(registry),
            "registry_status": "BLOCKED",
            "summary": {
                "answer_complete": None,
                "core_failures": None,
                "message": "Requirement registry is missing; legacy project needs backfill.",
            },
            "issues": [
                {
                    "severity": "BLOCKED",
                    "code": "MISSING_REQUIREMENT_REGISTRY",
                    "path": str(registry),
                }
            ],
        }

    rows = read_csv(registry)
    issues: list[dict] = []
    counts: Counter[str] = Counter()
    checked_rows: list[dict] = []

    for row_number, row in enumerate(rows, start=2):
        requirement_id = row.get("requirement_id", f"row_{row_number}").strip()
        status = row.get("status", "").strip().upper()
        counts[status] += 1
        row_issues: list[str] = []

        if status not in ALLOWED_REQUIREMENT_STATUS:
            row_issues.append("INVALID_STATUS")

        is_core = row.get("is_core", "true").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        code_path = resolve_project_path(project, row.get("code_entry", ""))
        result_path = resolve_project_path(project, row.get("result_artifact", ""))

        if status == "PASS":
            if not row.get("model_or_method", "").strip():
                row_issues.append("PASS_WITHOUT_MODEL")
            if code_path is not None and not code_path.exists():
                row_issues.append("MISSING_CODE_ARTIFACT")
            if result_path is None:
                row_issues.append("PASS_WITHOUT_RESULT_ARTIFACT")
            elif not result_path.exists():
                row_issues.append("MISSING_RESULT_ARTIFACT")
            if not row.get("validation_evidence", "").strip():
                row_issues.append("PASS_WITHOUT_VALIDATION")
            if not row.get("explicit_conclusion", "").strip():
                row_issues.append("PASS_WITHOUT_CONCLUSION")

        for code in row_issues:
            issues.append(
                {
                    "severity": "FAIL" if status == "PASS" else "WARNING",
                    "code": code,
                    "requirement_id": requirement_id,
                    "row": row_number,
                }
            )

        checked_rows.append(
            {
                "requirement_id": requirement_id,
                "status": status,
                "is_core": is_core,
                "code_artifact": str(code_path) if code_path else None,
                "code_exists": code_path.exists() if code_path else None,
                "result_artifact": str(result_path) if result_path else None,
                "result_exists": result_path.exists() if result_path else None,
                "row_issues": row_issues,
            }
        )

    core_rows = [row for row in checked_rows if row["is_core"]]
    all_core_pass = bool(core_rows) and all(
        row["status"] == "PASS" and not row["row_issues"] for row in core_rows
    )
    payload = {
        "checker": "requirement_coverage",
        "project": str(project),
        "registry": str(registry),
        "registry_status": "PASS",
        "summary": {
            "requirement_count": len(rows),
            "core_requirement_count": len(core_rows),
            "status_counts": dict(counts),
            "answer_complete": all_core_pass,
            "core_failures": [
                row["requirement_id"]
                for row in core_rows
                if row["status"] in {"FAIL", "PARTIAL"}
                or (row["status"] == "PASS" and row["row_issues"])
            ],
            "core_blocked": [
                row["requirement_id"]
                for row in core_rows
                if row["status"] == "BLOCKED"
            ],
        },
        "issues": issues,
    }
    if verbose:
        payload["requirements"] = checked_rows
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_requirements(
        args.project.resolve(), args.registry, verbose=args.verbose
    )
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
