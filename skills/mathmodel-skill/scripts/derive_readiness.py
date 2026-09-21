from __future__ import annotations

import argparse
from pathlib import Path

from audit_common import read_json, write_json


def derive(
    requirement_report: dict,
    claim_report: dict,
    cross_report: dict,
    manuscript_report: dict,
    figure_report: dict,
    encoding_report: dict,
) -> dict:
    answer_complete = requirement_report.get("summary", {}).get(
        "answer_complete"
    )
    manuscript_consistent = claim_report.get("summary", {}).get(
        "manuscript_consistent"
    )
    package_valid = cross_report.get("summary", {}).get("package_valid")
    emergency = cross_report.get("summary", {}).get(
        "emergency_package_available", False
    )
    state_submission_ready = cross_report.get("summary", {}).get(
        "state_submission_ready"
    )
    narrative_depth_pass = manuscript_report.get("summary", {}).get(
        "narrative_depth_pass"
    )
    figure_evidence_pass = figure_report.get("summary", {}).get(
        "figure_evidence_pass"
    )
    encoding_reproducible = encoding_report.get("summary", {}).get(
        "encoding_reproducible", True
    )

    if any(
        value is None
        for value in (
            answer_complete,
            manuscript_consistent,
            narrative_depth_pass,
            figure_evidence_pass,
        )
    ):
        verification_status = "BLOCKED_LEGACY_MIGRATION"
        result_ready = None
        manuscript_ready = None
        final_quality_ready = None
        submission_ready = None
    else:
        result_ready = answer_complete is True
        manuscript_ready = all(
            value is True
            for value in (
                result_ready,
                manuscript_consistent,
                narrative_depth_pass,
                figure_evidence_pass,
                encoding_reproducible,
            )
        )
        final_quality_ready = manuscript_ready and package_valid is True
        submission_ready = final_quality_ready
        verification_status = "PASS" if final_quality_ready else "FAIL"

    contradictions: list[dict] = []
    if (
        verification_status == "FAIL"
        and state_submission_ready is True
        and submission_ready is False
    ):
        contradictions.append(
            {
                "code": "STATE_READY_BUT_DERIVED_NOT_READY",
                "detail": (
                    "decision_log claims submission_ready=true, but requirement, "
                    "claim, or package gates do not derive true."
                ),
            }
        )
    elif (
        verification_status == "BLOCKED_LEGACY_MIGRATION"
        and state_submission_ready is True
    ):
        contradictions.append(
            {
                "code": "STATE_READY_UNVERIFIED_BY_NEW_REGISTRIES",
                "detail": (
                    "Existing state claims ready, while the new requirement and "
                    "claim registries are absent. This is a migration warning, "
                    "not a negative judgment on the manuscript."
                ),
            }
        )

    return {
        "verification_status": verification_status,
        "readiness": {
            "problem_ready": None,
            "model_ready": None,
            "result_ready": result_ready,
            "manuscript_ready": manuscript_ready,
            "package_valid": package_valid is True,
            "answer_complete": answer_complete,
            "manuscript_consistent": manuscript_consistent,
            "narrative_depth_pass": narrative_depth_pass,
            "figure_evidence_pass": figure_evidence_pass,
            "encoding_reproducible": encoding_reproducible,
            "final_quality_ready": final_quality_ready,
            "emergency_package_available": bool(emergency),
            "submission_ready": submission_ready,
        },
        "existing_state_submission_ready": state_submission_ready,
        "contradictions": contradictions,
        "source_reports": {
            "requirement_registry_status": requirement_report.get(
                "registry_status"
            ),
            "claim_registry_status": claim_report.get("registry_status"),
            "manuscript_evidence_status": manuscript_report.get("registry_status"),
            "figure_audit_status": figure_report.get("registry_status"),
            "encoding_registry_status": encoding_report.get("registry_status"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--claims", required=True, type=Path)
    parser.add_argument("--cross-files", required=True, type=Path)
    parser.add_argument("--manuscript-evidence", required=True, type=Path)
    parser.add_argument("--figure-audit", required=True, type=Path)
    parser.add_argument("--encoding-audit", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = derive(
        read_json(args.requirements),
        read_json(args.claims),
        read_json(args.cross_files),
        read_json(args.manuscript_evidence),
        read_json(args.figure_audit),
        read_json(args.encoding_audit) if args.encoding_audit else {},
    )
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
