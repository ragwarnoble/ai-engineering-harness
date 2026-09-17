import json
import subprocess
from pathlib import Path

from harness.approval import create_approval, write_approval
from harness.executor import execute
from harness.target import create_execution_target, write_execution_target


def init_repo(tmp_path: Path) -> tuple[Path, str]:
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

    commit_sha = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    return root, commit_sha


def prepare_authorized_repo(root: Path, commit_sha: str) -> None:
    artifacts = root / "artifacts"
    artifacts.mkdir()

    (artifacts / "gate.json").write_text(
        json.dumps({"passed": True}),
        encoding="utf-8",
    )

    (artifacts / "run.json").write_text(
        json.dumps({"commit_sha": commit_sha}),
        encoding="utf-8",
    )

    target = create_execution_target(
        root,
        gate_result="PASS",
    )
    write_execution_target(
        target,
        artifacts / "target.json",
    )

    approval = create_approval(
        approver="human",
        scope="production_changes",
        reason="Approved.",
        commit_sha=commit_sha,
        gate_result="PASS",
    )
    write_approval(approval, artifacts / "approval.json")


def test_execute_read_only(tmp_path: Path) -> None:
    root, _ = init_repo(tmp_path)

    result = execute(
        root,
        scope="read_only",
        action="inspect",
    )

    assert result.executed is True
    assert result.failures == ()


def test_execute_rejects_disallowed_action(tmp_path: Path) -> None:
    root, _ = init_repo(tmp_path)

    result = execute(
        root,
        scope="development_changes",
        action="deploy",
    )

    assert result.executed is False
    assert "is not allowed" in result.failures[0]


def test_execute_requires_authorization(tmp_path: Path) -> None:
    root, _ = init_repo(tmp_path)

    result = execute(
        root,
        scope="production_changes",
        action="commit",
    )

    assert result.executed is False
    assert "gate evidence does not exist" in result.failures


def test_execute_authorized_production_action(tmp_path: Path) -> None:
    root, commit_sha = init_repo(tmp_path)
    prepare_authorized_repo(root, commit_sha)

    result = execute(
        root,
        scope="production_changes",
        action="commit",
    )

    assert result.executed is True
    assert result.failures == ()
