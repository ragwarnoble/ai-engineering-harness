from pathlib import Path

import pytest

from harness.gate import (
    GateCheckResult,
    QualityGateResult,
    run_gate_check,
    run_quality_gate,
)
from harness.manifest import load_manifest
from harness.policy import PolicyResult


def test_run_gate_check_success(tmp_path: Path) -> None:
    result = run_gate_check(
        "success",
        ("python", "-c", "print('ok')"),
        tmp_path,
    )

    assert result == GateCheckResult(
        name="success",
        passed=True,
        returncode=0,
        output="ok\n",
    )


def test_run_gate_check_failure(tmp_path: Path) -> None:
    result = run_gate_check(
        "failure",
        ("python", "-c", "import sys; print('bad'); sys.exit(2)"),
        tmp_path,
    )

    assert result.name == "failure"
    assert result.passed is False
    assert result.returncode == 2
    assert "bad" in result.output


def test_run_quality_gate_uses_manifest_policy() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    commands = {
        "format": ("python", "-c", "print('format')"),
        "lint": ("python", "-c", "print('lint')"),
        "typecheck": ("python", "-c", "print('typecheck')"),
        "tests": ("python", "-c", "print('tests')"),
    }

    result = run_quality_gate(
        manifest,
        Path.cwd(),
        commands=commands,
    )

    assert isinstance(result, QualityGateResult)
    assert result.policy.passed is True
    assert [check.name for check in result.checks] == [
        "format",
        "lint",
        "typecheck",
        "tests",
    ]
    assert all(check.passed for check in result.checks)

    # The manifest currently requires gates that do not yet have
    # executable commands in the orchestrator.
    assert result.unsupported_checks == ("coverage", "security")
    assert result.passed is False


def test_run_quality_gate_stops_on_policy_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = load_manifest(Path("platform.yaml"))

    class FailingPolicyEngine:
        def evaluate(self, manifest: object) -> PolicyResult:
            return PolicyResult(
                passed=False,
                required_checks=("format",),
                required_evaluations=(),
                human_approval_required=(),
                failures=("policy failure",),
            )

    monkeypatch.setattr(
        "harness.gate.PolicyEngine",
        FailingPolicyEngine,
    )

    result = run_quality_gate(manifest, Path.cwd())

    assert result.passed is False
    assert result.checks == ()
    assert result.unsupported_checks == ()
    assert result.policy.failures == ("policy failure",)


def test_run_quality_gate_supports_security_check() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    commands = {
        "format": ("python", "-c", "print('format')"),
        "lint": ("python", "-c", "print('lint')"),
        "typecheck": ("python", "-c", "print('typecheck')"),
        "tests": ("python", "-c", "print('tests')"),
        "coverage": ("python", "-c", "print('coverage')"),
        "security": ("python", "-c", "print('security')"),
    }

    result = run_quality_gate(
        manifest,
        Path.cwd(),
        commands=commands,
    )

    assert result.passed is True
    assert result.unsupported_checks == ()
    assert [check.name for check in result.checks] == [
        "format",
        "lint",
        "typecheck",
        "tests",
        "coverage",
        "security",
    ]
