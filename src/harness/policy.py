from __future__ import annotations

from dataclasses import dataclass

from harness.manifest import PlatformManifest


@dataclass(frozen=True)
class PolicyResult:
    """Deterministic policy evaluation result."""

    passed: bool
    required_checks: tuple[str, ...]
    required_evaluations: tuple[str, ...]
    human_approval_required: tuple[str, ...]
    failures: tuple[str, ...] = ()


class PolicyEngine:
    """Translate a platform manifest into enforceable requirements."""

    def evaluate(self, manifest: PlatformManifest) -> PolicyResult:
        required_checks: list[str] = []
        required_evaluations: list[str] = []
        human_approval_required: list[str] = []
        failures: list[str] = []

        gates = manifest.quality_gates

        gate_mapping = {
            "format": gates.format,
            "lint": gates.lint,
            "typecheck": gates.typecheck,
            "tests": gates.tests,
            "coverage": gates.coverage,
            "security": gates.security,
        }

        for name, enabled in gate_mapping.items():
            if enabled:
                required_checks.append(name)

        if gates.evaluation:
            required_evaluations.append("engineering_evaluation")

        if manifest.ai.evaluation_required:
            required_evaluations.append("ai_evaluation")

        if manifest.ai.regression_testing_required:
            required_evaluations.append("ai_regression")

        if manifest.data.validation_required:
            required_evaluations.append("data_validation")

        if manifest.data.quality_checks_required:
            required_evaluations.append("data_quality")

        if manifest.data.observability_required:
            required_evaluations.append("data_observability")

        if manifest.human_in_the_loop.enabled:
            human_approval_required.extend(manifest.human_in_the_loop.required_for)

        if manifest.agents.human_approval_required and not (manifest.human_in_the_loop.enabled):
            failures.append(
                "Agent policy requires human approval but human_in_the_loop is disabled"
            )

        if not manifest.pillars.ai_engineering and (
            manifest.ai.evaluation_required or manifest.ai.regression_testing_required
        ):
            failures.append(
                "AI evaluation requirements enabled while AI engineering pillar is disabled"
            )

        if not manifest.pillars.data_engineering and (
            manifest.data.validation_required
            or manifest.data.quality_checks_required
            or manifest.data.observability_required
        ):
            failures.append(
                "Data quality requirements enabled while data engineering pillar is disabled"
            )

        return PolicyResult(
            passed=not failures,
            required_checks=tuple(required_checks),
            required_evaluations=tuple(required_evaluations),
            human_approval_required=tuple(human_approval_required),
            failures=tuple(failures),
        )
