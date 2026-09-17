import json
import subprocess
from pathlib import Path

from harness.executor import ExecutionResult
from harness.provenance import (
    build_execution_provenance,
    write_execution_provenance,
)


def init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()

    subprocess.run(("git", "init", "-q"), cwd=root, check=True)
    subprocess.run(
        ("git", "config", "user.email", "test@example.com"),
        cwd=root,
        check=True,
    )
    subprocess.run(
        ("git", "config", "user.name", "Test User"),
        cwd=root,
        check=True,
    )

    (root / "README.md").write_text("test\n", encoding="utf-8")

    subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
    subprocess.run(
        ("git", "commit", "-q", "-m", "test"),
        cwd=root,
        check=True,
    )

    return root


def test_build_execution_provenance_for_executed_result(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)

    result = ExecutionResult(
        executed=True,
        scope="read_only",
        action="inspect",
        failures=(),
    )

    provenance = build_execution_provenance(root, result)

    assert provenance.operation_id
    assert provenance.scope == "read_only"
    assert provenance.action == "inspect"
    assert provenance.result == "EXECUTED"
    assert provenance.commit_sha
    assert provenance.tree_sha
    assert provenance.gate_result == "UNKNOWN"
    assert provenance.approval_scope is None
    assert provenance.approver is None
    assert provenance.failures == ()


def test_build_execution_provenance_for_denied_result(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)

    result = ExecutionResult(
        executed=False,
        scope="production_changes",
        action="deploy",
        failures=("action 'deploy' is not allowed for scope 'production_changes'",),
    )

    provenance = build_execution_provenance(root, result)

    assert provenance.result == "DENIED"
    assert provenance.failures == result.failures


def test_write_execution_provenance(tmp_path: Path) -> None:
    root = init_repo(tmp_path)

    result = ExecutionResult(
        executed=False,
        scope="development_changes",
        action="deploy",
        failures=("action is not allowed",),
    )

    provenance = build_execution_provenance(root, result)
    path = root / "artifacts" / "execution.json"

    write_execution_provenance(provenance, path)

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["operation_id"] == provenance.operation_id
    assert data["result"] == "DENIED"
    assert data["scope"] == "development_changes"
    assert data["action"] == "deploy"
    assert data["failures"] == ["action is not allowed"]


def test_provenance_uses_target_and_approval(tmp_path: Path) -> None:
    root = init_repo(tmp_path)

    artifacts = root / "artifacts"
    artifacts.mkdir()

    commit_sha = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    tree_sha = subprocess.run(
        ("git", "rev-parse", "HEAD^{tree}"),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    (artifacts / "target.json").write_text(
        json.dumps(
            {
                "commit_sha": commit_sha,
                "tree_sha": tree_sha,
                "branch": "main",
                "created_at": "2026-01-01T00:00:00+00:00",
                "gate_result": "PASS",
            }
        ),
        encoding="utf-8",
    )

    (artifacts / "approval.json").write_text(
        json.dumps(
            {
                "approved": True,
                "approver": "human",
                "scope": "deployment_changes",
                "reason": "Approved deployment.",
                "commit_sha": commit_sha,
                "gate_result": "PASS",
                "timestamp": "2026-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    result = ExecutionResult(
        executed=True,
        scope="deployment_changes",
        action="deploy",
        failures=(),
    )

    provenance = build_execution_provenance(root, result)

    assert provenance.gate_result == "PASS"
    assert provenance.approval_scope == "deployment_changes"
    assert provenance.approver == "human"
