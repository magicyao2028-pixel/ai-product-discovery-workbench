from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


_DECISIONS = {"keep_baseline", "investigate_difference", "reject_change"}


def summarize_review_history(
    service_comparison: dict[str, Any],
    request_fingerprint: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize synthetic reviewer decisions without approving or mutating a mode."""
    if not isinstance(service_comparison, dict) or service_comparison.get("review_only") is not True:
        raise ValueError("Review history requires a review-only service comparison")
    if service_comparison.get("approval_applied") is not False or service_comparison.get("external_actions_executed") != 0:
        raise ValueError("Review history must remain non-executing")
    fingerprint = str(request_fingerprint).strip()
    if not fingerprint:
        raise ValueError("Review history requires a request fingerprint")
    if not isinstance(history, list) or not history:
        raise ValueError("Review history must contain entries")

    seen: set[str] = set()
    dates: list[date] = []
    decisions: Counter[str] = Counter()
    for entry in history:
        if not isinstance(entry, dict):
            raise ValueError("Every review-history entry must be an object")
        required = {"review_id", "request_fingerprint", "reviewed_on", "decision", "reviewer_role", "note", "approval_applied"}
        if required.difference(entry):
            raise ValueError("Review-history entry is incomplete")
        review_id = str(entry["review_id"]).strip()
        if not review_id or review_id in seen:
            raise ValueError("Review-history IDs must be unique")
        seen.add(review_id)
        if str(entry["request_fingerprint"]).strip() != fingerprint:
            raise ValueError("Review-history fingerprint does not match the current request")
        try:
            reviewed_on = date.fromisoformat(str(entry["reviewed_on"]))
        except ValueError as exc:
            raise ValueError("Review-history date must be ISO format") from exc
        if dates and reviewed_on < dates[-1]:
            raise ValueError("Review-history dates must be chronological")
        dates.append(reviewed_on)
        decision = str(entry["decision"]).strip()
        if decision not in _DECISIONS or not str(entry["reviewer_role"]).strip() or not str(entry["note"]).strip():
            raise ValueError("Review-history decision or reviewer note is invalid")
        if entry["approval_applied"] is not False:
            raise ValueError("Review-history entries cannot apply approval")
        decisions[decision] += 1

    return {
        "schema_version": "1.0",
        "entry_count": len(history),
        "decision_counts": dict(sorted(decisions.items())),
        "latest_reviewed_on": dates[-1].isoformat(),
        "request_fingerprint": fingerprint,
        "approval_applied": False,
        "external_actions_executed": 0,
        "boundary": "Review history records synthetic human decisions for service-output learning; it does not approve a mode or mutate evidence, requirements or the PRD.",
    }
