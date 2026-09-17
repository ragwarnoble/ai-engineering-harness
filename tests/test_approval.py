import json
from pathlib import Path

import pytest

from harness.approval import (
    create_approval,
    load_approval,
    validate_approval,
    write_approval,
)


def make_approval():
    return create_approval(
        approver="human",
        scope="production_changes",
        reason="Approved after successful quality gate.",
        commit_sha="abc123",
        gate_result="PASS",
    )


def test_create_approval() -> None:
    approval = make_approval()

    assert approval.approved is True
    assert approval.approver == "human"
    assert approval.scope == "production_changes"
    assert approval.commit_sha == "abc123"
    assert approval.gate_result == "PASS"
    assert approval.timestamp


def test_rejects_non_passing_gate() -> None:
    with pytest.raises(ValueError, match="passing quality gate"):
        create_approval(
            approver="human",
            scope="production_changes",
            reason="test",
            commit_sha="abc123",
            gate_result="FAIL",
        )


def test_write_and_load_approval(tmp_path: Path) -> None:
    path = tmp_path / "artifacts" / "approval.json"
    approval = make_approval()

    write_approval(approval, path)

    loaded = load_approval(path)

    assert loaded == approval

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["approved"] is True
    assert data["commit_sha"] == "abc123"


def test_validate_approval() -> None:
    approval = make_approval()

    passed, failures = validate_approval(
        approval,
        expected_commit_sha="abc123",
        gate_passed=True,
        allowed_scopes=("production_changes",),
    )

    assert passed is True
    assert failures == ()


def test_rejects_commit_mismatch() -> None:
    approval = make_approval()

    passed, failures = validate_approval(
        approval,
        expected_commit_sha="different",
        gate_passed=True,
        allowed_scopes=("production_changes",),
    )

    assert passed is False
    assert "approval commit does not match current commit" in failures


def test_rejects_failed_gate() -> None:
    approval = make_approval()

    passed, failures = validate_approval(
        approval,
        expected_commit_sha="abc123",
        gate_passed=False,
        allowed_scopes=("production_changes",),
    )

    assert passed is False
    assert "quality gate did not pass" in failures


def test_rejects_unauthorized_scope() -> None:
    approval = make_approval()

    passed, failures = validate_approval(
        approval,
        expected_commit_sha="abc123",
        gate_passed=True,
        allowed_scopes=("deployment_changes",),
    )

    assert passed is False
    assert "approval scope is not authorized" in failures


def test_rejects_blank_approver() -> None:
    with pytest.raises(ValueError, match="approver is required"):
        create_approval(
            approver=" ",
            scope="production_changes",
            reason="Approved after successful quality gate.",
            commit_sha="abc123",
            gate_result="PASS",
        )


def test_rejects_blank_scope() -> None:
    with pytest.raises(ValueError, match="scope is required"):
        create_approval(
            approver="human",
            scope=" ",
            reason="Approved after successful quality gate.",
            commit_sha="abc123",
            gate_result="PASS",
        )


def test_rejects_blank_reason() -> None:
    with pytest.raises(ValueError, match="reason is required"):
        create_approval(
            approver="human",
            scope="production_changes",
            reason=" ",
            commit_sha="abc123",
            gate_result="PASS",
        )


def test_rejects_blank_commit() -> None:
    with pytest.raises(ValueError, match="commit_sha is required"):
        create_approval(
            approver="human",
            scope="production_changes",
            reason="Approved after successful quality gate.",
            commit_sha=" ",
            gate_result="PASS",
        )
