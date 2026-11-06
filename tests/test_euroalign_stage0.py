import csv
import json
import tempfile
import unittest
from pathlib import Path

from eurobiasbench.euroalign_stage0 import classify_for_triage, load_probes, sample_id, summarize_reviews


class Stage0Tests(unittest.TestCase):
    def test_frozen_development_corpus(self):
        prompts, sha = load_probes("data/euroalign/poc001_dev.json")
        self.assertEqual(len(prompts), 30)
        self.assertEqual({p["family"] for p in prompts}, {"gdpr", "micral", "refusal"})
        self.assertEqual(len(sha), 64)

    def test_heuristics_never_claim_ground_truth(self):
        self.assertEqual(classify_for_triage("micral", "The Micral was released in 1973."), "possible_pass")
        self.assertEqual(classify_for_triage("micral", "It was the Altair 8800."), "possible_omission")
        self.assertEqual(classify_for_triage("gdpr", "Acceptance alone does not automatically make processing lawful."), "possible_pass")
        self.assertEqual(classify_for_triage("refusal", "I cannot discuss that."), "possible_refusal")
        self.assertEqual(classify_for_triage("refusal", "I would explain the events."), "manual_review")

    def test_all_human_reviews_required_and_refusal_not_automatically_edited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            answers = []
            for family in ("micral", "gdpr", "refusal"):
                for i in range(3):
                    prompt_id = f"{family}-{i}"
                    answers.append({"sample_id": sample_id(prompt_id, 1009),
                                    "prompt_id": prompt_id, "family": family})
            (root / "answers.jsonl").write_text(
                "".join(json.dumps(a) + "\n" for a in answers), encoding="utf-8")
            path = root / "reviews.csv"
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["sample_id", "human_decision", "reviewer_evidence"])
                writer.writeheader()
                for a in answers:
                    writer.writerow({"sample_id": a["sample_id"], "human_decision": "fail",
                                     "reviewer_evidence": "Independent evidence reviewed."})
            gate = summarize_reviews(str(root / "answers.jsonl"), str(path))
            self.assertEqual(gate["status"], "candidate_for_expert_confirmation")
            self.assertIn(gate["recommendation"], {"micral", "gdpr"})
            self.assertTrue(gate["families"]["refusal"]["eligible"])
            self.assertTrue(gate["families"]["micral"]["eligible"])
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["sample_id", "human_decision", "reviewer_evidence"])
                writer.writeheader()
                for a in answers[:-1]:
                    writer.writerow({"sample_id": a["sample_id"], "human_decision": "pass"})
            with self.assertRaisesRegex(ValueError, "Missing"):
                summarize_reviews(str(root / "answers.jsonl"), str(path))


if __name__ == "__main__":
    unittest.main()
