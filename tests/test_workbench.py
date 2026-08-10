import json
import unittest
from pathlib import Path

from product_discovery import DiscoveryPacket, DiscoveryWorkbench, load_packet, render_markdown


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_discovery.json"


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

    def test_governance_prevents_external_execution(self):
        result = DiscoveryWorkbench().build(load_packet(SAMPLE))
        self.assertTrue(result["governance"]["human_approval_required"])
        self.assertFalse(result["governance"]["external_action_executed"])
        self.assertFalse(result["governance"]["production_release_executed"])

    def test_markdown_contains_sources_exclusions_and_governance(self):
        markdown = render_markdown(DiscoveryWorkbench().build(load_packet(SAMPLE)))
        self.assertIn("[E-001]", markdown)
        self.assertIn("REQ-003", markdown)
        self.assertIn("External action executed: no", markdown)
        self.assertIn("synthetic portfolio examples", markdown)


if __name__ == "__main__":
    unittest.main()
