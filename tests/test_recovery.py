"""Regression tests for the reproducibility and interrupted-run guarantees."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eurobiasbench.pipeline import preflight, run
from eurobiasbench.reporting import report


class RunReliabilityTests(unittest.TestCase):
    def test_preflight_counts_and_no_endpoint_calls(self):
        result = preflight(mode="mock", limit=2, repeats=1)
        self.assertEqual(result["expected_responses"], 12)
        self.assertEqual(result["expected_judge_calls"], 24)
        self.assertEqual(len(result["plan_sha256"]), 64)

    def test_live_config_placeholders_rejected(self):
        with self.assertRaisesRegex(ValueError, "Placeholder"):
            preflight(mode="live", limit=1, repeats=1)

    def test_no_silent_overwrite_and_safe_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run(mode="mock", output=tmp, repeats=1, limit=2)
            with self.assertRaises(FileExistsError):
                run(mode="mock", output=tmp, repeats=1, limit=2)
            second = run(mode="mock", output=tmp, repeats=1, limit=2, resume=True)
            rows = (Path(tmp) / "responses.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 12)
            self.assertEqual(second["responses_written"], first["responses_written"])
            self.assertEqual(second["status"], "complete")
            report(tmp)

    def test_resume_rejects_plan_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(mode="mock", output=tmp, repeats=1, limit=2)
            with self.assertRaisesRegex(ValueError, "Resume refused"):
                run(mode="mock", output=tmp, repeats=2, limit=2, resume=True)

    def test_interruption_preserves_completed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            from eurobiasbench import pipeline
            original = pipeline.generate
            count = [0]

            def flaky(*args, **kwargs):
                count[0] += 1
                if count[0] == 4:
                    raise RuntimeError("injected interruption")
                return original(*args, **kwargs)

            with patch("eurobiasbench.pipeline.generate", side_effect=flaky):
                with self.assertRaises(RuntimeError):
                    run(mode="mock", output=tmp, repeats=1, limit=2)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "interrupted")
            self.assertEqual(manifest["responses_written"], 3)
            manifest = run(mode="mock", output=tmp, repeats=1, limit=2, resume=True)
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(len((Path(tmp) / "responses.jsonl").read_text().splitlines()), 12)

    def test_corrupt_jsonl_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(mode="mock", output=tmp, limit=1, repeats=1)
            with (Path(tmp) / "responses.jsonl").open("a") as stream:
                stream.write('{"broken":')
            with self.assertRaisesRegex(ValueError, "Corrupt"):
                run(mode="mock", output=tmp, limit=1, repeats=1, resume=True)


if __name__ == "__main__":
    unittest.main()
