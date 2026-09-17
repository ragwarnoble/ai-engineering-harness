import pytest

from harness.execution_policy import (
    get_execution_policy,
    is_action_allowed,
)


def test_read_only_policy() -> None:
    policy = get_execution_policy("read_only")

    assert policy.allowed is True
    assert policy.requires_human_approval is False
    assert "inspect" in policy.allowed_actions


def test_production_requires_approval() -> None:
    policy = get_execution_policy("production_changes")

    assert policy.allowed is True
    assert policy.requires_human_approval is True
    assert "commit" in policy.allowed_actions


def test_action_allowed() -> None:
    assert is_action_allowed("development_changes", "edit") is True
    assert is_action_allowed("development_changes", "deploy") is False


def test_unknown_scope() -> None:
    with pytest.raises(ValueError, match="unknown execution scope"):
        get_execution_policy("unknown")
