from pathlib import Path

from harness.manifest import load_manifest
from harness.policy import PolicyEngine


def test_platform_manifest_produces_expected_policy() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    result = PolicyEngine().evaluate(manifest)

    assert result.passed is True

    assert result.required_checks == (
        "format",
        "lint",
        "typecheck",
        "tests",
        "coverage",
        "security",
    )

    assert result.required_evaluations == (
        "engineering_evaluation",
        "ai_evaluation",
        "ai_regression",
        "data_validation",
        "data_quality",
        "data_observability",
    )

    assert result.human_approval_required == (
        "production_changes",
        "security_changes",
        "data_schema_changes",
        "deployment_changes",
    )

    assert result.failures == ()


def test_policy_rejects_ai_requirements_without_ai_pillar() -> None:
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

    assert result.passed is False
    assert (
        "AI evaluation requirements enabled while AI engineering pillar is disabled"
    ) in result.failures


def test_policy_rejects_data_requirements_without_data_pillar() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    broken = manifest.__class__(
        version=manifest.version,
        project=manifest.project,
        application=manifest.application,
        pillars=manifest.pillars.__class__(
            ai_engineering=manifest.pillars.ai_engineering,
            data_engineering=False,
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

    assert result.passed is False
    assert (
        "Data quality requirements enabled while data engineering pillar is disabled"
    ) in result.failures


def test_policy_rejects_missing_human_oversight() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    broken = manifest.__class__(
        version=manifest.version,
        project=manifest.project,
        application=manifest.application,
        pillars=manifest.pillars,
        agents=manifest.agents.__class__(
            provider_neutral=manifest.agents.provider_neutral,
            human_approval_required=True,
        ),
        quality_gates=manifest.quality_gates,
        data=manifest.data,
        ai=manifest.ai,
        human_in_the_loop=manifest.human_in_the_loop.__class__(
            enabled=False,
            required_for=manifest.human_in_the_loop.required_for,
        ),
    )

    result = PolicyEngine().evaluate(broken)

    assert result.passed is False
    assert (
        "Agent policy requires human approval but human_in_the_loop is disabled"
    ) in result.failures
