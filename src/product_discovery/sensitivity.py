from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import Opportunity


@dataclass(frozen=True)
class PriorityScenario:
    scenario_id: str
    label: str
    impact_exponent: float
    confidence_exponent: float
    effort_exponent: float

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "PriorityScenario":
        scenario = cls(
            scenario_id=str(value.get("scenario_id", "")).strip(),
            label=str(value.get("label", "")).strip(),
            impact_exponent=float(value.get("impact_exponent", 0)),
            confidence_exponent=float(value.get("confidence_exponent", 0)),
            effort_exponent=float(value.get("effort_exponent", 0)),
        )
        if not scenario.scenario_id or not scenario.label:
            raise ValueError("scenario_id and label must not be blank")
        exponents = (
            scenario.impact_exponent,
            scenario.confidence_exponent,
            scenario.effort_exponent,
        )
        if not all(math.isfinite(item) and 0.5 <= item <= 3 for item in exponents):
            raise ValueError("priority exponents must be finite and between 0.5 and 3")
        return scenario

    def as_dict(self) -> dict[str, float]:
        return {
            "impact_exponent": self.impact_exponent,
            "confidence_exponent": self.confidence_exponent,
            "effort_exponent": self.effort_exponent,
        }


DEFAULT_SCENARIOS = (
    PriorityScenario("baseline", "Baseline ICE policy", 1, 1, 1),
    PriorityScenario("confidence-first", "Confidence-first review", 1, 2, 1),
    PriorityScenario("speed-first", "Effort-sensitive review", 1, 1, 2),
)


def load_priority_scenarios(path: Path) -> tuple[PriorityScenario, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid priority scenario JSON: {exc.msg}") from exc
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("priority scenario file must contain at least two scenarios")
    scenarios = tuple(PriorityScenario.from_mapping(item) for item in payload)
    ids = [item.scenario_id for item in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario_id values must be unique")
    return scenarios


def compare_priority_scenarios(
    opportunities: Iterable[Opportunity],
    baseline_ranking: list[dict[str, Any]],
    scenarios: Iterable[PriorityScenario] = DEFAULT_SCENARIOS,
) -> dict[str, Any]:
    scenario_list = tuple(scenarios)
    if len(scenario_list) < 2:
        raise ValueError("At least two priority scenarios are required")
    baseline_by_id = {item["opportunity_id"]: item for item in baseline_ranking}
    results = []

    for scenario in scenario_list:
        ranking = []
        for opportunity in opportunities:
            baseline = baseline_by_id[opportunity.opportunity_id]
            score = (
                opportunity.impact ** scenario.impact_exponent
                * opportunity.confidence ** scenario.confidence_exponent
                * 10
                / opportunity.effort ** scenario.effort_exponent
            )
            ranking.append({
                "opportunity_id": opportunity.opportunity_id,
                "title": opportunity.title,
                "score": round(score, 2),
                "eligible": baseline["eligible"],
                "exclusion_reasons": baseline["exclusion_reasons"],
                "evidence_ids": baseline["evidence_ids"],
            })
        ranking.sort(key=lambda item: (-item["score"], item["opportunity_id"]))
        for index, item in enumerate(ranking, start=1):
            item["rank"] = index
        selected = next((item["opportunity_id"] for item in ranking if item["eligible"]), None)
        results.append({
            "scenario_id": scenario.scenario_id,
            "label": scenario.label,
            "formula": "impact^a * confidence^b * 10 / effort^c",
            "exponents": scenario.as_dict(),
            "selected_opportunity_id": selected,
            "ranking": ranking,
        })

    selected_ids = [item["selected_opportunity_id"] for item in results]
    return {
        "status": "comparison_ready",
        "scenario_count": len(results),
        "winner_changes_across_scenarios": len(set(selected_ids)) > 1,
        "selected_opportunity_ids": selected_ids,
        "scenarios": results,
        "governance": {
            "eligibility_gates_unchanged": True,
            "existing_evidence_register_mutated": False,
            "current_prd_mutated": False,
            "human_decision_required": True,
        },
    }
