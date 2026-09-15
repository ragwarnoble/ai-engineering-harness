from __future__ import annotations

import pytest

from harness.data_quality import (
    DataQualityCheck,
    DataQualityEngine,
)

RECORDS = (
    {"id": 1, "name": "Alice", "score": 10.5},
    {"id": 2, "name": "Bob", "score": 20.0},
)


def test_required_field_passes() -> None:
    result = DataQualityEngine().evaluate(
        RECORDS,
        (
            DataQualityCheck(
                name="name-required",
                kind="required_field",
                field="name",
            ),
        ),
    )

    assert result.passed is True
    assert result.passed_count == 1
    assert result.failed_count == 0


def test_required_field_fails() -> None:
    result = DataQualityEngine().evaluate(
        ({"id": 1},),
        (
            DataQualityCheck(
                name="name-required",
                kind="required_field",
                field="name",
            ),
        ),
    )

    assert result.passed is False
    assert result.results[0].details == ("missing_rows=1",)


def test_not_null_fails() -> None:
    result = DataQualityEngine().evaluate(
        ({"id": 1, "name": None},),
        (
            DataQualityCheck(
                name="name-not-null",
                kind="not_null",
                field="name",
            ),
        ),
    )

    assert result.passed is False
    assert result.results[0].details == ("null_rows=1",)


def test_unique_fails_for_duplicates() -> None:
    result = DataQualityEngine().evaluate(
        (
            {"id": 1},
            {"id": 1},
        ),
        (
            DataQualityCheck(
                name="id-unique",
                kind="unique",
                field="id",
            ),
        ),
    )

    assert result.passed is False
    assert result.results[0].details == ("duplicate_values=1",)


def test_type_check_passes() -> None:
    result = DataQualityEngine().evaluate(
        RECORDS,
        (
            DataQualityCheck(
                name="score-type",
                kind="type",
                field="score",
                expected_type=float,
            ),
        ),
    )

    assert result.passed is True


def test_type_check_fails() -> None:
    result = DataQualityEngine().evaluate(
        ({"score": "10"},),
        (
            DataQualityCheck(
                name="score-type",
                kind="type",
                field="score",
                expected_type=float,
            ),
        ),
    )

    assert result.passed is False
    assert result.results[0].details == ("invalid_rows=1",)


def test_row_count_bounds() -> None:
    engine = DataQualityEngine()

    minimum_failure = engine.evaluate(
        RECORDS,
        (
            DataQualityCheck(
                name="minimum-rows",
                kind="row_count",
                min_rows=3,
            ),
        ),
    )

    maximum_failure = engine.evaluate(
        RECORDS,
        (
            DataQualityCheck(
                name="maximum-rows",
                kind="row_count",
                max_rows=1,
            ),
        ),
    )

    assert minimum_failure.passed is False
    assert maximum_failure.passed is False


def test_row_count_passes() -> None:
    result = DataQualityEngine().evaluate(
        RECORDS,
        (
            DataQualityCheck(
                name="row-count",
                kind="row_count",
                min_rows=1,
                max_rows=3,
            ),
        ),
    )

    assert result.passed is True
    assert result.results[0].details == ("row_count=2",)


def test_invalid_check_configuration() -> None:
    with pytest.raises(ValueError, match="requires a field"):
        DataQualityEngine().evaluate(
            RECORDS,
            (
                DataQualityCheck(
                    name="invalid",
                    kind="required_field",
                ),
            ),
        )


def test_unsupported_check() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        DataQualityEngine().evaluate(
            RECORDS,
            (
                DataQualityCheck(
                    name="invalid",
                    kind="unknown",
                ),
            ),
        )


def test_unique_supports_unhashable_values() -> None:
    result = DataQualityEngine().evaluate(
        (
            {"tags": ["ai", "data"]},
            {"tags": ["ai", "data"]},
        ),
        (
            DataQualityCheck(
                name="tags-unique",
                kind="unique",
                field="tags",
            ),
        ),
    )

    assert result.passed is False
    assert result.results[0].details == ("duplicate_values=1",)
