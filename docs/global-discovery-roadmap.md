# Global Bias Discovery — research architecture and staged roadmap

**Version:** design 0.2 (6 November 2026). **Status:** proposal + bounded POC. No worldwide bias claims or new model inference.

## Scientific question

Can we automatically **discover previously unselected topics** for which descriptions vary across language communities or reference traditions, establish which differences are factual versus narrative, and then test whether model outputs systematically inherit these differences without replacing one national narrative with another?

## Core outputs and gates

| Stage | Planned POC output | Scientific gate |
| --- | --- | --- |
| 0 — Sampling | up to 100 candidate subjects selected without manually naming individual events | coverage & selection provenance, exclusions, fetch budget, reproducible IDs |
| 1 — Screening | up to 20 high-signal candidate *discrepancies* | source snapshots, language metadata; no inferred bias labels |
| 2 — Evidence | up to 10 candidate source dossiers | independently verified sources, date, precise claims, consensus / dispute / unknown |
| 3 — Test design | explicit factual, omission, source and framing test specs | human review of criteria and question materiality |
| 4 — Model study | separate bounded offline/paid study **only after authorization** | held-out tests, multiple repeats, baselines, calibrated judge/human audit |

Numbers are **aspirational caps**, not promised empirical yields. Yield and sampling coverage are themselves POC results.

## Taxonomy (complementary, not one alignment score)

1. **Fact suppression/refusal:** unjustified non-answer or omission of material established facts, under controlled prompt conditions.
2. **Factual distortion:** chronological, attribution, legal, geographic or numerical errors relative to verified evidence.
3. **Narrative selection:** disproportionate emphasis or omission of material actors/causes, carefully conditioned on the actual question.
4. **Source-selection skew:** preference for particular provenance under **equally relevant, equally trustworthy** source conditions; requires controlled tool/RAG experiments.
5. **Framing bias:** contested labels or causal claims presented as unqualified facts, regardless of political direction.
6. **Uncertainty calibration:** factual uncertainty hidden or inflated (false balance) when evidence is uneven.

## Data and provenance

Each candidate topic receives: stable Wikidata ID where available, source-language sampling frame, article titles, revision identifiers or retrieval timestamps, source URLs, fetch errors, candidate-discrepancy signals, metadata on type and dated scope if available, and a versioned corpus hash. The original source's language and institution are recorded but **never counted as proof of trustworthiness**.

Each *verified* evidence dossier additionally needs: atomic claim IDs, original quotations or faithful descriptions, precise source location, author/publisher/date, source type, dependencies among witnesses, claims supported, claims disputed, limitations, reviewer and review date. Wikipedia may guide discovery but **must not be treated as an independent historical authority merely because several editions agree**.

## Sampling and global coverage requirements

Begin by sampling across several Wikipedia language editions; **source language is not geographic origin**. Record uneven language coverage and absent cross-language links. In later phases, stratify by *actual region, historical period, event type and domain*, obtained from Wikidata claims and secondary catalogs, and audit underrepresented strata. A POC using a few language editions must not claim coverage of all epochs or regions.

To avoid a popularity-only benchmark, include both highly controversial topics and low-salience attribution, invention, scientific and cultural histories. No preferred narrative or list of exemplary controversies may dominate the discovery sampler.

## Automated screening is triage, not verification

Use Wikipedia and Wikidata to find entities and compare cross-language article coverage and elementary chronological signals. Differences in years mentioned, lead-page presence and source coverage are **warnings to investigate**, not automatically factual contradictions, censorship, political favoritism or omissions by a model. Translation and article-length differences can create false positives.

Only an independently sourced claim dossier can support scoring of a model's answer. Model-suggested citations, self-reported training sources or unverified Wikipedia summaries do not establish an evidence standard. A government statement documents that government's position but does not settle a disputed event.

## Automation boundary

**Automatable now:** bounded candidate retrieval, ID linking, article/metadata snapshotting, deterministic anomaly heuristics, report generation, de-duplication and extraction queues.

**Human or specialized verification:** historian/source criticism, contested interpretation, definition of 'material omission', legal applicability and validity of a claim-specific scoring key. Community annotators may do bounded microtasks with an abstain option; experts arbitrate high-stakes factual disputes.

**Human calibration remains separate:** [25 saved Run 002 responses, two independent raters](human-calibration-pilot-25.md). No new candidate-model inference is necessary for this work.

## Next work items

- P0: Ship a small, zero-GPU discovery CLI with offline fixtures, deterministic outputs, bounded live Wikimedia requests and CI tests.
- P0: Publish 100-candidate/20-signal/10-evidence schema with explicit provenance and no auto-truth claims.
- P1: Evidence dossier generator with structured source annotations and manual approval gate.
- P1: Multisource verifier with overlap/dependency detection and distinct categories for disagreement, uncertainty and factual contradiction.
- P1: Community microtask design building on the 25-response annotation experiment.
- P2: Region/period/domain-balanced discovery with documented coverage audits.
- P2: Controlled candidate-model tests and EuroAlign correction evaluation, separately budget-approved.

## External technical references

- [MediaWiki Action API random generator](https://www.mediawiki.org/wiki/API:Random)
- [Wikibase entity access](https://www.mediawiki.org/wiki/API:Presenting_Wikidata_knowledge)
- [Wikimedia REST APIs and access policy](https://www.mediawiki.org/wiki/Wikimedia_REST_API)
- [Wikidata Query Service limits](https://www.mediawiki.org/wiki/Wikidata_query_service/Implementation)

Respect Wikimedia identification, request limits, licenses and attribution requirements. No scheduled high-volume scraping or paid inference is introduced by this design.
