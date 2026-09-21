from __future__ import annotations

import argparse
from pathlib import Path

from audit_common import as_bool, read_csv, resolve_project_path, write_json


def check_encoding_registry(
    project: Path, registry: Path | None = None, verbose: bool = False
) -> dict:
    registry = registry or project / "reports" / "encoding_registry.csv"
    if not registry.exists():
        return {
            "checker": "encoding_registry",
            "project": str(project),
            "registry": str(registry),
            "registry_status": "NOT_APPLICABLE",
            "summary": {"encoding_reproducible": True, "applicable_count": 0},
            "issues": [],
        }

    rows = read_csv(registry)
    issues: list[dict] = []
    checked: list[dict] = []
    for row_number, row in enumerate(rows, start=2):
        entity_id = row.get("entity_id", f"row_{row_number}").strip()
        applicable = as_bool(row.get("applicable", "true"))
        row_issues: list[str] = []
        if applicable:
            for field in ("encoding_formula", "display_order", "decode_table", "roundtrip_test"):
                if not row.get(field, "").strip():
                    row_issues.append(f"MISSING_{field.upper()}")
            status = row.get("status", "").strip().upper()
            if status != "PASS":
                row_issues.append("ROUNDTRIP_STATUS_NOT_PASS")
            evidence = resolve_project_path(project, row.get("evidence_path", ""))
            if evidence is None or not evidence.exists():
                row_issues.append("MISSING_ENCODING_EVIDENCE")
        for code in row_issues:
            issues.append(
                {"severity": "FAIL", "code": code, "entity_id": entity_id, "row": row_number}
            )
        checked.append({"entity_id": entity_id, "applicable": applicable, "row_issues": row_issues})

    applicable_rows = [row for row in checked if row["applicable"]]
    payload = {
        "checker": "encoding_registry",
        "project": str(project),
        "registry": str(registry),
        "registry_status": "PASS",
        "summary": {
            "applicable_count": len(applicable_rows),
            "encoding_reproducible": all(not row["row_issues"] for row in applicable_rows),
        },
        "issues": issues,
    }
    if verbose:
        payload["encodings"] = checked
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_encoding_registry(args.project.resolve(), args.registry, args.verbose)
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
