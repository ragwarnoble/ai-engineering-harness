from __future__ import annotations

from collections.abc import Callable

from harness.engineering_evaluation import run_engineering_evaluation

EvaluationRunner = Callable[[], bool]

EVALUATION_RUNNERS: dict[str, EvaluationRunner] = {
    "engineering_evaluation": run_engineering_evaluation,
}


def run_configured_evaluations(
    required: tuple[str, ...],
) -> dict[str, bool]:
    """Run available evaluation adapters for required evaluation names."""

    results: dict[str, bool] = {}

    for name in required:
        runner = EVALUATION_RUNNERS.get(name)

        if runner is None:
            continue

        results[name] = runner()

    return results
