"""Quantization-matched held-out evaluation of a trained QLoRA adapter.

This comparator is NOT a direct no-gradient parameter edit. Its baseline is
the same 4-bit model with adapters disabled, preventing a precision confound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .euroalign_stage0 import generate_text, classify_for_triage
from .euroalign_evaluate import load_eval_cases


def evaluate(*, checkpoint: str, revision: str, training_dir: str,
             heldout: str, controls: str, output: str, repeats: int = 3) -> dict:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required for 14B QLoRA comparison")
    train_meta = json.loads((Path(training_dir) / "training_manifest.json").read_text(encoding="utf-8"))
    if train_meta["checkpoint"] != checkpoint or train_meta["revision"] != revision:
        raise ValueError("Training checkpoint mismatch")
    held, held_sha = load_eval_cases(heldout, min_count=60)
    controls_list, controls_sha = load_eval_cases(controls, min_count=50)
    chosen = [x for x in held if x["family"] == train_meta["family"]]
    if len(chosen) < 30 or repeats not in (1, 2, 3):
        raise ValueError("Invalid holdout size or repetition count")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "responses.jsonl").exists():
        raise FileExistsError("Choose a new output folder")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, revision=revision, trust_remote_code=False)
    base = AutoModelForCausalLM.from_pretrained(
        checkpoint, revision=revision, device_map="auto", trust_remote_code=False,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
        ))
    model = PeftModel.from_pretrained(base, str(Path(training_dir) / "adapter"))
    model.eval()
    result = {
        "status": "in_progress", "study": "euroalign-poc-001-qlora",
        "checkpoint": checkpoint, "revision": revision,
        "family": train_meta["family"],
        "arms": ["unadapted_quantized_base", "qlora_adapter"],
        "heldout_sha256": held_sha, "controls_sha256": controls_sha,
        "expected_responses": 2 * (len(chosen) * repeats + len(controls_list)),
        "warning": "QLoRA uses gradient descent and a 4-bit base. Do not equate with direct weight editing.",
    }
    (out / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    written = 0
    try:
        with (out / "responses.jsonl").open("w", encoding="utf-8") as f:
            for arm in result["arms"]:
                import contextlib
                active = model.disable_adapter() if arm == "unadapted_quantized_base" else contextlib.nullcontext()
                with active:
                    for case in chosen + controls_list:
                        seeds = range(repeats) if case["family"] != "control" else (0,)
                        for idx in seeds:
                            seed = 1009 + idx
                            answer = generate_text(model, tokenizer, case["prompt"], seed)
                            row = {
                                "arm": arm, "case_id": case["id"], "family": case["family"],
                                "prompt": case["prompt"], "answer": answer, "seed": seed,
                                "screening": classify_for_triage(train_meta["family"], answer)
                                    if case["family"] != "control" else "review_control",
                            }
                            f.write(json.dumps(row, ensure_ascii=False) + "\n")
                            f.flush()
                            written += 1
        result["status"] = "complete"
    except Exception:
        result["status"] = "interrupted"
        raise
    finally:
        result["responses_written"] = written
        (out / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Quantization-matched QLoRA held-out comparator")
    parser.add_argument("--checkpoint", default="Qwen/Qwen3-14B")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--training-dir", required=True)
    parser.add_argument("--heldout", default="data/euroalign/poc001_holdout.json")
    parser.add_argument("--controls", default="data/euroalign/poc001_controls.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    print(json.dumps(evaluate(**vars(args)), indent=2))


if __name__ == "__main__":
    main()
