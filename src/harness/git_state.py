from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitState:
    commit_sha: str
    tree_sha: str
    branch: str
    clean: bool


def _git_value(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def get_git_state(root: Path) -> GitState:
    status = _git_value(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude)artifacts/**",
    )

    return GitState(
        commit_sha=_git_value(root, "rev-parse", "HEAD"),
        tree_sha=_git_value(root, "rev-parse", "HEAD^{tree}"),
        branch=_git_value(root, "branch", "--show-current"),
        clean=not bool(status),
    )
