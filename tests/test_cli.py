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
    print_manifest,
    print_policy,
    run_check,
    run_checks,
)
from harness.gate import QualityGateResult
from harness.manifest import load_manifest
from harness.policy import PolicyEngine, PolicyResult


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


def test_print_manifest(capsys: pytest.CaptureFixture[str]) -> None:
    result = load_manifest(Path("platform.yaml"))

    print_manifest(result)

    output = capsys.readouterr().out

    assert "Platform manifest:" in output
    assert "Project: ai-engineering-platform" in output
    assert "Role: platform" in output
    assert "Profiles: personal, business, enterprise" in output
    assert "AI engineering: True" in output
    assert "Data engineering: True" in output
    assert "Software engineering: True" in output
    assert "Governance: True" in output


def test_print_policy(capsys: pytest.CaptureFixture[str]) -> None:
    manifest = load_manifest(Path("platform.yaml"))
    result = PolicyEngine().evaluate(manifest)

    print_policy(result)

    output = capsys.readouterr().out

    assert "Policy evaluation:" in output
    assert "Result: PASS" in output
    assert "- format" in output
    assert "- lint" in output
    assert "- ai_evaluation" in output
    assert "- data_quality" in output
    assert "- production_changes" in output


def test_print_policy_with_failures(
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = load_manifest(Path("platform.yaml"))

    broken = manifest.__class__(
        version=manifest.version,
        project=manifest.project,
        application=manifest.application,
        pillars=manifest.pillars.__class__(
            ai_engineering=False,
            data_engineering=manifest.pillars.data_engineering,
            software_engineering=manifest.pillars.software_engineering,
            governance=manifest.pillars.governance,
        ),
        agents=manifest.agents,
        quality_gates=manifest.quality_gates,
        data=manifest.data,
        ai=manifest.ai,
        human_in_the_loop=manifest.human_in_the_loop,
    )

    result = PolicyEngine().evaluate(broken)

    print_policy(result)

    output = capsys.readouterr().out

    assert "Result: FAIL" in output
    assert "Failures:" in output
    assert "AI evaluation requirements enabled" in output


def test_main_manifest_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "manifest"])

    main()

    output = capsys.readouterr().out

    assert "Platform manifest:" in output
    assert "Project: ai-engineering-platform" in output


def test_main_manifest_json_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "manifest", "--json"])

    main()

    output = capsys.readouterr().out
    data = json.loads(output)

    assert data["version"] == "1.0"
    assert data["project"]["name"] == "ai-engineering-platform"
    assert data["project"]["role"] == "platform"
    assert data["application"]["supported_profiles"] == [
        "personal",
        "business",
        "enterprise",
    ]


def test_main_policy_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "policy"])

    main()

    output = capsys.readouterr().out

    assert "Policy evaluation:" in output
    assert "Result: PASS" in output
    assert "engineering_evaluation" in output


def test_main_policy_json_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["harness", "policy", "--json"])

    main()

    output = capsys.readouterr().out
    data = json.loads(output)

    assert data["passed"] is True
    assert "format" in data["required_checks"]
    assert "ai_evaluation" in data["required_evaluations"]
    assert "production_changes" in data["human_approval_required"]
    assert data["failures"] == []


def test_main_policy_failure_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingPolicy:
        def evaluate(self, manifest: object) -> PolicyResult:
            return PolicyResult(
                passed=False,
                required_checks=(),
                required_evaluations=(),
                human_approval_required=(),
                failures=("policy failure",),
            )

    monkeypatch.setattr("harness.cli.PolicyEngine", FailingPolicy)
    monkeypatch.setattr("sys.argv", ["harness", "policy"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_gate_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    policy = PolicyResult(
        passed=True,
        required_checks=("format",),
        required_evaluations=(),
        human_approval_required=(),
    )
    gate_result = QualityGateResult(
        passed=True,
        policy=policy,
        checks=(),
    )

    monkeypatch.setattr("harness.cli.repository_root", lambda: tmp_path)
    monkeypatch.setattr("harness.cli.run_quality_gate", lambda manifest, root: gate_result)
    (tmp_path / "platform.yaml").write_text(
        Path("platform.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["harness", "gate", "--json"])

    main()

    output = capsys.readouterr().out
    assert '"passed": true' in output
    assert '"format"' in output


def test_main_approve_rejects_missing_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("harness.cli.repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "harness",
            "approve",
            "--approver",
            "human",
            "--scope",
            "production_changes",
            "--reason",
            "Approved.",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "gate evidence does not exist" in capsys.readouterr().out


def test_main_approve_rejects_failed_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "gate.json").write_text(
        json.dumps({"passed": False}),
        encoding="utf-8",
    )

    monkeypatch.setattr("harness.cli.repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "harness",
            "approve",
            "--approver",
            "human",
            "--scope",
            "production_changes",
            "--reason",
            "Approved.",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "quality gate did not pass" in capsys.readouterr().out


def test_main_authorize_denied(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    from harness.authorization import AuthorizationResult

    result = AuthorizationResult(
        authorized=False,
        scope="production_changes",
        commit_sha="abc123",
        failures=("approval evidence does not exist",),
    )

    monkeypatch.setattr("harness.cli.repository_root", lambda: tmp_path)
    monkeypatch.setattr("harness.cli.authorize", lambda root, scope, allowed_scopes: result)
    monkeypatch.setattr(
        "sys.argv",
        ["harness", "authorize", "--scope", "production_changes"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "Result: DENIED" in output
    assert "approval evidence does not exist" in output


def test_main_execute_denied(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    from harness.executor import ExecutionResult

    result = ExecutionResult(
        executed=False,
        scope="production_changes",
        action="deploy",
        failures=("authorization denied",),
    )

    monkeypatch.setattr("harness.cli.repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        "harness.cli.execute",
        lambda root, scope, action: result,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "harness",
            "execute",
            "--scope",
            "production_changes",
            "--action",
            "deploy",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "Result: DENIED" in output
    assert "authorization denied" in output
