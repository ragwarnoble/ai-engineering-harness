from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.approval import ApprovalRecord, load_approval


@dataclass(frozen=True)
class AuthorizationResult:
    authorized: bool
    scope: str
    commit_sha: str
    failures: tuple[str, ...]


def current_commit(root: Path) -> str:
    """Return the current Git commit SHA."""

    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )

    return completed.stdout.strip()


def authorize(
    root: Path,
    *,
    scope: str,
    allowed_scopes: tuple[str, ...],
) -> AuthorizationResult:
    """Validate whether an agent action is authorized."""

    failures: list[str] = []
    commit_sha = current_commit(root)

    gate_path = root / "artifacts" / "gate.json"
    run_path = root / "artifacts" / "run.json"
    approval_path = root / "artifacts" / "approval.json"

    if not gate_path.exists():
        failures.append("gate evidence does not exist")

    if not run_path.exists():
        failures.append("run provenance does not exist")

    if not approval_path.exists():
        failures.append("approval evidence does not exist")

    if failures:
        return AuthorizationResult(
            authorized=False,
            scope=scope,
            commit_sha=commit_sha,
            failures=tuple(failures),
        )

    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    run_data = json.loads(run_path.read_text(encoding="utf-8"))
    approval: ApprovalRecord = load_approval(approval_path)

    if not gate_data.get("passed", False):
        failures.append("quality gate did not pass")

    if run_data.get("commit_sha") != commit_sha:
        failures.append("run provenance does not match current commit")

    if approval.commit_sha != commit_sha:
        failures.append("approval does not match current commit")

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
        commit_sha=commit_sha,
        failures=tuple(failures),
    )
