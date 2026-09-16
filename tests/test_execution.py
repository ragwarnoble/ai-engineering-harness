import pytest

from harness.execution import create_execution_request


def test_create_execution_request() -> None:
    request = create_execution_request(
        target_commit="abc123",
        scope="production_changes",
        requested_by="agent",
    )

    assert request.target_commit == "abc123"
    assert request.scope == "production_changes"
    assert request.requested_by == "agent"
    assert request.requested_at


def test_requires_target_commit() -> None:
    with pytest.raises(ValueError, match="target_commit"):
        create_execution_request(
            target_commit="",
            scope="production_changes",
            requested_by="agent",
        )


def test_requires_scope() -> None:
    with pytest.raises(ValueError, match="scope"):
        create_execution_request(
            target_commit="abc123",
            scope="",
            requested_by="agent",
        )


def test_requires_requester() -> None:
    with pytest.raises(ValueError, match="requested_by"):
        create_execution_request(
            target_commit="abc123",
            scope="production_changes",
            requested_by="",
        )
