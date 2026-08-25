from __future__ import annotations

from typing import Any


GROUNDED_MODES = {"fallback", "local_extractive"}


def build_grounded_summary(result: dict[str, Any], mode: str = "fallback") -> dict[str, Any]:
    """Build a cited local response; no remote model call or external write is made."""
    if mode not in GROUNDED_MODES:
        raise ValueError("grounded_mode must be fallback or local_extractive")
    selected_id = result.get("discovery", {}).get("selected_opportunity_id")
    selected = next(
        (item for item in result.get("discovery", {}).get("opportunity_ranking", [])
         if item.get("opportunity_id") == selected_id),
        None,
    )
    if not selected:
        return _blocked(mode, "No evidence-eligible opportunity is available for a grounded response.")
    evidence_register = {
        item["evidence_id"]: item
        for item in result.get("discovery", {}).get("evidence_register", [])
        if isinstance(item, dict) and item.get("evidence_id")
    }
    selected_evidence_ids = list(selected.get("evidence_ids", []))
    included = [item for item in result.get("requirement_review", []) if item.get("status") == "included"]
    requirement_ids = [item["requirement_id"] for item in included]
    citation_ids = sorted(set(selected_evidence_ids))
    if not citation_ids or not set(citation_ids).issubset(evidence_register):
        return _blocked(mode, "Grounded response blocked because its citations are missing from the evidence register.")
    text = f"{selected['title']}: {selected.get('problem_statement', '').strip()}"
    if mode == "local_extractive":
        excerpts = [evidence_register[evidence_id]["summary"] for evidence_id in citation_ids]
        text += " Supporting evidence: " + " ".join(excerpts)
    else:
        text += " Evidence-eligible requirements: " + ", ".join(requirement_ids) + "."
    return {
        "mode": mode,
        "adapter": "deterministic-fallback" if mode == "fallback" else "local-extractive",
        "text": text,
        "citation_ids": citation_ids,
        "requirement_ids": requirement_ids,
        "grounded": True,
        "model_call_executed": False,
        "external_action_executed": False,
        "human_approval_required": True,
        "boundary": "This is a cited local summary of synthetic evidence, not semantic model output or a production recommendation.",
    }


def _blocked(mode: str, reason: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "adapter": "deterministic-fallback",
        "text": "",
        "citation_ids": [],
        "requirement_ids": [],
        "grounded": False,
        "blocked_reason": reason,
        "model_call_executed": False,
        "external_action_executed": False,
        "human_approval_required": True,
    }
