from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ExecutionRequest:
    target_commit: str
    scope: str
    requested_by: str
    requested_at: str


def create_execution_request(
    *,
    target_commit: str,
    scope: str,
    requested_by: str,
) -> ExecutionRequest:
    if not target_commit.strip():
        raise ValueError("target_commit is required")
    if not scope.strip():
        raise ValueError("scope is required")
    if not requested_by.strip():
        raise ValueError("requested_by is required")

    return ExecutionRequest(
        target_commit=target_commit.strip(),
        scope=scope.strip(),
        requested_by=requested_by.strip(),
        requested_at=datetime.now(UTC).isoformat(),
    )
