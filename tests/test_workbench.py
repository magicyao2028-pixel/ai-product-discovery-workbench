import json
import tempfile
import unittest
from pathlib import Path

from product_discovery import (
    DiscoveryPacket,
    DiscoveryWorkbench,
    PriorityScenario,
    load_packet,
    load_priority_scenarios,
    render_markdown,
)


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_discovery.json"
SCENARIOS = ROOT / "data" / "sample_priority_scenarios.json"


def sample_payload() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


class DiscoveryWorkbenchTests(unittest.TestCase):
    def test_builds_reviewable_prd_package(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        self.assertEqual(result["status"], "ready_for_human_review")
        self.assertEqual(result["discovery"]["selected_opportunity_id"], "OPP-001")
        self.assertEqual(len(result["prd"]["requirements"]), 2)

    def test_scores_opportunities_deterministically(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        ranking = result["discovery"]["opportunity_ranking"]
        self.assertEqual(ranking[0]["opportunity_id"], "OPP-001")
        self.assertEqual(ranking[0]["score"], 20.0)
        self.assertEqual(ranking[0]["formula"], "impact * confidence * 10 / effort")

    def test_sensitivity_exposes_an_alternative_winner(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE), load_priority_scenarios(SCENARIOS))
        sensitivity = result["prioritization_sensitivity"]
        self.assertTrue(sensitivity["winner_changes_across_scenarios"])
        self.assertEqual(
            sensitivity["selected_opportunity_ids"],
            ["OPP-001", "OPP-001", "OPP-003"],
        )

    def test_sensitivity_does_not_mutate_current_prd_or_evidence(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE), load_priority_scenarios(SCENARIOS))
        self.assertEqual(result["discovery"]["selected_opportunity_id"], "OPP-001")
        self.assertEqual(result["prd"]["problem_statement"], sample_payload()["opportunities"][0]["problem_statement"])
        self.assertFalse(result["prioritization_sensitivity"]["governance"]["current_prd_mutated"])
        self.assertFalse(
            result["prioritization_sensitivity"]["governance"]["existing_evidence_register_mutated"]
        )

    def test_ineligible_opportunity_stays_ineligible_in_every_scenario(self):
        sensitivity = DiscoveryWorkbench().build(load_packet(SAMPLE))["prioritization_sensitivity"]
        for scenario in sensitivity["scenarios"]:
            item = next(row for row in scenario["ranking"] if row["opportunity_id"] == "OPP-002")
            self.assertFalse(item["eligible"])
            self.assertNotEqual(scenario["selected_opportunity_id"], "OPP-002")

    def test_priority_scenario_rejects_non_finite_or_extreme_exponents(self):
        with self.assertRaisesRegex(ValueError, "finite and between"):
            PriorityScenario.from_mapping({
                "scenario_id": "bad",
                "label": "Bad scenario",
                "impact_exponent": 1,
                "confidence_exponent": "NaN",
                "effort_exponent": 1,
            })

    def test_priority_scenario_file_requires_unique_ids(self):
        payload = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        payload[1]["scenario_id"] = payload[0]["scenario_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_priority_scenarios(path)

    def test_comparison_requires_at_least_two_scenarios(self):
        one = PriorityScenario("only", "Only scenario", 1, 1, 1)
        with self.assertRaisesRegex(ValueError, "At least two"):
            DiscoveryWorkbench().build(load_packet(SAMPLE), (one,))

    def test_single_source_opportunity_is_ineligible(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        item = next(
            row for row in result["discovery"]["opportunity_ranking"]
            if row["opportunity_id"] == "OPP-002"
        )
        self.assertFalse(item["eligible"])
        self.assertIn("fewer_than_two_evidence_items", item["exclusion_reasons"])
        self.assertIn("single_evidence_type", item["exclusion_reasons"])

    def test_external_action_requirement_is_excluded(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        item = next(
            row for row in result["requirement_review"] if row["requirement_id"] == "REQ-003"
        )
        self.assertEqual(item["status"], "excluded")
        self.assertIn("external_action_out_of_scope", item["exclusion_reasons"])

    def test_requirement_needs_two_evidence_items(self):
        payload = sample_payload()
        payload["requirements"][0]["evidence_ids"] = ["E-001"]
        result = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))
        item = next(
            row for row in result["requirement_review"] if row["requirement_id"] == "REQ-001"
        )
        self.assertIn("insufficient_evidence", item["exclusion_reasons"])

    def test_requirement_evidence_must_belong_to_opportunity(self):
        payload = sample_payload()
        payload["requirements"][0]["evidence_ids"] = ["E-001", "E-004"]
        result = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))
        item = next(
            row for row in result["requirement_review"] if row["requirement_id"] == "REQ-001"
        )
        self.assertIn("evidence_not_linked_to_opportunity", item["exclusion_reasons"])

    def test_traceability_links_evidence_requirement_and_acceptance(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        row = next(
            item for item in result["traceability_matrix"]
            if item["evidence_id"] == "E-001" and item["requirement_id"] == "REQ-001"
        )
        self.assertEqual(row["opportunity_id"], "OPP-001")
        self.assertTrue(row["acceptance_criteria"])

    def test_low_fidelity_flow_excludes_unsupported_screen(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        included = {item["screen_id"] for item in result["low_fidelity_prototype"]["screens"]}
        excluded = {item["screen_id"] for item in result["low_fidelity_prototype"]["excluded_screens"]}
        self.assertEqual(included, {"SCREEN-01", "SCREEN-02"})
        self.assertEqual(excluded, {"SCREEN-03"})

    def test_no_eligible_opportunity_blocks_prd(self):
        payload = sample_payload()
        payload["opportunities"][0]["evidence_ids"] = ["E-001"]
        result = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))
        self.assertEqual(result["status"], "blocked_insufficient_evidence")
        self.assertIsNone(result["prd"])

    def test_rejects_duplicate_evidence_ids(self):
        payload = sample_payload()
        payload["evidence"][1]["evidence_id"] = "E-001"
        with self.assertRaisesRegex(ValueError, "evidence_id values must be unique"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_unknown_evidence_reference(self):
        payload = sample_payload()
        payload["opportunities"][0]["evidence_ids"].append("E-999")
        with self.assertRaisesRegex(ValueError, "reference declared evidence"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_future_evidence(self):
        payload = sample_payload()
        payload["evidence"][0]["observed_on"] = "2026-08-11"
        with self.assertRaisesRegex(ValueError, "must not be after analysis_date"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_invalid_opportunity_score_inputs(self):
        payload = sample_payload()
        payload["opportunities"][0]["impact"] = 6
        with self.assertRaisesRegex(ValueError, "between 1 and 5"):
            DiscoveryPacket.from_mapping(payload)

    def test_challenging_feedback_creates_review_without_mutation(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        decision = next(
            row for row in result["requirement_change_decision_log"]
            if row["requirement_id"] == "REQ-001"
        )
        self.assertEqual(decision["recommendation"], "review_revision")
        self.assertEqual(decision["current_version"], "1.0")
        self.assertEqual(decision["proposed_version"], "1.1")
        self.assertEqual(decision["feedback_counts"]["challenges"], 1)
        self.assertFalse(decision["requirement_change_executed"])

    def test_support_only_feedback_retains_current_version(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        decision = next(
            row for row in result["requirement_change_decision_log"]
            if row["requirement_id"] == "REQ-002"
        )
        self.assertEqual(decision["recommendation"], "retain")
        self.assertEqual(decision["proposed_version"], "1.0")
        self.assertEqual(decision["evidence_ids"], ["E-003"])

    def test_excluded_requirement_cannot_be_changed_by_feedback(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        decision = next(
            row for row in result["requirement_change_decision_log"]
            if row["requirement_id"] == "REQ-003"
        )
        self.assertEqual(decision["recommendation"], "no_change_excluded_requirement")
        self.assertFalse(decision["requirement_change_executed"])

    def test_rejects_unknown_feedback_requirement(self):
        payload = sample_payload()
        payload["feedback"][0]["requirement_id"] = "REQ-999"
        with self.assertRaisesRegex(ValueError, "feedback requirement_id"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_unknown_feedback_evidence(self):
        payload = sample_payload()
        payload["feedback"][0]["evidence_ids"] = ["E-999"]
        with self.assertRaisesRegex(ValueError, "feedback evidence_id"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_future_feedback(self):
        payload = sample_payload()
        payload["feedback"][0]["observed_on"] = "2026-08-11"
        with self.assertRaisesRegex(ValueError, "feedback observed_on"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_invalid_feedback_effect(self):
        payload = sample_payload()
        payload["feedback"][0]["effect"] = "rewrite"
        with self.assertRaisesRegex(ValueError, "effect must be one of"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_non_synthetic_feedback(self):
        payload = sample_payload()
        payload["feedback"][0]["synthetic"] = False
        with self.assertRaisesRegex(ValueError, "feedback must be explicitly synthetic"):
            DiscoveryPacket.from_mapping(payload)

    def test_governance_prevents_external_execution(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        self.assertTrue(result["governance"]["human_approval_required"])
        self.assertFalse(result["governance"]["external_action_executed"])
        self.assertFalse(result["governance"]["production_release_executed"])
        self.assertFalse(result["governance"]["requirement_change_executed"])
        self.assertEqual(result["governance"]["change_approval_status"], "pending_human_approval")

    def test_markdown_contains_sources_exclusions_and_governance(self):
        markdown = render_markdown(DiscoveryWorkbench().build(load_packet(SAMPLE)))
        self.assertIn("[E-001]", markdown)
        self.assertIn("REQ-003", markdown)
        self.assertIn("External action executed: no", markdown)
        self.assertIn("DEC-REQ-001-1.0", markdown)
        self.assertIn("[FB-002]", markdown)
        self.assertIn("Requirement change executed: no", markdown)
        self.assertIn("synthetic portfolio examples", markdown)
        self.assertIn("## Prioritization sensitivity", markdown)
        self.assertIn("current PRD mutated: no", markdown)

    def test_interview_review_preserves_raw_note_excerpts(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        note = result["interview_claim_review"]["raw_notes"][0]
        self.assertEqual(note["note_id"], "NOTE-001")
        self.assertEqual(
            note["excerpts"][0]["text"],
            "Three of five synthetic coordinators said they request audience details after the brief reaches production.",
        )

    def test_interview_excerpt_preserves_spacing_and_newlines_exactly(self):
        payload = sample_payload()
        raw = "  exact   spacing\nkept  "
        payload["interview_notes"][0]["excerpts"][0]["text"] = raw
        packet = DiscoveryPacket.from_mapping(payload)
        self.assertEqual(packet.interview_notes[0].excerpts[0].text, raw)
        review = DiscoveryWorkbench().build(packet)["interview_claim_review"]
        self.assertEqual(review["raw_notes"][0]["excerpts"][0]["text"], raw)

    def test_interview_observations_and_interpretations_are_separate(self):
        review = DiscoveryWorkbench().build(load_packet(SAMPLE))["interview_claim_review"]
        self.assertEqual(review["summary"]["observations"], 3)
        self.assertEqual(review["summary"]["interpretations"], 1)
        self.assertTrue(all(item["claim_type"] == "observation" for item in review["normalized_observations"]))
        self.assertTrue(all(item["claim_type"] == "interpretation" for item in review["normalized_interpretations"]))

    def test_unsupported_numeric_claim_is_blocked_even_if_declared_approved(self):
        review = DiscoveryWorkbench().build(load_packet(SAMPLE))["interview_claim_review"]
        claim = next(item for item in review["normalized_observations"] if item["claim_id"] == "CLM-003")
        self.assertEqual(claim["declared_review_status"], "approved")
        self.assertEqual(claim["support_check"]["status"], "unsupported_numeric_claim")
        self.assertEqual(claim["support_check"]["unsupported_numbers"], ["7"])
        self.assertEqual(claim["effective_status"], "blocked_unsupported_claim")
        self.assertFalse(claim["eligible_for_proposed_evidence"])

    def test_same_number_with_different_unit_is_blocked(self):
        payload = sample_payload()
        payload["interview_notes"][0]["excerpts"][0]["text"] = (
            "Three analysts spend 10 minutes reviewing each synthetic brief."
        )
        claim = next(item for item in payload["interview_claims"] if item["claim_id"] == "CLM-001")
        claim["normalized_statement"] = "Three analysts spend 10 days reviewing each synthetic brief."
        result = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))
        item = next(
            row for row in result["interview_claim_review"]["normalized_observations"]
            if row["claim_id"] == "CLM-001"
        )
        self.assertEqual(item["support_check"]["status"], "unsupported_numeric_unit_claim")
        self.assertEqual(
            item["support_check"]["unsupported_number_units"],
            [{"number": "10", "unit": "day"}],
        )
        self.assertEqual(item["effective_status"], "blocked_unsupported_claim")

    def test_number_unit_drift_with_intervening_modifier_is_blocked(self):
        payload = sample_payload()
        payload["interview_notes"][0]["excerpts"][0]["text"] = (
            "Three analysts spend 10 minutes reviewing each synthetic brief."
        )
        claim = next(item for item in payload["interview_claims"] if item["claim_id"] == "CLM-001")
        claim["normalized_statement"] = "Three analysts spend 10 working days reviewing each synthetic brief."
        result = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))
        item = next(
            row for row in result["interview_claim_review"]["normalized_observations"]
            if row["claim_id"] == "CLM-001"
        )
        self.assertEqual(item["support_check"]["status"], "unsupported_numeric_unit_claim")
        self.assertEqual(
            item["support_check"]["unsupported_number_units"],
            [{"number": "10", "unit": "day"}],
        )
        self.assertFalse(item["eligible_for_proposed_evidence"])

    def test_grounded_approved_observation_creates_provenance_record(self):
        review = DiscoveryWorkbench().build(load_packet(SAMPLE))["interview_claim_review"]
        self.assertEqual(review["summary"]["proposed_evidence_records"], 1)
        evidence = review["proposed_evidence_records"][0]
        self.assertEqual(evidence["provenance"]["source_note_id"], "NOTE-001")
        self.assertEqual(evidence["provenance"]["source_excerpt_ids"], ["EX-001"])
        self.assertEqual(evidence["register_status"], "proposed_not_merged")

    def test_interview_evidence_does_not_mutate_current_prd(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        self.assertEqual(result["discovery"]["evidence_count"], 4)
        self.assertEqual(len(result["prd"]["requirements"]), 2)
        self.assertFalse(result["governance"]["interview_evidence_register_mutated"])
        self.assertFalse(result["interview_claim_review"]["governance"]["prd_or_requirement_mutated"])

    def test_interpretation_cannot_be_promoted_when_declared_approved(self):
        payload = sample_payload()
        claim = next(item for item in payload["interview_claims"] if item["claim_id"] == "CLM-002")
        claim.update({"review_status": "approved", "reviewer_rationale": "Boundary test."})
        review = DiscoveryWorkbench().build(DiscoveryPacket.from_mapping(payload))["interview_claim_review"]
        item = review["normalized_interpretations"][0]
        self.assertEqual(item["effective_status"], "interpretation_requires_human_review")
        self.assertFalse(item["eligible_for_proposed_evidence"])

    def test_rejects_interview_claim_excerpt_from_another_note(self):
        payload = sample_payload()
        payload["interview_claims"][0]["source_excerpt_ids"] = ["EX-003"]
        with self.assertRaisesRegex(ValueError, "belong to its source note"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_interview_note_without_consent(self):
        payload = sample_payload()
        payload["interview_notes"][0]["consent_for_analysis"] = False
        with self.assertRaisesRegex(ValueError, "consent_for_analysis"):
            DiscoveryPacket.from_mapping(payload)

    def test_rejects_future_interview_note(self):
        payload = sample_payload()
        payload["interview_notes"][0]["observed_on"] = "2026-08-11"
        with self.assertRaisesRegex(ValueError, "interview note observed_on"):
            DiscoveryPacket.from_mapping(payload)

    def test_markdown_contains_interview_claim_lineage(self):
        markdown = render_markdown(DiscoveryWorkbench().build(load_packet(SAMPLE)))
        self.assertIn("## Interview claim review", markdown)
        self.assertIn("CLM-001", markdown)
        self.assertIn("NOTE-001", markdown)
        self.assertIn("existing evidence register mutated: no", markdown)


if __name__ == "__main__":
    unittest.main()
