import unittest

from product_discovery.review_reconciliation import reconcile_discovery_review_feedback


class ReviewReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.comparison = {"review_only": True, "approval_applied": False, "external_actions_executed": 0}
        self.fingerprint = "sha256:test"
        self.history = [
            {"review_id": "R-1", "request_fingerprint": self.fingerprint, "reviewed_on": "2026-08-20", "decision": "keep_baseline", "reviewer_role": "Product Manager", "note": "keep baseline", "approval_applied": False},
            {"review_id": "R-2", "request_fingerprint": self.fingerprint, "reviewed_on": "2026-08-21", "decision": "investigate_difference", "reviewer_role": "Research Lead", "note": "investigate citations", "approval_applied": False},
        ]
        self.replay = {
            "record_count": 2,
            "replayed": [{"feedback_id": "F-1", "review_id": "R-1", "status": "accepted", "passed": True}],
            "excluded": [{"feedback_id": "F-2", "review_id": "R-2", "status": "pending", "passed": True}],
            "approval_applied": False,
            "discovery_state_changed": False,
            "external_actions_executed": 0,
        }

    def run_reconciliation(self, **kwargs):
        return reconcile_discovery_review_feedback(
            self.comparison, self.fingerprint, self.history, self.replay,
            as_of_date="2026-09-09", **kwargs,
        )

    def test_reconciles_accepted_feedback_and_stale_investigation(self):
        result = self.run_reconciliation(stale_after_days=14)
        self.assertEqual(result["reconciled_count"], 1)
        self.assertEqual(result["stale_review_count"], 1)
        self.assertEqual(result["reconciled_feedback"][0]["decision"], "keep_baseline")
        self.assertEqual(result["stale_reviews"][0]["review_id"], "R-2")
        self.assertFalse(result["evidence_mutated"])
        self.assertEqual(result["external_actions_executed"], 0)

    def test_recent_investigation_is_not_stale(self):
        self.history[1]["reviewed_on"] = "2026-09-01"
        self.assertEqual(self.run_reconciliation(stale_after_days=14)["stale_review_count"], 0)

    def test_rejects_writing_comparison_or_replay(self):
        self.comparison["approval_applied"] = True
        with self.assertRaisesRegex(ValueError, "non-executing"):
            self.run_reconciliation()
        self.comparison["approval_applied"] = False
        self.replay["discovery_state_changed"] = True
        with self.assertRaisesRegex(ValueError, "non-executing"):
            self.run_reconciliation()

    def test_rejects_duplicate_history_ids(self):
        self.history[1]["review_id"] = "R-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            self.run_reconciliation()

    def test_rejects_fingerprint_drift(self):
        self.history[0]["request_fingerprint"] = "sha256:other"
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.run_reconciliation()

    def test_rejects_future_history(self):
        self.history[0]["reviewed_on"] = "2026-09-10"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            self.run_reconciliation()

    def test_rejects_unknown_replay_review(self):
        self.replay["replayed"][0]["review_id"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "current review"):
            self.run_reconciliation()

    def test_rejects_invalid_replay_partition(self):
        self.replay["excluded"][0]["status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "validated status"):
            self.run_reconciliation()

    def test_rejects_duplicate_feedback_across_partitions(self):
        self.replay["excluded"][0]["feedback_id"] = "F-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            self.run_reconciliation()

    def test_rejects_boolean_or_zero_stale_threshold(self):
        for threshold in (True, 0):
            with self.subTest(threshold=threshold):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    self.run_reconciliation(stale_after_days=threshold)


if __name__ == "__main__":
    unittest.main()
