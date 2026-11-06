"""Experimental gradient-free rank-one edit of a Qwen3 MLP down_proj weight.

This is a *hypothesis*, not established cultural circuit editing. Patch factors
are applied to actual model weights before inference, not to runtime prompts.
On low-precision tensors, effective edits can round away; measure them.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path

from .euroalign_stage0 import load_qwen, render_prompt, generate_text, summarize_reviews


def weight_hash(tensor) -> str:
    import torch
    obj = io.BytesIO()
    torch.save(tensor.detach().to("cpu").contiguous(), obj)
    return hashlib.sha256(obj.getvalue()).hexdigest()


def get_down_proj(model, layer_index: int):
    modules = model.model.layers
    if layer_index < len(modules) - 4 or layer_index >= len(modules) or layer_index < 0:
        raise ValueError("Only the last four model layers may be edited in this initial POC")
    linear = modules[layer_index].mlp.down_proj
    if not hasattr(linear, "weight") or linear.weight.ndim != 2:
        raise ValueError("Expected 2D down_proj weight")
    if not linear.weight.dtype.is_floating_point:
        raise ValueError("Not a floating-point tensor: use an unquantized checkpoint for direct editing")
    return linear


def _mean_key_and_output(model, tokenizer, module, prompts: list[str]):
    import torch
    keys = []
    outs = []

    def before(_mod, args):
        keys.append(args[0][0, -1].detach().float().cpu())

    def after(_mod, _args, output):
        outs.append(output[0, -1].detach().float().cpu())

    h1 = module.register_forward_pre_hook(before)
    h2 = module.register_forward_hook(after)
    try:
        with torch.inference_mode():
            for prompt in prompts:
                inputs = render_prompt(tokenizer, prompt, model.device)
                model(**inputs, use_cache=False)
    finally:
        h1.remove()
        h2.remove()
    if len(keys) != len(prompts) or len(outs) != len(prompts):
        raise RuntimeError("Activation capture failed")
    return torch.stack(keys).mean(0), torch.stack(outs).norm(dim=1).mean().item()


def _contrastive_direction(model, tokenizer, good: str, bad: str):
    import torch
    # Average output embedding vectors is an inexpensive proxy, not an
    # interpretable semantic representation; multiple tokens are flagged.
    good_ids = tokenizer.encode(good, add_special_tokens=False)
    bad_ids = tokenizer.encode(bad, add_special_tokens=False)
    if not good_ids or not bad_ids or good_ids == bad_ids:
        raise ValueError("Invalid contrastive token labels")
    emb = model.get_output_embeddings().weight.detach().float()
    vector = emb[good_ids].mean(dim=0) - emb[bad_ids].mean(dim=0)
    norm = torch.linalg.vector_norm(vector).item()
    if norm < 1e-9:
        raise ValueError("Contrastive direction is degenerate")
    return vector.cpu() / norm, {"good_token_ids": good_ids, "bad_token_ids": bad_ids}


def design_rank_one_patch(model, tokenizer, *, prompts: list[str],
                          layer_index: int, good: str, bad: str, strength: float):
    """Delta W = u v.T, with v = mean key / squared norm; u token contrast direction.

    Gradient-free. No guarantee that these directions encode a causal feature.
    Limited search on development prompts only; never optimize on hold-outs.
    """
    import torch
    if not 0 < strength <= 0.5:
        raise ValueError("strength must be >0 and <=0.5")
    if not 2 <= len(prompts) <= 30:
        raise ValueError("Need 2..30 documented failure prompts")
    layer = get_down_proj(model, layer_index)
    key, output_norm = _mean_key_and_output(model, tokenizer, layer, prompts)
    direction, token_meta = _contrastive_direction(model, tokenizer, good, bad)
    if key.numel() != layer.weight.shape[1] or direction.numel() != layer.weight.shape[0]:
        raise ValueError("Patch shape mismatch")
    key_norm_sq = torch.dot(key, key).item()
    if key_norm_sq < 1e-6:
        raise ValueError("Key vector norm is too small")
    u = (direction * (strength * output_norm)).contiguous()
    v = (key / key_norm_sq).contiguous()
    return u, v, {
        "layer_index": layer_index, "tensor": f"model.layers.{layer_index}.mlp.down_proj.weight",
        "strength": strength, "output_norm_reference": output_norm,
        "key_norm": key_norm_sq ** .5,
        "tensor_shape": list(layer.weight.shape),
        "tensor_base_sha256": weight_hash(layer.weight),
        **token_meta,
        "operator_warning": (
            "This gradient-free last-layer rank-one token-contrast hypothesis is "
            "not proof of a causal cultural circuit. Prompt generalization must be tested."
        ),
    }


@contextlib.contextmanager
def apply_patch(model, layer_index: int, u, v, *, expected_base_sha: str | None = None):
    """Patch before inference and restore exact original bits in finally."""
    import torch
    layer = get_down_proj(model, layer_index)
    w = layer.weight
    if tuple(w.shape) != (u.numel(), v.numel()):
        raise ValueError("Tensor factor dimensions do not match")
    original_hash = weight_hash(w)
    if expected_base_sha and original_hash != expected_base_sha:
        raise ValueError("Original weight fingerprint mismatch; wrong checkpoint or already patched")
    baseline = w.detach().clone()
    try:
        with torch.no_grad():
            update = u.to(device=w.device, dtype=torch.float32)[:, None] * v.to(
                device=w.device, dtype=torch.float32)[None, :]
            w.copy_((baseline.float() + update).to(dtype=w.dtype))
            changed = int(torch.count_nonzero(w != baseline).item())
        if not changed:
            raise RuntimeError("All low-rank edits rounded away under model dtype")
        yield {"modified_elements": changed, "total_elements": w.numel(),
               "weight_original_sha256": original_hash, "weight_modified_sha256": weight_hash(w)}
    finally:
        with torch.no_grad():
            w.copy_(baseline)
        if weight_hash(w) != original_hash:
            raise RuntimeError("Failed exact weight restoration")


def create_patch(*, checkpoint: str, revision: str, responses: str, reviews: str,
                 approval: str, layer_index: int, strength: float, output: str):
    """Approval file is manually created AFTER reviewing Stage 0 outputs."""
    import torch
    gate = summarize_reviews(responses, reviews)
    if gate["status"] != "candidate_for_expert_confirmation":
        raise ValueError("Baseline has no eligible, independently reviewed factual defect")
    approval_data = json.loads(Path(approval).read_text(encoding="utf-8"))
    family = approval_data.get("family")
    if (family != gate["recommendation"] or family not in {"micral", "gdpr"}
            or not approval_data.get("reviewer") or not approval_data.get("evidence")
            or not approval_data.get("good_text") or not approval_data.get("bad_text")):
        raise ValueError("Expert approval must match gate and provide evidence and contrastive tokens")
    if len(revision) < 32 or revision == "main":
        raise ValueError("Pin exact checkpoint revision")
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    if any((folder / p).exists() for p in ("patch.pt", "patch_manifest.json")):
        raise FileExistsError("Patch directory already populated")
    review_by_id = {}
    import csv
    with open(reviews, newline="", encoding="utf-8") as stream:
        review_by_id = {x["sample_id"]: x["human_decision"] for x in csv.DictReader(stream)}
    rows = [json.loads(x) for x in Path(responses).read_text(encoding="utf-8").splitlines() if x.strip()]
    prompts = sorted({r["prompt"] for r in rows
                     if r["family"] == family and review_by_id[r["sample_id"]] == "fail"})
    model, tokenizer = load_qwen(checkpoint, revision=revision)
    u, v, metadata = design_rank_one_patch(
        model, tokenizer, prompts=prompts, layer_index=layer_index,
        good=approval_data["good_text"], bad=approval_data["bad_text"],
        strength=strength)
    # Reversible, compact factors. No new runtime prompt or extra model component.
    torch.save({"u": u, "v": v}, folder / "patch.pt")
    with apply_patch(model, layer_index, u, v,
                     expected_base_sha=metadata["tensor_base_sha256"]) as applied:
        metadata.update(applied)
    manifest = {
        "experiment": "euroalign-poc-001",
        "patch_type": "gradient_free_rank_one_down_proj",
        "checkpoint": checkpoint, "revision": revision,
        "family": family, "reviewer": approval_data["reviewer"],
        "approval_evidence": approval_data["evidence"],
        "baseline_review_sha256": hashlib.sha256(Path(reviews).read_bytes()).hexdigest(),
        "baseline_responses_sha256": hashlib.sha256(Path(responses).read_bytes()).hexdigest(),
        "patch_sha256": hashlib.sha256((folder / "patch.pt").read_bytes()).hexdigest(),
        "source_prompt_count": len(prompts),
        "human_review_required_before_claims": True, "gradient_descent_used": False,
        **metadata,
    }
    (folder / "patch_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Experimental rank-one weight patch — NOT a validated cultural correction")
    parser.add_argument("--checkpoint", default="Qwen/Qwen3-14B")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--layer", type=int, required=True, dest="layer_index")
    parser.add_argument("--strength", type=float, default=0.1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = create_patch(**vars(args))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
