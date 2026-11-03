"""Case-clustered descriptive summaries; repetitions are not independent cases."""
from __future__ import annotations

import random
from statistics import mean


def bootstrap_case_mean(case_scores: dict[str, list[float]], *,
                        draws: int = 2000, seed: int = 20261103) -> dict:
    """Mean and percentile interval bootstrapped across *cases*, not generations.

    Treats the provided cases as an exchangeable pilot sample. This does not
    establish representativeness, correctness of judge labels, or legal validity.
    """
    if draws < 100:
        raise ValueError("At least 100 resamples required")
    values = [mean(v) for _, v in sorted(case_scores.items()) if v]
    if not values:
        raise ValueError("Need at least one nonempty case")
    result = {"mean": round(mean(values), 4), "case_count": len(values), "ci95": None}
    if len(values) < 3:
        return result
    rng = random.Random(seed)
    n = len(values)
    sampled = sorted(mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(draws))
    result["ci95"] = [
        round(sampled[int(0.025 * (draws - 1))], 4),
        round(sampled[int(0.975 * (draws - 1))], 4),
    ]
    return result
