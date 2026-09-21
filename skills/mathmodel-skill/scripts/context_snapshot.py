from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def get(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    project = args.project.resolve()
    state_path = project / "state" / "decision_log.json"
    if not state_path.exists():
        payload = {
            "status": "BLOCKED",
            "project": str(project),
            "issue": "state/decision_log.json not found",
        }
    else:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        stage = state.get("current_stage")
        stage_data = get(state, f"stages.{stage}", {}) if stage is not None else {}
        qi_status = get(state, "stages.5.qi_status", {})
        blocking = [
            key
            for key, value in qi_status.items()
            if str(value).lower() in {"block", "refine", "fail", "partial"}
        ]
        events = get(state, "events.log", [])
        payload = {
            "status": "PASS",
            "project": str(project),
            "competition": state.get("competition"),
            "problem": state.get("problem"),
            "mode": state.get("mode"),
            "current_stage": stage,
            "current_stage_label": (
                stage_data.get("_label") if isinstance(stage_data, dict) else None
            ),
            "human_model_checkpoint": get(
                state, "stages.3.human_model_checkpoint.status"
            ),
            "qi_status": qi_status,
            "blocking_qis": blocking,
            "stability_verdict": get(state, "stages.6.stability_verdict"),
            "submission_ready_claim": get(
                state, "stages.9.submission_ready"
            ),
            "final_pdf_path": get(state, "stages.9.final_pdf_path"),
            "authoritative_result_candidates": [
                path
                for path in (
                    "results/authoritative_summary.json",
                    "results/optimized_results.json",
                    "results/final_results.json",
                )
                if (project / path).exists()
            ],
            "latest_event": events[-1] if events else None,
            "next_action": (
                "read only the current stage protocol and unresolved items"
            ),
        }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
