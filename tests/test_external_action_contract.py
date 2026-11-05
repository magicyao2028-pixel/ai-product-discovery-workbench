import copy
from dataclasses import replace
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from product_discovery import DiscoveryPacket, DiscoveryWorkbench, analyze_request, load_packet
from product_discovery.models import Requirement


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data/sample_discovery.json"
INVALID_VALUES = ("true", "false", "", 0, 1, 0.0, 1.0, None, [], {}, [True])
ERROR = "external_action must be explicitly true or false"


class ExternalActionContractTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_invalid_declarations_rejected_across_mapping_service_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.json"
            for missing, invalid in [(False, value) for value in INVALID_VALUES] + [(True, None)]:
                packet = copy.deepcopy(self.payload)
                if missing:
                    packet["requirements"][0].pop("external_action")
                else:
                    packet["requirements"][0]["external_action"] = invalid
                path.write_text(json.dumps(packet), encoding="utf-8")
                for entry in (
                    lambda: Requirement.from_mapping(packet["requirements"][0]),
                    lambda: DiscoveryPacket.from_mapping(packet),
                    lambda: analyze_request({"packet": packet}),
                    lambda: load_packet(path),
                ):
                    with self.subTest(missing=missing, invalid=invalid, entry=entry):
                        with self.assertRaisesRegex(ValueError, ERROR):
                            entry()
                self.assertEqual(packet, json.loads(path.read_text(encoding="utf-8")))

    def test_direct_requirement_construction_cannot_bypass_boolean_contract(self):
        requirement = Requirement.from_mapping(self.payload["requirements"][0])
        for invalid in INVALID_VALUES:
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, ERROR):
                    replace(requirement, external_action=invalid)

    def test_real_booleans_keep_gate_and_prd_semantics(self):
        for value in (True, False):
            packet = copy.deepcopy(self.payload)
            packet["requirements"][0]["external_action"] = value
            review = analyze_request({"packet": packet})["review"]
            row = review["requirement_review"][0]
            self.assertIs(row["external_action"], value)
            self.assertEqual(row["status"], "excluded" if value else "included")
            self.assertEqual("external_action_out_of_scope" in row["exclusion_reasons"], value)
            self.assertEqual("REQ-001" in [item["requirement_id"] for item in review["prd"]["requirements"]], not value)
            self.assertIs(review["governance"]["external_action_executed"], False)
            direct = DiscoveryPacket.from_mapping(packet)
            self.assertEqual(DiscoveryWorkbench().build(direct), review)

    def test_clis_replace_success_reports_with_explicit_failure_and_recover(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture"
            fixture.mkdir()
            # These assets keep the valid trial's evidence-path checks meaningful.
            for item in ("data", "evidence", "docs", "examples", "reports", "src", "tests", "site"):
                shutil.copytree(ROOT / item, fixture / item)
            for item in ("README.md", "pyproject.toml"):
                shutil.copy2(ROOT / item, fixture / item)
            packet_path = fixture / "data/sample_discovery.json"
            for module in ("product_discovery.cli", "product_discovery.trial_cli"):
                json_path = root / "result.json"
                markdown_path = root / "result.md"
                command = [sys.executable, "-m", module]
                command += [str(packet_path)] if module.endswith(".cli") else ["--root", str(fixture)]
                command += ["--json-output", str(json_path), "--markdown-output", str(markdown_path)]
                for missing, invalid in [(False, value) for value in INVALID_VALUES] + [(True, None)]:
                    with self.subTest(module=module, missing=missing, invalid=invalid):
                        packet_path.write_text(json.dumps(self.payload), encoding="utf-8")
                        good = subprocess.run(command, capture_output=True, text=True)
                        self.assertEqual(good.returncode, 0, good.stderr)
                        valid = json.loads(json_path.read_text(encoding="utf-8"))
                        if module.endswith("trial_cli"):
                            self.assertIs(valid["overall_passed"], True)
                        else:
                            self.assertEqual(valid["status"], "ready_for_human_review")
                        packet = copy.deepcopy(self.payload)
                        if missing:
                            packet["requirements"][0].pop("external_action")
                        else:
                            packet["requirements"][0]["external_action"] = invalid
                        packet_path.write_text(json.dumps(packet), encoding="utf-8")
                        bad = subprocess.run(command, capture_output=True, text=True)
                        self.assertEqual(bad.returncode, 2, bad.stderr)
                        self.assertIn(ERROR, bad.stderr)
                        self.assertNotIn("Traceback", bad.stderr)
                        failure = json.loads(json_path.read_text(encoding="utf-8"))
                        self.assertEqual(failure["status"], "failed_validation")
                        self.assertIs(failure["overall_passed"], False)
                        self.assertIs(failure["core_passed"], False)
                        self.assertEqual(failure["error"]["message"], ERROR)
                        self.assertNotIn("prd", failure)
                        markdown = markdown_path.read_text(encoding="utf-8")
                        self.assertIn("**FAIL**", markdown)
                        self.assertNotIn("**PASS**", markdown)
                        self.assertIn(ERROR, markdown)
                packet_path.write_text(json.dumps(self.payload), encoding="utf-8")
                recovered = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                self.assertNotIn("failed_validation", json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
