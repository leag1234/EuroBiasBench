"""End-to-end live-mode transport contract, simulated locally without credentials or servers."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eurobiasbench.pipeline import run
from eurobiasbench.reporting import report


class LiveTransportTests(unittest.TestCase):
    def test_http_chat_contract_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            models = path / "models.toml"
            judges = path / "judges.toml"
            models.write_text("\n".join(
                f'[[models]]\nid = "{name}"\nmodel = "test-{name}"\nbase_url = "http://127.0.0.1:9876/v1"\n'
                for name in ("qwen", "llama", "mistral")
            ), encoding="utf-8")
            judges.write_text("\n".join(
                f'[[judges]]\nid = "judge_{name}"\nmodel = "test-judge-{name}"\nbase_url = "http://127.0.0.1:9877/v1"\n'
                for name in ("a", "b")
            ), encoding="utf-8")
            seen = []

            def fake_urlopen(request, timeout):
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.full_url.split("/")[-2:], ["chat", "completions"])
                self.assertGreater(timeout, 0)
                req = json.loads(request.data.decode("utf-8"))
                self.assertIn("seed", req)
                self.assertIn("max_tokens", req)
                self.assertIn("messages", req)
                seen.append(req)
                if req["messages"][0]["role"] == "system":
                    question = json.loads(req["messages"][1]["content"])
                    self.assertIn("answer", question)
                    self.assertIn("references", question)
                    response_text = json.dumps({
                        "scores": {name: 3 for name in
                                   ("axis_score", "factuality", "rights_respect",
                                    "pluralism", "refusal_appropriateness")},
                        "rationale": "Transport test, not a real evaluation.",
                        "uncertain": True,
                    })
                else:
                    response_text = "Transport-only test response, not a real model."
                response = {"choices": [{"message": {"content": response_text}}]}
                return io.BytesIO(json.dumps(response).encode("utf-8"))

            output = path / "out"
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                manifest = run(mode="live", models_path=str(models), judges_path=str(judges),
                               output=str(output), repeats=1, limit=1)
            self.assertEqual(manifest["status"], "complete")
            self.assertFalse(manifest["synthetic"])
            self.assertEqual(manifest["responses_written"], 6)
            self.assertEqual(len(seen), 18)  # 6 generations + 12 judge calls
            summary = report(str(output))
            self.assertEqual(summary["response_count"], 6)
            self.assertEqual(summary["human_audit_queue_count"], 6)  # All judges uncertain


if __name__ == "__main__":
    unittest.main()
