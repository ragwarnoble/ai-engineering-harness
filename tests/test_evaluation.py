from harness.evaluation import (
    DeterministicEvaluator,
    EvaluationCase,
    EvaluationResult,
    evaluate_cases,
)


def test_deterministic_evaluator_passes_exact_match() -> None:
    evaluator = DeterministicEvaluator(lambda value: value.upper())

    result = evaluator.evaluate(
        EvaluationCase(
            name="uppercase",
            input="hello",
            expected="HELLO",
        )
    )

    assert result == EvaluationResult(
        name="uppercase",
        passed=True,
        actual="HELLO",
        expected="HELLO",
        evidence=("exact-match",),
    )


def test_deterministic_evaluator_rejects_mismatch() -> None:
    evaluator = DeterministicEvaluator(lambda value: value.upper())

    result = evaluator.evaluate(
        EvaluationCase(
            name="uppercase",
            input="hello",
            expected="hello",
        )
    )

    assert result.passed is False
    assert result.actual == "HELLO"
    assert result.expected == "hello"


def test_evaluate_cases_returns_summary() -> None:
    evaluator = DeterministicEvaluator(lambda value: value.upper())

    summary = evaluate_cases(
        evaluator,
        (
            EvaluationCase("pass", "hello", "HELLO"),
            EvaluationCase("fail", "world", "wrong"),
        ),
    )

    assert summary.passed is False
    assert summary.total == 2
    assert summary.passed_count == 1
    assert summary.failed_count == 1
    assert len(summary.results) == 2


def test_evaluate_empty_cases_passes() -> None:
    evaluator = DeterministicEvaluator(lambda value: value)

    summary = evaluate_cases(evaluator, ())

    assert summary.passed is True
    assert summary.total == 0
    assert summary.passed_count == 0
    assert summary.failed_count == 0
    assert summary.results == ()
