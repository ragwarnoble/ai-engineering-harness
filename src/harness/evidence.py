from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from harness.evaluation import EvaluationSummary


@dataclass(frozen=True)
class EvidenceRecord:
    """Machine-readable evidence produced by an evaluation."""

    category: str
    name: str
    passed: bool
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationEvidence:
    """Evidence package for one evaluation run."""

    timestamp: str
    passed: bool
    records: tuple[EvidenceRecord, ...]


def build_evidence(
    summary: EvaluationSummary,
    *,
    category: str = "evaluation",
) -> EvaluationEvidence:
    """Convert an evaluation summary into immutable evidence."""

    records = tuple(
        EvidenceRecord(
            category=category,
            name=result.name,
            passed=result.passed,
            details=(
                f"expected={result.expected}",
                f"actual={result.actual}",
                *result.evidence,
            ),
        )
        for result in summary.results
    )

    return EvaluationEvidence(
        timestamp=datetime.now(UTC).isoformat(),
        passed=summary.passed,
        records=records,
    )
