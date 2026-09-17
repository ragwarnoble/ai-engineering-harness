import subprocess
from pathlib import Path

import pytest

from harness.target import (
    create_execution_target,
    load_execution_target,
    write_execution_target,
)


def init_repo(tmp_path: Path) -> tuple[Path, str, str]:
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

    tree_sha = subprocess.run(
        ("git", "rev-parse", "HEAD^{tree}"),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    return root, commit_sha, tree_sha


def test_create_execution_target(tmp_path: Path) -> None:
    root, commit_sha, tree_sha = init_repo(tmp_path)

    target = create_execution_target(root, gate_result="PASS")

    assert target.commit_sha == commit_sha
    assert target.tree_sha == tree_sha
    assert target.branch
    assert target.gate_result == "PASS"
    assert target.created_at


def test_rejects_failed_gate(tmp_path: Path) -> None:
    root, _, _ = init_repo(tmp_path)

    with pytest.raises(ValueError, match="passing quality gate"):
        create_execution_target(root, gate_result="FAIL")


def test_write_and_load_target(tmp_path: Path) -> None:
    root, _, _ = init_repo(tmp_path)

    target = create_execution_target(root, gate_result="PASS")
    path = tmp_path / "artifacts" / "target.json"

    write_execution_target(target, path)

    loaded = load_execution_target(path)

    assert loaded == target


def test_rejects_dirty_working_tree(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(("git", "init", "-q"), cwd=tmp_path, check=True)

    (tmp_path / "README.md").write_text(
        "initial\n",
        encoding="utf-8",
    )

    subprocess.run(("git", "add", "README.md"), cwd=tmp_path, check=True)
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-q",
            "-m",
            "initial",
        ),
        cwd=tmp_path,
        check=True,
    )

    (tmp_path / "README.md").write_text(
        "modified\n",
        encoding="utf-8",
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="clean working tree",
    ):
        create_execution_target(
            tmp_path,
            gate_result="PASS",
        )
