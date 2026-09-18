from harness.rag_evaluation import (
    RAGEvaluationCase,
    build_rag_evaluation,
    evaluate_case,
    evaluate_rag_cases,
    run_rag_evaluation,
)


def test_build_rag_evaluation() -> None:
    cases = build_rag_evaluation()

    assert len(cases) == 5
    assert cases[-1].name == "out_of_scope"
    assert cases[-1].out_of_scope is True


def test_rag_evaluation_passes() -> None:
    assert run_rag_evaluation() is True


def test_rag_metrics() -> None:
    case = RAGEvaluationCase(
        name="metric_case",
        query="test",
        retrieved=("a", "b", "c"),
        expected=("a", "b"),
    )

    result = evaluate_case(case)

    assert result.hit is True
    assert result.recall == 1.0
    assert result.precision == 2 / 3
    assert result.reciprocal_rank == 1.0
    assert result.duplicate_rate == 0.0
    assert result.passed is True


def test_duplicate_retrieval_is_detected() -> None:
    case = RAGEvaluationCase(
        name="duplicate_case",
        query="test",
        retrieved=("a", "a", "b"),
        expected=("a", "b"),
    )

    result = evaluate_case(case)

    assert result.hit is True
    assert result.recall == 1.0
    assert result.precision == 2 / 3
    assert result.reciprocal_rank == 1.0
    assert result.duplicate_rate == 1 / 3
    assert result.passed is False


def test_partial_recall_is_detected() -> None:
    case = RAGEvaluationCase(
        name="partial_recall_case",
        query="test",
        retrieved=("a",),
        expected=("a", "b"),
    )

    result = evaluate_case(case)

    assert result.hit is True
    assert result.recall == 0.5
    assert result.precision == 1.0
    assert result.reciprocal_rank == 1.0
    assert result.duplicate_rate == 0.0
    assert result.passed is False


def test_out_of_scope_rejection_passes() -> None:
    case = RAGEvaluationCase(
        name="out_of_scope",
        query="weather",
        retrieved=(),
        expected=(),
        out_of_scope=True,
    )

    result = evaluate_case(case)

    assert result.hit is False
    assert result.recall == 0.0
    assert result.precision == 0.0
    assert result.reciprocal_rank == 0.0
    assert result.duplicate_rate == 0.0
    assert result.passed is True


def test_summary_metrics() -> None:
    summary = evaluate_rag_cases(build_rag_evaluation())

    assert summary.total == 5
    assert summary.passed_count == 5
    assert summary.failed_count == 0
    assert summary.passed is True
    assert summary.hit_rate == 0.8
    assert summary.recall == 0.8
    assert summary.precision == 0.7
    assert summary.mrr == 0.8
    assert summary.duplicate_rate == 0.0
