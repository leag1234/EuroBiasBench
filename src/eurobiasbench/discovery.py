"""Global topic discovery prototype: signals for research, never historical truth.

Offline fixture mode makes no network requests. Live mode uses bounded Wikimedia
Action API reads; it never calls candidate LLMs or paid inference APIs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_LANGUAGES = ("en", "fr", "es", "ar", "zh", "ru")
YEAR_PATTERN = re.compile(r"(?<![0-9])(?:1[0-9]{3}|20[0-9]{2})(?![0-9])")
WIKIDATA_ENDPOINT = "https://www.wikidata.org/w/api.php"
USER_AGENT = "EuroBiasBench-Discovery/0.2 (https://github.com/leag1234/EuroBiasBench; research project contact via GitHub Issues)"


def batches(values: list[Any], size: int) -> list[list[Any]]:
    return [values[i:i + size] for i in range(0, len(values), size)]


@dataclass
class RequestBudget:
    """Finite, serial, identified Wikimedia access; explicit request counters."""
    max_requests: int = 80
    timeout_seconds: int = 15
    sleep_seconds: float = 0.2
    used: int = 0

    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.used >= self.max_requests:
            raise RuntimeError("Network request budget exhausted; aborting safely")
        if not endpoint.startswith("https://"):
            raise ValueError("HTTPS endpoint required")
        allowed = endpoint == WIKIDATA_ENDPOINT or (
            endpoint.endswith(".wikipedia.org/w/api.php")
            and endpoint.split("://")[1].split(".")[0] in DEFAULT_LANGUAGES
        )
        if not allowed:
            raise ValueError("Endpoint is not a permitted Wikimedia API")
        self.used += 1
        url = endpoint + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = response.read(6_000_001)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Wikimedia request failed ({endpoint}): {exc}") from exc
        if len(data) > 6_000_000:
            raise RuntimeError("Refusing oversized Wikimedia response")
        obj = json.loads(data.decode("utf-8"))
        if not isinstance(obj, dict) or obj.get("error"):
            raise RuntimeError(f"Wikimedia API error: {obj.get('error') if isinstance(obj, dict) else 'invalid body'}")
        if self.sleep_seconds:
            time.sleep(self.sleep_seconds)
        return obj


def wikipedia_api(lang: str) -> str:
    if lang not in DEFAULT_LANGUAGES:
        raise ValueError(f"Unsupported language edition: {lang}")
    return f"https://{lang}.wikipedia.org/w/api.php"


def sample_random_articles(lang: str, count: int, budget: RequestBudget) -> list[dict[str, str]]:
    """Unbiased within a wiki's random-page sampling frame, NOT world-representative."""
    data = budget.get(wikipedia_api(lang), {
        "action": "query", "generator": "random", "grnnamespace": 0,
        "grnlimit": min(count, 50), "prop": "pageprops",
        "ppprop": "wikibase_item|disambiguation", "format": "json",
        "formatversion": 2,
    })
    result = []
    for page in data.get("query", {}).get("pages", []):
        props = page.get("pageprops", {})
        qid = props.get("wikibase_item", "")
        if re.fullmatch(r"Q[0-9]+", qid) and "disambiguation" not in props:
            result.append({"qid": qid, "title": page.get("title", ""), "source_language": lang})
    return result


def wikidata_entities(qids: list[str], langs: tuple[str, ...], budget: RequestBudget) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for group in batches(qids, 25):
        result = budget.get(WIKIDATA_ENDPOINT, {
            "action": "wbgetentities", "ids": "|".join(group),
            "props": "sitelinks|labels|descriptions", "sitefilter": "|".join(x + "wiki" for x in langs),
            "languages": "|".join(langs), "format": "json",
        })
        for qid, value in result.get("entities", {}).items():
            if not value.get("missing") and re.fullmatch(r"Q[0-9]+", qid):
                out[qid] = value
    return out


def fetch_intro_pages(topics: list[dict], langs: tuple[str, ...], budget: RequestBudget) -> None:
    """Collect short leads + revision metadata; do not assume leads are factual authority."""
    for lang in langs:
        indexed = [(t, t["sitelinks"][lang]["title"]) for t in topics if lang in t["sitelinks"]]
        for group in batches(indexed, 15):
            titles = [title for _, title in group]
            result = budget.get(wikipedia_api(lang), {
                "action": "query", "prop": "extracts|revisions",
                "titles": "|".join(titles),
                "exintro": 1, "explaintext": 1, "exchars": 800,
                "rvprop": "ids|timestamp",
                "format": "json", "formatversion": 2,
            })
            found = {
                page.get("title", "").replace("_", " ").casefold(): page
                for page in result.get("query", {}).get("pages", [])
                if not page.get("missing")
            }
            for topic, title in group:
                page = found.get(title.replace("_", " ").casefold())
                if not page:
                    continue
                rev = (page.get("revisions") or [{}])[0]
                topic["leads"][lang] = {
                    "text": page.get("extract", "")[:1500],
                    "revision_id": rev.get("revid"),
                    "revision_timestamp": rev.get("timestamp"),
                }


def balanced_select(topics: list[dict], limit: int, langs: tuple[str, ...]) -> list[dict]:
    """Round robin over seed language; this does NOT equal geographic stratification."""
    groups = {
        lang: sorted((t for t in topics if t["source_language"] == lang), key=lambda t: t["qid"])
        for lang in langs
    }
    output: list[dict] = []
    index = 0
    while len(output) < limit and any(index < len(items) for items in groups.values()):
        for lang in langs:
            if index < len(groups[lang]):
                output.append(groups[lang][index])
                if len(output) == limit:
                    break
        index += 1
    return output


def discover_live(*, target: int, langs: tuple[str, ...], pages_per_language: int,
                  budget: RequestBudget) -> list[dict]:
    if target < 1 or pages_per_language < 1 or pages_per_language > 50:
        raise ValueError("target must be positive and pages_per_language 1..50")
    pool: dict[str, dict] = {}
    for lang in langs:
        for page in sample_random_articles(lang, pages_per_language, budget):
            if page["qid"] not in pool:
                pool[page["qid"]] = {**page, "sitelinks": {}, "leads": {}}
    entities = wikidata_entities(sorted(pool), langs, budget)
    eligible: list[dict] = []
    for qid, entity in entities.items():
        item = pool[qid]
        links = {}
        for lang in langs:
            entry = entity.get("sitelinks", {}).get(lang + "wiki")
            if entry and entry.get("title"):
                links[lang] = {"title": entry["title"], "url": "https://" + lang + ".wikipedia.org/wiki/" + urllib.parse.quote(entry["title"].replace(" ", "_"), safe="/")}
        if len(links) < 2:
            continue
        labels = entity.get("labels", {})
        item["label"] = (
            labels.get("en", {}).get("value")
            or next(iter(labels.values()), {}).get("value")
            or item["title"]
        )
        item["sitelinks"] = links
        eligible.append(item)
    selected = balanced_select(eligible, target, langs)
    fetch_intro_pages(selected, langs, budget)
    return selected


def signal_record(topic: dict, langs: tuple[str, ...]) -> dict:
    links = topic.get("sitelinks", {})
    leads = topic.get("leads", {})
    years = {lang: sorted(set(YEAR_PATTERN.findall(record.get("text", ""))))
             for lang, record in leads.items() if record.get("text")}
    union = set().union(*(set(x) for x in years.values())) if years else set()
    tags = []
    if len(links) < len(langs):
        tags.append("wikipedia_language_coverage_gap")
    if links and len(leads) < len(links):
        tags.append("article_lead_unavailable")
    if len(years) >= 2 and union and any(set(ys) != union for ys in years.values()):
        tags.append("lead_year_mention_asymmetry")
    score = len(tags)
    return {
        "qid": topic["qid"], "label": topic.get("label", ""),
        "source_language": topic.get("source_language", ""),
        "signal_tags": tags, "signal_count": score,
        "years_mentioned_by_language": years,
        "languages_with_articles": sorted(links),
        "languages_with_lead_snapshots": sorted(leads),
        "interpretation": "Candidate coverage/chronology discrepancy only; not verified historical truth or model bias.",
        "review_status": "unverified_candidate",
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def export(topics: list[dict], *, directory: str, langs: tuple[str, ...],
           source: str, request_count: int = 0, signal_limit: int = 20,
           dossier_limit: int = 10) -> dict:
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in (
        "topics.jsonl", "signals.jsonl", "dossier_queue.jsonl", "manifest.json"
    )):
        raise FileExistsError("Output already exists; use a new directory")
    unique = {item["qid"]: item for item in topics}
    subjects = sorted(unique.values(), key=lambda x: x["qid"])
    signals = sorted((signal_record(s, langs) for s in subjects),
                     key=lambda s: (-s["signal_count"], s["qid"]))[:signal_limit]
    dossier_queue = [
        {
            "qid": s["qid"], "label": s["label"], "signals": s["signal_tags"],
            "status": "needs_independent_sources_and_human_approval",
            "claim_verified": False,
            "research_question": (
                f"Which material facts, perspectives and uncertainties about {s['label']} "
                "are supported by independent primary and scholarly sources?"
            ),
        }
        for s in signals[:dossier_limit] if s["signal_count"] > 0
    ]
    _write_jsonl(out / "topics.jsonl", subjects)
    _write_jsonl(out / "signals.jsonl", signals)
    _write_jsonl(out / "dossier_queue.jsonl", dossier_queue)
    manifest = {
        "experiment": "global-discovery-poc-0.1", "source": source,
        "synthetic": source == "synthetic_fixture",
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "languages": list(langs), "wikipedia_source_languages_not_regions": True,
        "topics": len(subjects), "screened_signals": len(signals),
        "unverified_dossier_queue": len(dossier_queue), "request_count": request_count,
        "verified_historical_claims": 0, "model_inference_calls": 0,
        "limitations": [
            "Signals represent article/lead discrepancies, not bias or verified truth.",
            "No independent archival/scholarly evidence has been retrieved.",
            "Random Wikipedia pages are not a representative sample of world history.",
            "Different language editions are not independent historical sources.",
        ],
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tally = Counter(x["source_language"] for x in subjects)
    lines = [
        "# Global Discovery POC — screening only", "",
        f"- Source: {source}", f"- Synthetic fixture: {manifest['synthetic']}",
        f"- Candidate topics: {len(subjects)}",
        f"- Discrepancy signal records: {len(signals)}",
        f"- Unverified dossiers awaiting independent sources: {len(dossier_queue)}",
        f"- Wikimedia requests: {request_count}",
        "- Candidate-model inference calls: **0**", "",
        "## Sampling-language composition", "",
    ]
    lines.extend(f"- {lang}: {tally[lang]}" for lang in langs)
    lines += ["", "## Scientific warning", "",
              "**No topic in this run has been proven culturally biased or historically true by this tool.**",
              "Signals are deterministic Wikipedia lead/coverage differences for human triage.",
              "Different editions are neither independent sources nor a universal gold standard.",
              "Before any model study, independently verify exact claims with dated primary and scholarly sources.",
              "", "## Top candidates (NOT verified findings)", "",
              "| Wikidata ID | Label | Signals |", "| --- | --- | --- |"]
    for item in signals[:20]:
        lines.append("| " + item["qid"] + " | " + item["label"].replace("|", "\\|")
                     + " | " + ", ".join(item["signal_tags"]) + " |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    names = ("topics.jsonl", "signals.jsonl", "dossier_queue.jsonl", "manifest.json", "report.md")
    checksum_lines = [
        f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}"
        for name in names
    ]
    (out / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return manifest


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Bounded global candidate discovery (not model inference)")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--fixture", help="Offline JSON fixture containing synthetic topic records")
    modes.add_argument("--live", action="store_true", help="Explicitly allow bounded Wikimedia requests")
    parser.add_argument("--output", default="results/discovery")
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--pages-per-language", type=int, default=40)
    parser.add_argument("--max-requests", type=int, default=90)
    parser.add_argument("--signal-limit", type=int, default=20)
    parser.add_argument("--dossier-limit", type=int, default=10)
    parser.add_argument("--languages", default="en,fr,es,ar,zh,ru")
    args = parser.parse_args(argv)
    langs = tuple(x.strip() for x in args.languages.split(",") if x.strip())
    if not langs or len(langs) != len(set(langs)) or any(x not in DEFAULT_LANGUAGES for x in langs):
        parser.error("Languages must be a nonempty unique subset of en,fr,es,ar,zh,ru")
    if min(args.target, args.max_requests, args.signal_limit, args.dossier_limit) < 1:
        parser.error("Targets and request limits must be positive")
    if args.dossier_limit > args.signal_limit:
        parser.error("dossier-limit must not exceed signal-limit")
    if args.fixture:
        data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("topics"), list):
            parser.error("Fixture must have a topics array")
        topics = balanced_select(data["topics"], args.target, langs)
        source = "synthetic_fixture"
        count = 0
    else:
        budget = RequestBudget(max_requests=args.max_requests)
        topics = discover_live(target=args.target, langs=langs,
                               pages_per_language=args.pages_per_language, budget=budget)
        source, count = "wikimedia", budget.used
    result = export(topics, directory=args.output, langs=langs, source=source,
                    request_count=count, signal_limit=args.signal_limit,
                    dossier_limit=args.dossier_limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
