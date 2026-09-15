from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess, run

from harness.manifest import PlatformManifest
from harness.policy import PolicyEngine, PolicyResult


@dataclass(frozen=True)
class GateCheckResult:
    """Result of one quality-gate check."""

    name: str
    passed: bool
    returncode: int
    output: str = ""


@dataclass(frozen=True)
class QualityGateResult:
    """Aggregate result of the platform quality gate."""

    passed: bool
    policy: PolicyResult
    checks: tuple[GateCheckResult, ...]
    unsupported_checks: tuple[str, ...] = ()


CHECK_COMMANDS: dict[str, tuple[str, ...]] = {
    "format": ("ruff", "format", "--check", "."),
    "lint": ("ruff", "check", "."),
    "typecheck": ("mypy", "src"),
    "tests": ("pytest",),
}


def run_gate_check(
    name: str,
    command: tuple[str, ...],
    root: Path,
) -> GateCheckResult:
    """Run one deterministic quality-gate command."""

    result: CompletedProcess[str] = run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout
    if result.stderr:
        output += result.stderr

    return GateCheckResult(
        name=name,
        passed=result.returncode == 0,
        returncode=result.returncode,
        output=output,
    )


def run_quality_gate(
    manifest: PlatformManifest,
    root: Path,
    *,
    commands: dict[str, tuple[str, ...]] | None = None,
) -> QualityGateResult:
    """Evaluate policy and execute applicable engineering checks."""

    policy = PolicyEngine().evaluate(manifest)

    if not policy.passed:
        return QualityGateResult(
            passed=False,
            policy=policy,
            checks=(),
        )

    checks: list[GateCheckResult] = []
    unsupported_checks: list[str] = []
    available_commands = CHECK_COMMANDS if commands is None else commands

    for name in policy.required_checks:
        command = available_commands.get(name)

        if command is None:
            unsupported_checks.append(name)
            continue

        checks.append(run_gate_check(name, command, root))

    checks_tuple = tuple(checks)
    unsupported_tuple = tuple(unsupported_checks)

    checks_passed = all(check.passed for check in checks_tuple)
    no_unsupported_checks = not unsupported_tuple

    return QualityGateResult(
        passed=(policy.passed and checks_passed and no_unsupported_checks),
        policy=policy,
        checks=checks_tuple,
        unsupported_checks=unsupported_tuple,
    )
