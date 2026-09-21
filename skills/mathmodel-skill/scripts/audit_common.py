from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_REQUIREMENT_STATUS = {"PASS", "PARTIAL", "FAIL", "BLOCKED"}
ALLOWED_CLAIM_STATUS = {"PASS", "PARTIAL", "FAIL", "BLOCKED"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass"}


def path_part(value: str) -> str:
    """Return the file portion of values such as ``code/x.py::function``."""
    return value.split("::", 1)[0].strip()


def resolve_project_path(project: Path, value: str) -> Path | None:
    value = path_part(value)
    if not value or value.lower() in {
        "无",
        "none",
        "n/a",
        "待实现",
        "尚无正式入口",
        "尚无权威结果",
    }:
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else project / candidate


def nested_get(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

