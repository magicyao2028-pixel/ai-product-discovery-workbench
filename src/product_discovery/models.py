from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


EVIDENCE_TYPES = {"interview", "workflow_audit", "support_log", "stakeholder_request"}
FEEDBACK_EFFECTS = {"supports", "challenges", "no_effect"}
INTERVIEW_CLAIM_TYPES = {"observation", "interpretation"}
INTERVIEW_REVIEW_STATUSES = {"approved", "blocked", "pending_human_review"}


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    observed_on: str
    summary: str
    synthetic: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Evidence":
        item = cls(
            evidence_id=_required(value, "evidence_id"),
            evidence_type=_required(value, "evidence_type"),
            observed_on=_required(value, "observed_on"),
            summary=_required(value, "summary"),
            synthetic=value.get("synthetic") is True,
        )
        if item.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of: {', '.join(sorted(EVIDENCE_TYPES))}")
        _iso_date(item.observed_on, "observed_on")
        if not item.synthetic:
            raise ValueError("public portfolio evidence must be explicitly synthetic")
        return item


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    title: str
    problem_statement: str
    user_segment: str
    evidence_ids: tuple[str, ...]
    impact: int
    confidence: float
    effort: int

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Opportunity":
        item = cls(
            opportunity_id=_required(value, "opportunity_id"),
            title=_required(value, "title"),
            problem_statement=_required(value, "problem_statement"),
            user_segment=_required(value, "user_segment"),
            evidence_ids=_strings(value.get("evidence_ids"), "evidence_ids"),
            impact=int(value.get("impact", 0)),
            confidence=float(value.get("confidence", 0)),
            effort=int(value.get("effort", 0)),
        )
        if not 1 <= item.impact <= 5 or not 1 <= item.effort <= 5:
            raise ValueError("impact and effort must be between 1 and 5")
        if not 0 <= item.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return item


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    version: str
    opportunity_id: str
    title: str
    user_story: str
    acceptance_criteria: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    external_action: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Requirement":
        item = cls(
            requirement_id=_required(value, "requirement_id"),
            version=_required(value, "version"),
            opportunity_id=_required(value, "opportunity_id"),
            title=_required(value, "title"),
            user_story=_required(value, "user_story"),
            acceptance_criteria=_strings(value.get("acceptance_criteria"), "acceptance_criteria"),
            evidence_ids=_strings(value.get("evidence_ids"), "evidence_ids"),
            external_action=value.get("external_action") is True,
        )
        parts = item.version.split(".")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("requirement version must use MAJOR.MINOR")
        return item


@dataclass(frozen=True)
class Feedback:
    feedback_id: str
    requirement_id: str
    observed_on: str
    effect: str
    summary: str
    evidence_ids: tuple[str, ...]
    synthetic: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Feedback":
        item = cls(
            feedback_id=_required(value, "feedback_id"),
            requirement_id=_required(value, "requirement_id"),
            observed_on=_required(value, "observed_on"),
            effect=_required(value, "effect"),
            summary=_required(value, "summary"),
            evidence_ids=_strings(value.get("evidence_ids"), "evidence_ids"),
            synthetic=value.get("synthetic") is True,
        )
        _iso_date(item.observed_on, "observed_on")
        if item.effect not in FEEDBACK_EFFECTS:
            raise ValueError(f"effect must be one of: {', '.join(sorted(FEEDBACK_EFFECTS))}")
        if not item.synthetic:
            raise ValueError("public portfolio feedback must be explicitly synthetic")
        return item


@dataclass(frozen=True)
class InterviewExcerpt:
    excerpt_id: str
    text: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "InterviewExcerpt":
        return cls(
            excerpt_id=_required(value, "excerpt_id"),
            text=_required_raw(value, "text"),
        )


@dataclass(frozen=True)
class InterviewNote:
    note_id: str
    observed_on: str
    participant_role: str
    synthetic: bool
    consent_for_analysis: bool
    excerpts: tuple[InterviewExcerpt, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "InterviewNote":
        item = cls(
            note_id=_required(value, "note_id"),
            observed_on=_required(value, "observed_on"),
            participant_role=_required(value, "participant_role"),
            synthetic=value.get("synthetic") is True,
            consent_for_analysis=value.get("consent_for_analysis") is True,
            excerpts=_objects(value.get("excerpts"), "excerpts", InterviewExcerpt.from_mapping),
        )
        _iso_date(item.observed_on, "interview note observed_on")
        _unique([entry.excerpt_id for entry in item.excerpts], "interview excerpt_id")
        if not item.synthetic:
            raise ValueError("public interview notes must be explicitly synthetic")
        if not item.consent_for_analysis:
            raise ValueError("interview consent_for_analysis must be true")
        return item


@dataclass(frozen=True)
class InterviewClaim:
    claim_id: str
    note_id: str
    source_excerpt_ids: tuple[str, ...]
    claim_type: str
    normalized_statement: str
    review_status: str
    reviewer_rationale: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "InterviewClaim":
        item = cls(
            claim_id=_required(value, "claim_id"),
            note_id=_required(value, "note_id"),
            source_excerpt_ids=_strings(value.get("source_excerpt_ids"), "source_excerpt_ids"),
            claim_type=_required(value, "claim_type"),
            normalized_statement=" ".join(_required(value, "normalized_statement").split()),
            review_status=_required(value, "review_status"),
            reviewer_rationale=str(value.get("reviewer_rationale", "")).strip(),
        )
        if item.claim_type not in INTERVIEW_CLAIM_TYPES:
            raise ValueError(f"claim_type must be one of: {', '.join(sorted(INTERVIEW_CLAIM_TYPES))}")
        if item.review_status not in INTERVIEW_REVIEW_STATUSES:
            raise ValueError(
                f"review_status must be one of: {', '.join(sorted(INTERVIEW_REVIEW_STATUSES))}"
            )
        if item.review_status in {"approved", "blocked"} and not item.reviewer_rationale:
            raise ValueError("approved or blocked interview claims require reviewer_rationale")
        return item


@dataclass(frozen=True)
class PrototypeScreen:
    screen_id: str
    title: str
    purpose: str
    fields: tuple[str, ...]
    primary_action: str
    requirement_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "PrototypeScreen":
        return cls(
            screen_id=_required(value, "screen_id"),
            title=_required(value, "title"),
            purpose=_required(value, "purpose"),
            fields=_strings(value.get("fields"), "fields", allow_empty=True),
            primary_action=_required(value, "primary_action"),
            requirement_ids=_strings(value.get("requirement_ids"), "requirement_ids"),
        )


@dataclass(frozen=True)
class DiscoveryPacket:
    project_id: str
    project_name: str
    analysis_date: str
    decision_owner: str
    business_context: str
    goals: tuple[str, ...]
    non_goals: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    opportunities: tuple[Opportunity, ...]
    requirements: tuple[Requirement, ...]
    feedback: tuple[Feedback, ...]
    interview_notes: tuple[InterviewNote, ...]
    interview_claims: tuple[InterviewClaim, ...]
    prototype_screens: tuple[PrototypeScreen, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "DiscoveryPacket":
        item = cls(
            project_id=_required(value, "project_id"),
            project_name=_required(value, "project_name"),
            analysis_date=_required(value, "analysis_date"),
            decision_owner=_required(value, "decision_owner"),
            business_context=_required(value, "business_context"),
            goals=_strings(value.get("goals"), "goals"),
            non_goals=_strings(value.get("non_goals"), "non_goals"),
            evidence=_objects(value.get("evidence"), "evidence", Evidence.from_mapping),
            opportunities=_objects(value.get("opportunities"), "opportunities", Opportunity.from_mapping),
            requirements=_objects(value.get("requirements"), "requirements", Requirement.from_mapping),
            feedback=_objects(value.get("feedback"), "feedback", Feedback.from_mapping),
            interview_notes=_objects(
                value.get("interview_notes"), "interview_notes", InterviewNote.from_mapping
            ),
            interview_claims=_objects(
                value.get("interview_claims"), "interview_claims", InterviewClaim.from_mapping
            ),
            prototype_screens=_objects(
                value.get("prototype_screens"), "prototype_screens", PrototypeScreen.from_mapping
            ),
        )
        _iso_date(item.analysis_date, "analysis_date")
        _validate_relationships(item)
        return item


def load_packet(path: Path) -> DiscoveryPacket:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid discovery JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Discovery file must contain a JSON object")
    return DiscoveryPacket.from_mapping(payload)


def _required(value: dict[str, Any], field: str) -> str:
    result = str(value.get(field, "")).strip()
    if not result:
        raise ValueError(f"{field} must not be blank")
    return result


def _required_raw(value: dict[str, Any], field: str) -> str:
    result = str(value.get(field, ""))
    if not result.strip():
        raise ValueError(f"{field} must not be blank")
    return result


def _strings(value: Any, field: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(entry, str) for entry in value):
        raise ValueError(f"{field} must be a list of strings")
    result = tuple(entry.strip() for entry in value if entry.strip())
    if not result and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    return result


def _objects(value: Any, field: str, factory: Any) -> tuple[Any, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(entry, dict) for entry in value):
        raise ValueError(f"{field} must be a non-empty list of objects")
    return tuple(factory(entry) for entry in value)


def _iso_date(value: str, field: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD") from exc


def _unique(values: list[str], field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field} values must be unique")


def _validate_relationships(item: DiscoveryPacket) -> None:
    evidence_ids = [entry.evidence_id for entry in item.evidence]
    opportunity_ids = [entry.opportunity_id for entry in item.opportunities]
    requirement_ids = [entry.requirement_id for entry in item.requirements]
    feedback_ids = [entry.feedback_id for entry in item.feedback]
    note_ids = [entry.note_id for entry in item.interview_notes]
    claim_ids = [entry.claim_id for entry in item.interview_claims]
    screen_ids = [entry.screen_id for entry in item.prototype_screens]
    _unique(evidence_ids, "evidence_id")
    _unique(opportunity_ids, "opportunity_id")
    _unique(requirement_ids, "requirement_id")
    _unique(feedback_ids, "feedback_id")
    _unique(note_ids, "interview note_id")
    _unique(claim_ids, "interview claim_id")
    _unique(screen_ids, "screen_id")
    if any(entry.observed_on > item.analysis_date for entry in item.evidence):
        raise ValueError("evidence observed_on must not be after analysis_date")
    if any(entry.observed_on > item.analysis_date for entry in item.feedback):
        raise ValueError("feedback observed_on must not be after analysis_date")
    if any(entry.observed_on > item.analysis_date for entry in item.interview_notes):
        raise ValueError("interview note observed_on must not be after analysis_date")
    if any(set(entry.evidence_ids) - set(evidence_ids) for entry in item.opportunities):
        raise ValueError("every opportunity evidence_id must reference declared evidence")
    if any(entry.opportunity_id not in opportunity_ids for entry in item.requirements):
        raise ValueError("every requirement must reference a declared opportunity")
    if any(set(entry.evidence_ids) - set(evidence_ids) for entry in item.requirements):
        raise ValueError("every requirement evidence_id must reference declared evidence")
    if any(entry.requirement_id not in requirement_ids for entry in item.feedback):
        raise ValueError("every feedback requirement_id must reference a declared requirement")
    if any(set(entry.evidence_ids) - set(evidence_ids) for entry in item.feedback):
        raise ValueError("every feedback evidence_id must reference declared evidence")
    if any(set(screen.requirement_ids) - set(requirement_ids) for screen in item.prototype_screens):
        raise ValueError("every prototype requirement_id must reference a declared requirement")
    note_by_id = {entry.note_id: entry for entry in item.interview_notes}
    for claim in item.interview_claims:
        if claim.note_id not in note_by_id:
            raise ValueError("every interview claim note_id must reference a declared note")
        excerpt_ids = {entry.excerpt_id for entry in note_by_id[claim.note_id].excerpts}
        if set(claim.source_excerpt_ids) - excerpt_ids:
            raise ValueError("every interview claim excerpt must belong to its source note")
