from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_PROFILES = frozenset({"personal", "business", "enterprise"})


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    role: str
    description: str


@dataclass(frozen=True)
class ApplicationConfig:
    supported_profiles: tuple[str, ...]


@dataclass(frozen=True)
class PillarConfig:
    ai_engineering: bool
    data_engineering: bool
    software_engineering: bool
    governance: bool


@dataclass(frozen=True)
class AgentConfig:
    provider_neutral: bool
    human_approval_required: bool


@dataclass(frozen=True)
class QualityGateConfig:
    format: bool
    lint: bool
    typecheck: bool
    tests: bool
    coverage: bool
    security: bool
    evaluation: bool


@dataclass(frozen=True)
class DataConfig:
    validation_required: bool
    quality_checks_required: bool
    lineage_required: bool
    observability_required: bool


@dataclass(frozen=True)
class AIConfig:
    evaluation_required: bool
    regression_testing_required: bool
    rag_evaluation_supported: bool


@dataclass(frozen=True)
class HumanInTheLoopConfig:
    enabled: bool
    required_for: tuple[str, ...]


@dataclass(frozen=True)
class PlatformManifest:
    version: str
    project: ProjectConfig
    application: ApplicationConfig
    pillars: PillarConfig
    agents: AgentConfig
    quality_gates: QualityGateConfig
    data: DataConfig
    ai: AIConfig
    human_in_the_loop: HumanInTheLoopConfig


def _require_mapping(data: Any, name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a mapping")
    return data


def _require_string(data: dict[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}.{key} must be a non-empty string")
    return value


def _require_bool(data: dict[str, Any], key: str, path: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{path}.{key} must be a boolean")
    return value


def _require_bool_fields(
    data: dict[str, Any],
    fields: tuple[str, ...],
    path: str,
) -> dict[str, bool]:
    return {field: _require_bool(data, field, path) for field in fields}


def load_manifest(path: Path) -> PlatformManifest:
    raw = yaml.safe_load(path.read_text())

    root = _require_mapping(raw, "manifest")

    version = _require_string(root, "version", "manifest")

    project = _require_mapping(root.get("project"), "project")
    application = _require_mapping(root.get("application"), "application")
    pillars = _require_mapping(root.get("pillars"), "pillars")
    agents = _require_mapping(root.get("agents"), "agents")
    quality_gates = _require_mapping(root.get("quality_gates"), "quality_gates")
    data = _require_mapping(root.get("data"), "data")
    ai = _require_mapping(root.get("ai"), "ai")
    hitl = _require_mapping(
        root.get("human_in_the_loop"),
        "human_in_the_loop",
    )

    profiles = application.get("supported_profiles")
    if not isinstance(profiles, list) or not all(isinstance(profile, str) for profile in profiles):
        raise ValueError("application.supported_profiles must be a list of strings")

    unsupported = set(profiles) - SUPPORTED_PROFILES
    if unsupported:
        raise ValueError("Unsupported application profiles: " + ", ".join(sorted(unsupported)))

    required_for = hitl.get("required_for")
    if not isinstance(required_for, list) or not all(
        isinstance(item, str) for item in required_for
    ):
        raise ValueError("human_in_the_loop.required_for must be a list of strings")

    project_config = ProjectConfig(
        name=_require_string(project, "name", "project"),
        role=_require_string(project, "role", "project"),
        description=_require_string(project, "description", "project"),
    )

    pillar_values = _require_bool_fields(
        pillars,
        (
            "ai_engineering",
            "data_engineering",
            "software_engineering",
            "governance",
        ),
        "pillars",
    )

    agent_values = _require_bool_fields(
        agents,
        ("provider_neutral", "human_approval_required"),
        "agents",
    )

    quality_values = _require_bool_fields(
        quality_gates,
        (
            "format",
            "lint",
            "typecheck",
            "tests",
            "coverage",
            "security",
            "evaluation",
        ),
        "quality_gates",
    )

    data_values = _require_bool_fields(
        data,
        (
            "validation_required",
            "quality_checks_required",
            "lineage_required",
            "observability_required",
        ),
        "data",
    )

    ai_values = _require_bool_fields(
        ai,
        (
            "evaluation_required",
            "regression_testing_required",
            "rag_evaluation_supported",
        ),
        "ai",
    )

    return PlatformManifest(
        version=version,
        project=project_config,
        application=ApplicationConfig(tuple(profiles)),
        pillars=PillarConfig(**pillar_values),
        agents=AgentConfig(**agent_values),
        quality_gates=QualityGateConfig(**quality_values),
        data=DataConfig(**data_values),
        ai=AIConfig(**ai_values),
        human_in_the_loop=HumanInTheLoopConfig(
            enabled=_require_bool(hitl, "enabled", "human_in_the_loop"),
            required_for=tuple(required_for),
        ),
    )
