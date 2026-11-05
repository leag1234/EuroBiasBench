# EuroBiasBench

**An open-source research benchmark for evaluating cultural, geopolitical and normative behaviors of open-weight language models against European Union fundamental rights and legal principles.**

**Research status (5 November 2026): exploratory pilot completed; automated judging is not yet a validated measurement instrument.**

## Pilot finding: AI judges disagree

Two inference campaigns with three model checkpoints and 60 paired French scenarios have been reported by the execution team. In the second campaign, **five AI judges disagreed substantially on the same answers** (reported Krippendorff's alpha ≈ **0.33**). Their average severity also differed markedly (**2.44–3.59 / 4**), despite relatively strong within-judge retest stability.

This is a meaningful **negative methodological result**: agreement of AI graders cannot be assumed, and uncalibrated absolute “EU alignment” scores should not be published as scientific truth. The reported model ordering was consistent across judges, but **it is provisional and cannot establish European normative alignment, legal compliance, or any causal effect of model provenance**.

**[Read the full preliminary findings, methods caveats, and low-burden next steps](docs/pilot-findings-2026-11-05.md)**

The recommended next step is **not another large inference run**. It is to review the benchmark's legal anchors and question pairs, then begin with **24–30 double-blind human-rated responses**, optionally plus 6–12 separate diagnostic examples. That is a small *calibration pilot*, not a sufficient human gold standard for publication.

## Research principles

- One **EU-level normative reference** grounded in the Treaties and Charter of Fundamental Rights; no national European cultural profiles.
- No reward for praising EU institutions or penalty for legitimate democratic criticism.
- Source- and date-sensitive legal assessment, human-calibrated judging, and explicitly documented limitations.
- No presumption that model provenance establishes a cultural or political bias.
- No model weight editing has yet been undertaken.

## Repository status and work in progress

The runnable experimental evaluation pipeline and 60 draft scenario pairs are currently in **[Pull Request #1](https://github.com/leag1234/EuroBiasBench/pull/1)**. They have not been merged into the default branch. The first infrastructure mission is documented in **[Issue #7](https://github.com/leag1234/EuroBiasBench/issues/7)**.

For the current CLI, reproducibility guidance and draft data, see the [pilot implementation branch](https://github.com/leag1234/EuroBiasBench/tree/feature/eurobiasbench-mvp-0.1). The pilot dataset remains **unvalidated** and its A/B pairs must not be treated as causal tests of cultural bias.

This repository publishes methodological findings and planning in English. Benchmark prompts and original model outputs may remain in French.
