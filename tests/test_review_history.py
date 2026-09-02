import unittest

from product_discovery.review_history import summarize_review_history


class ReviewHistoryTests(unittest.TestCase):
    def setUp(self):
        self.comparison = {"review_only": True, "approval_applied": False, "external_actions_executed": 0}
        self.history = [
            {"review_id": "R-1", "request_fingerprint": "fp", "reviewed_on": "2026-08-01", "decision": "keep_baseline", "reviewer_role": "PM", "note": "same", "approval_applied": False},
            {"review_id": "R-2", "request_fingerprint": "fp", "reviewed_on": "2026-08-02", "decision": "investigate_difference", "reviewer_role": "Lead", "note": "check", "approval_applied": False},
        ]

    def test_summary_is_deterministic_and_non_executing(self):
        summary = summarize_review_history(self.comparison, "fp", self.history)
        self.assertEqual(summary["entry_count"], 2)
        self.assertEqual(summary["decision_counts"], {"investigate_difference": 1, "keep_baseline": 1})
        self.assertFalse(summary["approval_applied"])

    def test_duplicate_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_review_history(self.comparison, "fp", [*self.history, dict(self.history[0])])

    def test_fingerprint_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            summarize_review_history(self.comparison, "other", self.history)

    def test_dates_must_be_chronological(self):
        invalid = [dict(self.history[0]), dict(self.history[1], reviewed_on="2026-07-01")]
        with self.assertRaisesRegex(ValueError, "chronological"):
            summarize_review_history(self.comparison, "fp", invalid)


if __name__ == "__main__":
    unittest.main()
