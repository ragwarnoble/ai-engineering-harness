from pathlib import Path

import pytest

from harness.cli import inspect_repository, main


def test_inspect_repository_detects_harness_files(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").touch()
    (tmp_path / "README.md").touch()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "Makefile").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    result = inspect_repository(tmp_path)

    assert result["has_agents"] is True
    assert result["has_readme"] is True
    assert result["has_pyproject"] is True
    assert result["has_makefile"] is True
    assert result["has_tests"] is True
    assert result["has_ci"] is True


def test_inspect_repository_detects_missing_controls(tmp_path: Path) -> None:
    result = inspect_repository(tmp_path)

    assert result["has_agents"] is False
    assert result["has_readme"] is False
    assert result["has_pyproject"] is False
    assert result["has_makefile"] is False
    assert result["has_tests"] is False
    assert result["has_ci"] is False


def test_main_inspect_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "inspect"])

    main()

    output = capsys.readouterr().out

    assert "AI Engineering Harness" in output
    assert "Engineering controls:" in output
    assert "AGENTS.md" in output


def test_main_without_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness"])

    main()

    output = capsys.readouterr().out

    assert "usage:" in output
