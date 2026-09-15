import json
from pathlib import Path

import pytest

from harness.cli import (
    CheckResult,
    RepositoryInspection,
    inspect_repository,
    main,
    print_check_results,
    print_inspection,
    run_check,
    run_checks,
)


def test_inspect_repository_detects_harness_files(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").touch()
    (tmp_path / "README.md").touch()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "Makefile").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    result = inspect_repository(tmp_path)

    assert result == RepositoryInspection(
        root=str(tmp_path),
        has_agents=True,
        has_readme=True,
        has_pyproject=True,
        has_makefile=True,
        has_tests=True,
        has_ci=True,
    )


def test_inspect_repository_detects_missing_controls(tmp_path: Path) -> None:
    result = inspect_repository(tmp_path)

    assert result.has_agents is False
    assert result.has_readme is False
    assert result.has_pyproject is False
    assert result.has_makefile is False
    assert result.has_tests is False
    assert result.has_ci is False


def test_run_check_success(tmp_path: Path) -> None:
    result = run_check(
        "success",
        ("python", "-c", "print('ok')"),
        tmp_path,
    )

    assert result == CheckResult(
        name="success",
        passed=True,
        returncode=0,
        output="ok\n",
    )


def test_run_check_failure(tmp_path: Path) -> None:
    result = run_check(
        "failure",
        ("python", "-c", "import sys; print('bad'); sys.exit(2)"),
        tmp_path,
    )

    assert result.name == "failure"
    assert result.passed is False
    assert result.returncode == 2
    assert "bad" in result.output


def test_run_checks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run_check(
        name: str,
        command: tuple[str, ...],
        root: Path,
    ) -> CheckResult:
        calls.append((name, command))
        return CheckResult(name, True, 0, "")

    monkeypatch.setattr("harness.cli.run_check", fake_run_check)

    results = run_checks(tmp_path)

    assert len(results) == 4
    assert [result.name for result in results] == [
        "format",
        "lint",
        "typecheck",
        "tests",
    ]
    assert len(calls) == 4


def test_print_inspection(capsys: pytest.CaptureFixture[str]) -> None:
    result = RepositoryInspection(
        root="/repo",
        has_agents=True,
        has_readme=False,
        has_pyproject=True,
        has_makefile=True,
        has_tests=True,
        has_ci=False,
    )

    print_inspection(result)

    output = capsys.readouterr().out

    assert "Repository: /repo" in output
    assert "✓ AGENTS.md" in output
    assert "✗ README.md" in output
    assert "✓ tests/" in output
    assert "✗ .github/workflows/" in output


def test_print_check_results(capsys: pytest.CaptureFixture[str]) -> None:
    results = [
        CheckResult("format", True, 0, ""),
        CheckResult("lint", False, 1, "lint failed"),
    ]

    print_check_results(results)

    output = capsys.readouterr().out

    assert "✓ format" in output
    assert "✗ lint" in output
    assert "lint failed" in output
    assert "Result: FAIL" in output


def test_main_inspect_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "inspect"])

    main()

    output = capsys.readouterr().out

    assert "AI Engineering Platform" in output
    assert "Engineering controls:" in output
    assert "AGENTS.md" in output


def test_main_inspect_json_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "inspect", "--json"])

    main()

    output = capsys.readouterr().out
    data = json.loads(output)

    assert data["root"] == str(Path.cwd())
    assert data["has_agents"] is True
    assert data["has_pyproject"] is True
    assert data["has_tests"] is True


def test_main_without_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness"])

    main()

    output = capsys.readouterr().out

    assert "usage:" in output
