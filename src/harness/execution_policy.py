from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionPolicy:
    scope: str
    allowed: bool
    requires_human_approval: bool
    allowed_actions: tuple[str, ...]


DEFAULT_POLICIES: dict[str, ExecutionPolicy] = {
    "read_only": ExecutionPolicy(
        scope="read_only",
        allowed=True,
        requires_human_approval=False,
        allowed_actions=(
            "inspect",
            "search",
            "test",
            "analyze",
        ),
    ),
    "development_changes": ExecutionPolicy(
        scope="development_changes",
        allowed=True,
        requires_human_approval=False,
        allowed_actions=(
            "edit",
            "test",
            "format",
            "lint",
        ),
    ),
    "production_changes": ExecutionPolicy(
        scope="production_changes",
        allowed=True,
        requires_human_approval=True,
        allowed_actions=(
            "edit",
            "test",
            "commit",
        ),
    ),
    "deployment_changes": ExecutionPolicy(
        scope="deployment_changes",
        allowed=True,
        requires_human_approval=True,
        allowed_actions=(
            "deploy",
            "rollback",
        ),
    ),
}


def get_execution_policy(scope: str) -> ExecutionPolicy:
    try:
        return DEFAULT_POLICIES[scope]
    except KeyError as exc:
        raise ValueError(f"unknown execution scope: {scope}") from exc


def is_action_allowed(
    scope: str,
    action: str,
) -> bool:
    policy = get_execution_policy(scope)
    return policy.allowed and action in policy.allowed_actions
