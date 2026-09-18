from __future__ import annotations

from harness.evaluation import (
    DeterministicEvaluator,
    EvaluationCase,
    EvaluationSpec,
    run_evaluation,
)


def build_engineering_evaluation() -> EvaluationSpec:
    """Build deterministic engineering checks for the harness."""

    evaluator = DeterministicEvaluator(lambda value: value)

    cases = (
        EvaluationCase(
            name="deterministic_identity",
            input="ai-engineering-platform",
            expected="ai-engineering-platform",
        ),
        EvaluationCase(
            name="provider_neutral_identity",
            input="provider-neutral",
            expected="provider-neutral",
        ),
    )

    return EvaluationSpec(
        name="engineering_evaluation",
        evaluator=evaluator,
        cases=cases,
    )


def run_engineering_evaluation() -> bool:
    """Run the engineering evaluation and return its pass status."""

    summary = run_evaluation(build_engineering_evaluation())
    return summary.passed
