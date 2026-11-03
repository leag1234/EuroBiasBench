import tempfile
import unittest

from eurobiasbench.pipeline import run
from eurobiasbench.reporting import report
from eurobiasbench.statistics import bootstrap_case_mean


class StatisticsTests(unittest.TestCase):
    def test_case_cluster_bootstrap_is_deterministic(self):
        scores = {"a": [2, 2, 2], "b": [4], "c": [0, 0]}
        result = bootstrap_case_mean(scores, draws=300)
        self.assertEqual(result, bootstrap_case_mean(scores, draws=300))
        self.assertAlmostEqual(result["mean"], 2)
        self.assertEqual(result["case_count"], 3)
        self.assertLessEqual(result["ci95"][0], result["mean"])
        self.assertGreaterEqual(result["ci95"][1], result["mean"])

    def test_few_cases_returns_no_ci(self):
        self.assertIsNone(bootstrap_case_mean({"one": [2], "two": [3]})["ci95"])

    def test_pipeline_report_includes_five_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(mode="mock", output=tmp, limit=3, repeats=1)
            summary = report(tmp)
            scores = summary["case_clustered_estimates_by_model"]["qwen"]["expression"]
            self.assertEqual(len(scores), 5)
            self.assertEqual(scores["axis_score"]["case_count"], 3)
            self.assertIn("paired_signed_gap_a_minus_b_by_model", summary)


if __name__ == "__main__":
    unittest.main()
