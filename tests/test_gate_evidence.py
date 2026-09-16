from pathlib import Path

from harness.gate import GateCheckResult, QualityGateResult
from harness.gate_evidence import write_gate_evidence
from harness.policy import PolicyResult


def make_result() -> QualityGateResult:
    policy = PolicyResult(
        passed=True,
        required_checks=("format", "lint"),
        required_evaluations=("engineering_evaluation",),
        human_approval_required=("production_changes",),
        failures=(),
    )

    checks = (
        GateCheckResult(
            name="format",
            passed=True,
            returncode=0,
            output="21 files already formatted\n",
        ),
        GateCheckResult(
            name="lint",
            passed=True,
            returncode=0,
            output="All checks passed!\n",
        ),
    )

    return QualityGateResult(
        passed=True,
        policy=policy,
        checks=checks,
        unsupported_checks=(),
    )


def test_write_gate_evidence(tmp_path: Path) -> None:
    path = tmp_path / "artifacts" / "gate.json"

    write_gate_evidence(make_result(), path)

    assert path.exists()

    content = path.read_text(encoding="utf-8")

    assert '"passed": true' in content
    assert '"name": "format"' in content
    assert '"name": "lint"' in content
    assert '"production_changes"' in content


def test_write_gate_evidence_creates_parent_directory(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "artifacts" / "gate.json"

    write_gate_evidence(make_result(), path)

    assert path.exists()
