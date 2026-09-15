from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DataQualityCheck:
    """Definition of one deterministic data-quality check."""

    name: str
    kind: str
    field: str | None = None
    expected_type: type[Any] | None = None
    min_rows: int | None = None
    max_rows: int | None = None


@dataclass(frozen=True)
class DataQualityResult:
    """Result of one data-quality check."""

    name: str
    kind: str
    passed: bool
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class DataQualitySummary:
    """Aggregate result for a data-quality run."""

    passed: bool
    total: int
    passed_count: int
    failed_count: int
    results: tuple[DataQualityResult, ...]


class DataQualityEngine:
    """Run deterministic data-quality checks against tabular records."""

    def evaluate(
        self,
        records: Sequence[Mapping[str, Any]],
        checks: Sequence[DataQualityCheck],
    ) -> DataQualitySummary:
        results = tuple(self._evaluate_check(records, check) for check in checks)
        passed_count = sum(result.passed for result in results)
        failed_count = len(results) - passed_count

        return DataQualitySummary(
            passed=failed_count == 0,
            total=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            results=results,
        )

    def _evaluate_check(
        self,
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        if check.kind == "required_field":
            return self._required_field(records, check)

        if check.kind == "not_null":
            return self._not_null(records, check)

        if check.kind == "unique":
            return self._unique(records, check)

        if check.kind == "type":
            return self._type_check(records, check)

        if check.kind == "row_count":
            return self._row_count(records, check)

        raise ValueError(f"Unsupported data-quality check: {check.kind}")

    @staticmethod
    def _required_field(
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        if check.field is None:
            raise ValueError("required_field check requires a field")

        missing = [index for index, record in enumerate(records) if check.field not in record]

        return DataQualityResult(
            name=check.name,
            kind=check.kind,
            passed=not missing,
            details=(f"missing_rows={len(missing)}",),
        )

    @staticmethod
    def _not_null(
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        if check.field is None:
            raise ValueError("not_null check requires a field")

        null_rows = [
            index for index, record in enumerate(records) if record.get(check.field) is None
        ]

        return DataQualityResult(
            name=check.name,
            kind=check.kind,
            passed=not null_rows,
            details=(f"null_rows={len(null_rows)}",),
        )

    @staticmethod
    def _unique(
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        if check.field is None:
            raise ValueError("unique check requires a field")

        values = [record.get(check.field) for record in records]
        unique_values: list[Any] = []
        duplicate_count = 0

        for value in values:
            if value in unique_values:
                duplicate_count += 1
            else:
                unique_values.append(value)

        return DataQualityResult(
            name=check.name,
            kind=check.kind,
            passed=duplicate_count == 0,
            details=(f"duplicate_values={duplicate_count}",),
        )

    @staticmethod
    def _type_check(
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        if check.field is None or check.expected_type is None:
            raise ValueError("type check requires field and expected_type")

        invalid_rows = [
            index
            for index, record in enumerate(records)
            if check.field in record
            and record[check.field] is not None
            and not isinstance(record[check.field], check.expected_type)
        ]

        return DataQualityResult(
            name=check.name,
            kind=check.kind,
            passed=not invalid_rows,
            details=(f"invalid_rows={len(invalid_rows)}",),
        )

    @staticmethod
    def _row_count(
        records: Sequence[Mapping[str, Any]],
        check: DataQualityCheck,
    ) -> DataQualityResult:
        count = len(records)

        if check.min_rows is not None and count < check.min_rows:
            return DataQualityResult(
                name=check.name,
                kind=check.kind,
                passed=False,
                details=(
                    f"row_count={count}",
                    f"minimum={check.min_rows}",
                ),
            )

        if check.max_rows is not None and count > check.max_rows:
            return DataQualityResult(
                name=check.name,
                kind=check.kind,
                passed=False,
                details=(
                    f"row_count={count}",
                    f"maximum={check.max_rows}",
                ),
            )

        return DataQualityResult(
            name=check.name,
            kind=check.kind,
            passed=True,
            details=(f"row_count={count}",),
        )
