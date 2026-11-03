# Live execution guide (research prototype)

This page describes how to connect real models. The repository does not
provision GPUs, download checkpoints, or include remote API credentials.

## Prerequisites

- Python 3.11+ and a checkout of the repository.
- At least one OpenAI-compatible chat-completions inference endpoint for each
  configured model (the baseline declares three: Qwen, Llama, Mistral).
- Two judge endpoints using different checkpoint IDs, ideally independent model
  families. Sharing providers or training data can create correlated judge biases.
- Sufficient hardware for the specific selected checkpoints, prompts, context lengths,
  quantization and desired generation budget. Hardware depends on actual models.

The provided model IDs are deliberately placeholders. **Do not assume that
a model's origin predicts its response quality.**

## Step-by-step

1. Install the package with: python -m pip install -e .
2. Start the actual inference services and check their own model-list endpoints.
   For vLLM or llama.cpp, consult the version-matched server documentation.
3. Edit config/models.toml: set exact served model IDs, base URLs ending in /v1,
   token budgets and timeouts. For protected endpoints set api_key_env to the
   NAME of an environment variable whose value holds the token.
4. Do the same for config/judges.toml with distinct judge model IDs.
5. Validate that the local pilot dataset has 60 cases: eurobiasbench validate --pilot
6. Check the configuration and request count without contacting any server:

       eurobiasbench preflight --mode live --limit 1 --repeats 1

7. Execute a small live end-to-end smoke run (18 API calls: 6 candidate
   generations + 12 judge evaluations):

       eurobiasbench run --mode live --limit 1 --repeats 1 --output results/live-smoke

8. Inspect the raw responses and any error messages; ensure judges returned
   valid JSON and did not merely repeat an institution's political position.
9. Once satisfactory, run a new full campaign in a new directory:

       eurobiasbench preflight --mode live
       eurobiasbench run --mode live --output results/live-full
       eurobiasbench report --input results/live-full

10. If interrupted, resume the identical full campaign with:

       eurobiasbench run --mode live --output results/live-full --resume

For a full campaign on the default configuration there are 1,080 candidate
generations and 2,160 judge evaluations. They may be costly or slow. There
is no concurrency, provider rate-limit handling, or token/cost accounting in
this prototype; plan accordingly.

## Protocol requirements

- Record exact checkpoint paths AND revisions, model licenses, quantization,
  chat templates, inference backend version, context length and token caps.
- For runtime comparability use equivalent task instructions, sampling settings,
  output budgets and the same reference texts for every candidate.
- Do not treat a numeric seed as sufficient reproducibility across GPU stacks.
- Do not publish raw sensitive personal data; audit logs before sharing them.
- Judges receive links but do **not** retrieve or independently verify external
  webpages. Their factual and legal scores need an external evidence check.
- The full pilot is not expert-reviewed. No pair has been validated as a causal
  experiment, and no output is certified compliant with EU law.
- Before any publication, review the scenarios listed in pilot_quality_review.md,
  validate source citations at article level, and calibrate the judge ratings
  against a blinded independent human sample.

## Troubleshooting

- Placeholder model ID: edit the corresponding TOML file.
- HTTP or timeout failure: verify the service, its URL, auth environment and
  endpoint compatibility with seed, temperature and max_tokens.
- Judge JSON parse failure: adjust the judge's chat format / JSON-mode support;
  save the run as interrupted and resume only after handling the failure.
- Resume rejected: configuration, input dataset or the run plan changed. Start
  a new output directory; do not combine results from different experiments.
- Existing output directory: choose a fresh name, or use --resume for a run with
  exactly the same fingerprint.

The test suite includes a mocked HTTP transport integration test. Passing it
proves the client plumbing is exercised, **not** that live LLM services were used.
