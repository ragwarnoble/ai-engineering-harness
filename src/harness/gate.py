from __future__ import annotations

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from harness.manifest import PlatformManifest
from harness.policy import PolicyEngine, PolicyResult

EvaluationStatus = Literal["PASS", "FAIL", "NOT_CONFIGURED"]


@dataclass(frozen=True)
class GateCheckResult:
    name: str
    passed: bool
    returncode: int
    output: str


@dataclass(frozen=True)
class GateEvaluationResult:
    """Status of one policy-required evaluation."""

    name: str
    status: EvaluationStatus
    passed: bool


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    policy: PolicyResult
    checks: tuple[GateCheckResult, ...]
    unsupported_checks: tuple[str, ...] = ()
    evaluations: tuple[GateEvaluationResult, ...] = ()


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


def evaluate_required_evaluations(
    required: tuple[str, ...],
    results: Mapping[str, bool] | None,
) -> tuple[GateEvaluationResult, ...]:
    """Resolve required evaluation names into explicit gate statuses."""

    configured = results or {}
    evaluations: list[GateEvaluationResult] = []

    for name in required:
        if name not in configured:
            evaluations.append(
                GateEvaluationResult(
                    name=name,
                    status="NOT_CONFIGURED",
                    passed=False,
                )
            )
            continue

        passed = configured[name]

        evaluations.append(
            GateEvaluationResult(
                name=name,
                status="PASS" if passed else "FAIL",
                passed=passed,
            )
        )

    return tuple(evaluations)


def run_quality_gate(
    manifest: PlatformManifest,
    root: Path,
    commands: Mapping[str, tuple[str, ...]] | None = None,
    evaluations: Mapping[str, bool] | None = None,
) -> QualityGateResult:
    """Evaluate platform policy and execute the required quality checks."""

    policy_result = PolicyEngine().evaluate(manifest)

    if not policy_result.passed:
        return QualityGateResult(
            passed=False,
            policy=policy_result,
            checks=(),
            unsupported_checks=(),
            evaluations=(),
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

    evaluation_results = evaluate_required_evaluations(
        policy_result.required_evaluations,
        evaluations,
    )

    passed = (
        policy_result.passed and not unsupported_checks and all(check.passed for check in checks)
    )

    # Configured evaluations participate in the gate.
    # Missing evaluations remain explicitly NOT_CONFIGURED for now.
    if any(evaluation.status == "FAIL" for evaluation in evaluation_results):
        passed = False

    return QualityGateResult(
        passed=passed,
        policy=policy_result,
        checks=tuple(checks),
        unsupported_checks=tuple(unsupported_checks),
        evaluations=evaluation_results,
    )
