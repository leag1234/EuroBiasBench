"""Conservative offline Wikimedia discrepancy triage; never a historical truth test."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

YEAR = re.compile(r"(?<![0-9])(?:1[0-9]{3}|20[0-9]{2})(?![0-9])")


def classify(topic: dict, minimum_agreement: int = 3) -> dict:
    if minimum_agreement < 2:
        raise ValueError("minimum_agreement must be >=2")
    leads = topic.get("leads", {})
    opening = {}
    for lang, record in sorted(leads.items()):
        match = YEAR.search((record.get("text") or "")[:800])
        opening[lang] = match.group(0) if match else None
    votes = Counter(value for value in opening.values() if value is not None)
    winner, count = sorted(votes.items(), key=lambda x: (-x[1], x[0]))[0] if votes else (None, 0)
    outliers = {lang: value for lang, value in opening.items() if value is not None and value != winner}
    candidate = count >= minimum_agreement and bool(outliers)
    category = ("opening_year_review_candidate" if candidate else
                "insufficient_dated_leads" if len([v for v in opening.values() if v]) < 2 else
                "same_opening_year" if len(votes) == 1 else
                "inconclusive_opening_year_variation")
    return {
        "qid": topic["qid"], "label": topic.get("label", ""),
        "category": category, "review_priority": int(candidate),
        "opening_years": opening, "consensus_year": winner,
        "consensus_language_count": count, "other_opening_years": outliers,
        "historical_claims_verified": 0, "review_status": "unreviewed",
        "warning": "First mentioned years can refer to different facts. Not a historical contradiction or cultural bias.",
    }


def triage(source: str, output: str, *, min_consensus: int = 3, limit: int = 20) -> dict:
    if limit < 1:
        raise ValueError("limit must be positive")
    raw = Path(source).read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not records:
        raise ValueError("Empty topics file")
    ids = [item["qid"] for item in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate Wikidata subject ID")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    files = ("triage.jsonl", "review_queue.csv", "report.md", "manifest.json", "SHA256SUMS")
    if any((out / name).exists() for name in files):
        raise FileExistsError("Existing output found; choose a new directory")
    rows = [classify(record, min_consensus) for record in records]
    rows.sort(key=lambda r: (-r["review_priority"], -r["consensus_language_count"], r["qid"]))
    selected = [r for r in rows if r["review_priority"]][:limit]
    (out / "triage.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows), encoding="utf-8")
    with (out / "review_queue.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "qid", "label", "consensus_year", "languages_agreeing",
            "other_years_json", "review_outcome", "review_reason", "independent_source_url"])
        writer.writeheader()
        for row in selected:
            writer.writerow({
                "qid": row["qid"], "label": row["label"],
                "consensus_year": row["consensus_year"],
                "languages_agreeing": row["consensus_language_count"],
                "other_years_json": json.dumps(row["other_opening_years"], ensure_ascii=False),
                "review_outcome": "", "review_reason": "", "independent_source_url": ""})
    categories = dict(Counter(r["category"] for r in rows))
    manifest = {
        "version": "offline-triage-0.1",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "subject_count": len(rows), "selected_for_review": len(selected),
        "category_counts": categories, "minimum_agreement": min_consensus,
        "new_network_requests": 0, "llm_calls": 0, "verified_historical_claims": 0,
        "warning": "Language coverage is not evidence of bias; dates here are unverified editorial cues.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    lines = ["# Offline pilot triage", "",
             "No LLM or Wikimedia requests were made. These are unverified editorial cues.", "",
             f"Subjects: {len(rows)}; review candidates: {len(selected)}", "",
             "## Category counts"]
    lines.extend(f"- {name}: {count}" for name, count in sorted(categories.items()))
    lines.extend(["", "## Candidate shortlist (not proven bias)", "",
                  "| QID | Subject | Majority first year | Other first year(s) |",
                  "| --- | --- | --- | --- |"])
    for item in selected:
        other = ", ".join(f"{k}: {v}" for k, v in item["other_opening_years"].items())
        lines.append(f"| {item['qid']} | {item['label'].replace('|', '/')} | {item['consensus_year']} | {other} |")
    lines.extend(["", "Opening years may refer to different propositions. An independent",
                  "historical source is required before claiming factual contradiction.",
                  "Source-language gaps are not counted as priority evidence.",
                  "This convenience Wikipedia sample is not globally representative.", ""])
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}\n"
        for name in files if name != "SHA256SUMS"), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Offline-only triage of already collected subjects")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-consensus", type=int, default=3)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    print(json.dumps(triage(args.input, args.output,
                            min_consensus=args.min_consensus, limit=args.limit), indent=2))


if __name__ == "__main__":
    main()
