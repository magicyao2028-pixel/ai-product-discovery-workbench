from __future__ import annotations

from datetime import date, timedelta
from typing import Any


_DECISIONS = {"keep_baseline", "investigate_difference", "reject_change"}
_OPEN_DECISIONS = {"investigate_difference"}


def reconcile_discovery_review_feedback(
    service_comparison: dict[str, Any],
    request_fingerprint: str,
    review_history: list[dict[str, Any]],
    feedback_replay: dict[str, Any],
    *,
    as_of_date: str,
    stale_after_days: int = 14,
) -> dict[str, Any]:
    """Reconcile accepted feedback and expose stale discovery reviews without mutation."""
    if isinstance(stale_after_days, bool) or not isinstance(stale_after_days, int) or stale_after_days < 1:
        raise ValueError("stale_after_days must be a positive integer")
    try:
        as_of = date.fromisoformat(as_of_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("as_of_date must be ISO format") from exc

    if not isinstance(service_comparison, dict) or service_comparison.get("review_only") is not True:
        raise ValueError("reconciliation requires a review-only service comparison")
    if service_comparison.get("approval_applied") is not False or service_comparison.get("external_actions_executed") != 0:
        raise ValueError("service comparison must remain non-executing")
    fingerprint = str(request_fingerprint).strip()
    if not fingerprint:
        raise ValueError("request fingerprint is required")

    if not isinstance(review_history, list) or not review_history:
        raise ValueError("review history must contain entries")
    reviews: dict[str, dict[str, Any]] = {}
    for entry in review_history:
        if not isinstance(entry, dict):
            raise ValueError("review-history entries must be objects")
        review_id = str(entry.get("review_id", "")).strip()
        decision = str(entry.get("decision", "")).strip()
        reviewer_role = str(entry.get("reviewer_role", "")).strip()
        if not review_id or review_id in reviews:
            raise ValueError("review-history IDs must be unique")
        if str(entry.get("request_fingerprint", "")).strip() != fingerprint:
            raise ValueError("review-history fingerprint must match the current request")
        if decision not in _DECISIONS or not reviewer_role or not str(entry.get("note", "")).strip():
            raise ValueError("review-history decision and reviewer context must be valid")
        if entry.get("approval_applied") is not False:
            raise ValueError("review history cannot apply approval")
        try:
            reviewed_on = date.fromisoformat(str(entry.get("reviewed_on", "")))
        except ValueError as exc:
            raise ValueError("review-history date must be ISO format") from exc
        if reviewed_on > as_of:
            raise ValueError("review history cannot be future-dated")
        reviews[review_id] = {
            "review_id": review_id,
            "decision": decision,
            "reviewer_role": reviewer_role,
            "reviewed_on": reviewed_on,
        }

    if not isinstance(feedback_replay, dict):
        raise ValueError("feedback replay must be an object")
    replayed = feedback_replay.get("replayed")
    excluded = feedback_replay.get("excluded")
    if not isinstance(replayed, list) or not isinstance(excluded, list):
        raise ValueError("feedback replay must expose replayed and excluded records")
    if (
        feedback_replay.get("approval_applied") is not False
        or feedback_replay.get("discovery_state_changed") is not False
        or feedback_replay.get("external_actions_executed") != 0
    ):
        raise ValueError("feedback replay must remain non-executing")
    if feedback_replay.get("record_count") != len(replayed) + len(excluded):
        raise ValueError("feedback replay counts must reconcile")

    seen_feedback: set[str] = set()
    reconciled: list[dict[str, Any]] = []
    for collection, expected_statuses in ((replayed, {"accepted"}), (excluded, {"pending", "rejected"})):
        for record in collection:
            feedback_id = str(record.get("feedback_id", "")).strip() if isinstance(record, dict) else ""
            review_id = str(record.get("review_id", "")).strip() if isinstance(record, dict) else ""
            status = str(record.get("status", "")).strip() if isinstance(record, dict) else ""
            if not feedback_id or feedback_id in seen_feedback:
                raise ValueError("feedback replay IDs must be unique")
            seen_feedback.add(feedback_id)
            if review_id not in reviews or status not in expected_statuses or record.get("passed") is not True:
                raise ValueError("feedback replay records must retain validated status and current review references")
            if status == "accepted":
                current = reviews[review_id]
                reconciled.append({
                    "feedback_id": feedback_id,
                    "review_id": review_id,
                    "decision": current["decision"],
                    "reviewer_role": current["reviewer_role"],
                    "closure_state": "open" if current["decision"] in _OPEN_DECISIONS else "closed",
                })

    cutoff = as_of - timedelta(days=stale_after_days)
    stale_reviews = [
        {
            "review_id": item["review_id"],
            "decision": item["decision"],
            "reviewer_role": item["reviewer_role"],
            "age_days": (as_of - item["reviewed_on"]).days,
        }
        for item in reviews.values()
        if item["decision"] in _OPEN_DECISIONS and item["reviewed_on"] <= cutoff
    ]
    stale_reviews.sort(key=lambda item: (-item["age_days"], item["review_id"]))
    reconciled.sort(key=lambda item: (item["review_id"], item["feedback_id"]))
    return {
        "schema_version": "1.0",
        "request_fingerprint": fingerprint,
        "as_of_date": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "reconciled_count": len(reconciled),
        "stale_review_count": len(stale_reviews),
        "reconciled_feedback": reconciled,
        "stale_reviews": stale_reviews,
        "approval_applied": False,
        "evidence_mutated": False,
        "requirements_mutated": False,
        "prd_mutated": False,
        "external_actions_executed": 0,
        "boundary": "Reconciliation exposes accepted feedback and stale investigation reviews for human follow-up; it does not approve a mode or mutate evidence, requirements or the PRD.",
    }


__all__ = ["reconcile_discovery_review_feedback"]
