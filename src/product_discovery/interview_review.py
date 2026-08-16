from __future__ import annotations

import re
from typing import Any

from .models import DiscoveryPacket


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}
UNIT_ALIASES = {
    "minute": "minute", "minutes": "minute", "min": "minute", "mins": "minute",
    "hour": "hour", "hours": "hour", "hr": "hour", "hrs": "hour",
    "day": "day", "days": "day", "week": "week", "weeks": "week",
    "month": "month", "months": "month", "percent": "percent", "percentage": "percent",
    "usd": "usd", "dollar": "usd", "dollars": "usd", "cny": "cny", "yuan": "cny",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was", "were",
}


def build_interview_claim_review(packet: DiscoveryPacket) -> dict[str, Any]:
    notes = {item.note_id: item for item in packet.interview_notes}
    raw_notes = [
        {
            "note_id": note.note_id,
            "observed_on": note.observed_on,
            "participant_role": note.participant_role,
            "synthetic": note.synthetic,
            "consent_for_analysis": note.consent_for_analysis,
            "excerpts": [
                {"excerpt_id": excerpt.excerpt_id, "text": excerpt.text}
                for excerpt in note.excerpts
            ],
        }
        for note in packet.interview_notes
    ]
    reviewed_claims: list[dict[str, Any]] = []
    proposed_evidence: list[dict[str, Any]] = []
    for claim in packet.interview_claims:
        note = notes[claim.note_id]
        excerpts_by_id = {item.excerpt_id: item for item in note.excerpts}
        source_text = " ".join(excerpts_by_id[item].text for item in claim.source_excerpt_ids)
        support = _support_check(claim.normalized_statement, source_text)
        if claim.claim_type == "interpretation":
            effective_status = "interpretation_requires_human_review"
        elif support["status"] != "traceable":
            effective_status = "blocked_unsupported_claim"
        elif claim.review_status == "approved":
            effective_status = "approved_observation"
        elif claim.review_status == "blocked":
            effective_status = "blocked_by_reviewer"
        else:
            effective_status = "pending_human_review"
        eligible = effective_status == "approved_observation"
        reviewed_claims.append({
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type,
            "normalized_statement": claim.normalized_statement,
            "source_note_id": claim.note_id,
            "source_excerpt_ids": list(claim.source_excerpt_ids),
            "source_excerpts": [excerpts_by_id[item].text for item in claim.source_excerpt_ids],
            "declared_review_status": claim.review_status,
            "reviewer_rationale": claim.reviewer_rationale,
            "support_check": support,
            "effective_status": effective_status,
            "eligible_for_proposed_evidence": eligible,
        })
        if eligible:
            proposed_evidence.append({
                "evidence_id": f"INT-EV-{claim.claim_id}",
                "evidence_type": "interview",
                "observed_on": note.observed_on,
                "summary": claim.normalized_statement,
                "reliability": "indicative",
                "synthetic": True,
                "provenance": {
                    "source_note_id": claim.note_id,
                    "source_excerpt_ids": list(claim.source_excerpt_ids),
                    "source_claim_id": claim.claim_id,
                },
                "register_status": "proposed_not_merged",
            })
    observations = [item for item in reviewed_claims if item["claim_type"] == "observation"]
    interpretations = [item for item in reviewed_claims if item["claim_type"] == "interpretation"]
    return {
        "raw_notes": raw_notes,
        "normalized_observations": observations,
        "normalized_interpretations": interpretations,
        "proposed_evidence_records": proposed_evidence,
        "summary": {
            "notes": len(raw_notes),
            "claims": len(reviewed_claims),
            "observations": len(observations),
            "interpretations": len(interpretations),
            "proposed_evidence_records": len(proposed_evidence),
            "blocked_or_pending": sum(not item["eligible_for_proposed_evidence"] for item in reviewed_claims),
        },
        "governance": {
            "human_review_required": True,
            "existing_evidence_register_mutated": False,
            "prd_or_requirement_mutated": False,
            "synthetic_public_data": True,
        },
    }


def _support_check(statement: str, source_text: str) -> dict[str, Any]:
    claim_numbers = _numbers(statement)
    source_numbers = _numbers(source_text)
    unsupported_numbers = sorted(claim_numbers - source_numbers)
    claim_number_units = _number_unit_pairs(statement)
    source_number_units = _number_unit_pairs(source_text)
    unsupported_number_units = sorted(claim_number_units - source_number_units)
    claim_tokens = _meaningful_tokens(statement)
    source_tokens = _meaningful_tokens(source_text)
    overlap = claim_tokens & source_tokens
    overlap_ratio = round(len(overlap) / max(len(claim_tokens), 1), 2)
    if unsupported_numbers:
        status = "unsupported_numeric_claim"
    elif unsupported_number_units:
        status = "unsupported_numeric_unit_claim"
    elif overlap_ratio < 0.3:
        status = "insufficient_excerpt_support"
    else:
        status = "traceable"
    return {
        "status": status,
        "lexical_overlap_ratio": overlap_ratio,
        "overlap_tokens": sorted(overlap),
        "unsupported_numbers": unsupported_numbers,
        "unsupported_number_units": [
            {"number": number, "unit": unit} for number, unit in unsupported_number_units
        ],
    }


def _meaningful_tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.casefold()) if token not in STOPWORDS}


def _numbers(value: str) -> set[str]:
    tokens = TOKEN_PATTERN.findall(value.casefold())
    return set(NUMBER_PATTERN.findall(value)) | {NUMBER_WORDS[token] for token in tokens if token in NUMBER_WORDS}


def _number_unit_pairs(value: str) -> set[tuple[str, str]]:
    tokens = TOKEN_PATTERN.findall(value.casefold().replace("%", " percent"))
    pairs: set[tuple[str, str]] = set()
    for index, token in enumerate(tokens):
        number = NUMBER_WORDS.get(token, token if NUMBER_PATTERN.fullmatch(token) else None)
        if number is None:
            continue
        for candidate in tokens[index + 1:index + 4]:
            if NUMBER_WORDS.get(candidate) is not None or NUMBER_PATTERN.fullmatch(candidate):
                break
            unit = UNIT_ALIASES.get(candidate)
            if unit is not None:
                pairs.add((number, unit))
                break
    return pairs
