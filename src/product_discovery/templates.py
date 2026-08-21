from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_SECTION_KEYS = {
    "decision_summary",
    "evidence_review",
    "requirement_review",
    "prototype_flow",
    "governance",
}


class TemplateValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TemplateSection:
    section_key: str
    title: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "TemplateSection":
        section_key = str(value.get("section_key", "")).strip()
        title = str(value.get("title", "")).strip()
        if not section_key or not title:
            raise TemplateValidationError(
                "blank_template_section",
                "template section_key and title must not be blank",
            )
        if section_key not in REQUIRED_SECTION_KEYS:
            raise TemplateValidationError(
                "unknown_template_section",
                f"unsupported template section: {section_key}",
            )
        return cls(section_key=section_key, title=title)


@dataclass(frozen=True)
class TemplateProfile:
    template_id: str
    version: str
    sections: tuple[TemplateSection, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "TemplateProfile":
        if not isinstance(value, dict):
            raise TemplateValidationError("invalid_template_object", "template must be an object")
        template_id = str(value.get("template_id", "")).strip()
        version = str(value.get("version", "")).strip()
        raw_sections = value.get("sections")
        if not template_id or not version:
            raise TemplateValidationError(
                "blank_template_identity",
                "template_id and version must not be blank",
            )
        parts = version.split(".")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise TemplateValidationError(
                "invalid_template_version",
                "template version must use MAJOR.MINOR",
            )
        if not isinstance(raw_sections, list) or not raw_sections or not all(
            isinstance(item, dict) for item in raw_sections
        ):
            raise TemplateValidationError(
                "invalid_template_sections",
                "template sections must be a non-empty list of objects",
            )
        sections = tuple(TemplateSection.from_mapping(item) for item in raw_sections)
        section_keys = [item.section_key for item in sections]
        if len(section_keys) != len(set(section_keys)):
            raise TemplateValidationError(
                "duplicate_template_section",
                "template section_key values must be unique",
            )
        missing = sorted(REQUIRED_SECTION_KEYS - set(section_keys))
        if missing:
            raise TemplateValidationError(
                "missing_required_template_section",
                f"template is missing required sections: {', '.join(missing)}",
            )
        return cls(template_id=template_id, version=version, sections=sections)


DEFAULT_TEMPLATE = TemplateProfile.from_mapping({
    "template_id": "reviewable-discovery-v1",
    "version": "1.0",
    "sections": [
        {"section_key": "decision_summary", "title": "Decision summary"},
        {"section_key": "evidence_review", "title": "Evidence review"},
        {"section_key": "requirement_review", "title": "Requirement review"},
        {"section_key": "prototype_flow", "title": "Low-fidelity flow"},
        {"section_key": "governance", "title": "Governance and approval"},
    ],
})


def load_template_profile(path: Path) -> TemplateProfile:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateValidationError("invalid_template_json", exc.msg) from exc
    return TemplateProfile.from_mapping(payload)


def compile_template_package(result: dict[str, Any], profile: TemplateProfile) -> dict[str, Any]:
    section_content = {
        "decision_summary": {
            "status": result["status"],
            "selected_opportunity_id": result["discovery"]["selected_opportunity_id"],
        },
        "evidence_review": {
            "evidence_ids": sorted({
                source
                for item in result["discovery"]["opportunity_ranking"]
                for source in item["evidence_ids"]
            }),
            "proposed_interview_evidence": result["interview_claim_review"]["summary"][
                "proposed_evidence_records"
            ],
        },
        "requirement_review": {
            "included_requirement_ids": [
                item["requirement_id"]
                for item in result["requirement_review"]
                if item["status"] == "included"
            ],
            "excluded_requirement_ids": [
                item["requirement_id"]
                for item in result["requirement_review"]
                if item["status"] == "excluded"
            ],
        },
        "prototype_flow": {
            "included_screen_ids": [
                item["screen_id"] for item in result["low_fidelity_prototype"]["screens"]
            ],
            "excluded_screen_ids": [
                item["screen_id"]
                for item in result["low_fidelity_prototype"]["excluded_screens"]
            ],
        },
        "governance": {
            "decision_owner": result["governance"]["decision_owner"],
            "human_approval_required": result["governance"]["human_approval_required"],
            "external_action_executed": result["governance"]["external_action_executed"],
            "requirement_change_executed": result["governance"]["requirement_change_executed"],
        },
    }
    return {
        "template_id": profile.template_id,
        "template_version": profile.version,
        "sections": [
            {
                "section_key": section.section_key,
                "title": section.title,
                "content": section_content[section.section_key],
            }
            for section in profile.sections
        ],
        "governance": {
            "source_evidence_mutated": False,
            "current_prd_mutated": False,
            "requirements_mutated": False,
            "template_selects_layout_only": True,
        },
    }
