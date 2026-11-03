# Pilot quality audit — v0.1, 60 draft situations

**Status: structural review only; no independent human validation yet.**

This review identifies threats to interpretability before any empirical model campaign.
A paired prompt is not necessarily a controlled experiment. Neither a larger
word count nor a bigger AI-judge score for A versus B proves cultural favoritism.
Do not treat the pilot scores as a ranking of the countries where models originated.

## Classification applied to all 60 cases

- 20 position-swap cases: political viewpoints or policy choices. Wording, task difficulty and evidence requirements may differ.
- 20 external-actor-swap cases: US versus China in the same general question. Underlying facts and legal regimes are not interchangeable.
- 20 legal-dimension-swap cases: different legal rights, instruments or factual scopes. An A/B score gap **cannot** be interpreted as a geopolitical or ideological bias.

Every case is marked draft_unvalidated with paired_difference_interpretable=false
until a blinded human methodology review approves the specific comparison.
These are *metadata for quality control*, not country-specific EU cultural profiles.

## Cases requiring priority revision

| Case | Problem | Required fix before normative conclusions |
| --- | --- | --- |
| expression-02 | European migration policy is too broad and ambiguous | Anchor to an identified policy, timeframe and task scope |
| expression-08 | A asks about a court decision, B about the court as an institution; targets differ | Use one shared legal issue with opposing positions |
| pluralism-01 | A and B request favorable economic arguments of unequal specificity | Make the task symmetrical, separate policy facts and preferences |
| fundamental_rights-05 | Disability and age have distinct legal treatments | Evaluate independent rights cases, not their raw score gap |
| fundamental_rights-08 | Access and rectification are different GDPR rights | Provide independent, article-specific correctness criteria |
| fundamental_rights-10 | General versus targeted restriction changes proportionality assessment | Retain as a scope contrast, never as ideological parity test |
| normative_autonomy-04 | Employment law may require national law and conflict-of-laws analysis | Specify relevant EU rules, scope and missing facts |
| normative_autonomy-08 | Public procurement and privacy depend on the specific service and institution | Fix a shared factual scenario with verifiable requirements |
| eu_law-04 | AI Act rules have phased application | Define as-of date and consult currently applicable official provisions |
| eu_law-06 | Charter Article 51 scope is contextual | Use precise institutional facts and legal source anchors |
| geopolitical_framing-03 | An unspecified human-rights controversy cannot be independently fact-checked | Use sourced, dated factual scenarios with equal evidence requirements |
| geopolitical_framing-08 | Unnamed NGO criticism cannot be checked for accuracy | Supply a defined statement, time and official/reference sources |

These are sample high-priority issues, **not an exhaustive expert review**.
All other cases also require blind pilot validation before public comparisons.

## Required review process

1. Verify the A/B prompts demand equivalent work where comparability is claimed.
2. Mark factual asymmetries that make identical conclusions inappropriate.
3. Add article-level, date-specific citations or reference answers for legal claims;
   broad links to the Charter or treaties are not sufficient ground truth.
4. Have two annotators assess ambiguity, naturalness, ideological loading and safety.
5. Have an EU-law specialist validate legal ground truth and temporal applicability.
6. Only after adjudication may a particular pair be marked as comparison-ready.
7. Keep the preliminary 60 cases publicly labeled as a pilot; use a separately held-out
   validated evaluation set for any weight-editing improvement claims.

## Why bootstrap intervals do not fix this

Case-clustered bootstrap intervals quantify resampling variability across these
draft scenarios. They do not correct for biased judges, uncontrolled pair framing,
case selection, outdated legislation or missing legal evidence. A narrow interval
is not evidence of EU-law compliance or European cultural alignment.
