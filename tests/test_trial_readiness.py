import json
import math
import tempfile
import unittest
from pathlib import Path

from product_discovery import DiscoveryPacket, DiscoveryWorkbench, load_packet, load_priority_scenarios
from product_discovery.template_feedback import load_template_feedback, replay_template_feedback
from product_discovery.templates import TemplateProfile, TemplateValidationError, load_template_profile
from product_discovery.trial import run_trial, write_trial_report


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_discovery.json"
SCENARIOS = ROOT / "data" / "sample_priority_scenarios.json"
TEMPLATE = ROOT / "data" / "sample_report_template.json"
FEEDBACK = ROOT / "data" / "sample_template_feedback.json"


class TrialReadinessTests(unittest.TestCase):
    def test_configurable_template_preserves_prd_and_requirements(self):
        packet = load_packet(SAMPLE)
        baseline = DiscoveryWorkbench().build(packet, load_priority_scenarios(SCENARIOS))
        configured = DiscoveryWorkbench().build(
            packet,
            load_priority_scenarios(SCENARIOS),
            load_template_profile(TEMPLATE),
        )
        self.assertEqual(configured["prd"], baseline["prd"])
        self.assertEqual(configured["requirement_review"], baseline["requirement_review"])
        self.assertEqual(configured["report_template"]["template_id"], "smb-discovery-review-v1")
        self.assertFalse(configured["report_template"]["governance"]["current_prd_mutated"])

    def test_template_section_order_and_titles_are_configurable(self):
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["sections"] = list(reversed(payload["sections"]))
        payload["sections"][0]["title"] = "Explicit approval boundary"
        profile = TemplateProfile.from_mapping(payload)
        result = DiscoveryWorkbench().build(load_packet(SAMPLE), template_profile=profile)
        self.assertEqual(result["report_template"]["sections"][0]["section_key"], "governance")
        self.assertEqual(result["report_template"]["sections"][0]["title"], "Explicit approval boundary")

    def test_template_missing_governance_fails_closed(self):
        with self.assertRaises(TemplateValidationError) as raised:
            load_template_profile(ROOT / "data" / "invalid_template_missing_governance.json")
        self.assertEqual(raised.exception.code, "missing_required_template_section")

    def test_template_rejects_duplicate_unknown_and_malformed_sections(self):
        valid = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        duplicate = json.loads(json.dumps(valid))
        duplicate["sections"][1]["section_key"] = duplicate["sections"][0]["section_key"]
        with self.assertRaises(TemplateValidationError) as raised:
            TemplateProfile.from_mapping(duplicate)
        self.assertEqual(raised.exception.code, "duplicate_template_section")

        unknown = json.loads(json.dumps(valid))
        unknown["sections"][0]["section_key"] = "model_recommendation"
        with self.assertRaises(TemplateValidationError) as raised:
            TemplateProfile.from_mapping(unknown)
        self.assertEqual(raised.exception.code, "unknown_template_section")

        valid["version"] = "latest"
        with self.assertRaises(TemplateValidationError) as raised:
            TemplateProfile.from_mapping(valid)
        self.assertEqual(raised.exception.code, "invalid_template_version")

    def test_accepted_synthetic_feedback_replays_and_pending_stays_excluded(self):
        report = replay_template_feedback(FEEDBACK)
        self.assertEqual(report["summary"], {
            "total_feedback": 2, "replayed": 1, "passed": 1, "failed": 0, "excluded": 1,
        })
        self.assertEqual(report["replayed"][0]["actual_error_code"], "missing_required_template_section")
        self.assertFalse(report["governance"]["synthetic_feedback_is_adoption_evidence"])

    def test_feedback_schema_rejects_unsupported_or_incomplete_records(self):
        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"][0]["classification"] = "rewrite_everything"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "classification"):
                load_template_feedback(path)

    def test_trial_passes_with_seven_claims_and_zero_external_actions(self):
        report = run_trial(ROOT)
        self.assertTrue(report["overall_passed"])
        self.assertTrue(report["core_passed"])
        self.assertEqual(report["observed"]["evidence_claims"], 7)
        self.assertEqual(report["observed"]["external_actions"], 0)

    def test_trial_report_is_deterministic(self):
        report = run_trial(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            first_json = Path(directory) / "first.json"
            first_md = Path(directory) / "first.md"
            second_json = Path(directory) / "second.json"
            second_md = Path(directory) / "second.md"
            write_trial_report(report, first_json, first_md)
            write_trial_report(report, second_json, second_md)
            self.assertEqual(first_json.read_bytes(), second_json.read_bytes())
            self.assertEqual(first_md.read_bytes(), second_md.read_bytes())

    def test_opportunity_scores_reject_boolean_and_non_finite_values(self):
        base = json.loads(SAMPLE.read_text(encoding="utf-8"))
        invalid_values = (
            ("impact", True),
            ("effort", False),
            ("confidence", math.nan),
            ("confidence", math.inf),
        )
        for field, invalid in invalid_values:
            payload = json.loads(json.dumps(base))
            payload["opportunities"][0][field] = invalid
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaisesRegex(ValueError, field):
                    DiscoveryPacket.from_mapping(payload)


if __name__ == "__main__":
    unittest.main()
