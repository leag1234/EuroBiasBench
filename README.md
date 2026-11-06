# EuroBiasBench

**A global, evidence-grounded research framework for discovering and evaluating cultural, historical, geopolitical, and knowledge-selection biases in language models.**

> **Research status — 6 November 2026:** exploratory evaluation infrastructure exists in [PR #1](https://github.com/leag1234/EuroBiasBench/pull/1), the first pilot identified severe disagreement between LLM judges, and a 25-response human calibration has been planned but **not yet performed**. An automated discovery proof of concept is the next technical workstream. No scientifically validated overall model ranking is claimed.

## Immediate priority: EuroAlign weight-editing feasibility (P0)

**The primary project question is whether an open-weight model can be corrected at the weight level for a real, measured cultural/normative behavior, while preserving general capability.** The generalized discovery engine is supportive research and **must not become a prerequisite for answering that question**.

The [EuroAlign POC 001 go/no-go protocol (Issue #15)](https://github.com/leag1234/EuroBiasBench/issues/15) and [executable experimental implementation (PR #16)](https://github.com/leag1234/EuroBiasBench/pull/16) specifies **one model (Qwen3-14B), one reproducible observed defect, a bounded direct weight-edit attempt without gradients, a separate LoRA baseline, frozen unseen prompts and safety/capability controls**. No cloud budget is committed merely by opening this issue.

**Research decision:** prioritize this small, falsifiable edit test; pause further expansions of the global discovery pipeline and community benchmark until a direct patch or a clear negative outcome is documented.

## Mission

**Discover, document, and test model behavior across world history and knowledge, not just a hand-picked set of political controversies.** EuroBiasBench investigates factual errors, missing material information, source-selection asymmetries, narrative framing, unjustified refusals and miscalibrated uncertainty. It distinguishes the *truth of a proposition* from its *narrative salience* and from the *origin of the evidence used to support it*.

Researchers should be able to explore topics from **any period, geographical region and academic or cultural domain**. European Union principles provide the governance and pluralism framework, **not** a requirement that models endorse the EU, favor European sources, or adopt country-specific EU value profiles. Legal compliance and ethical values remain different from historical truth.

## Architecture

1. **Bias Discovery:** sample candidate topics across languages and structured knowledge graphs; detect *possible* coverage, chronology or framing asymmetries, including low-salience omissions.
2. **Evidence Verification:** gather independent primary and scholarly sources; build versioned, contestable atomic claims, chronology, contested interpretations and uncertainty records.
3. **Behavioral Evaluation:** generate controlled, multilingual questions; measure verifiable errors, omissions relative to a question, source use, framing, refusals and uncertainty. Report each dimension separately.
4. **Human Calibration:** validate the specific claims and scoring criteria; use community contributors for bounded microtasks while escalating complex historical or legal disputes to specialists.
5. **EuroAlign (future):** compare prompt/context fixes, adapters and experimental weight edits on genuinely held-out cases while monitoring general-capability and safety regressions.

**Important:** Differences between language editions of Wikipedia are *candidate discovery signals*, not proof of a model bias or historical truth. A source's nationality is not a credibility score. Model origins do not establish ideological behavior. We do not endorse a preferred interpretation of disputed political events.

## Research track status

| Track | Status |
| --- | --- |
| Historical/evaluative pilot: 60 pairs / 3 models / two campaigns | Operator-reported, exploratory, not validated |
| AI judge reliability | Reported low cross-judge agreement; do not publish absolute EU alignment scores |
| 25-response human calibration | [Protocol agreed](docs/human-calibration-pilot-25.md); corpus selection/annotation pending |
| Discovery engine (new) | POC in progress: automatic candidate generation, source metadata and cautious discrepancy signals |
| Independent historical evidence dossiers | Planned; requires independent source checks and expert adjudication |
| Paid candidate-model inference | **Not authorized** by the discovery POC |

## Project documents

- [Architecture, scientific rules and staged roadmap](docs/global-discovery-roadmap.md)
- [Automated Discovery POC — PR #9](https://github.com/leag1234/EuroBiasBench/pull/9) and [bounded live screening — issue #10](https://github.com/leag1234/EuroBiasBench/issues/10)
- [First bounded real discovery screening: 100 candidate topics, no model inference](docs/discovery-run-001-2026-11-06.md)
- [Offline re-triage of the same 100 subjects: six unverified source-review cues, no inference](docs/discovery-offline-triage-2026-11-06.md)
- [Independent evidence dossier design — issue #11](https://github.com/leag1234/EuroBiasBench/issues/11), [worldwide coverage audit — issue #12](https://github.com/leag1234/EuroBiasBench/issues/12), [future model tests — issue #13](https://github.com/leag1234/EuroBiasBench/issues/13)
- [Preliminary pilot findings: why LLM judges disagree](docs/pilot-findings-2026-11-05.md)
- [25-response human calibration protocol](docs/human-calibration-pilot-25.md)
- [Pilot technical implementation (PR #1)](https://github.com/leag1234/EuroBiasBench/pull/1)
- [Earlier Scaleway inference mission and results discussion (issue #7)](https://github.com/leag1234/EuroBiasBench/issues/7)

## Guiding scientific rules

- Separate *documented facts*, *legitimate contested interpretations*, *inadequately supported claims*, and *unknowns*.
- Distinguish omission from ignorance or bias: an absent fact is a failure only when it is material to the specific prompt and its declared task.
- Require provenance, dated sources, independent evidence and explicit criteria before treating a discovered discrepancy as a benchmark item.
- Record sampling frames and coverage gaps instead of claiming global representativeness from an English-centric or convenience corpus.
- Keep original model outputs intact; do not use one model to certify another without human calibration.
- No automatic geopolitical, religious, cultural or political correctness ranking. Political disagreement with EU institutions is legitimate.
- Reuse saved model responses and offline data wherever possible to limit inference spend.

## Contributing

Methodological critique, source verification, technical contributions and reproducible counterexamples are welcome. The research documentation and all GitHub issues and reports are **in English**. Source texts and saved model responses remain in their original languages. See also the implementation branch's [contribution guide](https://github.com/leag1234/EuroBiasBench/blob/feature/eurobiasbench-mvp-0.1/CONTRIBUTING.md).
