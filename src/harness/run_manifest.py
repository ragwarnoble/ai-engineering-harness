from __future__ import annotations

import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from harness import __version__


def _command_version(command: tuple[str, ...]) -> str:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    output = completed.stdout.strip() or completed.stderr.strip()

    return output.splitlines()[0] if output else "unknown"


def _git_value(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    return completed.stdout.strip() or "unknown"


def build_run_manifest(root: Path) -> dict[str, object]:
    """Build reproducibility metadata for a harness execution."""

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "commit_sha": _git_value(root, "rev-parse", "HEAD"),
        "branch": _git_value(root, "branch", "--show-current"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "harness_version": __version__,
        "tools": {
            "ruff": _command_version(("ruff", "--version")),
            "mypy": _command_version(("mypy", "--version")),
            "pytest": _command_version(("pytest", "--version")),
            "bandit": _command_version(("bandit", "--version")),
        },
        "python_executable": sys.executable,
    }


def write_run_manifest(root: Path, path: Path) -> None:
    """Persist execution provenance as JSON."""

    import json

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            build_run_manifest(root),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
