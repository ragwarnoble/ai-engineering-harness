import json
import subprocess
from pathlib import Path

from harness.approval import create_approval, write_approval
from harness.authorization import authorize


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()

    subprocess.run(
        ("git", "init", "-q"),
        cwd=root,
        check=True,
    )

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

    subprocess.run(
        ("git", "add", "README.md"),
        cwd=root,
        check=True,
    )

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


def prepare_evidence(root: Path, commit_sha: str) -> None:
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

    approval = create_approval(
        approver="human",
        scope="production_changes",
        reason="Approved.",
        commit_sha=commit_sha,
        gate_result="PASS",
    )

    write_approval(approval, artifacts / "approval.json")


def test_authorize_valid_request(tmp_path: Path) -> None:
    root, commit_sha = init_repo(tmp_path)
    prepare_evidence(root, commit_sha)

    result = authorize(
        root,
        scope="production_changes",
        allowed_scopes=("production_changes",),
    )

    assert result.authorized is True
    assert result.failures == ()


def test_rejects_scope_mismatch(tmp_path: Path) -> None:
    root, commit_sha = init_repo(tmp_path)
    prepare_evidence(root, commit_sha)

    result = authorize(
        root,
        scope="deployment_changes",
        allowed_scopes=("deployment_changes",),
    )

    assert result.authorized is False
    assert "approval scope does not match requested scope" in result.failures


def test_rejects_unauthorized_scope(tmp_path: Path) -> None:
    root, commit_sha = init_repo(tmp_path)
    prepare_evidence(root, commit_sha)

    result = authorize(
        root,
        scope="unknown_changes",
        allowed_scopes=("production_changes",),
    )

    assert result.authorized is False
    assert "approval scope does not match requested scope" in result.failures
    assert "requested scope is not authorized" in result.failures


def test_rejects_failed_gate(tmp_path: Path) -> None:
    root, commit_sha = init_repo(tmp_path)
    prepare_evidence(root, commit_sha)

    gate_path = root / "artifacts" / "gate.json"
    gate_path.write_text(
        json.dumps({"passed": False}),
        encoding="utf-8",
    )

    result = authorize(
        root,
        scope="production_changes",
        allowed_scopes=("production_changes",),
    )

    assert result.authorized is False
    assert "quality gate did not pass" in result.failures
