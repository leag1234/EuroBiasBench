"""Run a saved gradient-free weight patch on held-out prompts, plus matched controls.

No patch optimization occurs here. Human adjudication of generated answers is
necessary; the simple heuristic fields are ONLY reviewer hints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .euroalign_stage0 import load_qwen, generate_text, classify_for_triage
from .euroalign_weight import apply_patch


def load_eval_cases(file: str, *, min_count: int) -> tuple[list[dict], str]:
    raw = Path(file).read_bytes()
    obj = json.loads(raw)
    cases = obj["prompts"]
    if len(cases) < min_count or len({x["id"] for x in cases}) != len(cases):
        raise ValueError(f"Need >= {min_count} unique evaluation questions")
    if any(not case.get("prompt") for case in cases):
        raise ValueError("Empty evaluation prompt")
    return cases, hashlib.sha256(raw).hexdigest()


def rand_control_direction(u, seed: int = 1451):
    """Same-norm random output vector orthogonal to u, same input key v."""
    import torch
    generator = torch.Generator(device="cpu").manual_seed(seed)
    random = torch.randn(u.shape, generator=generator, dtype=torch.float32)
    random -= (torch.dot(random, u) / torch.dot(u, u)) * u
    norm = random.norm()
    if norm < 1e-8:
        raise RuntimeError("Degenerate random control")
    return random / norm * u.norm()


def evaluate(checkpoint: str, revision: str, patch_dir: str, heldout: str,
             controls: str, output: str, repeats: int = 3) -> dict:
    import torch
    if not 1 <= repeats <= 3:
        raise ValueError("Only 1..3 fixed repetitions supported")
    manifest_path = Path(patch_dir) / "patch_manifest.json"
    patch_file = Path(patch_dir) / "patch.pt"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["checkpoint"] != checkpoint or manifest["revision"] != revision:
        raise ValueError("Patch model/checkpoint mismatch")
    if hashlib.sha256(patch_file.read_bytes()).hexdigest() != manifest["patch_sha256"]:
        raise ValueError("Patch checksum mismatch")
    held, heldhash = load_eval_cases(heldout, min_count=60)
    chosen = [x for x in held if x["family"] == manifest["family"]]
    if len(chosen) < 30:
        raise ValueError("Need at least 30 frozen holdout questions for selected family")
    control, controlhash = load_eval_cases(controls, min_count=50)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "responses.jsonl").exists():
        raise FileExistsError("Use a new output path; never silently overwrite results")
    tensors = torch.load(patch_file, map_location="cpu", weights_only=True)
    u, v = tensors["u"], tensors["v"]
    random_u = rand_control_direction(u)
    model, tokenizer = load_qwen(checkpoint, revision=revision)
    plan = {
        "experiment": "euroalign-poc-001-evaluation",
        "patch_sha256": manifest["patch_sha256"],
        "model": checkpoint, "revision": revision,
        "heldout_sha256": heldhash, "controls_sha256": controlhash,
        "family": manifest["family"], "arms": ["base", "random_matched", "direct_weight_patch"],
        "repeats_on_holdout": repeats, "controls_repetitions": 1,
        "expected_generations": 3 * (len(chosen) * repeats + len(control)),
        "note": "Raw outputs require blind source-aware human review. No proven cultural correction.",
    }
    (output_dir / "manifest.json").write_text(json.dumps({**plan, "status": "in_progress"}, indent=2) + "\n", encoding="utf-8")
    done = 0
    try:
        with (output_dir / "responses.jsonl").open("w", encoding="utf-8") as stream:
            for arm in plan["arms"]:
                import contextlib
                if arm == "base":
                    patch_context = contextlib.nullcontext(None)
                else:
                    patch_context = apply_patch(
                        model, manifest["layer_index"], random_u if arm == "random_matched" else u, v,
                        expected_base_sha=manifest["tensor_base_sha256"])
                with patch_context as patch_state:
                    for case in chosen + control:
                        seeds = range(repeats) if case["family"] != "control" else (0,)
                        for i in seeds:
                            seed = 1009 + i
                            answer = generate_text(model, tokenizer, case["prompt"], seed)
                            row = {
                                "arm": arm, "case_id": case["id"],
                                "family": case["family"], "prompt": case["prompt"],
                                "seed": seed, "answer": answer,
                                "screening": classify_for_triage(manifest["family"], answer)
                                    if case["family"] != "control" else "review_control",
                                "warning": "Heuristic screening, not validated outcome",
                            }
                            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                            stream.flush()
                            done += 1
        plan["status"] = "complete"
    except Exception:
        plan["status"] = "interrupted"
        raise
    finally:
        plan["generations_written"] = done
        (output_dir / "manifest.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Single blind held-out evaluation of saved rank-one weight patch")
    parser.add_argument("--checkpoint", default="Qwen/Qwen3-14B")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--patch-dir", required=True)
    parser.add_argument("--heldout", default="data/euroalign/poc001_holdout.json")
    parser.add_argument("--controls", default="data/euroalign/poc001_controls.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    print(json.dumps(evaluate(**vars(args)), indent=2))


if __name__ == "__main__":
    main()
