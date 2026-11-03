"""Descriptive reports and targeted human audit queue (not a certification)."""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .core import AXES


def report(directory: str, *, audit_fraction: float = 0.1) -> dict[str, Any]:
    if not 0 <= audit_fraction <= 1:
        raise ValueError("audit_fraction must be in [0, 1]")
    folder = Path(directory)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (folder / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("No responses found")
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    pairs: dict[tuple[str, str, str, int], float] = {}
    axis_by_case = {r["case_id"]: r["axis"] for r in rows}
    disagreement_count = 0
    flag: set[int] = set()
    for index, row in enumerate(rows):
        ratings = row["judgments"]
        if len(ratings) != 2:
            raise ValueError("Expected exactly two judge ratings")
        a, b = (item["scores"]["axis_score"] for item in ratings)
        if a != b:
            disagreement_count += 1
        if abs(a - b) >= 2 or any(item["uncertain"] for item in ratings):
            flag.add(index)
        average = (a + b) / 2
        groups[(row["model_id"], row["axis"])].append(average)
        pairs[(row["model_id"], row["case_id"], row["variant"], row["repeat"])] = average
    rng = random.Random(20261103)
    random_indices = set(rng.sample(range(len(rows)), k=round(len(rows) * audit_fraction)))
    all_flags = flag | random_indices
    with (folder / "human_audit_queue.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["case_id", "axis", "model_id", "variant", "repeat", "prompt",
                  "answer", "expected_behavior", "references", "judge_a", "judge_b",
                  "reason", "human_score", "human_notes"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index in sorted(all_flags):
            r = rows[index]
            writer.writerow({
                "case_id": r["case_id"], "axis": r["axis"], "model_id": r["model_id"],
                "variant": r["variant"], "repeat": r["repeat"], "prompt": r["prompt"],
                "answer": r["answer"], "expected_behavior": r["expected_behavior"],
                "references": ";".join(r["references"]),
                "judge_a": r["judgments"][0]["scores"]["axis_score"],
                "judge_b": r["judgments"][1]["scores"]["axis_score"],
                "reason": "uncertain_or_large_disagreement" if index in flag else "random_sample",
                "human_score": "", "human_notes": "",
            })
    models = sorted({m for m, _ in groups})
    axis_means = {
        m: {a: round(mean(v), 3) for (mm, a), v in sorted(groups.items()) if mm == m}
        for m in models
    }
    gaps: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (model, case, variant, rep), value in pairs.items():
        if variant != "a":
            continue
        other = pairs.get((model, case, "b", rep))
        if other is not None:
            gaps[(model, axis_by_case[case])].append(abs(value - other))
    paired_gaps = {
        model: {axis: round(mean(v), 3) for (m, axis), v in sorted(gaps.items()) if m == model}
        for model in models
    }
    summary = {
        "synthetic": manifest["synthetic"], "response_count": len(rows),
        "human_audit_queue_count": len(all_flags),
        "judge_disagreement_rate": disagreement_count / len(rows),
        "axis_score_mean_by_model": axis_means,
        "paired_absolute_gap_by_model": paired_gaps,
    }
    (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# EuroBiasBench v0.1 — exploratory run", "",
        "Mode: " + ("SYNTHETIC MOCK" if manifest["synthetic"] else "live (unvalidated LLM judge ratings)"),
        "",
        f"Responses: {len(rows)}. Human audit queue: {len(all_flags)}.",
        f"Judge axis-score disagreement: {disagreement_count / len(rows):.1%}.", "",
    ]
    if manifest["synthetic"]:
        lines += ["> ALL OUTPUTS AND SCORES ARE SYNTHETIC. NO MODEL WAS EVALUATED.", ""]
    else:
        lines += ["> Automated grades have not been calibrated against human ratings.", ""]
    lines += [
        "## Average axis score, out of 4 (descriptive only)", "",
        "| Model | " + " | ".join(AXES) + " |",
        "| --- | " + " | ".join("---:" for _ in AXES) + " |",
    ]
    for model, scores in axis_means.items():
        lines.append("| " + model + " | " + " | ".join(str(scores.get(a, "—")) for a in AXES) + " |")
    lines += [
        "", "## Limits", "",
        "- Scoring is exploratory and not certification of EU law or political neutrality.",
        "- Pairwise score differences do not by themselves demonstrate bias.",
        "- Facts may justify asymmetric conclusions.",
        "- Audit a random sample and all important disagreements; measure human agreement.",
        "- Use a held-out benchmark for later weight editing and report regression tests.",
        "",
    ]
    (folder / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary
