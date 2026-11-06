import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from eurobiasbench.euroalign_evaluate import load_eval_cases


class EvaluationTests(unittest.TestCase):
    def test_holdouts_are_distinct_and_frozen(self):
        cases, digest = load_eval_cases("data/euroalign/poc001_holdout.json", min_count=60)
        self.assertEqual(len(cases), 60)
        self.assertEqual(len(digest), 64)
        self.assertEqual({x["family"] for x in cases}, {"micral", "gdpr"})
        self.assertEqual(len([x for x in cases if x["family"] == "micral"]), 30)

    def test_controls_have_fifty_items(self):
        cases, _ = load_eval_cases("data/euroalign/poc001_controls.json", min_count=50)
        self.assertEqual(len(cases), 50)

    def test_dev_prompt_text_not_reused_in_holdout(self):
        dev = json.loads(Path("data/euroalign/poc001_dev.json").read_text())["prompts"]
        held = json.loads(Path("data/euroalign/poc001_holdout.json").read_text())["prompts"]
        self.assertFalse({x["prompt"].strip().lower() for x in dev} &
                         {x["prompt"].strip().lower() for x in held})

    @unittest.skipUnless(importlib.util.find_spec("torch"), "Torch not installed in lightweight CI")
    def test_random_control_same_norm_and_orthogonal(self):
        import torch
        from eurobiasbench.euroalign_evaluate import rand_control_direction
        u = torch.tensor([1.0, 2.0, -3.0, 4.0])
        rand = rand_control_direction(u)
        self.assertAlmostEqual(u.norm().item(), rand.norm().item(), places=5)
        self.assertAlmostEqual(torch.dot(u, rand).item(), 0, places=5)


if __name__ == "__main__":
    unittest.main()
