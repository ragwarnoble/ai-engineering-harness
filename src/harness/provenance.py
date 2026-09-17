from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from harness.approval import load_approval
from harness.executor import ExecutionResult
from harness.git_state import get_git_state
from harness.target import load_execution_target


@dataclass(frozen=True)
class ExecutionProvenance:
    """Immutable audit record for an execution attempt."""

    operation_id: str
    timestamp: str
    scope: str
    action: str
    result: str
    commit_sha: str
    tree_sha: str
    gate_result: str
    approval_scope: str | None
    approver: str | None
    failures: tuple[str, ...] = ()


def build_execution_provenance(
    root: Path,
    result: ExecutionResult,
) -> ExecutionProvenance:
    """Build provenance for an execution attempt."""

    state = get_git_state(root)

    gate_result = "UNKNOWN"
    approval_scope: str | None = None
    approver: str | None = None

    target_path = root / "artifacts" / "target.json"
    approval_path = root / "artifacts" / "approval.json"

    if target_path.exists():
        target = load_execution_target(target_path)
        gate_result = target.gate_result

    if approval_path.exists():
        approval = load_approval(approval_path)
        approval_scope = approval.scope
        approver = approval.approver

    return ExecutionProvenance(
        operation_id=str(uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        scope=result.scope,
        action=result.action,
        result="EXECUTED" if result.executed else "DENIED",
        commit_sha=state.commit_sha,
        tree_sha=state.tree_sha,
        gate_result=gate_result,
        approval_scope=approval_scope,
        approver=approver,
        failures=result.failures,
    )


def write_execution_provenance(
    provenance: ExecutionProvenance,
    path: Path,
) -> None:
    """Persist execution provenance as deterministic JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            asdict(provenance),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
