"""Benchmark runner; records provenance for every generated answer."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .core import load_dataset, load_entries
from .engine import generate, judge


def run(*, mode: str = "mock", dataset_path: str | None = None,
        models_path: str = "config/models.toml", judges_path: str = "config/judges.toml",
        output: str = "results/pilot", repeats: int = 3,
        limit: int | None = None) -> dict[str, Any]:
    if mode not in ("mock", "live"):
        raise ValueError("mode must be mock or live")
    if not 1 <= repeats <= 20:
        raise ValueError("repeats must be 1..20")
    cases, dataset_hash = load_dataset(dataset_path)
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        cases = cases[:limit]
    models = load_entries(models_path, "models")
    judges = load_entries(judges_path, "judges")
    if len(judges) != 2:
        raise ValueError("Exactly two independent judge configurations are required")
    if mode == "live" and judges[0]["model"] == judges[1]["model"]:
        raise ValueError("Configure distinct judge models")
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "0.1.0", "mode": mode, "synthetic": mode == "mock",
        "dataset_sha256": dataset_hash, "cases_run": len(cases), "repeats": repeats,
        "models": [{k: m[k] for k in ("id", "model")} for m in models],
        "judges": [{k: m[k] for k in ("id", "model")} for m in judges],
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "in_progress",
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    count = 0
    with (folder / "responses.jsonl").open("w", encoding="utf-8") as stream:
        for case in cases:
            for variant in ("a", "b"):
                prompt = case["prompt_" + variant]
                for model in models:
                    for repeat in range(repeats):
                        seed = 1009 + repeat
                        answer = generate(model, prompt, mode=mode, seed=seed)
                        ratings = [
                            {"judge_id": j["id"], **judge(j, case, prompt, answer, mode=mode, seed=seed)}
                            for j in judges
                        ]
                        row = {
                            "case_id": case["id"], "axis": case["axis"],
                            "variant": variant, "variation": case["variation"],
                            "expected_behavior": case["expected_behavior"],
                            "references": case["references"], "prompt": prompt,
                            "model_id": model["id"], "repeat": repeat,
                            "answer": answer, "judgments": ratings,
                        }
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        stream.flush()
                        count += 1
    manifest.update({
        "responses_written": count, "status": "complete",
        "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
