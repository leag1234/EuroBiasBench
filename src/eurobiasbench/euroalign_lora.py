"""Optional QLoRA baseline, deliberately separate from gradient-free rank-one edit.

NEVER call an adapted LoRA checkpoint a direct gradient-free weight-space edit.
Only operator-curated development corrections are admitted; held-out cases are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .euroalign_stage0 import load_probes


def validate_corrections(path: str, dev_path: str, family: str) -> list[dict]:
    if family not in ("micral", "gdpr"):
        raise ValueError("No political/refusal training without separate expert review")
    dev, _ = load_probes(dev_path)
    valid = {item["prompt"]: item for item in dev if item["family"] == family}
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not 2 <= len(rows) <= 30:
        raise ValueError("Expected 2..30 operator-reviewed development corrections")
    unique = set()
    for row in rows:
        p = row.get("prompt")
        if p not in valid or p in unique:
            raise ValueError("Correction prompt must be unique and exactly from development set")
        unique.add(p)
        if not row.get("corrected_answer") or not row.get("reviewer") or not row.get("evidence"):
            raise ValueError("Every correction needs corrected_answer, reviewer and source/evidence")
    return rows


def train(*, checkpoint: str, revision: str, family: str,
          corrections: str, output: str, dev: str = "data/euroalign/poc001_dev.json",
          max_steps: int = 24):
    if len(revision) < 32 or revision == "main":
        raise ValueError("Pin an immutable checkpoint commit SHA")
    if max_steps < 1 or max_steps > 40:
        raise ValueError("Only 1..40 bounded gradient updates permitted")
    examples = validate_corrections(corrections, dev, family)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "training_manifest.json").exists():
        raise FileExistsError("Existing training results; choose a fresh directory")
    import torch
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
        Trainer, TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA requires a CUDA GPU")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, revision=revision, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint, revision=revision, trust_remote_code=False, device_map="auto",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
        ),
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0, bias="none",
        target_modules=["q_proj", "v_proj", "down_proj"],
        task_type="CAUSAL_LM",
    ))

    class CorrectedDataset(torch.utils.data.Dataset):
        def __len__(self):
            return len(examples)

        def __getitem__(self, index):
            row = examples[index]
            before = tokenizer.apply_chat_template(
                [{"role": "user", "content": row["prompt"]}],
                tokenize=True, add_generation_prompt=True, enable_thinking=False)
            after = tokenizer.encode(row["corrected_answer"], add_special_tokens=False)
            after += [tokenizer.eos_token_id]
            ids = (before + after)[:1024]
            labels = ([-100] * len(before) + after)[:1024]
            if all(x == -100 for x in labels):
                raise ValueError("Truncation removed training target")
            return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels}

    def collate(batch):
        size = max(len(x["input_ids"]) for x in batch)
        pad = tokenizer.pad_token_id
        return {
            "input_ids": torch.tensor([x["input_ids"] + [pad] * (size - len(x["input_ids"])) for x in batch]),
            "attention_mask": torch.tensor([x["attention_mask"] + [0] * (size - len(x["attention_mask"])) for x in batch]),
            "labels": torch.tensor([x["labels"] + [-100] * (size - len(x["labels"])) for x in batch]),
        }

    args = TrainingArguments(
        output_dir=str(out / "trainer"),
        per_device_train_batch_size=1, gradient_accumulation_steps=2,
        max_steps=max_steps, learning_rate=2e-4, bf16=True,
        optim="paged_adamw_8bit", logging_steps=5, save_strategy="no",
        report_to="none", remove_unused_columns=False,
        gradient_checkpointing=True, seed=31415, dataloader_num_workers=0,
    )
    trainer = Trainer(model=model, args=args, train_dataset=CorrectedDataset(), data_collator=collate)
    trainer.train()
    model.save_pretrained(str(out / "adapter"))
    manifest = {
        "experiment": "euroalign-poc-001-qlora-comparator",
        "procedure": "gradient_descent_qlora_training_NOT_direct_weight_editing",
        "checkpoint": checkpoint, "revision": revision, "family": family,
        "corrections_sha256": hashlib.sha256(Path(corrections).read_bytes()).hexdigest(),
        "correction_count": len(examples), "steps": max_steps,
        "separate_heldout_required": True, "trained_adapter_dir": "adapter",
    }
    (out / "training_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="QLoRA comparator — not gradient-free weight editing")
    parser.add_argument("--checkpoint", default="Qwen/Qwen3-14B")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--family", required=True, choices=("micral", "gdpr"))
    parser.add_argument("--corrections", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dev", default="data/euroalign/poc001_dev.json")
    parser.add_argument("--max-steps", type=int, default=24)
    args = parser.parse_args(argv)
    print(json.dumps(train(**vars(args)), indent=2))


if __name__ == "__main__":
    main()
