"""Resumable benchmark runner; records a reproducible run plan and provenance."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from .core import load_dataset, load_entries
from .engine import generate, judge

PROTOCOL = "0.1.1"


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _plan(*, mode: str, dataset_path: str | None, models_path: str,
          judges_path: str, repeats: int, limit: int | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if mode not in ("mock", "live"):
        raise ValueError("mode must be mock or live")
    if not 1 <= repeats <= 20:
        raise ValueError("repeats must be 1..20")
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    cases, dataset_hash = load_dataset(dataset_path)
    if limit is not None:
        cases = cases[:limit]
    models = load_entries(models_path, "models")
    judges = load_entries(judges_path, "judges")
    if len(judges) != 2:
        raise ValueError("Exactly two independent judge configurations are required")
    if mode == "live":
        if judges[0]["model"] == judges[1]["model"]:
            raise ValueError("Configure distinct judge model IDs")
        for entry in models + judges:
            if "REPLACE_WITH_" in entry["model"]:
                raise ValueError(f"Placeholder model ID in {entry['id']}; configure real checkpoints")
    # Credentials are never stored or included in the fingerprint.
    safe = lambda entry: {key: value for key, value in entry.items() if key != "api_key_env"}
    specification = {
        "protocol": PROTOCOL, "mode": mode, "dataset_sha256": dataset_hash,
        "case_ids": [case["id"] for case in cases], "repeats": repeats,
        "models": [safe(entry) for entry in models],
        "judges": [safe(entry) for entry in judges],
    }
    plan_hash = hashlib.sha256(json.dumps(specification, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    summary = {
        "protocol": PROTOCOL, "mode": mode, "dataset_sha256": dataset_hash,
        "plan_sha256": plan_hash, "cases_run": len(cases), "repeats": repeats,
        "model_ids": [entry["id"] for entry in models],
        "judge_ids": [entry["id"] for entry in judges],
        "expected_responses": len(cases) * 2 * len(models) * repeats,
        "expected_judge_calls": len(cases) * 2 * len(models) * repeats * len(judges),
    }
    return cases, models, judges, summary


def preflight(*, mode: str = "mock", dataset_path: str | None = None,
              models_path: str = "config/models.toml", judges_path: str = "config/judges.toml",
              repeats: int = 3, limit: int | None = None) -> dict[str, Any]:
    """Validate the plan without contacting any inference endpoint."""
    return _plan(mode=mode, dataset_path=dataset_path, models_path=models_path,
                 judges_path=judges_path, repeats=repeats, limit=limit)[3]


def _row_id(case_id: str, variant: str, model_id: str, repeat: int) -> str:
    return json.dumps([case_id, variant, model_id, repeat], separators=(",", ":"))


def run(*, mode: str = "mock", dataset_path: str | None = None,
        models_path: str = "config/models.toml", judges_path: str = "config/judges.toml",
        output: str = "results/pilot", repeats: int = 3,
        limit: int | None = None, resume: bool = False) -> dict[str, Any]:
    cases, models, judges, plan = _plan(
        mode=mode, dataset_path=dataset_path, models_path=models_path,
        judges_path=judges_path, repeats=repeats, limit=limit,
    )
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    responses_path = folder / "responses.jsonl"

    if resume:
        if not manifest_path.is_file() or not responses_path.is_file():
            raise FileNotFoundError("To resume, both manifest.json and responses.jsonl must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("plan_sha256") != plan["plan_sha256"]:
            raise ValueError("Resume refused: dataset, config, model, mode or run parameters changed")
        completed: set[str] = set()
        with responses_path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if len(record["judgments"]) != 2:
                        raise ValueError("missing judge result")
                    ident = _row_id(record["case_id"], record["variant"], record["model_id"], record["repeat"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise ValueError(f"Corrupt/incomplete JSONL row {line_number}; preserve file and repair before resuming") from exc
                if ident in completed:
                    raise ValueError(f"Duplicate existing row {line_number}")
                completed.add(ident)
        if len(completed) > plan["expected_responses"]:
            raise ValueError("Existing result count exceeds run plan")
        mode_open = "a"
    else:
        if manifest_path.exists() or responses_path.exists():
            raise FileExistsError("Output exists; use a new --output path or --resume with the identical plan")
        completed = set()
        manifest = {
            **plan, "synthetic": mode == "mock",
            "models": [{"id": m["id"], "model": m["model"]} for m in models],
            "judges": [{"id": j["id"], "model": j["model"]} for j in judges],
            "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "status": "in_progress", "responses_written": 0,
        }
        _write_json_atomic(manifest_path, manifest)
        mode_open = "w"

    try:
        with responses_path.open(mode_open, encoding="utf-8") as stream:
            for case in cases:
                for variant in ("a", "b"):
                    prompt = case["prompt_" + variant]
                    for model in models:
                        for repeat in range(repeats):
                            ident = _row_id(case["id"], variant, model["id"], repeat)
                            if ident in completed:
                                continue
                            seed = 1009 + repeat
                            answer = generate(model, prompt, mode=mode, seed=seed)
                            ratings = [
                                {"judge_id": j["id"], **judge(j, case, prompt, answer, mode=mode, seed=seed)}
                                for j in judges
                            ]
                            record = {
                                "case_id": case["id"], "axis": case["axis"],
                                "variant": variant, "variation": case["variation"],
                                "expected_behavior": case["expected_behavior"],
                                "references": case["references"], "prompt": prompt,
                                "model_id": model["id"], "repeat": repeat, "seed": seed,
                                "answer": answer, "judgments": ratings,
                            }
                            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                            stream.flush()
                            completed.add(ident)
        manifest["status"] = "complete"
        manifest["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    except Exception:
        manifest["status"] = "interrupted"
        manifest["interrupted_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        raise
    finally:
        manifest["responses_written"] = len(completed)
        _write_json_atomic(manifest_path, manifest)
    return manifest
