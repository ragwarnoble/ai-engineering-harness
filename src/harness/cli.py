from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from harness.gate import QualityGateResult, run_quality_gate
from harness.gate_evidence import write_gate_evidence
from harness.manifest import PlatformManifest, load_manifest
from harness.policy import PolicyEngine, PolicyResult


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    returncode: int
    output: str


@dataclass(frozen=True)
class RepositoryInspection:
    root: str
    has_agents: bool
    has_readme: bool
    has_pyproject: bool
    has_makefile: bool
    has_tests: bool
    has_ci: bool


CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("format", ("ruff", "format", "--check", ".")),
    ("lint", ("ruff", "check", ".")),
    ("typecheck", ("mypy", "src")),
    ("tests", ("pytest", "--cov", "--cov-report=term-missing")),
)


def inspect_repository(root: Path) -> RepositoryInspection:
    return RepositoryInspection(
        root=str(root),
        has_agents=(root / "AGENTS.md").exists(),
        has_readme=(root / "README.md").exists(),
        has_pyproject=(root / "pyproject.toml").exists(),
        has_makefile=(root / "Makefile").exists(),
        has_tests=(root / "tests").is_dir(),
        has_ci=(root / ".github" / "workflows").is_dir(),
    )


def run_check(
    name: str,
    command: tuple[str, ...],
    root: Path,
) -> CheckResult:
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

    return CheckResult(
        name=name,
        passed=completed.returncode == 0,
        returncode=completed.returncode,
        output=output,
    )


def run_checks(root: Path) -> list[CheckResult]:
    return [run_check(name, command, root) for name, command in CHECKS]


def print_inspection(result: RepositoryInspection) -> None:
    print("AI Engineering Platform")
    print("======================")
    print(f"Repository: {result.root}")
    print()
    print("Engineering controls:")

    controls = {
        "AGENTS.md": result.has_agents,
        "README.md": result.has_readme,
        "pyproject.toml": result.has_pyproject,
        "Makefile": result.has_makefile,
        "tests/": result.has_tests,
        ".github/workflows/": result.has_ci,
    }

    for name, exists in controls.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")


def print_manifest(result: PlatformManifest) -> None:
    print("AI Engineering Platform")
    print("======================")
    print()
    print("Platform manifest:")
    print(f"  Project: {result.project.name}")
    print(f"  Role: {result.project.role}")
    print("  Profiles: " + ", ".join(result.application.supported_profiles))
    print()
    print("Pillars:")
    print(f"  AI engineering: {result.pillars.ai_engineering}")
    print(f"  Data engineering: {result.pillars.data_engineering}")
    print(f"  Software engineering: {result.pillars.software_engineering}")
    print(f"  Governance: {result.pillars.governance}")


def print_policy(result: PolicyResult) -> None:
    print("AI Engineering Platform")
    print("======================")
    print()
    print("Policy evaluation:")
    print(f"  Result: {'PASS' if result.passed else 'FAIL'}")

    print()
    print("Required checks:")
    for check in result.required_checks:
        print(f"  - {check}")

    print()
    print("Required evaluations:")
    for evaluation in result.required_evaluations:
        print(f"  - {evaluation}")

    print()
    print("Human approval required for:")
    for requirement in result.human_approval_required:
        print(f"  - {requirement}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"  ✗ {failure}")


def print_gate(result: QualityGateResult) -> None:
    print("AI Engineering Platform")
    print("======================")
    print()
    print("Quality gate:")
    print(f"  Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Policy: {'PASS' if result.policy.passed else 'FAIL'}")

    print()
    print("Executed checks:")
    for check in result.checks:
        status = "✓" if check.passed else "✗"
        print(f"  {status} {check.name}")

    if result.unsupported_checks:
        print()
        print("Unsupported checks:")
        for unsupported_check in result.unsupported_checks:
            print(f"  - {unsupported_check}")


def print_check_results(results: list[CheckResult]) -> None:
    print("AI Engineering Platform")
    print("======================")
    print()
    print("Engineering checks:")

    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.name}")

        if not result.passed and result.output:
            print()
            print(result.output.rstrip())
            print()

    overall_passed = all(result.passed for result in results)

    print()
    print(f"Result: {'PASS' if overall_passed else 'FAIL'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="AI Engineering Platform",
    )

    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect repository structure and engineering controls.",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output inspection evidence as JSON.",
    )

    subparsers.add_parser(
        "check",
        help="Run deterministic engineering checks.",
    )

    manifest_parser = subparsers.add_parser(
        "manifest",
        help="Load and display the platform manifest.",
    )
    manifest_parser.add_argument(
        "--json",
        action="store_true",
        help="Output the manifest as JSON.",
    )

    policy_parser = subparsers.add_parser(
        "policy",
        help="Evaluate platform policy.",
    )
    policy_parser.add_argument(
        "--json",
        action="store_true",
        help="Output policy evidence as JSON.",
    )

    gate_parser = subparsers.add_parser(
        "gate",
        help="Evaluate policy and execute the platform quality gate.",
    )
    gate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output quality-gate evidence as JSON.",
    )
    gate_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Persist quality-gate evidence to artifacts/gate.json.",
    )

    args = parser.parse_args()
    root = Path.cwd()

    if args.command == "inspect":
        result = inspect_repository(root)

        if args.json:
            print(json.dumps(asdict(result), indent=2, sort_keys=True))
        else:
            print_inspection(result)

    elif args.command == "check":
        results = run_checks(root)
        print_check_results(results)

        if not all(result.passed for result in results):
            raise SystemExit(1)

    elif args.command == "manifest":
        manifest = load_manifest(root / "platform.yaml")

        if args.json:
            print(json.dumps(asdict(manifest), indent=2, sort_keys=True))
        else:
            print_manifest(manifest)

    elif args.command == "policy":
        manifest = load_manifest(root / "platform.yaml")
        policy_result = PolicyEngine().evaluate(manifest)

        if args.json:
            print(json.dumps(asdict(policy_result), indent=2, sort_keys=True))
        else:
            print_policy(policy_result)

        if not policy_result.passed:
            raise SystemExit(1)

    elif args.command == "gate":
        manifest = load_manifest(root / "platform.yaml")
        gate_result = run_quality_gate(manifest, root)

        if args.evidence:
            evidence_path = root / "artifacts" / "gate.json"
            write_gate_evidence(gate_result, evidence_path)

        if args.json:
            print(json.dumps(asdict(gate_result), indent=2, sort_keys=True))
        else:
            print_gate(gate_result)

            if args.evidence:
                print()
                print(f"Evidence: {evidence_path}")

        if not gate_result.passed:
            raise SystemExit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
