# Offline re-triage of Discovery Run 001

**6 November 2026 | Preliminary engineering check — NOT a historical truth or model-bias assessment.**

Following the original [Wikimedia discovery run](https://github.com/leag1234/EuroBiasBench/actions/runs/42189493325), we analyzed the **same 100 saved candidate topics entirely offline**, avoiding new web retrieval and all candidate-model inference.

Implementation: [global discovery PR #9](https://github.com/leag1234/EuroBiasBench/pull/9), command documentation in docs/discovery-triage.md on the feature branch.

**[Successful GitHub Actions triage run](https://github.com/leag1234/EuroBiasBench/actions/runs/42209971209)**, artifact: eurobiasbench-offline-triage-001 (source-hashed outputs, reviewer CSV, English report, SHA256SUMS).

## Results

| Classification of first-year mentions in Wikipedia leads | Topics |
| --- | ---: |
| At least 3 editions begin with one year, another begins with a different year (review queue) | **6** |
| Inconclusive variation among year cues | 13 |
| Too few leads containing dates to compare | 36 |
| Identical first year among leads containing a date | 45 |
| **Total analyzed** | **100** |

**0 new Wikimedia requests, 0 LLM calls, 0 independently verified historical claims.**

The revised screen no longer treats an absent Wikipedia language edition as evidence of bias and no longer promotes every additional year mentioned by an article. Its shortlist is *not* a list of proven cultural discrepancies or historical mistakes.

## Six subjects queued for further source/context review

| Subject | Common opening-year cue | Different cue(s) |
| --- | --- | --- |
| .357 Magnum | 1934 | English: 1935 |
| Kübler–Ross model | 1969 | Spanish: 1926 |
| Mobile Telephone Service | 1946 | Chinese: 1965 |
| German Empire's 9th Army | 1914 | Russian: 1918 |
| Roe v. Wade | 1973 | Chinese: 1969 |
| Trinity County | 2000 | Arabic: 2010; English: 2020; French: 1850 |

These examples illustrate the danger of treating year mismatches as contradictions. For instance, legal proceedings may begin years before a ruling, and population statistics are routinely taken in different years. These cases need proposition-level examination and independent references. **None has been established as wrong, censored or culturally biased.**

## Scientific implications

The output is smaller and more focused (**6 rather than 20 heuristic priorities**), but a smaller candidate set is **not itself evidence of increased precision**. Precision can only be measured by independent review of accepted and rejected candidates, with transparent sampling and false-negative assessment. We should retain all 100 screened topics for that audit.

**Next necessary improvement:** structured Wikidata entity typing, genuine geography/era/domain stratification, claim-level extraction and source verification. Avoid optimizing one simplistic date heuristic into a purported model-bias score. See [issue #14](https://github.com/leag1234/EuroBiasBench/issues/14), [issue #12](https://github.com/leag1234/EuroBiasBench/issues/12), and [issue #11](https://github.com/leag1234/EuroBiasBench/issues/11).

**No new paid inference or recurring crawling is authorized by this report.**
