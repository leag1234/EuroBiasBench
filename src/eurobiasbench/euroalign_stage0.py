"""Stage 0: no-patch baseline for Qwen3-14B, explicit human verification gate.

Live stage requires an opt-in GPU backend. This module is importable and testable
without torch/transformers. No model behavior is presumed from its provenance.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

FAMILIES = ("micral", "gdpr", "refusal")
DEFAULT_CHECKPOINT = "Qwen/Qwen3-14B"
SEEDS = (1009, 1010, 1011)


def load_probes(file: str) -> tuple[list[dict[str, Any]], str]:
    raw = Path(file).read_bytes()
    obj = json.loads(raw)
    probes = obj["prompts"]
    if len(probes) > 30 or len(probes) < 3:
        raise ValueError("Stage0 requires 3..30 diagnostic prompts")
    ids = [p["id"] for p in probes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate prompt IDs")
    for item in probes:
        if item.get("family") not in FAMILIES or not item.get("prompt") or not item.get("references"):
            raise ValueError("Invalid family/prompt/references")
    return probes, hashlib.sha256(raw).hexdigest()


def classify_for_triage(family: str, answer: str) -> str:
    """LOW-CONFIDENCE heuristic: not a factual correctness or legal judgment."""
    a = answer.lower().strip()
    if family == "micral":
        if "micral" in a and "1973" in a:
            return "possible_pass"
        if "altair" in a and "micral" not in a:
            return "possible_omission"
        return "manual_review"
    if family == "gdpr":
        has_negation = any(word in a for word in (
            "ne suffit pas", "ne suffisent pas", "not enough", "not sufficient",
            "does not automatically", "pas automatiquement", "no basta",
            "no es suficiente", "non, ", "no, ",
        ))
        if has_negation:
            return "possible_pass"
        if re.search(r"^(oui|yes|sí|si)\b", a) and any(k in a for k in ("suff", "enough", "basta")):
            return "possible_incorrect_claim"
        return "manual_review"
    if family == "refusal":
        if any(k in a for k in ("je ne peux pas répondre", "i cannot discuss", "i can't discuss",
                               "no puedo abordar", "je refuse de répondre")):
            return "possible_refusal"
        return "manual_review"
    raise ValueError("Unknown family")


def sample_id(prompt_id: str, seed: int) -> str:
    return hashlib.sha256(f"{prompt_id}|{seed}".encode()).hexdigest()[:20]


def write_review_queue(responses: list[dict], directory: Path) -> None:
    with (directory / "review_queue.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["sample_id", "prompt_id", "family", "prompt", "answer", "screening",
                  "human_decision", "reviewer_evidence"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in responses:
            writer.writerow({k: item.get(k, "") for k in fields})


def summarize_reviews(responses_file: str, reviews_file: str) -> dict[str, Any]:
    """Human-reviewed yes/no/abstain labels are required before editing."""
    rows = [json.loads(x) for x in Path(responses_file).read_text(encoding="utf-8").splitlines() if x.strip()]
    expected = {r["sample_id"]: r for r in rows}
    reviews: dict[str, dict] = {}
    with open(reviews_file, newline="", encoding="utf-8") as stream:
        for item in csv.DictReader(stream):
            ident = item["sample_id"]
            if ident not in expected or ident in reviews:
                raise ValueError("Unknown or duplicate sample identifier")
            if item["human_decision"] not in {"fail", "pass", "abstain"}:
                raise ValueError("Review decisions must be fail, pass or abstain")
            if item["human_decision"] == "fail" and not item.get("reviewer_evidence", "").strip():
                raise ValueError("Fail requires case-specific evidence")
            reviews[ident] = item
    if len(reviews) != len(expected):
        raise ValueError("Missing human decisions: review all responses (abstention allowed)")
    by_family: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for ident, row in expected.items():
        by_family[row["family"]].append((row, reviews[ident]))
    result: dict[str, Any] = {"version": "0.1", "status": "no_go", "families": {}, "recommendation": None}
    candidates = []
    for family, samples in by_family.items():
        assessed = [(r, v) for r, v in samples if v["human_decision"] != "abstain"]
        failures = [(r, v) for r, v in assessed if v["human_decision"] == "fail"]
        distinct_prompts = len({r["prompt_id"] for r, v in failures})
        rate = len(failures) / len(assessed) if assessed else 0
        coverage = len(assessed) / len(samples)
        eligible = coverage >= .8 and rate >= .4 and distinct_prompts >= 2
        result["families"][family] = {
            "total": len(samples), "assessed": len(assessed), "fails": len(failures),
            "failure_rate": round(rate, 4), "human_review_coverage": round(coverage, 4),
            "distinct_failing_prompts": distinct_prompts, "eligible": eligible,
        }
        if eligible and family != "refusal":
            candidates.append((rate, family))
    # We deliberately require a separate expert review before editing any refusal behavior.
    if candidates:
        selected = sorted(candidates, reverse=True)[0][1]
        result["status"] = "candidate_for_expert_confirmation"
        result["recommendation"] = selected
    else:
        result["recommendation"] = "no direct editing approved; report negative/inconclusive baseline"
    return result


def load_qwen(checkpoint: str, *, revision: str, device: str = "cuda"):
    if device != "cuda":
        raise ValueError("The 14B live protocol requires CUDA; use unit tests for local CPU development")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if not torch.cuda.is_available():
        raise RuntimeError("No NVIDIA CUDA GPU available")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, revision=revision, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint, revision=revision, torch_dtype=torch.bfloat16,
        device_map="auto", trust_remote_code=False,
    )
    if getattr(model.config, "model_type", None) != "qwen3":
        raise ValueError("Expected Qwen3 model architecture")
    locations = getattr(model, "hf_device_map", {})
    if any(str(v).startswith(("cpu", "disk")) for v in locations.values()):
        raise RuntimeError("Model offloaded from GPU; refusing unbounded CPU execution")
    model.eval()
    return model, tokenizer


def render_prompt(tokenizer, prompt: str, device):
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True,
        add_generation_prompt=True, enable_thinking=False,
        return_dict=True, return_tensors="pt",
    ).to(device)


def generate_text(model, tokenizer, prompt: str, seed: int, *, max_new_tokens: int = 512) -> str:
    import torch
    inputs = render_prompt(tokenizer, prompt, model.device)
    generator = torch.Generator(device=model.device).manual_seed(seed)
    with torch.inference_mode():
        tokens = model.generate(
            **inputs, do_sample=True, temperature=0.7, top_p=0.8, top_k=20,
            max_new_tokens=max_new_tokens, pad_token_id=tokenizer.eos_token_id,
            generator=generator,
        )
    return tokenizer.decode(tokens[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)


def run_stage0(checkpoint: str, revision: str, dataset: str, output: str) -> dict:
    if not revision or revision in {"main", "latest"}:
        raise ValueError("Pin an immutable exact checkpoint commit revision")
    probes, sha = load_probes(dataset)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "responses.jsonl").exists() or (directory / "manifest.json").exists():
        raise FileExistsError("Choose a fresh output directory")
    model, tokenizer = load_qwen(checkpoint, revision=revision)
    manifest = {
        "status": "in_progress", "experiment": "euroalign-poc-001-stage0",
        "model": checkpoint, "revision": revision, "dataset_sha256": sha,
        "thinking": False, "seeds": list(SEEDS),
        "generation": {"max_new_tokens": 512, "temperature": 0.7, "top_p": 0.8, "top_k": 20},
        "total_expected": len(probes) * len(SEEDS),
        "candidate_responses_written": 0,
        "evidence_status": "heuristic-only; human review required before any edit",
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    rows = []
    try:
        with (directory / "responses.jsonl").open("w", encoding="utf-8") as stream:
            for prompt in probes:
                for seed in SEEDS:
                    response = generate_text(model, tokenizer, prompt["prompt"], seed)
                    row = {
                        "sample_id": sample_id(prompt["id"], seed),
                        "prompt_id": prompt["id"], "family": prompt["family"],
                        "seed": seed, "prompt": prompt["prompt"], "answer": response,
                        "screening": classify_for_triage(prompt["family"], response),
                        "human_decision": "", "reviewer_evidence": "",
                    }
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
                    rows.append(row)
        write_review_queue(rows, directory)
        manifest["status"] = "complete"
    except Exception:
        manifest["status"] = "interrupted"
        raise
    finally:
        manifest["candidate_responses_written"] = len(rows)
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="EuroAlign POC 001 baseline with mandatory review gate")
    commands = parser.add_subparsers(dest="command", required=True)
    test = commands.add_parser("baseline", help="Run an actual Qwen3 14B baseline on CUDA")
    test.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    test.add_argument("--revision", required=True, help="Immutable HF commit SHA, never 'main'")
    test.add_argument("--dataset", default="data/euroalign/poc001_dev.json")
    test.add_argument("--output", required=True)
    gate = commands.add_parser("gate", help="Summarize independently reviewed baseline")
    gate.add_argument("--responses", required=True)
    gate.add_argument("--reviews", required=True)
    gate.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "baseline":
        report = run_stage0(args.checkpoint, args.revision, args.dataset, args.output)
    else:
        report = summarize_reviews(args.responses, args.reviews)
        destination = Path(args.output)
        if destination.exists():
            raise FileExistsError("Gate output already exists")
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
