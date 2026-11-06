# Discovery POC — operator guide

**Status:** executable candidate-discovery and discrepancy-screening prototype; no historical facts verified; no LLM inference. This module depends on the pilot implementation branch and is being reviewed in a stacked pull request.

## What this prototype actually does

1. Samples Wikipedia main-namespace pages using a **bounded** query to several language editions (en, fr, es, ar, zh, ru). All sampling is at the *language-edition level*, **not** by country or historical period.
2. Uses Wikidata item IDs to deduplicate subjects and look up their cross-language article sitelinks.
3. Records a bounded lead extract and page revision information for available language editions.
4. Emits deterministic screening signals for absent language editions, missing extracts and mismatched **mentions of years** in leads.
5. Queues up to 10 subjects for **independent historical/source verification**. These are **not completed evidence dossiers**.

Nothing here establishes that any article or model is culturally biased, that an omission is material, or that the historical facts in any encyclopedia article are correct.

## Quick start without internet

From the implementation branch:

~~~bash
python -m pip install -e .
eurobiasbench discover --fixture tests/fixtures/discovery_synthetic.json --target 6 --output results/discovery-demo
~~~

The fixture contains entirely synthetic fictional subjects and is tagged synthetic_fixture. This validates the pipeline only, not the existence of global disparities.

## Explicitly authorized live Wikimedia run (zero GPUs, zero candidate-model calls)

~~~bash
eurobiasbench discover --live --target 100 --pages-per-language 40 --max-requests 90 --signal-limit 20 --dossier-limit 10 --output results/discovery-live-001
~~~

This requires Wikimedia connectivity and is **never invoked by default, during installation or by unit tests**. It makes serial identified GET requests and raises if the specified request limit is reached. The budget covers only request count, **not** a guaranteed completion time or worldwide sampling coverage. Follow Wikimedia access and content-licensing policies. Source texts are placed in the local results folder, which should not be committed automatically.

## Output files

| Name | Meaning |
| --- | --- |
| topics.jsonl | Candidate Wikidata-linked subjects, source language, Wikipedia article titles and available excerpts |
| signals.jsonl | Possible lead-year and language-coverage divergences, flagged unverified |
| dossier_queue.jsonl | Subjects needing independent dated primary/scholarly source research; **no verified claims** |
| manifest.json | Collection date, language sampling frame, request count, synthetic flag, counts and limitations |
| report.md | Plain-English screening report; **no model rankings or inferred historical truth** |
| SHA256SUMS | Digests of all output artifacts |

Every run must use a **new output folder** to avoid silent overwrites. Preserve the hashes, article revision metadata, collection date and configuration when comparing snapshots.

## Scientific limits and design obligations

- Wikipedia editions are not independent evidence: translations and shared sources create dependence.
- A change in a year mentioned may reflect summary length or editorial emphasis, **not** disagreement about the year.
- Wikipedia language coverage does not establish geographic or cultural representativeness; a global sampling audit is future work.
- Question generation, atomic-claim verification and scoring of model responses are **not** implemented in this prototype.
- An independent source dossier must be approved before an omission or contradiction can become a scored benchmark criterion.
- No automatic 600-case expansion, paid inference, weight editing or scheduled Wikimedia scraping is authorized.
- The 25-response human calibration based on saved Run 002 answers remains a separate [ongoing issue](https://github.com/leag1234/EuroBiasBench/issues/8).

## Planned next layer

Add curated primary-source and scholarly-source connectors, provenance graphs, source dependency audits, region/period/domain stratification and reviewer-mediated claim assertions. Only then generate controlled tests and compare model responses against a validated reference. See [global roadmap on main](https://github.com/leag1234/EuroBiasBench/blob/main/docs/global-discovery-roadmap.md).
