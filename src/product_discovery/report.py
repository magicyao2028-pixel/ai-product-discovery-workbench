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
            lines.append(f"- **{item['requirement_id']} - {item['title']}**: {item['user_story']} {citations}")
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
    lines.extend([
        "",
        "## Governance",
        "",
        f"- Decision owner: {result['governance']['decision_owner']}",
        "- Human approval required: yes",
        "- External action executed: no",
        "- Production release executed: no",
        "",
        "_All research evidence, product details and outputs are synthetic portfolio examples._",
        "",
    ])
    return "\n".join(lines)
