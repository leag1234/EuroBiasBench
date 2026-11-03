"""Descriptive reports, case-clustered uncertainty, and targeted audit samples."""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .core import AXES
from .engine import METRICS
from .statistics import bootstrap_case_mean


def report(directory: str, *, audit_fraction: float = 0.1) -> dict[str, Any]:
    if not 0 <= audit_fraction <= 1:
        raise ValueError("audit_fraction must be in [0, 1]")
    folder = Path(directory)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (folder / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("No responses found")
    if manifest.get("status") != "complete":
        raise ValueError("Run not complete. Resume with eurobiasbench run --resume before reporting.")

    clusters: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
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
        for metric in METRICS:
            value = mean(item["scores"][metric] for item in ratings)
            clusters[(row["model_id"], row["axis"], metric)][row["case_id"]].append(value)
        pairs[(row["model_id"], row["case_id"], row["variant"], row["repeat"])] = mean((a, b))

    random_indices = set(random.Random(20261103).sample(range(len(rows)), k=round(len(rows) * audit_fraction)))
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

    models = sorted({model for model, _, _ in clusters})
    estimates = {
        model: {
            axis: {
                metric: bootstrap_case_mean(clusters[(model, axis, metric)])
                for metric in METRICS if (model, axis, metric) in clusters
            }
            for axis in AXES if (model, axis, "axis_score") in clusters
        }
        for model in models
    }
    axis_means = {
        model: {axis: values["axis_score"]["mean"] for axis, values in axes.items()}
        for model, axes in estimates.items()
    }
    absolute: dict[tuple[str, str], list[float]] = defaultdict(list)
    signed: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (model, case, variant, rep), value in pairs.items():
        if variant != "a":
            continue
        other = pairs.get((model, case, "b", rep))
        if other is not None:
            absolute[(model, axis_by_case[case])].append(abs(value - other))
            signed[(model, axis_by_case[case])].append(value - other)

    def summarize_gaps(source: dict[tuple[str, str], list[float]]) -> dict[str, dict[str, float]]:
        return {
            model: {axis: round(mean(v), 4) for (m, axis), v in sorted(source.items()) if m == model}
            for model in models
        }

    summary = {
        "synthetic": manifest["synthetic"], "response_count": len(rows),
        "human_audit_queue_count": len(all_flags),
        "random_audit_sample_count": len(random_indices),
        "judge_disagreement_rate": round(disagreement_count / len(rows), 4),
        "axis_score_mean_by_model": axis_means,
        "case_clustered_estimates_by_model": estimates,
        "paired_absolute_gap_by_model": summarize_gaps(absolute),
        "paired_signed_gap_a_minus_b_by_model": summarize_gaps(signed),
        "caveat": "Bootstrap intervals quantify sampling variation across draft cases only, not label or legal uncertainty.",
    }
    (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# EuroBiasBench v0.1 — exploratory run", "",
        "Mode: " + ("SYNTHETIC MOCK" if manifest["synthetic"] else "live (unvalidated LLM judge ratings)"),
        "", f"Responses: {len(rows)}. Human audit queue: {len(all_flags)}.",
        f"Judge axis-score disagreement: {disagreement_count / len(rows):.1%}.", "",
    ]
    if manifest["synthetic"]:
        lines += ["> ALL OUTPUTS AND SCORES ARE SYNTHETIC. NO MODEL WAS EVALUATED.", ""]
    else:
        lines += ["> Automated grades have not been calibrated against human ratings.", ""]
    lines += [
        "## Axis score, mean of case means (0–4)", "",
        "| Model | " + " | ".join(AXES) + " |",
        "| --- | " + " | ".join("---:" for _ in AXES) + " |",
    ]
    for model, scores in axis_means.items():
        lines.append("| " + model + " | " + " | ".join(str(scores.get(a, "—")) for a in AXES) + " |")
    lines += ["", "## Case-clustered bootstrap intervals (95%, descriptive only)", "",
              "| Model | Axis | Cases | Mean | Percentile interval |",
              "| --- | --- | ---: | ---: | --- |"]
    for model, axes in estimates.items():
        for axis, scores in axes.items():
            value = scores["axis_score"]
            ci = value["ci95"]
            lines.append(f"| {model} | {axis} | {value['case_count']} | {value['mean']} | {str(ci) if ci else 'Not estimated (<3 cases)'} |")
    lines += [
        "", "## Interpretation safeguards", "",
        "- These intervals only resample draft cases; they do not validate the judge, legal claims, or sampling representativeness.",
        "- Repeats and both variants are clustered within each case, not counted as independent observations.",
        "- Signed A-minus-B differences are diagnostics, not direct evidence of any country's political bias.",
        "- Do not aggregate axes to conceal failures in rights or law.",
        "- Use independent, blind human double annotation with legal expertise for hard cases.",
        "- Retain sealed held-out cases when subsequently editing model weights.",
        "",
    ]
    (folder / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary
