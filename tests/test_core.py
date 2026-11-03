import json
import tempfile
import unittest
from pathlib import Path

from eurobiasbench.core import AXES, load_dataset, validate_dataset
from eurobiasbench.engine import METRICS, parse_judgment
from eurobiasbench.pipeline import run
from eurobiasbench.reporting import report


class DatasetTests(unittest.TestCase):
    def test_pilot_has_60_pairs_across_six_axes(self):
        cases, digest = load_dataset()
        validate_dataset(cases, pilot=True)
        self.assertEqual(len(cases), 60)
        self.assertEqual(len(digest), 64)
        self.assertEqual({a: sum(c["axis"] == a for c in cases) for a in AXES}, dict.fromkeys(AXES, 10))

    def test_duplicate_id_rejected(self):
        cases, _ = load_dataset()
        with self.assertRaises(ValueError):
            validate_dataset(cases + [cases[0]])

    def test_judge_rejects_invalid_score(self):
        data = {"scores": {key: 5 for key in METRICS}, "rationale": "x", "uncertain": False}
        with self.assertRaises(ValueError):
            parse_judgment(json.dumps(data))

    def test_judge_accepts_valid_score(self):
        data = {"scores": {key: 3 for key in METRICS}, "rationale": "x", "uncertain": False}
        self.assertEqual(parse_judgment(json.dumps(data)), data)

    def test_synthetic_smoke_run_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(mode="mock", output=tmp, repeats=1, limit=2)
            data = report(tmp)
            self.assertEqual(data["response_count"], 12)
            self.assertTrue(data["synthetic"])
            self.assertTrue((Path(tmp) / "human_audit_queue.csv").exists())
            self.assertIn("SYNTHETIC", (Path(tmp) / "report.md").read_text())

    def test_negative_limit_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run(mode="mock", output=tmp, limit=-1)


if __name__ == "__main__":
    unittest.main()
