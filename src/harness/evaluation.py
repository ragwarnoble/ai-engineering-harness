from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EvaluationCase:
    """A deterministic evaluation case."""

    name: str
    input: str
    expected: str


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating one case."""

    name: str
    passed: bool
    actual: str
    expected: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregate result for an evaluation run."""

    passed: bool
    total: int
    passed_count: int
    failed_count: int
    results: tuple[EvaluationResult, ...]


class Evaluator(Protocol):
    """Provider-neutral evaluation interface."""

    def evaluate(self, case: EvaluationCase) -> EvaluationResult:
        """Evaluate one case."""
        ...


class DeterministicEvaluator:
    """Simple evaluator for exact deterministic comparisons."""

    def __init__(self, handler: Callable[[str], str]) -> None:
        self._handler = handler

    def evaluate(self, case: EvaluationCase) -> EvaluationResult:
        actual = str(self._handler(case.input))
        passed = actual == case.expected

        return EvaluationResult(
            name=case.name,
            passed=passed,
            actual=actual,
            expected=case.expected,
            evidence=("exact-match",),
        )


def evaluate_cases(
    evaluator: Evaluator,
    cases: tuple[EvaluationCase, ...],
) -> EvaluationSummary:
    """Evaluate all cases and return a deterministic summary."""

    results = tuple(evaluator.evaluate(case) for case in cases)
    passed_count = sum(result.passed for result in results)
    failed_count = len(results) - passed_count

    return EvaluationSummary(
        passed=failed_count == 0,
        total=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=results,
    )
