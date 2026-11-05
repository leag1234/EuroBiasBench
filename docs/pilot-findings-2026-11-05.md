# EuroBiasBench pilot: the limits of automated LLM judging

**Research note — 5 November 2026**  
**Status: preliminary operator-reported results; not independently audited or human-validated**

> **Main finding:** Agreement between five LLM judges was too low for their absolute ratings to serve as a trustworthy reference standard. This is a measurement result, not proof that any model or national model family is better aligned with European Union values.

EuroBiasBench evaluates the behavior of open-weight language models against an **EU-wide** reference framework: fundamental rights, pluralism, freedom of expression, context-sensitive EU legal reasoning, normative autonomy and geopolitical framing. It does not define separate national European value profiles, and it must not reward praise of EU institutions over legitimate criticism.

The data below summarize an infrastructure partner's report dated 5 November 2026. **The underlying response-level archives and calculations have not been independently reviewed as part of this GitHub publication.** This note intentionally excludes raw responses and personally identifiable information.

## Pilot design and execution

The initial pilot has 60 draft scenarios, each with two French-language prompts (120 prompts), evaluated with three candidate models and three repetitions. The operator reported two complete candidate-generation campaigns on 4 November 2026, each producing 1,080 answers.

| Campaign | Candidate output limit | Automated judges | Valid main judgments | Reported inference cost |
| --- | ---: | ---: | ---: | ---: |
| Run 001 (infrastructure mission, [issue #7](https://github.com/leag1234/EuroBiasBench/issues/7)) | 768 tokens | 2: gpt-oss-120b; Mistral Small 3.2 | 2,160 / 2,160 | €3.30 |
| Run 002 (follow-up diagnostic campaign) | 2,048 tokens | 5: the above plus Gemma 4, DeepSeek V4.1 and GLM-5.3 | 5,399 / 5,400, plus 540 reported repeat judgments | €8.44 |

**Reported total inference cost: €11.74**, excluding staff time and any unreported operating costs. The campaigns differ in token budget and judging protocol, so their raw scores must not be treated as a controlled like-for-like comparison.

The 768-token budget in Run 001 reportedly truncated 92% of Qwen answers; increasing it to 2,048 tokens reduced Qwen truncation to 4.7% and other candidate truncation to less than 1%. This is a major inference-configuration confound. Baseline evaluations require explicit truncation and finish-reason audits.

## Central methodological result: judge disagreement

The operator reported:

- **Krippendorff's alpha: approximately 0.33** across the five judges, well below common exploratory agreement thresholds (for example, 0.667). Interpretation depends on the alpha distance function, sampling and task, which must be documented.
- Judge means on the 0–4 axis-rating scale ranged from **2.44 (GLM-5.3)** to **3.59 (Mistral Small 3.2)** on the same response pool.
- On an identical-response retest of 108 answers per judge, exact same-axis-rating repeatability ranged from **69% to 99%**. These are within-judge retests, **not** evidence that a judge is factually correct.
- For the axis criterion, a reported interval-scale alpha of **0.39** rose to **0.54** after mean-centering by judge. Different levels of severity explain some, but not all, disagreement. Mean-centering does not establish validity.

Averaging several systematically different LLM judges does **not** create an independent ground truth. Even agreement among judges can reflect shared training data, shared factual errors or common rubrics.

## What can and cannot be inferred

**Provisional signals worth investigating:**

1. All five judges reportedly ranked the three tested checkpoints **Qwen3-8B > Llama-3.1-8B-Instruct > Mistral-7B-Instruct-v0.3**. The reported average Qwen–Mistral axis-score difference was **+0.51 / 4 (95% CI 0.40 to 0.63)**. These are **judge-conditioned comparisons**, not human-validated rankings or proof of cultural/national superiority.
2. The EU law axis received some of the weakest reported ratings, around **2.5–2.9 / 4** across the three candidates. Specific legal fact errors may be more objectively testable than broad ideological preferences.
3. The operator reported misstatements about **Article 2 of the Treaty on European Union** and the **AI Act** in candidate outputs. One judge reportedly missed some such errors itself. Each claim should be checked against a dated, article-level official source before being labelled a hallucination.
4. Long-answer advantage alone did not appear to explain the relative ranking in the operator's length-controlled analyses, but these analyses require independent review.

**Claims that are *not* supported by this pilot:**

- Absolute statements like “Model X scores 3.4 / 4 in EU alignment.”
- Certification of EU-law compliance or of political neutrality.
- Causal statements attributing behaviors to a model's country of origin.
- Interpreting A/B score gaps as political/cultural bias without validating question equivalence and factual context.
- Treating five AI judgments as a replacement for a source-verified human reference set.

**Dataset limitation:** all 60 pairs remain unvalidated; the operator specifically identified **16 / 60** pairs with materially different questions. References often point to entire treaties or the Charter instead of the relevant article or legal provision. The pilot's original **[quality review on the implementation branch](https://github.com/leag1234/EuroBiasBench/blob/feature/eurobiasbench-mvp-0.1/docs/pilot_quality_review.md)** already documents illustrative pairing problems.

## Why this negative result matters scientifically

A benchmark needs evidence that its scores measure the intended construct. Here, several individually repeatable graders assigned substantially different absolute judgments to the same answers. **Reliability within a judge is not inter-judge agreement, and neither guarantees correctness against EU legal and rights-based criteria.**

This result helps separate three problems that should not be collapsed into one number:

1. **Instrument reliability:** do different graders, applying a common rubric, reach comparable ratings?
2. **Ground-truth validity:** are the questions, dates and relevant EU legal provisions correctly specified, and are factual conclusions independently verified?
3. **Model behavior:** once the instrument is calibrated, which model differences persist across cases, formulations and judge identities?

Publishing a well-described limitation now is preferable to expanding the pilot to 600 scenarios and obtaining narrow confidence intervals around potentially biased measurements.

## Smaller, staged next steps (no immediate large annotation project)

The earlier suggestion of 150 human-reviewed answers is **not a prerequisite for the next decision**. Five seconds per complex response is unrealistic: a meaningful annotation may require reading the answer, checking an EU article, and distinguishing legitimate criticism from inaccuracies.

### Gate 1 — Source and question audit, no new inference

- Revise the 60 draft pairs, starting with the 16 flagged mismatches.
- Add article-level EUR-Lex references and applicability dates to legal items.
- Define an explicit case-specific observable rubric: what factual statement is right or wrong; what response constitutes an unjustified refusal; what remains a legitimately contested value judgment.
- Record which A/B comparisons are comparable. Preserve original prompts and output hashes for reproducibility.

### Gate 2 — Small blind human calibration, no new candidate inference

**Proposed starting size:** 24–30 responses drawn by stratified random sampling across the three models and six axes, with two independent blind raters. Optionally reserve **6–12 additional high-disagreement or legal-error examples** as a separate *diagnostic* sample, never pooled into a representative estimate.

Have each rater initially score **one primary 0–4 case criterion**, plus a simple refusal/uncertainty flag and a short evidence-based explanation. Ask a reviewer with EU-law expertise to check legal items and any disputed legal anchor. This cuts effort relative to five fully reasoned scores on 150 answers.

The goal is a **go/no-go diagnostic**, not publishable reference accuracy. Measure human–human agreement first, followed by each AI judge versus the adjudicated human labels. If human agreement is low, rewrite the questions or rubric *before* paying for more annotation. Only scale annotation if this gate succeeds.

### Gate 3 — Optional evidence-grounded judge experiment

After the legal source audit, re-evaluate **the same saved candidate responses** with relevant *verified article extracts supplied to judges*, against an unchanged control with no supplied text. Measure improvement against humans, not merely judge–judge consensus. Treat this as a new, separately versioned judging protocol. No regeneration of the candidate answers is needed.

### Gate 4 — Decide whether to scale

Only after a reliable human-calibrated instrument exists should the project consider 600 scenarios, more model families, public scoring, or weight-editing comparisons. Maintain an independent held-out set so future EuroAlign patches are not optimized directly against their reported evaluation questions.

## Publication and reproducibility limits

- These statistics are **reported by the execution team**; the response-level archives, hashes, code and exact alpha implementation should be checked before submitting a paper or making definitive comparative claims.
- Run 001 and Run 002 are *not interchangeable*. Keep distinct manifests, token limits, judges and outputs.
- This note publishes aggregated findings only. No raw generations or evaluation data are distributed here.
- The original candidate prompts and responses are in French; research documentation and GitHub reports are in English.
- Research code for the current experimental pilot is still under review in **[PR #1](https://github.com/leag1234/EuroBiasBench/pull/1)**, rather than merged into the default branch.

**Recommended current status:** **measurement calibration needed; no further model inference planned until source and human-calibration gates are reviewed.**

---

*Source: execution partner's EuroBiasBench Run 001 / Run 002 summary provided 5 November 2026. This is a preliminary research communication, not a peer-reviewed study.*
