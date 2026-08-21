from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import DiscoveryWorkbench
from .models import load_packet
from .sensitivity import load_priority_scenarios
from .template_feedback import replay_template_feedback
from .templates import TemplateValidationError, load_template_profile


def run_trial(root: Path) -> dict[str, Any]:
    result = DiscoveryWorkbench().build(
        load_packet(root / "data" / "sample_discovery.json"),
        priority_scenarios=load_priority_scenarios(root / "data" / "sample_priority_scenarios.json"),
        template_profile=load_template_profile(root / "data" / "sample_report_template.json"),
    )
    feedback = replay_template_feedback(root / "data" / "sample_template_feedback.json")
    failure_code = None
    try:
        load_template_profile(root / "data" / "invalid_template_missing_governance.json")
    except TemplateValidationError as exc:
        failure_code = exc.code
    evidence_index = json.loads((root / "evidence" / "evidence_index.json").read_text(encoding="utf-8"))
    evidence_paths_valid = _evidence_paths_exist(root, evidence_index)
    template_keys = [item["section_key"] for item in result["report_template"]["sections"]]
    checks = {
        "core_review_ready": result["status"] == "ready_for_human_review",
        "expected_opportunity_selected": result["discovery"]["selected_opportunity_id"] == "OPP-001",
        "all_template_sections_present": set(template_keys) == {
            "decision_summary", "evidence_review", "requirement_review", "prototype_flow", "governance",
        },
        "template_does_not_mutate_prd": not any(
            result["report_template"]["governance"][key]
            for key in ("source_evidence_mutated", "current_prd_mutated", "requirements_mutated")
        ),
        "missing_governance_template_blocked": failure_code == "missing_required_template_section",
        "accepted_feedback_replayed": feedback["summary"]["replayed"] == 1
        and feedback["summary"]["passed"] == 1,
        "pending_feedback_excluded": feedback["summary"]["excluded"] == 1,
        "evidence_index_has_seven_claims": len(evidence_index.get("claims", [])) == 7,
        "evidence_paths_exist": evidence_paths_valid,
        "no_external_action": result["governance"]["external_action_executed"] is False
        and feedback["governance"]["external_action_executed"] is False,
    }
    return {
        "trial_version": "0.5",
        "source_data": "synthetic",
        "overall_passed": all(checks.values()),
        "core_passed": all(checks[key] for key in (
            "core_review_ready", "expected_opportunity_selected", "all_template_sections_present",
            "template_does_not_mutate_prd", "missing_governance_template_blocked",
        )),
        "checks": checks,
        "observed": {
            "selected_opportunity_id": result["discovery"]["selected_opportunity_id"],
            "included_requirement_ids": [
                item["requirement_id"]
                for item in result["requirement_review"]
                if item["status"] == "included"
            ],
            "template_id": result["report_template"]["template_id"],
            "template_sections": template_keys,
            "failure_code": failure_code,
            "feedback_passed": feedback["summary"]["passed"],
            "feedback_excluded": feedback["summary"]["excluded"],
            "evidence_claims": len(evidence_index.get("claims", [])),
            "external_actions": 0,
        },
        "limitations": [
            "All discovery, feedback and trial inputs are synthetic.",
            "Template validation proves structural governance, not product-market demand or design quality.",
            "The trial performs no model call, external write, deployment or requirement approval.",
        ],
    }


def _evidence_paths_exist(root: Path, evidence_index: dict[str, Any]) -> bool:
    claims = evidence_index.get("claims")
    if not isinstance(claims, list) or not claims:
        return False
    for claim in claims:
        paths = claim.get("evidence_paths") if isinstance(claim, dict) else None
        if not isinstance(paths, list) or not paths:
            return False
        for raw_path in paths:
            if not isinstance(raw_path, str):
                return False
            candidate = Path(raw_path)
            if candidate.is_absolute() or ".." in candidate.parts or not (root / candidate).exists():
                return False
    return True


def write_trial_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Trial Readiness Report",
        "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**",
        f"- Core path: **{'PASS' if report['core_passed'] else 'FAIL'}**",
        "- Inputs: synthetic",
        "- External actions: 0",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in report["checks"].items()
    )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
