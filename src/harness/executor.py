from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.authorization import authorize
from harness.execution_policy import (
    get_execution_policy,
    is_action_allowed,
)


@dataclass(frozen=True)
class ExecutionResult:
    executed: bool
    scope: str
    action: str
    failures: tuple[str, ...]


def execute(
    root: Path,
    *,
    scope: str,
    action: str,
) -> ExecutionResult:
    failures: list[str] = []

    try:
        policy = get_execution_policy(scope)
    except ValueError as exc:
        return ExecutionResult(
            executed=False,
            scope=scope,
            action=action,
            failures=(str(exc),),
        )

    if not policy.allowed:
        failures.append("execution scope is disabled")

    if not is_action_allowed(scope, action):
        failures.append(f"action '{action}' is not allowed for scope '{scope}'")

    if policy.requires_human_approval:
        authorization = authorize(
            root,
            scope=scope,
            allowed_scopes=tuple(
                {
                    "read_only",
                    "development_changes",
                    "production_changes",
                    "deployment_changes",
                }
            ),
        )

        if not authorization.authorized:
            failures.extend(authorization.failures)

    return ExecutionResult(
        executed=not failures,
        scope=scope,
        action=action,
        failures=tuple(failures),
    )
