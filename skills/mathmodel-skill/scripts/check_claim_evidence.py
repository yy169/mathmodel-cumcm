from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from audit_common import ALLOWED_CLAIM_STATUS, as_bool, read_csv, write_json


ALLOWED_EVIDENCE_LEVELS = {
    "structural_proof",
    "formal_derivation",
    "exact_enumeration",
    "numerical_validation",
    "empirical_crosscheck",
    "sensitivity_only",
    "source_supported",
    "direct_result",
}


def evidence_supports(claim_level: str, evidence_level: str) -> bool:
    claim_level = claim_level.lower()
    if "global_optimum" in claim_level or "unique_global" in claim_level:
        return evidence_level in {"structural_proof", "exact_enumeration"}
    if "proof" in claim_level or "impossibility" in claim_level:
        return evidence_level in {"structural_proof", "formal_derivation"}
    if "exact_global_enumeration" in claim_level:
        return evidence_level == "exact_enumeration"
    return True


def check_claims(
    project: Path, registry: Path | None = None, verbose: bool = False
) -> dict:
    registry = registry or project / "reports" / "claim_registry.csv"
    if not registry.exists():
        return {
            "checker": "claim_evidence",
            "project": str(project),
            "registry": str(registry),
            "registry_status": "BLOCKED",
            "summary": {
                "manuscript_consistent": None,
                "message": "Claim registry is missing; legacy project needs backfill.",
            },
            "issues": [
                {
                    "severity": "BLOCKED",
                    "code": "MISSING_CLAIM_REGISTRY",
                    "path": str(registry),
                }
            ],
        }

    rows = read_csv(registry)
    issues: list[dict] = []
    checked: list[dict] = []
    counts: Counter[str] = Counter()

    for row_number, row in enumerate(rows, start=2):
        claim_id = row.get("claim_id", f"row_{row_number}").strip()
        status = row.get("evidence_status", "").strip().upper()
        claim_level = row.get("claim_level", "").strip()
        evidence_level = row.get("evidence_level", "").strip().lower()
        allowed = as_bool(row.get("allowed_in_manuscript", "false"))
        counts[status] += 1
        row_issues: list[str] = []

        if status not in ALLOWED_CLAIM_STATUS:
            row_issues.append("INVALID_EVIDENCE_STATUS")
        if allowed and status != "PASS":
            row_issues.append("OVERCLAIM_ALLOWED_WITHOUT_PASS")
        if not row.get("evidence", "").strip():
            row_issues.append("MISSING_EVIDENCE_DESCRIPTION")
        if not row.get("claim_text", "").strip():
            row_issues.append("MISSING_CLAIM_TEXT")
        if evidence_level not in ALLOWED_EVIDENCE_LEVELS:
            row_issues.append("MISSING_OR_INVALID_EVIDENCE_LEVEL")
        elif not evidence_supports(claim_level, evidence_level):
            row_issues.append("CLAIM_STRENGTH_EXCEEDS_EVIDENCE_LEVEL")

        # The registry is defined as a list of claims currently requiring audit.
        # A blocked claim therefore keeps manuscript_consistent false until it is
        # rewritten or its evidence status becomes PASS.
        if not allowed:
            row_issues.append("CLAIM_REQUIRES_REMOVAL_OR_DOWNGRADE")

        for code in row_issues:
            issues.append(
                {
                    "severity": "FAIL"
                    if code
                    in {
                        "OVERCLAIM_ALLOWED_WITHOUT_PASS",
                        "CLAIM_REQUIRES_REMOVAL_OR_DOWNGRADE",
                        "MISSING_OR_INVALID_EVIDENCE_LEVEL",
                        "CLAIM_STRENGTH_EXCEEDS_EVIDENCE_LEVEL",
                    }
                    else "WARNING",
                    "code": code,
                    "claim_id": claim_id,
                    "row": row_number,
                }
            )

        checked.append(
            {
                "claim_id": claim_id,
                "evidence_status": status,
                "evidence_level": evidence_level,
                "allowed_in_manuscript": allowed,
                "row_issues": row_issues,
            }
        )

    manuscript_consistent = all(
        row["evidence_status"] == "PASS"
        and row["allowed_in_manuscript"]
        and not row["row_issues"]
        for row in checked
    )
    payload = {
        "checker": "claim_evidence",
        "project": str(project),
        "registry": str(registry),
        "registry_status": "PASS",
        "summary": {
            "claim_count": len(rows),
            "status_counts": dict(counts),
            "allowed_claim_count": sum(
                row["allowed_in_manuscript"] for row in checked
            ),
            "blocked_claim_count": sum(
                not row["allowed_in_manuscript"] for row in checked
            ),
            "manuscript_consistent": manuscript_consistent,
        },
        "issues": issues,
    }
    if verbose:
        payload["claims"] = checked
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_claims(
        args.project.resolve(), args.registry, verbose=args.verbose
    )
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
