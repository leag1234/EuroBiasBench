# Offline triage of the first real discovery run

**Status: unvalidated screening heuristic, not an evaluation of historical truth.**

The initial 100-topic Wikimedia run scored missing Wikipedia editions and differences in any year mentioned in the article lead. This produced many weak candidates: municipalities, TV seasons and sports listings.

The new baseline is deliberately stricter: missing language editions are not evidence of bias. Dates appearing in only one edition do not count. A topic is queued for review only if at least three editions first mention the same four-digit year and a fourth first mentions a different year.

This *opening-year cue* is **not** a historical contradiction: one lead may mention an invention date and another a commercial launch, or a legal case filing date and another its judgment date. The selected topics are only a reviewer queue, not confirmed omissions or errors.

## Offline execution

Extract the successful GitHub Action artifact from discovery run 42189493325. From the project root:

    eurobiasbench triage --input results/discovery-run/topics.jsonl --output results/triage-001

Outputs: triage.jsonl, review_queue.csv, manifest.json, report.md and SHA256SUMS.

No new network requests and no model inference. The CSV leaves review outcome and independent-source fields empty. Reviewers should record: **not comparable**, **needs independent sources**, **potentially material**, or **cannot assess**. Verified primary or scholarly source references are required before using any row as a model benchmark case.

This is a screen for potentially useful verification work. It neither identifies cultural bias automatically nor solves world-region/period/domain representativeness. For that, see GitHub issues #11, #12 and #14.
