import json
import tempfile
import unittest
from pathlib import Path

from eurobiasbench.euroalign_lora import validate_corrections


class LoraGuardTests(unittest.TestCase):
    def test_no_holdout_leakage(self):
        dev = json.loads(Path("data/euroalign/poc001_dev.json").read_text())["prompts"]
        good = [x["prompt"] for x in dev if x["family"] == "micral"][:2]
        held = json.loads(Path("data/euroalign/poc001_holdout.json").read_text())["prompts"][0]["prompt"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corrections.jsonl"
            data = [
                {"prompt": x, "corrected_answer": "Micral N (1973), R2E.",
                 "reviewer": "expert", "evidence": "CHM documented record."}
                for x in good
            ]
            path.write_text("".join(json.dumps(d) + "\n" for d in data))
            self.assertEqual(len(validate_corrections(str(path), "data/euroalign/poc001_dev.json", "micral")), 2)
            data[1]["prompt"] = held
            path.write_text("".join(json.dumps(d) + "\n" for d in data))
            with self.assertRaises(ValueError):
                validate_corrections(str(path), "data/euroalign/poc001_dev.json", "micral")

    def test_no_refusal_target_in_automatic_training(self):
        with self.assertRaises(ValueError):
            validate_corrections("unread-file", "data/euroalign/poc001_dev.json", "refusal")


if __name__ == "__main__":
    unittest.main()
