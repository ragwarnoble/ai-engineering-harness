from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from harness.data_quality import DataQualitySummary
from harness.evaluation import EvaluationSummary


class EvidenceResult(Protocol):
    """Common interface for results that can produce evidence."""

    name: str
    passed: bool


@dataclass(frozen=True)
class EvidenceRecord:
    """Machine-readable evidence produced by an evaluation or data check."""

    category: str
    name: str
    passed: bool
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationEvidence:
    """Evidence package for one evaluation or data-quality run."""

    timestamp: str
    passed: bool
    records: tuple[EvidenceRecord, ...]


def build_evidence(
    summary: EvaluationSummary | DataQualitySummary,
    *,
    category: str = "evaluation",
) -> EvaluationEvidence:
    """Convert an evaluation or data-quality summary into immutable evidence."""

    if isinstance(summary, EvaluationSummary):
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
    else:
        records = tuple(
            EvidenceRecord(
                category=category,
                name=result.name,
                passed=result.passed,
                details=result.details,
            )
            for result in summary.results
        )

    return EvaluationEvidence(
        timestamp=datetime.now(UTC).isoformat(),
        passed=summary.passed,
        records=records,
    )
