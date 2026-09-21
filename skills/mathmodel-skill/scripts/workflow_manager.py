#!/usr/bin/env python3
"""Central execution helper for the local 26math ten-stage workflow.

The manifest is the execution SSOT; decision_log.json remains the decision/reason SSOT.
This tool never runs modeling code by itself. It validates stage readiness, records
checkpoints, and produces the smallest auditable rerun plan for a set of changed files.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = SKILL_ROOT / "assets" / "workflow_manifest.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def project_root(value: str | None) -> Path:
    return Path(value or ".").expanduser().resolve()


def load_context(args: argparse.Namespace) -> tuple[Path, dict[str, Any], dict[str, Any], Path]:
    root = project_root(args.project)
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else DEFAULT_MANIFEST
    manifest = read_json(manifest_path)
    decision_rel = manifest["artifact_contracts"]["decision_log"]
    decision_path = root / decision_rel
    decision = read_json(decision_path)
    return root, manifest, decision, decision_path


def get_path(data: Any, dotted: str) -> tuple[bool, Any]:
    current = data
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def matching_paths(root: Path, pattern: str) -> list[Path]:
    normalized = pattern.replace("\\", "/")
    if any(ch in normalized for ch in "*?["):
        return [p for p in root.glob(normalized) if p.is_file()]
    path = root / normalized
    return [path] if path.is_file() else []


def check_one(root: Path, decision: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    kind = check["kind"]
    allow_missing = bool(check.get("allow_missing", False))
    message = check.get("message", kind)
    result = False
    detail = ""

    if kind.startswith("state_"):
        exists, value = get_path(decision, check["path"])
        if not exists and allow_missing:
            return {"ok": True, "message": message, "detail": "missing allowed"}
        if not exists:
            return {"ok": False, "message": message, "detail": f"missing {check['path']}"}
        if kind == "state_equals":
            result = value == check.get("value")
        elif kind == "state_not_equals":
            result = value != check.get("value")
        elif kind == "state_nonempty":
            result = nonempty(value)
        elif kind == "state_map_excludes":
            banned = set(check.get("values", []))
            result = isinstance(value, dict) and all(v not in banned for v in value.values())
        else:
            raise ValueError(f"Unsupported state check: {kind}")
        detail = repr(value)
    elif kind in {"artifact_exists", "artifact_any"}:
        hits: list[str] = []
        for pattern in check.get("paths", []):
            hits.extend(str(path.relative_to(root)) for path in matching_paths(root, pattern))
        if not hits and allow_missing:
            return {"ok": True, "message": message, "detail": "missing allowed"}
        result = bool(hits)
        detail = ", ".join(hits) if hits else "no matching artifact"
    elif kind == "artifact_json_equals":
        path = root / check["file"]
        if not path.exists() and allow_missing:
            return {"ok": True, "message": message, "detail": "missing allowed"}
        if not path.exists():
            return {"ok": False, "message": message, "detail": f"missing {check['file']}"}
        data = read_json(path)
        exists, value = get_path(data, check["path"])
        result = exists and value == check.get("value")
        detail = repr(value) if exists else f"missing {check['path']}"
    else:
        raise ValueError(f"Unsupported check: {kind}")

    return {"ok": result, "message": message, "detail": detail}


def validate_stage(
    root: Path,
    manifest: dict[str, Any],
    decision: dict[str, Any],
    stage_id: int,
    include_dependencies: bool = True,
) -> dict[str, Any]:
    stages = manifest["stages"]
    key = str(stage_id)
    if key not in stages:
        raise SystemExit(f"Unknown stage: {stage_id}")
    stage = stages[key]
    dependency_results = []
    if include_dependencies:
        for dep in stage.get("depends_on", []):
            dependency_results.append(
                validate_stage(root, manifest, decision, int(dep), include_dependencies=False)
            )
    checks = [check_one(root, decision, check) for check in stage.get("checks", [])]
    deps_ok = all(item["ok"] for item in dependency_results)
    checks_ok = all(item["ok"] for item in checks)
    return {
        "stage": stage_id,
        "name": stage["name"],
        "protocol": stage["protocol"],
        "ok": deps_ok and checks_ok,
        "dependencies": dependency_results,
        "checks": checks,
    }


def print_stage(result: dict[str, Any], verbose: bool = True) -> None:
    label = "PASS" if result["ok"] else "WAIT"
    print(f"[{label}] Stage {result['stage']}: {result['name']}")
    if verbose:
        for dep in result.get("dependencies", []):
            if not dep["ok"]:
                print(f"  - dependency Stage {dep['stage']} not ready")
        for check in result.get("checks", []):
            marker = "ok" if check["ok"] else "x"
            print(f"  - [{marker}] {check['message']}: {check['detail']}")


def command_status(args: argparse.Namespace) -> int:
    root, manifest, decision, _ = load_context(args)
    current = decision.get("current_stage", 0)
    print(f"Project: {root}")
    print(f"Competition: {decision.get('competition')}")
    print(f"Current stage in state: {current}")
    for stage_id in manifest["stage_order"]:
        result = validate_stage(root, manifest, decision, int(stage_id), include_dependencies=False)
        prefix = "->" if int(stage_id) == int(current) else "  "
        label = "PASS" if result["ok"] else "WAIT"
        print(f"{prefix} [{label}] {stage_id} {result['name']}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    root, manifest, decision, _ = load_context(args)
    result = validate_stage(root, manifest, decision, args.stage, include_dependencies=True)
    print_stage(result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_next(args: argparse.Namespace) -> int:
    root, manifest, decision, _ = load_context(args)
    for stage_id in manifest["stage_order"]:
        result = validate_stage(root, manifest, decision, int(stage_id), include_dependencies=False)
        if not result["ok"]:
            print_stage(result)
            return 0
    print("All stages pass the manifest checks.")
    return 0


def normalized_change(root: Path, value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root)
        except ValueError:
            return path.as_posix()
    return path.as_posix().lstrip("./")


def path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    pattern = pattern.replace("\\", "/")
    variants = {pattern}
    if "/**/" in pattern:
        variants.add(pattern.replace("/**/", "/"))
    return any(candidate.match(item) or fnmatch.fnmatch(normalized, item) for item in variants)


def plan_rerun(manifest: dict[str, Any], root: Path, changed: list[str]) -> dict[str, Any]:
    normalized = [normalized_change(root, item) for item in changed]
    matched_rules = []
    stages: set[int] = set()
    actions: list[str] = []
    unmatched = []

    for path in normalized:
        path_hit = False
        for rule in manifest.get("change_impact_rules", []):
            if any(path_matches(path, ex) for ex in rule.get("exclude", [])):
                continue
            if any(path_matches(path, pat) for pat in rule.get("patterns", [])):
                path_hit = True
                if rule["id"] not in matched_rules:
                    matched_rules.append(rule["id"])
                stages.update(int(stage) for stage in rule.get("stages", []))
                for action in rule.get("actions", []):
                    if action not in actions:
                        actions.append(action)
        if not path_hit:
            unmatched.append(path)

    if unmatched:
        for stage in (8, 9):
            stages.add(stage)
        actions.append("未知文件类型：人工判断是否影响模型、结果、论文或提交包")

    ordered_stages = [stage for stage in manifest["stage_order"] if int(stage) in stages]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changed_files": normalized,
        "matched_rules": matched_rules,
        "unmatched_files": unmatched,
        "rerun_stages": ordered_stages,
        "earliest_stage": ordered_stages[0] if ordered_stages else None,
        "actions": actions,
    }


def command_plan_rerun(args: argparse.Namespace) -> int:
    root, manifest, _, _ = load_context(args)
    plan = plan_rerun(manifest, root, args.changed)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if args.write:
        output = root / manifest["artifact_contracts"]["rerun_plan"]
        write_json(output, plan)
        print(f"Wrote: {output}")
    return 0


def command_checkpoint(args: argparse.Namespace) -> int:
    root, manifest, decision, decision_path = load_context(args)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_dir = root / manifest["artifact_contracts"]["checkpoint_dir"]
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    target = checkpoint_dir / f"stage_{args.stage}_{stamp}.json"
    shutil.copy2(decision_path, target)
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": args.stage,
        "source": str(decision_path.relative_to(root)),
        "checkpoint": str(target.relative_to(root)),
        "note": args.note or "",
        "current_stage": decision.get("current_stage"),
    }
    write_json(target.with_suffix(".meta.json"), metadata)
    print(f"Checkpoint: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="User project root; default current directory")
    parser.add_argument("--manifest", help="Override workflow manifest path")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show all ten stage states")
    status.set_defaults(func=command_status)

    validate = sub.add_parser("validate", help="Validate one stage and dependencies")
    validate.add_argument("--stage", type=int, required=True)
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=command_validate)

    next_stage = sub.add_parser("next", help="Show the earliest incomplete stage")
    next_stage.set_defaults(func=command_next)

    rerun = sub.add_parser("plan-rerun", help="Plan the smallest rerun from changed paths")
    rerun.add_argument("--changed", nargs="+", required=True)
    rerun.add_argument("--write", action="store_true")
    rerun.set_defaults(func=command_plan_rerun)

    checkpoint = sub.add_parser("checkpoint", help="Copy decision_log into state/checkpoints")
    checkpoint.add_argument("--stage", type=int, required=True)
    checkpoint.add_argument("--note")
    checkpoint.set_defaults(func=command_checkpoint)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
