# EuroAlign POC 001 — Qwen3-14B direct weight editing

**Status:** executable GPU research prototype, not yet run on the real 14B checkpoint. This branch is stacked on the experimental EuroBiasBench code. **No cultural bias or correction has been demonstrated.**

## Scientific question and stop criteria

Can a single, **human-confirmed and reproducible** factual/normative failure of **Qwen/Qwen3-14B** be reduced by a compact, directly applied **no-gradient rank-one weight update** without destroying unrelated capabilities or safety?

- Do not choose the failure before seeing the *real 14B* baseline. There are 30 development probes (10 each: Micral historical attribution, GDPR legal-basis claims, and lawful historical/political refusals).
- Historical attribution evidence: [Computer History Museum on 1973 Micral](https://www.computerhistory.org/revolution/story/297) and [1973 timeline](https://www.computerhistory.org/timeline/1973/). This is **definition-specific**; Kenbak-1 (1971) was a personal computer without a microprocessor, and Altair (1975) achieved greater sales.
- GDPR evidence: [Regulation 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj), especially Articles 6 and 7; mere blanket acceptance of general terms is not automatically a lawful basis for every processing purpose.
- Historical and geopolitical questions have **no presumed model failure**. They are only refusal-screening probes; facts and significance require independent review.
- A 40% failure rate on multiple wordings is only an engineering trigger for **expert confirmation**, not an automatic instruction to edit.
- **Stop with a negative/inconclusive result** if no target meets this standard.

## Hardware and budget (proposal, not authorization)

A **single NVIDIA L40S 48 GB** with sufficient system RAM/disk may support the 14B BF16 forward pass; the 4-bit LoRA path has different dependencies. GPU usage and optimization must be measured in a small stage rather than assumed.

**Suggested operator cap:** 24 billable GPU hours, €150 excluding VAT infrastructure, 7-calendar-day delivery window once started; abort on first limit reached. These are ceiling proposals requiring authorization. No VM has been created by this repository. Human engineering and annotation time are additional.

Use an isolated Linux environment with CUDA, Python >=3.11, PyTorch, Transformers >=4.51, Accelerate, and optionally PEFT/bitsandbytes for LoRA. Pin environment versions in the final manifest. Avoid CPU/disk offloading disguised as GPU operation.

Qwen3 explicitly supports `enable_thinking=False` via the official tokenizer chat template; all arms use this mode and fixed decoding (`temperature=0.7`, `top_p=0.8`, `top_k=20`, max 512 new tokens). A token budget should not be compared to a different thinking-mode configuration.

## Preflight and baseline (no patch)

From the repository root, install the package and optional GPU requirements:

```bash
python -m pip install -e .
python -m pip install "torch>=2.5" "transformers>=4.51" "accelerate>=1.0"
python -m unittest discover -s tests -v
python - <<'PY'
from huggingface_hub import model_info
print(model_info("Qwen/Qwen3-14B").sha)
PY
```

Use the printed **full immutable revision SHA**, not `main`. The Qwen checkpoint and tokenizer licenses must be respected. Then:

```bash
export REVISION="<the-real-immutable-hf-commit-sha>"
python -m eurobiasbench.euroalign_stage0 baseline \
  --checkpoint Qwen/Qwen3-14B --revision "$REVISION" \
  --dataset data/euroalign/poc001_dev.json --output results/euroalign-001-baseline
```

The baseline produces exactly **90 responses** (30 prompts × 3 seeds) if complete, plus a CSV for **human review**. The heuristic screen is **not** a human-validated correctness score. The operator must fill `human_decision` (pass/fail/abstain) and cite case-specific evidence for each failure. Uninteresting families may be marked abstain; a candidate family must have >=80% assessed coverage.

Evaluate the gate:

```bash
python -m eurobiasbench.euroalign_stage0 gate \
  --responses results/euroalign-001-baseline/responses.jsonl \
  --reviews results/euroalign-001-baseline/review_queue.csv \
  --output results/euroalign-001-baseline/gate.json
```

**Do not edit if gate is NO-GO or if no expert has confirmed the factual/behavioral criterion.** Refusal prompts are not eligible for auto-weight-editing in this POC.

## Direct weight edit — gradient-free hypothesis

Create a **locally controlled**, reviewed approval JSON (never copy credentials or private personal data into it):

```json
{
  "family": "micral",
  "reviewer": "REPLACE_WITH_REAL_REVIEWER",
  "evidence": "REPLACE_WITH_PRECISE_SOURCE_CITATIONS_AND_FAILURE_IDS",
  "good_text": " Micral",
  "bad_text": " Altair"
}
```

For GDPR, an operator-approved contrastive pair would differ and should be tested for tokenizer multi-token artifacts. This JSON is only an **illustrative example**, not permission to assume that Qwen failed.

Choose one of the last four layers and **one predeclared edit strength** (for example 0.1), using the actual model configuration rather than hardcoding the layer count:

```bash
python - <<'PY'
from transformers import AutoConfig
c = AutoConfig.from_pretrained("Qwen/Qwen3-14B", revision=__import__("os").environ["REVISION"])
print("Last layer index:", c.num_hidden_layers - 1)
PY
```

```bash
python -m eurobiasbench.euroalign_weight \
  --checkpoint Qwen/Qwen3-14B --revision "$REVISION" \
  --responses results/euroalign-001-baseline/responses.jsonl \
  --reviews results/euroalign-001-baseline/review_queue.csv \
  --approval results/euroalign-001-baseline/approval.json \
  --layer "<LAST_LAYER_INDEX>" --strength 0.1 \
  --output results/euroalign-001-patch
```

The patch formula is **ΔW = u vᵀ** on an MLP `down_proj` matrix. The input key `v` comes from last-prompt-token MLP activations averaged across independently reviewed failures; the desired direction `u` is an **unvalidated proxy** derived from output token embeddings. No gradient descent is used. This may fail or merely push a particular word: **do not call it cultural correction** until independent prompts demonstrate semantic generalization and unrelated controls remain stable.

Output includes a compact `patch.pt` (rank-one factors), a tensor-name/revision/fingerprint manifest, change count and a verified exact restoration to original weights in memory. A patched model is obtained by applying those factors to the frozen original weights before inference; no system prompt or RAG is added.

### Evaluate the frozen unseen set — once

The repository separately freezes **30 unseen prompts per eligible family** and **50 controls**. They are public and therefore not blind to a determined operator; this is a limitation of the POC. Do not use them to choose layer, strength, target tokens or training examples.

```bash
python -m eurobiasbench.euroalign_evaluate \
  --checkpoint Qwen/Qwen3-14B --revision "$REVISION" \
  --patch-dir results/euroalign-001-patch \
  --heldout data/euroalign/poc001_holdout.json \
  --controls data/euroalign/poc001_controls.json \
  --output results/euroalign-001-evaluation
```

This generates **420 raw answers** across (1) unmodified BF16 base; (2) a same-norm random-direction edit; (3) the proposed direct rank-one edit. The saved model tensor is restored exactly between arms. Heuristic fields are strictly triage hints; scoring must be **blind and source-aware**, not a five-judge aggregate.

### Conventional training comparator (separate; only if baseline defect confirmed)

A curated development-only `corrections.jsonl` must provide `prompt`, `corrected_answer`, `reviewer`, and `evidence`. The code refuses prompts absent from the development set and refuses direct training on the censorship/refusal family.

```bash
python -m pip install "peft>=0.15" "bitsandbytes>=0.45"
python -m eurobiasbench.euroalign_lora \
  --checkpoint Qwen/Qwen3-14B --revision "$REVISION" \
  --family micral --corrections results/euroalign-001-baseline/corrections.jsonl \
  --output results/euroalign-001-qlora --max-steps 24
python -m eurobiasbench.euroalign_evaluate_lora \
  --checkpoint Qwen/Qwen3-14B --revision "$REVISION" \
  --training-dir results/euroalign-001-qlora \
  --output results/euroalign-001-qlora-eval
```

QLoRA uses gradients and a 4-bit model. Its evaluation includes a **same-precision, no-adapter 4-bit base** and an adapted arm: do not compare their raw scores to BF16 without acknowledging the quantization difference. LoRA success does **not** imply the gradient-free edit worked.

## Success conditions, failure conditions and handover

**Technical GO (engineering-only):** >=20 percentage-point reduction in the externally reviewed target-failure rate on truly unseen prompts, no material negative change to unrelated functioning, no severe safety regression, reloadable/reversible weight factors, no illicit prompt-conditioned steering. The tiny 50-control set cannot reliably establish a <3-point regression probability; report denominators and uncertainty. There must be no selective filtering of bad generations.

**NO-GO:** no reproducible baseline issue; weak/no effect on unseen prompts; a mere token substitution that destroys semantic correctness; an unjustified safety regression; or loss of ability to restore the original weights.

**Required English handover:** source revision, dataset SHA256, model and environment versions, raw baseline and blinded evaluation records, human review evidence, patch factor/hash metadata, random-control comparison, LoRA adapter if created, token/time/GPU bills, and a report explicitly distinguishing **direct edit / only LoRA / neither / inconclusive**. Keep raw output private until reviewed.

No real Qwen3-14B benchmark has been run in this branch; the current GitHub CI verifies **pure-Python corpus guards and mock-safe interfaces**, not GPU viability or edit success.
