from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .templates import TemplateProfile, TemplateValidationError


SOURCE_TYPES = {"real", "synthetic"}
CLASSIFICATIONS = {"defect", "requirement", "usability", "performance", "safety", "documentation"}
DISPOSITIONS = {"accepted_for_regression", "pending", "rejected"}


def load_template_feedback(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not str(payload.get("batch_id", "")).strip():
        raise ValueError("template feedback requires a batch_id")
    records = payload.get("records")
    if not isinstance(records, list) or not records or not all(isinstance(item, dict) for item in records):
        raise ValueError("template feedback records must be a non-empty list of objects")
    seen: set[str] = set()
    for record in records:
        feedback_id = str(record.get("feedback_id", "")).strip()
        required = (
            "source_type", "recorded_on", "classification", "disposition",
            "reviewer_alias", "rationale",
        )
        if not feedback_id or feedback_id in seen:
            raise ValueError("template feedback_id values must be present and unique")
        seen.add(feedback_id)
        if any(not str(record.get(field, "")).strip() for field in required):
            raise ValueError("template feedback metadata is incomplete")
        date.fromisoformat(str(record["recorded_on"]))
        if record["source_type"] not in SOURCE_TYPES:
            raise ValueError("template feedback source_type is unsupported")
        if record["classification"] not in CLASSIFICATIONS:
            raise ValueError("template feedback classification is unsupported")
        if record["disposition"] not in DISPOSITIONS:
            raise ValueError("template feedback disposition is unsupported")
        if record["disposition"] == "accepted_for_regression":
            if not isinstance(record.get("replay_profile"), dict):
                raise ValueError("accepted template feedback requires replay_profile")
            if not str(record.get("expected_error_code", "")).strip():
                raise ValueError("accepted template feedback requires expected_error_code")
            if not str(record.get("resolution", "")).strip():
                raise ValueError("accepted template feedback requires a resolution")
    return payload


def replay_template_feedback(path: Path) -> dict[str, Any]:
    payload = load_template_feedback(path)
    replayed, excluded = [], []
    for record in payload["records"]:
        if record["disposition"] != "accepted_for_regression":
            excluded.append({
                "feedback_id": record["feedback_id"],
                "disposition": record["disposition"],
                "reason": "Only accepted_for_regression records enter deterministic replay.",
            })
            continue
        actual_error_code = None
        try:
            TemplateProfile.from_mapping(record["replay_profile"])
        except TemplateValidationError as exc:
            actual_error_code = exc.code
        passed = actual_error_code == record["expected_error_code"]
        replayed.append({
            "feedback_id": record["feedback_id"],
            "source_type": record["source_type"],
            "classification": record["classification"],
            "expected_error_code": record["expected_error_code"],
            "actual_error_code": actual_error_code,
            "resolution": record["resolution"],
            "passed": passed,
            "external_action_executed": False,
            "prd_or_requirement_mutated": False,
        })
    return {
        "replay_version": "0.5",
        "batch_id": payload["batch_id"],
        "source_data": "synthetic",
        "summary": {
            "total_feedback": len(payload["records"]),
            "replayed": len(replayed),
            "passed": sum(item["passed"] for item in replayed),
            "failed": sum(not item["passed"] for item in replayed),
            "excluded": len(excluded),
        },
        "replayed": replayed,
        "excluded": excluded,
        "governance": {
            "feedback_changes_template_automatically": False,
            "external_action_executed": False,
            "prd_or_requirement_mutated": False,
            "synthetic_feedback_is_adoption_evidence": False,
        },
    }


def write_feedback_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Template Feedback Replay",
        "",
        f"- Result: **{report['summary']['passed']}/{report['summary']['replayed']} accepted cases passed**",
        "- Source: synthetic public fixture",
        "- Automatic PRD or requirement change: no",
        "",
        "| Feedback | Classification | Expected | Actual | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["replayed"]:
        lines.append(
            f"| {item['feedback_id']} | {item['classification']} | "
            f"{item['expected_error_code']} | {item['actual_error_code'] or 'none'} | "
            f"{'PASS' if item['passed'] else 'FAIL'} |"
        )
    lines.extend([
        "",
        "Pending or rejected feedback remains excluded from replay and cannot change template behavior.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
