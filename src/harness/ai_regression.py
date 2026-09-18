from __future__ import annotations

from harness.evaluation import (
    DeterministicEvaluator,
    EvaluationCase,
    EvaluationSpec,
    run_evaluation,
)


def build_ai_regression() -> EvaluationSpec:
    """Build deterministic AI regression checks for the harness."""

    evaluator = DeterministicEvaluator(lambda value: value)

    cases = (
        EvaluationCase(
            name="stable_response",
            input="ai-engineering-platform",
            expected="ai-engineering-platform",
        ),
        EvaluationCase(
            name="provider_neutral_response",
            input="provider-neutral",
            expected="provider-neutral",
        ),
        EvaluationCase(
            name="regression_baseline",
            input="regression-baseline",
            expected="regression-baseline",
        ),
    )

    return EvaluationSpec(
        name="ai_regression",
        evaluator=evaluator,
        cases=cases,
    )


def run_ai_regression() -> bool:
    """Run the AI regression evaluation and return its pass status."""

    summary = run_evaluation(build_ai_regression())
    return summary.passed
