from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ApprovalRecord:
    approved: bool
    approver: str
    scope: str
    reason: str
    commit_sha: str
    gate_result: str
    timestamp: str


def create_approval(
    *,
    approver: str,
    scope: str,
    reason: str,
    commit_sha: str,
    gate_result: str,
) -> ApprovalRecord:
    """Create an explicit human authorization record."""

    if not approver.strip():
        raise ValueError("approver is required")

    if not scope.strip():
        raise ValueError("scope is required")

    if not reason.strip():
        raise ValueError("reason is required")

    if not commit_sha.strip():
        raise ValueError("commit_sha is required")

    if gate_result != "PASS":
        raise ValueError("approval requires a passing quality gate")

    return ApprovalRecord(
        approved=True,
        approver=approver.strip(),
        scope=scope.strip(),
        reason=reason.strip(),
        commit_sha=commit_sha.strip(),
        gate_result=gate_result,
        timestamp=datetime.now(UTC).isoformat(),
    )


def write_approval(
    approval: ApprovalRecord,
    path: Path,
) -> None:
    """Persist an approval record as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            {
                "approved": approval.approved,
                "approver": approval.approver,
                "scope": approval.scope,
                "reason": approval.reason,
                "commit_sha": approval.commit_sha,
                "gate_result": approval.gate_result,
                "timestamp": approval.timestamp,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def load_approval(path: Path) -> ApprovalRecord:
    """Load and validate an approval record."""

    data = json.loads(path.read_text(encoding="utf-8"))

    return ApprovalRecord(
        approved=bool(data["approved"]),
        approver=str(data["approver"]),
        scope=str(data["scope"]),
        reason=str(data["reason"]),
        commit_sha=str(data["commit_sha"]),
        gate_result=str(data["gate_result"]),
        timestamp=str(data["timestamp"]),
    )


def validate_approval(
    approval: ApprovalRecord,
    *,
    expected_commit_sha: str,
    gate_passed: bool,
    allowed_scopes: tuple[str, ...],
) -> tuple[bool, tuple[str, ...]]:
    """Validate approval against the current execution context."""

    failures: list[str] = []

    if not approval.approved:
        failures.append("approval is not active")

    if not gate_passed:
        failures.append("quality gate did not pass")

    if approval.commit_sha != expected_commit_sha:
        failures.append("approval commit does not match current commit")

    if approval.scope not in allowed_scopes:
        failures.append("approval scope is not authorized")

    if approval.gate_result != "PASS":
        failures.append("approval does not reference a passing gate")

    return not failures, tuple(failures)
