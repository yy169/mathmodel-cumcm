from __future__ import annotations

import argparse
from pathlib import Path

from audit_common import write_json
from check_claim_evidence import check_claims
from check_cross_file_consistency import check_cross_files
from check_encoding_registry import check_encoding_registry
from check_figure_audit import check_figure_audit
from check_manuscript_evidence import check_manuscript_evidence
from check_requirement_coverage import check_requirements
from derive_readiness import derive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    reports = {
        "requirements": check_requirements(project, verbose=args.verbose),
        "claims": check_claims(project, verbose=args.verbose),
        "cross": check_cross_files(project, verbose=args.verbose),
        "manuscript": check_manuscript_evidence(project, verbose=args.verbose),
        "figures": check_figure_audit(project, verbose=args.verbose),
        "encoding": check_encoding_registry(project, verbose=args.verbose),
    }
    for name, payload in reports.items():
        write_json(out / f"{name}.json", payload)

    readiness = derive(
        reports["requirements"],
        reports["claims"],
        reports["cross"],
        reports["manuscript"],
        reports["figures"],
        reports["encoding"],
    )
    write_json(out / "readiness.json", readiness)
    print(out / "readiness.json")


if __name__ == "__main__":
    main()
