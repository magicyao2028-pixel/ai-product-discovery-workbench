from __future__ import annotations

from typing import Any


def compare_service_outputs(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare two offline service results without selecting or approving either one."""
    for label, payload in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0" or payload.get("status") != "ok":
            raise ValueError(f"{label} service output is invalid")
        if payload.get("governance", {}).get("external_action_executed") is not False:
            raise ValueError(f"{label} service output must declare no external action")
    baseline_review = baseline.get("review", {})
    candidate_review = candidate.get("review", {})
    if not isinstance(baseline_review, dict) or not isinstance(candidate_review, dict):
        raise ValueError("Service review output is missing")
    def projection(review: dict[str, Any]) -> dict[str, Any]:
        discovery = review.get("discovery", {})
        requirements = review.get("requirement_review", [])
        grounded = review.get("grounded_response", {})
        return {
            "status": review.get("status"),
            "selected_opportunity_id": discovery.get("selected_opportunity_id"),
            "included_requirement_ids": sorted(
                item.get("requirement_id") for item in requirements
                if isinstance(item, dict) and item.get("status") == "included"
            ),
            "citation_ids": sorted(grounded.get("citation_ids", [])) if isinstance(grounded, dict) else [],
        }

    baseline_projection = projection(baseline_review)
    candidate_projection = projection(candidate_review)
    fields = ("status", "selected_opportunity_id", "included_requirement_ids", "citation_ids")
    differences = []
    for field in fields:
        if baseline_projection[field] != candidate_projection[field]:
            differences.append({"field": field, "baseline": baseline_projection[field], "candidate": candidate_projection[field]})
    return {
        "schema_version": "1.0",
        "comparison_version": "0.7",
        "baseline_mode": baseline.get("request_receipt", {}).get("grounded_mode", "fallback"),
        "candidate_mode": candidate.get("request_receipt", {}).get("grounded_mode", "fallback"),
        "same_selected_opportunity": baseline_projection["selected_opportunity_id"] == candidate_projection["selected_opportunity_id"],
        "differences": differences,
        "difference_count": len(differences),
        "review_only": True,
        "approval_applied": False,
        "external_actions_executed": 0,
        "boundary": "This comparison exposes bounded output differences for human review; it does not mutate requirements, evidence or the PRD and does not approve a mode.",
    }
