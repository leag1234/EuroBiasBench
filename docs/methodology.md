# EuroBiasBench — study design, v0.1

## Construct definition and exclusions

This is an **EU-level** behavioral comparison benchmark, not a survey of European national values. Six measurement axes operationalize particular outcomes; they are **not national cultural categories**.

The primary outcome is whether a response addresses a lawful question accurately, respects relevant rights, and fairly handles legitimate disagreement while applying the correct jurisdiction. Positive sentiment toward the EU is **never** an outcome.

Definitions:
1. **Expression**: unwarranted refusals and distortion of lawful political critique.
2. **Pluralism**: accurate treatment of reasonable disagreement without ungrounded pejorative framing.
3. **Fundamental rights**: awareness of non-discrimination, equality, liberty, privacy, procedural fairness and proportionality.
4. **Normative autonomy**: using EU-applicable legal and ethical context instead of automatically substituting foreign norms.
5. **EU law**: accurate contextual legal explanations (not simulated legal advice or adjudication).
6. **Geopolitical framing**: consistency of evidentiary standards in paired questions about foreign powers.

## Pilot construction

60 draft cases, 10 per axis, each with A/B paired prompts. A pair changes a topic stance or actor/context, usually holding the analytical task constant. Review whether the changed factual context makes identical answers inappropriate; score fairness of method, not identical conclusions. All cases contain a natural-language success criterion and official EU reference links. These are coarse anchors, **not case-specific gold answers**.

All examples are in French for pilot consistency. Adding EU official languages later is language robustness testing, not a set of national normative profiles. Validate linguistic equivalence before treating translations as paired tests.

## Execution protocol

Evaluate each checkpoint on both prompts with three generations (seeds 1009–1011). Save checkpoint ID, inference backend and version, quantization, prompt format/chat template, token budget, sampling settings, hardware, environment, UTC time, dataset SHA256 and failure logs. v0.1 captures only some of these; document the rest manually.

Use two distinct judging models, ideally separate provider families; anonymize model identity in judge-visible content. Judgments have 0–4 scores for axis adherence, factual accuracy, rights respect, pluralism and refusal appropriateness. Scores must include rationale and uncertainty. Distinguish inappropriate refusals from appropriate refusal to supply hazardous instructions.

A refusal itself is not a legal or cultural violation. For example, asking for discriminatory harm does not entitle a user to compliance.

## Statistical validity

The current report provides **descriptive** means and absolute paired gaps only; it does not estimate causal effects or confidence intervals. Repeated answers within a case are dependent observations. In validated research, estimate uncertainty with a case-clustered bootstrap or hierarchical model, and report effect sizes, stratified confidence intervals, judge agreement and error rates.

Do not interpret a score gap between US- and China-framed scenarios as proof of cultural bias. Evidence strength, event facts and question semantics can differ, and prompt pairing needs review. Compare source fidelity, strength of claims, refusals and accuracy individually.

No single composite score may hide a severe failure on EU legal accuracy or fundamental rights.

## Human validation gates

Before publishing comparative claims:
1. Two independent raters validate question framing and rubric criteria; a legally trained reviewer audits legal cases.
2. Human raters, blind to model identity and AI-judge output, double-label a stratified random sample plus systematically disputed/uncertain answers.
3. Report inter-rater agreement (e.g., weighted kappa/Krippendorff alpha), AI-vs-human confusion matrices and systematic failure patterns.
4. Adjudicate disagreements without treating any judge model as ground truth. Revise or exclude invalid questions.
5. Re-run on a held-out test sample; disclose protocol changes and exploratory analyses.

The initial target of 10–20% random human checks is only a staffing assumption, **not** a universal statistical guarantee.

## Data governance and harm safeguards

Never include identifiable persons' private information in scenarios or logs. Publish a dataset card with test limitations; respect model licenses and terms of endpoints. Avoid reproducing slurs or extremist propaganda unnecessarily. Audit whether legal interpretations are still current before each major release. Preserve safety protections.

## Weight-editing phase (future)

Do not optimize patches using the same data on which their benefit will be claimed. Preserve a sealed held-out evaluation set. Compare identical checkpoint + prompt, reference LoRA/DPO and localized edits with matched compute where feasible; test independent reasoning, knowledge, safety and response quality regressions.

**Research claims are prospective. v0.1 contains no human validation and no model evaluations by default.**

## Pair metadata and comparability (pilot revision)

Each public pilot case has a pair_type (position_swap, external_actor_swap or legal_dimension_swap), review_status, and paired_difference_interpretable=false. These are **quality metadata**, not validated controls. The reported signed and absolute A/B rating gaps are descriptive diagnostics only; **none of the initial pairs are approved as causal tests of cultural bias**. A future release must validate evidence symmetry, question specificity and legal gold standards independently before promoting any comparison to a scientific claim. See [pilot quality review](pilot_quality_review.md).
