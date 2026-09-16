from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.manifest import PlatformManifest
from harness.policy import PolicyEngine, PolicyResult


@dataclass(frozen=True)
class GateCheckResult:
    name: str
    passed: bool
    returncode: int
    output: str


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    policy: PolicyResult
    checks: tuple[GateCheckResult, ...]
    unsupported_checks: tuple[str, ...] = ()


CHECK_COMMANDS: dict[str, tuple[str, ...]] = {
    "format": ("ruff", "format", "--check", "."),
    "lint": ("ruff", "check", "."),
    "typecheck": ("mypy", "src"),
    "tests": ("pytest",),
    "security": ("bandit", "-r", "src", "-ll"),
}


def run_gate_check(
    name: str,
    command: tuple[str, ...],
    root: Path,
) -> GateCheckResult:
    """Execute one deterministic quality-gate check."""

    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    output = completed.stdout
    if completed.stderr:
        output += completed.stderr

    return GateCheckResult(
        name=name,
        passed=completed.returncode == 0,
        returncode=completed.returncode,
        output=output,
    )


def run_quality_gate(
    manifest: PlatformManifest,
    root: Path,
    commands: dict[str, tuple[str, ...]] | None = None,
) -> QualityGateResult:
    """Evaluate platform policy and execute the required quality checks."""

    policy_result = PolicyEngine().evaluate(manifest)

    if not policy_result.passed:
        return QualityGateResult(
            passed=False,
            policy=policy_result,
            checks=(),
            unsupported_checks=(),
        )

    check_commands = commands or CHECK_COMMANDS

    if commands is None and manifest.quality_gates.coverage:
        check_commands = dict(check_commands)

        check_commands["coverage"] = (
            "pytest",
            "--cov",
            "--cov-report=term-missing",
            f"--cov-fail-under={manifest.quality_gates.coverage_threshold}",
        )

    checks: list[GateCheckResult] = []
    unsupported_checks: list[str] = []

    for check_name in policy_result.required_checks:
        command = check_commands.get(check_name)

        if command is None:
            unsupported_checks.append(check_name)
            continue

        result = run_gate_check(
            name=check_name,
            command=command,
            root=root,
        )

        checks.append(result)

        if not result.passed:
            break

    passed = (
        policy_result.passed and not unsupported_checks and all(check.passed for check in checks)
    )

    return QualityGateResult(
        passed=passed,
        policy=policy_result,
        checks=tuple(checks),
        unsupported_checks=tuple(unsupported_checks),
    )
