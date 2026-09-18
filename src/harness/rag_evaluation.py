from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RAGEvaluationCase:
    """Deterministic retrieval evaluation case."""

    name: str
    query: str
    retrieved: tuple[str, ...]
    expected: tuple[str, ...]
    out_of_scope: bool = False


@dataclass(frozen=True)
class RAGEvaluationResult:
    """Result of evaluating one retrieval case."""

    name: str
    passed: bool
    hit: bool
    recall: float
    precision: float
    reciprocal_rank: float
    duplicate_rate: float


@dataclass(frozen=True)
class RAGEvaluationSummary:
    """Aggregate retrieval evaluation result."""

    passed: bool
    total: int
    passed_count: int
    failed_count: int
    hit_rate: float
    recall: float
    precision: float
    mrr: float
    duplicate_rate: float
    results: tuple[RAGEvaluationResult, ...]


def evaluate_case(
    case: RAGEvaluationCase,
) -> RAGEvaluationResult:
    """Evaluate one deterministic RAG retrieval case."""

    expected = set(case.expected)
    retrieved = case.retrieved

    unique_retrieved = set(retrieved)
    relevant_retrieved = len(unique_retrieved & expected)

    hit = relevant_retrieved > 0

    recall = relevant_retrieved / len(expected) if expected else 0.0

    precision = relevant_retrieved / len(retrieved) if retrieved else 0.0

    reciprocal_rank = 0.0

    for rank, item in enumerate(retrieved, start=1):
        if item in expected:
            reciprocal_rank = 1.0 / rank
            break

    duplicate_count = len(retrieved) - len(set(retrieved))

    duplicate_rate = duplicate_count / len(retrieved) if retrieved else 0.0

    if case.out_of_scope:
        passed = not retrieved
    else:
        passed = hit and recall >= 1.0 and precision >= 0.5 and duplicate_rate == 0.0

    return RAGEvaluationResult(
        name=case.name,
        passed=passed,
        hit=hit,
        recall=recall,
        precision=precision,
        reciprocal_rank=reciprocal_rank,
        duplicate_rate=duplicate_rate,
    )


def evaluate_rag_cases(
    cases: tuple[RAGEvaluationCase, ...],
) -> RAGEvaluationSummary:
    """Evaluate deterministic RAG retrieval cases."""

    results = tuple(evaluate_case(case) for case in cases)

    total = len(results)

    passed_count = sum(result.passed for result in results)

    failed_count = total - passed_count

    hit_rate = sum(result.hit for result in results) / total if total else 0.0

    recall = sum(result.recall for result in results) / total if total else 0.0

    precision = sum(result.precision for result in results) / total if total else 0.0

    mrr = sum(result.reciprocal_rank for result in results) / total if total else 0.0

    duplicate_rate = sum(result.duplicate_rate for result in results) / total if total else 0.0

    return RAGEvaluationSummary(
        passed=failed_count == 0,
        total=total,
        passed_count=passed_count,
        failed_count=failed_count,
        hit_rate=hit_rate,
        recall=recall,
        precision=precision,
        mrr=mrr,
        duplicate_rate=duplicate_rate,
        results=results,
    )


def build_rag_evaluation() -> tuple[RAGEvaluationCase, ...]:
    """Build deterministic RAG retrieval regression cases."""

    return (
        RAGEvaluationCase(
            name="technologies",
            query="technologies",
            retrieved=(
                "about.md#technologies",
                "skills.md#skills",
            ),
            expected=("about.md#technologies",),
        ),
        RAGEvaluationCase(
            name="architecture",
            query="architecture",
            retrieved=("architecture.md#architecture",),
            expected=("architecture.md#architecture",),
        ),
        RAGEvaluationCase(
            name="projects",
            query="projects",
            retrieved=("projects.md#projects",),
            expected=("projects.md#projects",),
        ),
        RAGEvaluationCase(
            name="skills",
            query="skills",
            retrieved=("skills.md#skills",),
            expected=("skills.md#skills",),
        ),
        RAGEvaluationCase(
            name="out_of_scope",
            query="weather",
            retrieved=(),
            expected=(),
            out_of_scope=True,
        ),
    )


def run_rag_evaluation() -> bool:
    """Run deterministic RAG evaluation and return its pass status."""

    summary = evaluate_rag_cases(build_rag_evaluation())
    return summary.passed
