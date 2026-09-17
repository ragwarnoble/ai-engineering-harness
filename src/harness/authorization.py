from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from harness.approval import ApprovalRecord, load_approval
from harness.target import ExecutionTarget, load_execution_target


@dataclass(frozen=True)
class AuthorizationResult:
    authorized: bool
    scope: str
    commit_sha: str
    failures: tuple[str, ...]


def authorize(
    root: Path,
    *,
    scope: str,
    allowed_scopes: tuple[str, ...],
) -> AuthorizationResult:
    failures: list[str] = []

    gate_path = root / "artifacts" / "gate.json"
    run_path = root / "artifacts" / "run.json"
    target_path = root / "artifacts" / "target.json"
    approval_path = root / "artifacts" / "approval.json"

    if not gate_path.exists():
        failures.append("gate evidence does not exist")
    if not run_path.exists():
        failures.append("run provenance does not exist")
    if not target_path.exists():
        failures.append("execution target does not exist")
    if not approval_path.exists():
        failures.append("approval evidence does not exist")

    if failures:
        return AuthorizationResult(
            authorized=False,
            scope=scope,
            commit_sha="unknown",
            failures=tuple(failures),
        )

    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    run_data = json.loads(run_path.read_text(encoding="utf-8"))
    target: ExecutionTarget = load_execution_target(target_path)
    approval: ApprovalRecord = load_approval(approval_path)

    if not gate_data.get("passed", False):
        failures.append("quality gate did not pass")

    if run_data.get("commit_sha") != target.commit_sha:
        failures.append("run provenance does not match execution target")

    if target.gate_result != "PASS":
        failures.append("execution target does not reference a passing gate")

    if approval.commit_sha != target.commit_sha:
        failures.append("approval does not match execution target")

    if approval.scope != scope:
        failures.append("approval scope does not match requested scope")

    if scope not in allowed_scopes:
        failures.append("requested scope is not authorized")

    if not approval.approved:
        failures.append("approval is not active")

    if approval.gate_result != "PASS":
        failures.append("approval does not reference a passing gate")

    return AuthorizationResult(
        authorized=not failures,
        scope=scope,
        commit_sha=target.commit_sha,
        failures=tuple(failures),
    )
