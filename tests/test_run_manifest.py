import json
from pathlib import Path

from harness.run_manifest import build_run_manifest, write_run_manifest


def test_build_run_manifest(tmp_path: Path) -> None:
    manifest = build_run_manifest(tmp_path)

    assert "timestamp" in manifest
    assert "commit_sha" in manifest
    assert "branch" in manifest
    assert "python_version" in manifest
    assert "platform" in manifest
    assert "harness_version" in manifest
    assert "tools" in manifest

    tools = manifest["tools"]

    assert isinstance(tools, dict)
    assert "ruff" in tools
    assert "mypy" in tools
    assert "pytest" in tools
    assert "bandit" in tools


def test_write_run_manifest(tmp_path: Path) -> None:
    path = tmp_path / "artifacts" / "run.json"

    write_run_manifest(tmp_path, path)

    assert path.exists()

    data = json.loads(path.read_text(encoding="utf-8"))

    assert "timestamp" in data
    assert "commit_sha" in data
    assert "tools" in data
