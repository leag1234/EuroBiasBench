# Global Discovery POC — first real screening run

**Date:** 6 November 2026 (UTC)  
**Status:** source-discovery and pipeline validation only; not a bias finding

## Execution

- [GitHub Actions run 42189493325](https://github.com/leag1234/EuroBiasBench/actions/runs/42189493325) — successful after fixing an unsupported multi-page MediaWiki revision parameter in the first attempt.
- Implementation: [stacked PR #9](https://github.com/leag1234/EuroBiasBench/pull/9), based on the unmerged evaluation implementation [PR #1](https://github.com/leag1234/EuroBiasBench/pull/1).
- Artifact name: **eurobiasbench-discovery-screening-only**, uploaded in the run (14-day artifact retention). The output archive contains SHA256SUMS, manifest.json, topics.jsonl, signals.jsonl, dossier_queue.jsonl and report.md.

| Quantity | Observed |
| --- | ---: |
| Linked candidate topics | **100** |
| Discrepancy signal records selected for screening | **20** |
| Unverified topics placed in the independent evidence queue | **10** |
| Wikimedia HTTP requests | **42** (hard cap was 90) |
| Candidate LLM calls / paid inference | **0 / €0 inference** |
| Source language editions | English, French, Spanish, Arabic, Chinese, Russian |

The 100 subjects were deliberately sampled in balanced **language-edition strata** (17 each from en/fr/es/ar, and 16 each from zh/ru). **These are not six countries or geographic regions.** The topic selection was random within each Wikipedia edition subject to deduplication and cross-language availability; it was not a representative world-history sample.

## What the first run taught us

**The data transport works; discovery quality is not yet good enough.** The leading signal records include municipalities, sports competitions, entertainment entries, biographies and other subjects where absent language editions or year mentions are often ordinary editorial differences. Examples from the unverified queue include James Hill Township, a 2022 South American Games volleyball page, a Japanese electoral district and a television season.

That noise is an important negative result: selecting 20 top scores under simplistic heuristics **does not** mean we have discovered 20 culturally relevant disputes, and the ten generated queue entries are **not verified historical evidence dossiers**.

**Zero historical claims have been independently verified and zero model biases demonstrated** by this run. The signal tags (coverage gaps and divergent year mentions in short leads) are highly susceptible to article scope, popularity, translation and date-selection effects.

## Next technical corrections before another broad discovery run

1. **Stratify by actual subject type, time period and geographic region**, not only by Wikipedia language. Use Wikidata claims with explicit provenance and missingness. Preserve low-salience inventions/science/culture as well as contentious historical events.
2. **Improve signal relevance**: exclude mismatched lead scopes, report base rates and compare against random controls. Do not rank articles merely because an edition is missing or a year is mentioned in one lead.
3. **Add independent source research** (archives, museum collections, specialist literature), record evidence dependencies, and require case-specific verified facts and materiality before calling any item a benchmark question.
4. Human reviewers should inspect a small, stratified subset of discovered signals and **measure the false-positive rate of the discovery tool**, separately from the existing 25-answer human calibration in [Issue #8](https://github.com/leag1234/EuroBiasBench/issues/8).
5. **Do not trigger new paid model inference** or build a public leaderboard until the evidence and measurement gates succeed.

### Related issues

- [#10 — bounded live discovery screening](https://github.com/leag1234/EuroBiasBench/issues/10)
- [#11 — independent evidence dossiers](https://github.com/leag1234/EuroBiasBench/issues/11)
- [#12 — geographic, temporal and domain coverage](https://github.com/leag1234/EuroBiasBench/issues/12)
- [#13 — future behavioral model tests](https://github.com/leag1234/EuroBiasBench/issues/13)

**Research principle:** difference of narratives is a useful hypothesis-generator. Historical truth and cultural bias require additional evidence and calibrated, contestable tests; neither can be inferred from language-edition differences alone.
