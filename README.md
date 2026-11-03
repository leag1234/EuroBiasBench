# EuroBiasBench

**An open-source, exploratory benchmark for cultural, geopolitical and normative behavior of open-weight language models, assessed against EU-level rights and institutional principles.**

Status: **v0.1 experimental pilot — not validated, not certification**.

EuroBiasBench does **not** attempt to make models support the European Union, and does not define a single correct political opinion. Criticism of EU institutions, European integration, governments and policies is legitimate speech. The EU-level frame is anchored in the Treaties and the Charter of Fundamental Rights, not in national cultural profiles.

## Research questions

1. Do open-weight model families exhibit systematic differences in justified refusals, factual accuracy, treatment of legitimate opposing arguments, and applicable legal framing?
2. Are those differences robust under paired prompts and repeated generations?
3. Which detected behaviors can later be corrected using conventional adapters versus localized weight editing **without** regressions or diminished safeguards?

**This repository is the measurement framework, not a weight-editing project.** It must not be used to assert that a nationality inherently determines a model's behavior.

## The pilot

- 60 curated **draft** situations (10 per axis), each with paired prompts = 120 prompt variants.
- Six EU-level axes: expression, pluralism, fundamental rights, normative autonomy, EU legal accuracy, geopolitical framing. **No country-specific EU subcultures or profiles.**
- Three configurable open-weight model slots: Qwen, Llama and Mistral (examples, not endorsements).
- Two configurable independent judge slots. Five 0–4 ratings per response, plus rationale and an uncertainty flag.
- Three repeat generations per prompt, producing 60 × 2 × 3 × 3 = **1,080 answers** and 2,160 judge assessments in a full run.
- Raw JSONL responses, dataset checksum, per-axis descriptive summaries, paired gaps and a human audit queue.

The initial prompts are **unvalidated research material**. Their references are anchors for human evaluation, not self-executing legal conclusions. See [methodology](docs/methodology.md).

## Quick start (Python 3.11+)

Run from the repository root:

    python -m pip install -e .
    eurobiasbench validate --pilot
    eurobiasbench run --mode mock --limit 2 --repeats 1 --output results/demo
    eurobiasbench report --input results/demo

Inspect:

- results/demo/manifest.json
- results/demo/responses.jsonl
- results/demo/summary.json
- results/demo/report.md
- results/demo/human_audit_queue.csv

**Mock mode never calls a model and produces deliberately synthetic responses and scores. It is only a pipeline smoke test. It must never be published as empirical model performance.**

Full synthetic dry run:

    eurobiasbench run --mode mock --output results/pilot
    eurobiasbench report --input results/pilot

## Connecting real models

Edit [config/models.toml](config/models.toml) and [config/judges.toml](config/judges.toml). Use actual checkpoint IDs and OpenAI-compatible completion endpoints (for example, separate locally served models). The example IDs and URLs are placeholders. Run:

    eurobiasbench run --mode live --output results/live
    eurobiasbench report --input results/live

The live runner uses the Python standard library and supports an optional api_key_env per configuration entry. Put credentials only in environment variables, never in the repository. Check compatibility of the backend's seed, temperature and max_tokens parameters; **reproducibility is not guaranteed across different inference engines**.

**Important v0.1 limitations:** requests are sequential, so a full run can be slow; a failed request interrupts the run; there is no retry/resumption/cost accounting or automated source-verification engine yet. Real results require a documented human calibration before comparative scientific claims. The LLM judges' explanations are not proof of legal correctness.

## EU-level normative foundation

- [Article 2, Treaty on European Union](https://eur-lex.europa.eu/eli/treaty/teu_2016/oj) — fundamental Union values.
- [EU Charter of Fundamental Rights](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:12012P/TXT) — expression, pluralism, equality, data protection and scope of application.
- [Treaty on the Functioning of the EU](https://eur-lex.europa.eu/eli/treaty/tfeu_2016/oj) — EU acts and competences.
- [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — personal data protection.
- [AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) — applicable AI risk and governance duties.

Interpret law in light of the relevant facts, dates, amendments and case law. A legal citation by itself cannot establish whether a model's answer is correct. See [EU framework](docs/eu_framework.md).

## Evaluation integrity

- No reward for praising the EU. Negative conclusions about the EU may be well supported.
- No assumed symmetrical facts for the US and China; equivalent **standards of evidence**, not forced identical answers.
- Blind model identification during human grading wherever feasible.
- Independent human annotation on random and disagreement samples, plus expert review of hard legal issues.
- Publish model checkpoint revisions, prompt and rubric versions, inference engine versions, seeds and statistical uncertainty.
- Keep a held-out, access-controlled benchmark for future alignment/weight-editing experiments to mitigate contamination.
- Preserve protections for genuinely dangerous requests rather than treating all safety refusals as cultural bias.

## Repository overview

    config/                      OpenAI-compatible model and judge endpoints
    src/eurobiasbench/            Validation, inference, judging, reporting, CLI
    src/eurobiasbench/data/       60 paired exploratory cases
    docs/                         EU foundations, methods, annotation protocol
    tests/                        Unit and synthetic end-to-end smoke tests
    .github/workflows/ci.yml      Python 3.11 CI

## Roadmap

- v0.1: runnable mock/live pilot, dataset and audit queue.
- v0.2: independently review and refine 60 cases; calibrate judge reliability against human ratings; add explicit safe refusal tests, resume/retry and model provenance.
- v0.3: expand to 600 vetted scenarios, multilingual robustness within the single EU-level frame, held-out evaluation, and uncertainty intervals.
- Later: benchmark original vs prompt-only vs LoRA/DPO vs localized weight edits, including capability and safety regressions.

Contributions and methodological critique are welcome. See [contributing](CONTRIBUTING.md).

License: Apache-2.0 (code). Check redistribution rights for independently sourced data; this pilot's prompts are project-authored drafts.

## Campaign reliability and pilot validity (v0.1.1)

Preview the number of inference and judge calls without any network access:

    eurobiasbench preflight --mode mock
    eurobiasbench preflight --mode live --limit 2 --repeats 1

The second command rejects placeholder model IDs until config files contain actual identifiers. Choose a *fresh* output directory for each new campaign. To continue an interrupted campaign using exactly the same dataset, configuration and generation parameters:

    eurobiasbench run --mode live --output results/live --resume

Resuming rejects changes in the run fingerprint and does not silently overwrite completed answers. For each axis, reporting now includes case-clustered descriptive 95% bootstrap intervals and separate evaluations of five rubric dimensions. These intervals reflect only draft-case sampling, not external scientific validation.

**Quality-control hold:** all 60 situations remain unvalidated drafts; no A/B comparison is yet approved as evidence of a cultural bias. Review [the pilot's known risks](docs/pilot_quality_review.md) before publishing any comparative results.
