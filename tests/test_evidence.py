from datetime import datetime

from harness.evaluation import (
    DeterministicEvaluator,
    EvaluationCase,
    evaluate_cases,
)
from harness.evidence import (
    EvidenceRecord,
    build_evidence,
)


def test_build_evidence_from_evaluation() -> None:
    evaluator = DeterministicEvaluator(lambda value: value.upper())

    summary = evaluate_cases(
        evaluator,
        (EvaluationCase("uppercase", "hello", "HELLO"),),
    )

    evidence = build_evidence(summary)

    assert evidence.passed is True
    assert len(evidence.records) == 1
    assert evidence.records[0] == EvidenceRecord(
        category="evaluation",
        name="uppercase",
        passed=True,
        details=(
            "expected=HELLO",
            "actual=HELLO",
            "exact-match",
        ),
    )


def test_build_evidence_supports_custom_category() -> None:
    evaluator = DeterministicEvaluator(lambda value: value)

    summary = evaluate_cases(
        evaluator,
        (EvaluationCase("data-quality", "valid", "valid"),),
    )

    evidence = build_evidence(summary, category="data")

    assert evidence.records[0].category == "data"


def test_build_evidence_preserves_failure() -> None:
    evaluator = DeterministicEvaluator(lambda value: value.upper())

    summary = evaluate_cases(
        evaluator,
        (EvaluationCase("mismatch", "hello", "wrong"),),
    )

    evidence = build_evidence(summary)

    assert evidence.passed is False
    assert evidence.records[0].passed is False


def test_evidence_timestamp_is_valid_utc_iso_format() -> None:
    evaluator = DeterministicEvaluator(lambda value: value)

    summary = evaluate_cases(
        evaluator,
        (EvaluationCase("identity", "value", "value"),),
    )

    evidence = build_evidence(summary)

    timestamp = datetime.fromisoformat(evidence.timestamp)

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() is not None
