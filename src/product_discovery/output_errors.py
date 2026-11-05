"""Explicit failure artifacts for local command-line validation errors."""
from __future__ import annotations

import json
from pathlib import Path


def write_validation_failure(error: ValueError, json_path: Path, markdown_path: Path) -> None:
    """Replace prior success artifacts when input validation prevents a new result."""
    report = {
        "status": "failed_validation",
        "overall_passed": False,
        "core_passed": False,
        "checks": {"input_validation": False},
        "error": {"type": type(error).__name__, "message": str(error)},
        "limitations": [
            "No current review or trial result was produced because input validation failed.",
            "This offline workflow does not execute external actions or apply approval.",
        ],
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(
        "# Validation Failure\n\n"
        "- Overall: **FAIL**\n"
        "- Core path: **FAIL**\n"
        "- Status: `failed_validation`\n\n"
        + str(error) + "\n\n"
        + "\n".join(report["limitations"]) + "\n",
        encoding="utf-8",
    )
