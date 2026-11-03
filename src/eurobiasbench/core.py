"""Dataset validation and model configuration."""
from __future__ import annotations

import hashlib
import json
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

AXES = ("expression", "pluralism", "fundamental_rights", "normative_autonomy",
        "eu_law", "geopolitical_framing")
REQUIRED = {"id", "axis", "prompt_a", "prompt_b", "variation", "expected_behavior", "references"}


def load_dataset(path: str | None = None) -> tuple[list[dict[str, Any]], str]:
    raw = Path(path).read_text(encoding="utf-8") if path else (
        resources.files("eurobiasbench").joinpath("data/pilot_60.json").read_text(encoding="utf-8")
    )
    data = json.loads(raw)
    cases = data["cases"] if isinstance(data, dict) else data
    validate_dataset(cases)
    return cases, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_dataset(cases: list[dict[str, Any]], *, pilot: bool = False) -> None:
    if not isinstance(cases, list) or not cases:
        raise ValueError("Expected a nonempty case list")
    counts = dict.fromkeys(AXES, 0)
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not REQUIRED.issubset(case):
            raise ValueError("Case missing required fields")
        ident = case["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError(f"Invalid or duplicate case ID {ident!r}")
        seen.add(ident)
        axis = case["axis"]
        if axis not in counts:
            raise ValueError(f"Invalid axis: {axis}")
        counts[axis] += 1
        for field in ("prompt_a", "prompt_b", "variation", "expected_behavior"):
            if not isinstance(case[field], str) or not case[field].strip():
                raise ValueError(f"{ident}: empty {field}")
        if case["prompt_a"].strip() == case["prompt_b"].strip():
            raise ValueError(f"{ident}: prompts must differ")
        if not isinstance(case["references"], list) or not case["references"] or not all(
            isinstance(x, str) and x.startswith("http") for x in case["references"]
        ):
            raise ValueError(f"{ident}: invalid references")
    if pilot and (len(cases) != 60 or set(counts.values()) != {10}):
        raise ValueError(f"Pilot must contain 60 cases (10 per axis): {counts}")


def load_entries(path: str, group: str) -> list[dict[str, Any]]:
    with open(path, "rb") as stream:
        entries = tomllib.load(stream).get(group)
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"Expected nonempty [[{group}]] array")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or any(not entry.get(k) for k in ("id", "model", "base_url")):
            raise ValueError(f"Each [[{group}]] requires id, model, base_url")
        if entry["id"] in seen:
            raise ValueError(f"Duplicate {group} id")
        seen.add(entry["id"])
        if not entry["base_url"].startswith(("http://", "https://")):
            raise ValueError("Endpoint must be http(s)")
    return entries
