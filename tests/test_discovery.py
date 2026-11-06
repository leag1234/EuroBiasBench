"""Network-free tests for topic discovery, screening and provenance."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eurobiasbench.discovery import (
    DEFAULT_LANGUAGES, RequestBudget, balanced_select, discover_live, export,
    signal_record, wikipedia_api,
)

FIXTURE = Path(__file__).parent / "fixtures" / "discovery_synthetic.json"


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.topics = json.loads(FIXTURE.read_text(encoding="utf-8"))["topics"]

    def test_offline_fixture_is_clearly_synthetic(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = export(self.topics, directory=tmp, langs=DEFAULT_LANGUAGES,
                            source="synthetic_fixture", signal_limit=5, dossier_limit=3)
            self.assertEqual(result["topics"], 6)
            self.assertTrue(result["synthetic"])
            self.assertEqual(result["model_inference_calls"], 0)
            self.assertEqual(result["verified_historical_claims"], 0)
            self.assertTrue((Path(tmp) / "SHA256SUMS").exists())
            self.assertIn("NOT verified", (Path(tmp) / "report.md").read_text())

    def test_refuses_to_overwrite_existing_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            export(self.topics, directory=tmp, langs=DEFAULT_LANGUAGES,
                   source="synthetic_fixture")
            with self.assertRaises(FileExistsError):
                export(self.topics, directory=tmp, langs=DEFAULT_LANGUAGES,
                       source="synthetic_fixture")

    def test_year_difference_is_signal_not_a_fact_claim(self):
        item = signal_record(self.topics[0], DEFAULT_LANGUAGES)
        self.assertIn("lead_year_mention_asymmetry", item["signal_tags"])
        self.assertEqual(item["review_status"], "unverified_candidate")
        self.assertIn("not verified", item["interpretation"])

    def test_no_year_difference_if_same_mentions(self):
        item = signal_record(self.topics[3], DEFAULT_LANGUAGES)
        self.assertNotIn("lead_year_mention_asymmetry", item["signal_tags"])

    def test_balanced_select_and_no_duplicates(self):
        items = balanced_select(self.topics, limit=5, langs=DEFAULT_LANGUAGES)
        self.assertEqual(len(items), 5)
        self.assertEqual(len({x["qid"] for x in items}), 5)

    def test_invalid_wiki_endpoint(self):
        with self.assertRaises(ValueError):
            wikipedia_api("xx")
        budget = RequestBudget(max_requests=1, sleep_seconds=0)
        with self.assertRaises(ValueError):
            budget.get("https://example.com/w/api.php", {})
        self.assertEqual(budget.used, 0)

    def test_live_read_uses_only_mocked_wikimedia_endpoints(self):
        budget = RequestBudget(max_requests=8, sleep_seconds=0)
        calls = []

        def fake_get(url, args):
            calls.append((url, args["action"]))
            if args["action"] == "query" and "generator" in args:
                lang = url.split("://")[1].split(".")[0]
                return {"query": {"pages": [
                    {"title": "Sample " + lang, "pageprops": {"wikibase_item": "Q123"}}
                ]}}
            if args["action"] == "wbgetentities":
                return {"entities": {"Q123": {
                    "labels": {"en": {"value": "Example"}},
                    "sitelinks": {
                        "enwiki": {"title": "Sample en"},
                        "frwiki": {"title": "Sample fr"},
                    },
                }}}
            if args["action"] == "query":
                self.assertNotIn("rvlimit", args)
                titles = args["titles"].split("|")
                return {"query": {"pages": [
                    {"title": t, "extract": "An example from 1973.", "revisions": [{"revid": 7}]}
                    for t in titles
                ]}}
            raise AssertionError("Unexpected API call")

        with patch.object(budget, "get", side_effect=fake_get):
            result = discover_live(target=1, langs=("en", "fr"),
                                   pages_per_language=1, budget=budget)
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]["leads"]), {"en", "fr"})
        self.assertEqual(len(calls), 5)
        self.assertTrue(all("wikipedia.org" in url or "wikidata.org" in url for url, _ in calls))


if __name__ == "__main__":
    unittest.main()
