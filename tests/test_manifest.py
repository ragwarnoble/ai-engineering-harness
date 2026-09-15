from pathlib import Path

import pytest

from harness.manifest import load_manifest


def _valid_manifest() -> str:
    return """
version: "1.0"
project:
  name: test
  role: platform
  description: test
application:
  supported_profiles:
    - personal
pillars:
  ai_engineering: true
  data_engineering: true
  software_engineering: true
  governance: true
agents:
  provider_neutral: true
  human_approval_required: true
quality_gates:
  format: true
  lint: true
  typecheck: true
  tests: true
  coverage: true
  coverage_threshold: 85
  security: true
  evaluation: true
data:
  validation_required: true
  quality_checks_required: true
  lineage_required: false
  observability_required: true
ai:
  evaluation_required: true
  regression_testing_required: true
  rag_evaluation_supported: true
human_in_the_loop:
  enabled: true
  required_for:
    - production_changes
"""


def test_load_platform_manifest() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    assert manifest.version == "1.0"
    assert manifest.project.name == "ai-engineering-platform"
    assert manifest.project.role == "platform"
    assert manifest.application.supported_profiles == (
        "personal",
        "business",
        "enterprise",
    )
    assert manifest.pillars.ai_engineering is True
    assert manifest.pillars.data_engineering is True
    assert manifest.quality_gates.evaluation is True
    assert manifest.ai.rag_evaluation_supported is True
    assert manifest.human_in_the_loop.enabled is True


def test_reject_unsupported_application_profile(tmp_path: Path) -> None:
    manifest_path = tmp_path / "platform.yaml"
    manifest_path.write_text(
        _valid_manifest().replace(
            "    - personal\n",
            "    - personal\n    - unsupported\n",
            1,
        )
    )

    with pytest.raises(ValueError, match="Unsupported application profiles"):
        load_manifest(manifest_path)


def test_reject_missing_boolean(tmp_path: Path) -> None:
    manifest_path = tmp_path / "platform.yaml"
    manifest_path.write_text(
        _valid_manifest().replace(
            "  ai_engineering: true\n",
            "",
            1,
        )
    )

    with pytest.raises(ValueError, match="pillars.ai_engineering"):
        load_manifest(manifest_path)


def test_manifest_loads_coverage_threshold() -> None:
    manifest = load_manifest(Path("platform.yaml"))

    assert manifest.quality_gates.coverage_threshold == 85


def test_manifest_rejects_invalid_coverage_threshold(
    tmp_path: Path,
) -> None:
    path = tmp_path / "platform.yaml"
    path.write_text(
        Path("platform.yaml")
        .read_text()
        .replace("coverage_threshold: 85", "coverage_threshold: 101")
    )

    with pytest.raises(ValueError, match="coverage_threshold"):
        load_manifest(path)
