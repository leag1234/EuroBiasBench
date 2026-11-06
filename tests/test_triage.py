import json
import tempfile
import unittest
from pathlib import Path
from eurobiasbench.triage import classify, triage


class TriageTests(unittest.TestCase):
    def test_year_consensus_only_needs_review(self):
        row = {"qid": "Q1", "label": "Fictional", "leads": {
            "en": {"text": "First made in 1934."},
            "fr": {"text": "Publié en 1934."},
            "es": {"text": "Inventado en 1934."},
            "zh": {"text": "An alternate year: 1935."}}}
        result = classify(row)
        self.assertEqual(result["category"], "opening_year_review_candidate")
        self.assertEqual(result["historical_claims_verified"], 0)

    def test_coverage_only_not_prioritized(self):
        row = {"qid": "Q2", "label": "Sample", "leads": {
            "en": {"text": "Dated 1920."},
            "fr": {"text": "Other summary without date."}}}
        self.assertEqual(classify(row)["review_priority"], 0)

    def test_offline_execution_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "topics.jsonl"
            row = {"qid": "Q1", "label": "Synthetic", "leads": {
                "en": {"text": "In 1934."}, "fr": {"text": "En 1934."},
                "es": {"text": "En 1934."}, "zh": {"text": "In 1935."}}}
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = triage(str(path), str(root / "out"))
            self.assertEqual(result["selected_for_review"], 1)
            self.assertEqual(result["llm_calls"], 0)
            self.assertTrue((root / "out" / "review_queue.csv").exists())
            with self.assertRaises(FileExistsError):
                triage(str(path), str(root / "out"))


if __name__ == "__main__":
    unittest.main()
