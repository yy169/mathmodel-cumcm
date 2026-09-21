#!/usr/bin/env python3
"""Generate a reproducible code inventory and Markdown code appendix.

The default appendix is concise: it lists files, roles, hashes, entrypoints, imports,
and run commands. Pass --include-source only when the contest or user explicitly
needs source listings inside the appendix.
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


LANGUAGES = {
    ".py": "Python",
    ".m": "MATLAB",
    ".r": "R",
    ".R": "R",
    ".jl": "Julia",
    ".ipynb": "Jupyter Notebook",
    ".ps1": "PowerShell",
    ".sh": "Shell",
    ".bat": "Batch",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
}

DEFAULT_CODE_DIRS = ("code", "src", "scripts")
DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "build",
    "dist",
    ".python-packages",
}
ENTRYPOINT_NAMES = {
    "main",
    "run",
    "run_all",
    "solve",
    "analysis",
    "pipeline",
    "driver",
    "app",
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def python_metadata(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "module_doc": "",
        "imports": [],
        "functions": [],
        "classes": [],
        "has_main_guard": False,
    }
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        result["parse_error"] = f"{exc.msg} at line {exc.lineno}"
        return result
    result["module_doc"] = (ast.get_docstring(tree) or "").strip().splitlines()[0:1]
    result["module_doc"] = result["module_doc"][0] if result["module_doc"] else ""
    imports: set[str] = set()
    functions: list[str] = []
    classes: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(
                    isinstance(comp, ast.Constant) and comp.value == "__main__"
                    for comp in test.comparators
                )
            ):
                result["has_main_guard"] = True
    result["imports"] = sorted(imports)
    result["functions"] = functions
    result["classes"] = classes
    return result


def generic_metadata(text: str) -> dict[str, Any]:
    first_comment = ""
    for line in text.splitlines()[:30]:
        stripped = line.strip()
        if stripped.startswith(("#", "%", "//", "/*")):
            first_comment = stripped.lstrip("#%/ *").strip()
            if first_comment:
                break
    return {"module_doc": first_comment}


def output_references(text: str) -> list[str]:
    candidates = re.findall(
        r"""["']([^"']+\.(?:json|csv|npy|npz|png|pdf|svg|xlsx|tex|md))["']""",
        text,
        flags=re.IGNORECASE,
    )
    return sorted(set(item.replace("\\", "/") for item in candidates))[:100]


def is_entrypoint(path: Path, metadata: dict[str, Any]) -> bool:
    stem = path.stem.lower()
    if metadata.get("has_main_guard"):
        return True
    return stem in ENTRYPOINT_NAMES or stem.startswith(("run_", "main_", "solve_"))


def iter_code_files(root: Path, directories: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for directory in directories:
        base = (root / directory).resolve()
        if not base.exists():
            continue
        if base.is_file() and base.suffix in LANGUAGES:
            files.add(base)
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in LANGUAGES:
                continue
            try:
                relative_parts = path.relative_to(root).parts
            except ValueError:
                continue
            if any(part in DEFAULT_EXCLUDES for part in relative_parts):
                continue
            files.add(path.resolve())
    return sorted(files, key=lambda p: p.as_posix().lower())


def detect_run_commands(root: Path, entries: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for name in ("run_all.ps1", "run.ps1", "run_all.sh", "run.sh", "Makefile"):
        path = root / name
        if path.is_file():
            if path.suffix == ".ps1":
                commands.append(f".\\{name}")
            elif path.suffix == ".sh":
                commands.append(f"bash {name}")
            else:
                commands.append("make")
    for item in entries:
        if not item["entrypoint"]:
            continue
        path = item["path"]
        language = item["language"]
        command = None
        if language == "Python":
            command = f"python {path}"
        elif language == "MATLAB":
            command = f"matlab -batch \"run('{path}')\""
        elif language == "R":
            command = f"Rscript {path}"
        elif language == "Julia":
            command = f"julia {path}"
        elif language == "PowerShell":
            ps_path = path.replace("/", "\\")
            command = f".\\{ps_path}"
        elif language == "Shell":
            command = f"bash {path}"
        if command and command not in commands:
            commands.append(command)
    return commands


def build_manifest(root: Path, code_dirs: list[str]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in iter_code_files(root, code_dirs):
        relative = path.relative_to(root).as_posix()
        text = read_text(path)
        metadata = python_metadata(text) if path.suffix == ".py" else generic_metadata(text)
        entry = {
            "path": relative,
            "language": LANGUAGES[path.suffix],
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "purpose": metadata.get("module_doc", ""),
            "entrypoint": is_entrypoint(path, metadata),
            "imports": metadata.get("imports", []),
            "functions": metadata.get("functions", []),
            "classes": metadata.get("classes", []),
            "referenced_artifacts": output_references(text),
        }
        if metadata.get("parse_error"):
            entry["parse_error"] = metadata["parse_error"]
        entries.append(entry)
    return {
        "_schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "code_dirs": code_dirs,
        "file_count": len(entries),
        "entrypoints": [item["path"] for item in entries if item["entrypoint"]],
        "run_commands": detect_run_commands(root, entries),
        "files": entries,
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_appendix(
    manifest: dict[str, Any],
    root: Path,
    include_source: bool,
    source_max_bytes: int,
) -> str:
    lines = [
        "# 代码清单与复现入口",
        "",
        f"- 代码文件数：{manifest['file_count']}",
        f"- 生成时间：{manifest['generated_at']}",
        "- 文件哈希以 `results/code_manifest.json` 为准。",
        "",
        "## 运行入口",
        "",
    ]
    if manifest["run_commands"]:
        for command in manifest["run_commands"]:
            lines.extend(["```text", command, "```", ""])
    else:
        lines.append("未自动识别统一入口；提交前应在 README 中明确运行顺序。")
        lines.append("")

    lines.extend(
        [
            "## 文件清单",
            "",
            "| 文件 | 语言 | 用途 | 入口 | 大小/bytes | SHA-256（前12位） |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    for item in manifest["files"]:
        lines.append(
            "| {path} | {language} | {purpose} | {entrypoint} | {bytes} | `{hash}` |".format(
                path=f"`{item['path']}`",
                language=item["language"],
                purpose=markdown_escape(item.get("purpose") or "待团队补充用途说明"),
                entrypoint="是" if item["entrypoint"] else "否",
                bytes=item["bytes"],
                hash=item["sha256"][:12],
            )
        )

    lines.extend(
        [
            "",
            "## 复现说明",
            "",
            "1. 原始数据保持只读；程序输出写入 `processed_data/`、`results/` 和 `figures/`。",
            "2. 依赖版本以项目 `requirements.txt`、环境文件或 README 为准。",
            "3. 正式论文数字、图表和代码清单必须来自同一权威运行。",
            "",
        ]
    )

    if include_source:
        lines.extend(["## 源代码附录", ""])
        for item in manifest["files"]:
            path = root / item["path"]
            if item["bytes"] > source_max_bytes:
                lines.append(
                    f"### `{item['path']}`\n\n"
                    f"文件大小 {item['bytes']} bytes，超过附录阈值，完整源码见支撑材料。\n"
                )
                continue
            fence = "python" if item["language"] == "Python" else ""
            lines.extend(
                [
                    f"### `{item['path']}`",
                    "",
                    f"```{fence}",
                    read_text(path).rstrip(),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def canonical_for_check(manifest: dict[str, Any]) -> dict[str, Any]:
    copy = dict(manifest)
    copy.pop("generated_at", None)
    copy.pop("project_root", None)
    return copy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="User project root")
    parser.add_argument(
        "--code-dir",
        action="append",
        dest="code_dirs",
        help="Code directory relative to project; repeatable",
    )
    parser.add_argument("--output", default="results/code_manifest.json")
    parser.add_argument("--appendix", default="paper_workspace/code_appendix.md")
    parser.add_argument("--include-source", action="store_true")
    parser.add_argument("--source-max-bytes", type=int, default=100_000)
    parser.add_argument("--check", action="store_true", help="Fail if existing manifest is stale")
    parser.add_argument("--json", action="store_true", help="Print generated manifest")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.project).expanduser().resolve()
    code_dirs = args.code_dirs or list(DEFAULT_CODE_DIRS)
    manifest = build_manifest(root, code_dirs)
    output_path = root / args.output
    appendix_path = root / args.appendix

    if args.check:
        if not output_path.is_file():
            print(f"Missing manifest: {output_path}", file=sys.stderr)
            return 2
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        if canonical_for_check(existing) != canonical_for_check(manifest):
            print("Code manifest is stale.", file=sys.stderr)
            return 2
        print("Code manifest is current.")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    appendix_path.parent.mkdir(parents=True, exist_ok=True)
    appendix_path.write_text(
        render_appendix(manifest, root, args.include_source, args.source_max_bytes),
        encoding="utf-8",
    )
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Wrote: {output_path}")
    print(f"Wrote: {appendix_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
