from __future__ import annotations

from typing import Any


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Product Discovery Review",
        "",
        f"**Project:** {result['project_name']}",
        f"**Analysis date:** {result['analysis_date']}",
        f"**Status:** {result['status']}",
        "",
        "## Opportunity ranking",
        "",
    ]
    for item in result["discovery"]["opportunity_ranking"]:
        eligibility = "eligible" if item["eligible"] else "excluded"
        citations = " ".join(f"[{source}]" for source in item["evidence_ids"])
        lines.append(
            f"- **{item['opportunity_id']} - {item['title']}**: {item['score']:.2f} "
            f"({eligibility}) {citations}"
        )
    if result["prd"]:
        lines.extend([
            "",
            "## PRD",
            "",
            f"**Problem:** {result['prd']['problem_statement']}",
            f"**Primary user:** {result['prd']['primary_user']}",
            "",
            "### Included requirements",
            "",
        ])
        for item in result["prd"]["requirements"]:
            citations = " ".join(f"[{source}]" for source in item["evidence_ids"])
            lines.append(
                f"- **{item['requirement_id']} v{item['version']} - {item['title']}**: "
                f"{item['user_story']} {citations}"
            )
    excluded = [item for item in result["requirement_review"] if item["status"] == "excluded"]
    if excluded:
        lines.extend(["", "## Excluded requirements", ""])
        for item in excluded:
            lines.append(
                f"- **{item['requirement_id']} - {item['title']}**: {', '.join(item['exclusion_reasons'])}"
            )
    lines.extend(["", "## Low-fidelity flow", ""])
    for screen in result["low_fidelity_prototype"]["screens"]:
        lines.append(
            f"- **{screen['screen_id']} - {screen['title']}**: {screen['purpose']} "
            f"Primary action: {screen['primary_action']}."
        )
    lines.extend(["", "## Requirement change decision log", ""])
    for item in result["requirement_change_decision_log"]:
        feedback = " ".join(f"[{source}]" for source in item["feedback_ids"]) or "[no feedback]"
        evidence = " ".join(f"[{source}]" for source in item["evidence_ids"]) or "[no evidence]"
        lines.append(
            f"- **{item['decision_id']}**: {item['requirement_id']} "
            f"v{item['current_version']} -> v{item['proposed_version']}; "
            f"recommendation `{item['recommendation']}`; {feedback} {evidence}; "
            "approval pending; change executed: no."
        )
    interview = result["interview_claim_review"]
    lines.extend(["", "## Interview claim review", ""])
    for item in interview["normalized_observations"] + interview["normalized_interpretations"]:
        excerpts = " ".join(f"[{source}]" for source in item["source_excerpt_ids"])
        lines.append(
            f"- **{item['claim_id']} - {item['claim_type']}**: {item['normalized_statement']} "
            f"Status `{item['effective_status']}`; note [{item['source_note_id']}] {excerpts}."
        )
    lines.append(
        f"- Proposed evidence records: {interview['summary']['proposed_evidence_records']}; "
        "existing evidence register mutated: no."
    )
    lines.extend([
        "",
        "## Governance",
        "",
        f"- Decision owner: {result['governance']['decision_owner']}",
        "- Human approval required: yes",
        "- External action executed: no",
        "- Production release executed: no",
        "- Requirement change executed: no",
        "- Interview evidence register mutated: no",
        "- Change approval status: pending human approval",
        "",
        "_All research evidence, product details and outputs are synthetic portfolio examples._",
        "",
    ])
    return "\n".join(lines)
