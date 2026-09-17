from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from harness.git_state import get_git_state


@dataclass(frozen=True)
class ExecutionTarget:
    commit_sha: str
    tree_sha: str
    branch: str
    created_at: str
    gate_result: str


def create_execution_target(
    root: Path,
    *,
    gate_result: str,
) -> ExecutionTarget:
    if gate_result != "PASS":
        raise ValueError("execution target requires a passing quality gate")

    state = get_git_state(root)

    if not state.clean:
        raise ValueError("execution target requires a clean working tree")

    return ExecutionTarget(
        commit_sha=state.commit_sha,
        tree_sha=state.tree_sha,
        branch=state.branch,
        created_at=datetime.now(UTC).isoformat(),
        gate_result=gate_result,
    )


def write_execution_target(
    target: ExecutionTarget,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            {
                "commit_sha": target.commit_sha,
                "tree_sha": target.tree_sha,
                "branch": target.branch,
                "created_at": target.created_at,
                "gate_result": target.gate_result,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def load_execution_target(path: Path) -> ExecutionTarget:
    data = json.loads(path.read_text(encoding="utf-8"))

    return ExecutionTarget(
        commit_sha=str(data["commit_sha"]),
        tree_sha=str(data["tree_sha"]),
        branch=str(data["branch"]),
        created_at=str(data["created_at"]),
        gate_result=str(data["gate_result"]),
    )
