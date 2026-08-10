from __future__ import annotations

from typing import Any

from .models import DiscoveryPacket, Opportunity, Requirement


class DiscoveryWorkbench:
    """Compiles synthetic discovery evidence into a reviewable PRD package."""

    def build(self, packet: DiscoveryPacket) -> dict[str, Any]:
        evidence_by_id = {item.evidence_id: item for item in packet.evidence}
        opportunity_by_id = {item.opportunity_id: item for item in packet.opportunities}
        ranked = [self._score_opportunity(item, evidence_by_id) for item in packet.opportunities]
        ranked.sort(key=lambda item: (-item["score"], item["opportunity_id"]))
        eligible = [item for item in ranked if item["eligible"]]
        selected_id = eligible[0]["opportunity_id"] if eligible else None
        requirement_reviews = [
            self._review_requirement(item, selected_id, evidence_by_id, opportunity_by_id)
            for item in packet.requirements
        ]
        included = [item for item in requirement_reviews if item["status"] == "included"]
        selected = next(
            (item for item in packet.opportunities if item.opportunity_id == selected_id), None
        )
        status = "ready_for_human_review" if selected and included else "blocked_insufficient_evidence"
        return {
            "project_id": packet.project_id,
            "project_name": packet.project_name,
            "analysis_date": packet.analysis_date,
            "status": status,
            "discovery": {
                "business_context": packet.business_context,
                "evidence_count": len(packet.evidence),
                "opportunity_ranking": ranked,
                "selected_opportunity_id": selected_id,
            },
            "prd": self._build_prd(packet, selected, included),
            "requirement_review": requirement_reviews,
            "traceability_matrix": self._traceability(included, evidence_by_id),
            "low_fidelity_prototype": self._prototype(packet, {item["requirement_id"] for item in included}),
            "governance": {
                "decision_owner": packet.decision_owner,
                "human_approval_required": True,
                "external_action_executed": False,
                "production_release_executed": False,
            },
            "trace": [
                {"step": "validate_discovery_packet", "status": "completed"},
                {"step": "rank_opportunities", "status": "completed"},
                {"step": "gate_requirements", "status": "completed"},
                {"step": "compile_prd", "status": "completed" if selected and included else "blocked"},
                {"step": "map_low_fidelity_flow", "status": "completed"},
                {"step": "request_human_approval", "status": "required"},
            ],
            "limitations": [
                "All discovery evidence and product details are synthetic.",
                "Scores are prioritization aids, not validated market demand or commercial outcomes.",
                "The low-fidelity flow communicates structure and behavior, not final visual design.",
                "No LLM call, production deployment or external business action is implemented.",
            ],
        }

    @staticmethod
    def _score_opportunity(opportunity: Opportunity, evidence_by_id: dict[str, Any]) -> dict[str, Any]:
        evidence_types = sorted({evidence_by_id[item].evidence_type for item in opportunity.evidence_ids})
        score = round(opportunity.impact * opportunity.confidence * 10 / opportunity.effort, 2)
        reasons = []
        if len(opportunity.evidence_ids) < 2:
            reasons.append("fewer_than_two_evidence_items")
        if len(evidence_types) < 2:
            reasons.append("single_evidence_type")
        if opportunity.confidence < 0.5:
            reasons.append("confidence_below_threshold")
        return {
            "opportunity_id": opportunity.opportunity_id,
            "title": opportunity.title,
            "score": score,
            "formula": "impact * confidence * 10 / effort",
            "evidence_ids": list(opportunity.evidence_ids),
            "evidence_types": evidence_types,
            "eligible": not reasons,
            "exclusion_reasons": reasons,
        }

    @staticmethod
    def _review_requirement(
        requirement: Requirement,
        selected_opportunity_id: str | None,
        evidence_by_id: dict[str, Any],
        opportunity_by_id: dict[str, Opportunity],
    ) -> dict[str, Any]:
        reasons = []
        if requirement.opportunity_id != selected_opportunity_id:
            reasons.append("not_linked_to_selected_opportunity")
        if len(set(requirement.evidence_ids)) < 2:
            reasons.append("insufficient_evidence")
        if not set(requirement.evidence_ids).issubset(
            set(opportunity_by_id[requirement.opportunity_id].evidence_ids)
        ):
            reasons.append("evidence_not_linked_to_opportunity")
        if requirement.external_action:
            reasons.append("external_action_out_of_scope")
        return {
            "requirement_id": requirement.requirement_id,
            "title": requirement.title,
            "opportunity_id": requirement.opportunity_id,
            "status": "included" if not reasons else "excluded",
            "exclusion_reasons": reasons,
            "user_story": requirement.user_story,
            "acceptance_criteria": list(requirement.acceptance_criteria),
            "evidence_ids": list(requirement.evidence_ids),
            "evidence_types": sorted({evidence_by_id[item].evidence_type for item in requirement.evidence_ids}),
            "external_action": requirement.external_action,
        }

    @staticmethod
    def _build_prd(
        packet: DiscoveryPacket,
        selected: Opportunity | None,
        requirements: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if selected is None or not requirements:
            return None
        return {
            "title": packet.project_name,
            "problem_statement": selected.problem_statement,
            "primary_user": selected.user_segment,
            "goals": list(packet.goals),
            "non_goals": list(packet.non_goals),
            "requirements": requirements,
            "release_gate": "Human owner approves evidence, scope and acceptance criteria.",
        }

    @staticmethod
    def _traceability(
        requirements: list[dict[str, Any]], evidence_by_id: dict[str, Any]
    ) -> list[dict[str, Any]]:
        rows = []
        for requirement in requirements:
            for evidence_id in requirement["evidence_ids"]:
                evidence = evidence_by_id[evidence_id]
                rows.append({
                    "evidence_id": evidence_id,
                    "evidence_type": evidence.evidence_type,
                    "opportunity_id": requirement["opportunity_id"],
                    "requirement_id": requirement["requirement_id"],
                    "acceptance_criteria": requirement["acceptance_criteria"],
                })
        return rows

    @staticmethod
    def _prototype(packet: DiscoveryPacket, included_ids: set[str]) -> dict[str, Any]:
        screens = []
        excluded = []
        for screen in packet.prototype_screens:
            if set(screen.requirement_ids).issubset(included_ids):
                screens.append({
                    "screen_id": screen.screen_id,
                    "title": screen.title,
                    "purpose": screen.purpose,
                    "fields": list(screen.fields),
                    "primary_action": screen.primary_action,
                    "requirement_ids": list(screen.requirement_ids),
                })
            else:
                excluded.append({
                    "screen_id": screen.screen_id,
                    "reason": "references_excluded_requirement",
                })
        return {
            "fidelity": "low",
            "screens": screens,
            "excluded_screens": excluded,
            "note": "Structure and interaction intent only; no final visual specification.",
        }
