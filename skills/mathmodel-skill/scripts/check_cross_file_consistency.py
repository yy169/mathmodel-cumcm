from __future__ import annotations

import argparse
import re
from pathlib import Path

from audit_common import nested_get, read_json, sha256, write_json


def find_tex(project: Path) -> Path | None:
    for candidate in (
        project / "paper" / "main.tex",
        project / "paper.tex",
    ):
        if candidate.exists():
            return candidate
    return None


def find_pdf(project: Path, state: dict | None) -> Path | None:
    if state:
        relative = nested_get(state, "stages.9.final_pdf_path")
        if relative:
            candidate = project / relative
            if candidate.exists():
                return candidate
    for candidate in (
        project / "paper" / "main.pdf",
        project / "output" / "final_paper.pdf",
    ):
        if candidate.exists():
            return candidate
    return None


def resolve_graphic(tex_path: Path, tex: str, value: str) -> Path:
    macros = dict(
        re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{([^{}]+)\}", tex)
    )
    for name, replacement in macros.items():
        value = value.replace(f"\\{name}", replacement)
    candidate = (tex_path.parent / value).resolve()
    if candidate.suffix:
        return candidate
    for suffix in (".png", ".pdf", ".jpg", ".jpeg"):
        with_suffix = candidate.with_suffix(suffix)
        if with_suffix.exists():
            return with_suffix
    return candidate


def check_code_manifest(project: Path) -> tuple[list[dict], bool | None]:
    path = project / "results" / "code_manifest.json"
    if not path.exists():
        return [{"severity": "BLOCKED", "code": "MISSING_CODE_MANIFEST"}], None
    data = read_json(path)
    issues: list[dict] = []
    listed_paths = set()
    for item in data.get("files", []):
        rel = item.get("path", "")
        listed_paths.add(rel.replace("\\", "/"))
        file_path = project / rel
        if not file_path.exists():
            issues.append(
                {"severity": "FAIL", "code": "MANIFEST_FILE_MISSING", "path": rel}
            )
            continue
        expected = str(item.get("sha256", "")).lower()
        if expected and sha256(file_path).lower() != expected:
            issues.append(
                {"severity": "FAIL", "code": "CODE_HASH_MISMATCH", "path": rel}
            )

    actual_code = {
        str(path.relative_to(project)).replace("\\", "/")
        for folder in ("code", "src", "scripts")
        for path in (project / folder).rglob("*")
        if (project / folder).exists()
        and path.is_file()
        and path.suffix.lower() in {".py", ".r", ".m", ".jl"}
        and "__pycache__" not in path.parts
    }
    unlisted = sorted(actual_code - listed_paths)
    if unlisted:
        issues.append(
            {
                "severity": "FAIL",
                "code": "UNLISTED_CODE_FILES",
                "paths": unlisted,
            }
        )
    return issues, not any(x["severity"] == "FAIL" for x in issues)


def check_figure_provenance(project: Path) -> tuple[list[dict], bool | None]:
    path = project / "results" / "figure_provenance.json"
    if not path.exists():
        return [
            {"severity": "BLOCKED", "code": "MISSING_FIGURE_PROVENANCE"}
        ], None
    data = read_json(path)
    issues: list[dict] = []
    for item in data.get("figures", []):
        rel = item.get("file_path", "")
        file_path = project / rel
        if not file_path.exists():
            issues.append(
                {"severity": "FAIL", "code": "FIGURE_FILE_MISSING", "path": rel}
            )
            continue
        expected = str(item.get("sha256", "")).lower()
        if expected and sha256(file_path).lower() != expected:
            issues.append(
                {"severity": "FAIL", "code": "FIGURE_HASH_MISMATCH", "path": rel}
            )
    return issues, not any(x["severity"] == "FAIL" for x in issues)


def check_cross_files(project: Path, verbose: bool = False) -> dict:
    issues: list[dict] = []
    state_path = project / "state" / "decision_log.json"
    state = read_json(state_path) if state_path.exists() else None
    tex_path = find_tex(project)
    pdf_path = find_pdf(project, state)

    if tex_path is None:
        issues.append({"severity": "FAIL", "code": "MISSING_TEX"})
    if pdf_path is None:
        issues.append({"severity": "FAIL", "code": "MISSING_PDF"})

    figure_refs: list[dict] = []
    bibliography_refs: list[dict] = []
    if tex_path is not None:
        tex = tex_path.read_text(encoding="utf-8", errors="replace")
        for raw in re.findall(
            r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex
        ):
            resolved = resolve_graphic(tex_path, tex, raw)
            exists = resolved.exists()
            figure_refs.append(
                {"raw": raw, "resolved": str(resolved), "exists": exists}
            )
            if not exists:
                issues.append(
                    {
                        "severity": "FAIL",
                        "code": "TEX_FIGURE_MISSING",
                        "path": str(resolved),
                    }
                )
        for raw in re.findall(r"\\bibliography\{([^}]+)\}", tex):
            for part in raw.split(","):
                candidate = (tex_path.parent / part.strip()).resolve()
                if candidate.suffix != ".bib":
                    candidate = candidate.with_suffix(".bib")
                exists = candidate.exists()
                bibliography_refs.append(
                    {
                        "raw": part.strip(),
                        "resolved": str(candidate),
                        "exists": exists,
                    }
                )
                if not exists:
                    issues.append(
                        {
                            "severity": "FAIL",
                            "code": "BIBLIOGRAPHY_FILE_MISSING",
                            "path": str(candidate),
                        }
                    )

    code_issues, code_manifest_valid = check_code_manifest(project)
    figure_issues, figure_provenance_valid = check_figure_provenance(project)
    issues.extend(code_issues)
    issues.extend(figure_issues)

    ai_candidates = [
        project / "AI工具使用详情.pdf",
        project / "support_materials" / "AI工具使用详情.pdf",
    ]
    ai_exists = any(path.exists() for path in ai_candidates)
    if not ai_exists:
        issues.append({"severity": "WARNING", "code": "AI_DISCLOSURE_NOT_FOUND"})

    state_submission_ready = (
        nested_get(state, "stages.9.submission_ready") if state else None
    )
    compliance_values = {
        key: nested_get(state, f"stages.9.compliance_checks.{key}")
        if state
        else None
        for key in (
            "rules_verified",
            "anonymity_passed",
            "page_limit_passed",
            "ai_disclosure_passed",
            "supporting_materials_passed",
        )
    }
    compliance_known_pass = all(value is True for value in compliance_values.values())
    critical_fail = any(item["severity"] == "FAIL" for item in issues)
    package_valid = (
        not critical_fail
        and pdf_path is not None
        and code_manifest_valid is True
        and (figure_provenance_valid is True or figure_provenance_valid is None)
        and compliance_known_pass
    )
    emergency_package_available = pdf_path is not None and tex_path is not None

    payload = {
        "checker": "cross_file_consistency",
        "project": str(project),
        "summary": {
            "tex_path": str(tex_path) if tex_path else None,
            "pdf_path": str(pdf_path) if pdf_path else None,
            "pdf_bytes": pdf_path.stat().st_size if pdf_path else None,
            "state_submission_ready": state_submission_ready,
            "code_manifest_valid": code_manifest_valid,
            "figure_provenance_valid": figure_provenance_valid,
            "compliance_values": compliance_values,
            "package_valid": package_valid,
            "emergency_package_available": emergency_package_available,
        },
        "issues": issues,
    }
    if verbose:
        payload["tex_figure_references"] = figure_refs
        payload["bibliography_references"] = bibliography_refs
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    payload = check_cross_files(args.project.resolve(), verbose=args.verbose)
    write_json(args.output, payload)
    print(args.output)


if __name__ == "__main__":
    main()
