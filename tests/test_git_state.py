from __future__ import annotations

import subprocess
from pathlib import Path

from harness.git_state import get_git_state


def init_repo(path: Path) -> None:
    subprocess.run(("git", "init", "-q"), cwd=path, check=True)

    (path / "README.md").write_text(
        "initial\n",
        encoding="utf-8",
    )

    subprocess.run(("git", "add", "README.md"), cwd=path, check=True)

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
        cwd=path,
        check=True,
    )


def test_clean_repository(tmp_path: Path) -> None:
    init_repo(tmp_path)

    state = get_git_state(tmp_path)

    assert state.clean is True
    assert state.commit_sha
    assert state.tree_sha
    assert state.branch


def test_dirty_repository(tmp_path: Path) -> None:
    init_repo(tmp_path)

    (tmp_path / "README.md").write_text(
        "modified\n",
        encoding="utf-8",
    )

    state = get_git_state(tmp_path)

    assert state.clean is False
