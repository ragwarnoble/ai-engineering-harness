from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.approval import create_approval, write_approval
from harness.authorization import authorize
from harness.executor import execute
from harness.gate import QualityGateResult, run_quality_gate
from harness.gate_evidence import write_gate_evidence
from harness.manifest import PlatformManifest, load_manifest
from harness.policy import PolicyEngine, PolicyResult
from harness.provenance import (
    build_execution_provenance,
    write_execution_provenance,
)
from harness.run_manifest import write_run_manifest
from harness.target import create_execution_target, load_execution_target, write_execution_target


@dataclass(frozen=True)
class RepositoryInspection:
    root: str
    has_agents: bool
    has_readme: bool
    has_pyproject: bool
    has_makefile: bool
    has_tests: bool
    has_ci: bool


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    returncode: int
    output: str


CHECK_COMMANDS: dict[str, tuple[str, ...]] = {
    "format": ("ruff", "format", "--check", "."),
    "lint": ("ruff", "check", "."),
    "typecheck": ("mypy", "src"),
    "tests": ("pytest",),
}


def inspect_repository(root: Path) -> RepositoryInspection:
    return RepositoryInspection(
        root=str(root),
        has_agents=(root / "AGENTS.md").exists(),
        has_readme=(root / "README.md").exists(),
        has_pyproject=(root / "pyproject.toml").exists(),
        has_makefile=(root / "Makefile").exists(),
        has_tests=(root / "tests").exists(),
        has_ci=(root / ".github" / "workflows").exists(),
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


def run_checks(root: Path) -> tuple[CheckResult, ...]:
    return tuple(run_check(name, command, root) for name, command in CHECK_COMMANDS.items())


def print_inspection(result: RepositoryInspection) -> None:
    print("Repository:", result.root)
    print()
    print("Engineering controls:")
    print(f"  {'✓' if result.has_agents else '✗'} AGENTS.md")
    print(f"  {'✓' if result.has_readme else '✗'} README.md")
    print(f"  {'✓' if result.has_pyproject else '✗'} pyproject.toml")
    print(f"  {'✓' if result.has_makefile else '✗'} Makefile")
    print(f"  {'✓' if result.has_tests else '✗'} tests/")
    print(f"  {'✓' if result.has_ci else '✗'} .github/workflows/")


def print_check_results(results: tuple[CheckResult, ...]) -> None:
    passed = all(result.passed for result in results)

    print("Checks:")

    for result in results:
        print(f"  {'✓' if result.passed else '✗'} {result.name}")

        if result.output and not result.passed:
            print(result.output.rstrip())

    print()
    print(f"Result: {'PASS' if passed else 'FAIL'}")


def print_manifest(manifest: PlatformManifest) -> None:
    print("Platform manifest:")
    print(f"  Project: {manifest.project.name}")
    print(f"  Role: {manifest.project.role}")
    print("  Profiles: " + ", ".join(manifest.application.supported_profiles))
    print(f"  AI engineering: {manifest.pillars.ai_engineering}")
    print(f"  Data engineering: {manifest.pillars.data_engineering}")
    print(f"  Software engineering: {manifest.pillars.software_engineering}")
    print(f"  Governance: {manifest.pillars.governance}")


def print_policy(result: PolicyResult) -> None:
    print("Policy evaluation:")
    print(f"  Result: {'PASS' if result.passed else 'FAIL'}")

    if result.required_checks:
        print()
        print("Required checks:")
        for check in result.required_checks:
            print(f"  - {check}")

    if result.required_evaluations:
        print()
        print("Required evaluations:")
        for evaluation in result.required_evaluations:
            print(f"  - {evaluation}")

    if result.human_approval_required:
        print()
        print("Human approval required:")
        for scope in result.human_approval_required:
            print(f"  - {scope}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"  - {failure}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="AI Engineering Platform",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=False,
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect repository structure and engineering controls.",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON.",
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
        help="Output JSON.",
    )

    policy_parser = subparsers.add_parser(
        "policy",
        help="Evaluate platform policy.",
    )
    policy_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON.",
    )

    gate_parser = subparsers.add_parser(
        "gate",
        help="Evaluate policy and execute the platform quality gate.",
    )
    gate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON.",
    )
    gate_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Persist quality gate and run evidence.",
    )

    approve_parser = subparsers.add_parser(
        "approve",
        help="Record explicit human approval.",
    )
    approve_parser.add_argument(
        "--approver",
        required=True,
        help="Human approver identity.",
    )
    approve_parser.add_argument(
        "--scope",
        required=True,
        help="Authorized change scope.",
    )
    approve_parser.add_argument(
        "--reason",
        required=True,
        help="Reason for approval.",
    )

    authorize_parser = subparsers.add_parser(
        "authorize",
        help="Validate authorization for an execution scope.",
    )
    authorize_parser.add_argument(
        "--scope",
        required=True,
        help="Requested execution scope.",
    )

    execute_parser = subparsers.add_parser(
        "execute",
        help="Validate authorization for an approved action.",
    )
    execute_parser.add_argument(
        "--scope",
        required=True,
        help="Execution scope.",
    )
    execute_parser.add_argument(
        "--action",
        required=True,
        help="Requested action.",
    )

    return parser


def repository_root() -> Path:
    return Path.cwd()


def print_gate_result(result: QualityGateResult) -> None:
    print("AI Engineering Platform")
    print("======================")
    print()
    print("Quality gate:")
    print(f"  Result: {'PASS' if result.passed else 'FAIL'}")

    print()
    print("Policy:")
    print(f"  Result: {'PASS' if result.policy.passed else 'FAIL'}")

    if result.checks:
        print()
        print("Checks:")
        for check in result.checks:
            print(f"  {'✓' if check.passed else '✗'} {check.name}")

    if result.evaluations:
        print()
        print("Evaluations:")
        for evaluation in result.evaluations:
            symbol = {
                "PASS": "✓",
                "FAIL": "✗",
                "NOT_CONFIGURED": "⚠",
            }[evaluation.status]
            print(f"  {symbol} {evaluation.name}  {evaluation.status}")

    if result.unsupported_checks:
        print()
        print("Unsupported checks:")
        for check_name in result.unsupported_checks:
            print(f"  ✗ {check_name}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    root = repository_root()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "inspect":
        result = inspect_repository(root)

        if args.json:
            print(
                json.dumps(
                    {
                        "root": result.root,
                        "has_agents": result.has_agents,
                        "has_readme": result.has_readme,
                        "has_pyproject": result.has_pyproject,
                        "has_makefile": result.has_makefile,
                        "has_tests": result.has_tests,
                        "has_ci": result.has_ci,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return

        print("AI Engineering Platform")
        print("======================")
        print()
        print_inspection(result)
        return

    if args.command == "check":
        results = run_checks(root)
        print_check_results(results)

        if not all(result.passed for result in results):
            raise SystemExit(1)

        return

    if args.command == "manifest":
        manifest = load_manifest(root / "platform.yaml")

        if args.json:
            payload = {
                "version": manifest.version,
                "project": {
                    "name": manifest.project.name,
                    "role": manifest.project.role,
                    "description": manifest.project.description,
                },
                "application": {
                    "supported_profiles": (manifest.application.supported_profiles),
                },
                "pillars": {
                    "ai_engineering": manifest.pillars.ai_engineering,
                    "data_engineering": manifest.pillars.data_engineering,
                    "software_engineering": (manifest.pillars.software_engineering),
                    "governance": manifest.pillars.governance,
                },
                "agents": {
                    "provider_neutral": (manifest.agents.provider_neutral),
                    "human_approval_required": (manifest.agents.human_approval_required),
                },
                "quality_gates": {
                    "format": manifest.quality_gates.format,
                    "lint": manifest.quality_gates.lint,
                    "typecheck": manifest.quality_gates.typecheck,
                    "tests": manifest.quality_gates.tests,
                    "coverage": manifest.quality_gates.coverage,
                    "coverage_threshold": (manifest.quality_gates.coverage_threshold),
                    "security": manifest.quality_gates.security,
                    "evaluation": manifest.quality_gates.evaluation,
                },
                "data": {
                    "validation_required": (manifest.data.validation_required),
                    "quality_checks_required": (manifest.data.quality_checks_required),
                    "lineage_required": (manifest.data.lineage_required),
                    "observability_required": (manifest.data.observability_required),
                },
                "ai": {
                    "evaluation_required": (manifest.ai.evaluation_required),
                    "regression_testing_required": (manifest.ai.regression_testing_required),
                    "rag_evaluation_supported": (manifest.ai.rag_evaluation_supported),
                },
                "human_approval_required": (manifest.agents.human_approval_required),
                "human_in_the_loop": {
                    "enabled": manifest.human_in_the_loop.enabled,
                    "required_for": (manifest.human_in_the_loop.required_for),
                },
            }

            print(json.dumps(payload, indent=2, sort_keys=True))
            return

        print_manifest(manifest)
        return

    if args.command == "policy":
        manifest = load_manifest(root / "platform.yaml")
        policy_result = PolicyEngine().evaluate(manifest)

        if args.json:
            print(
                json.dumps(
                    {
                        "passed": policy_result.passed,
                        "required_checks": (policy_result.required_checks),
                        "required_evaluations": (policy_result.required_evaluations),
                        "human_approval_required": (policy_result.human_approval_required),
                        "failures": policy_result.failures,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print_policy(policy_result)

        if not policy_result.passed:
            raise SystemExit(1)

        return

    if args.command == "gate":
        manifest = load_manifest(root / "platform.yaml")

        gate_result = run_quality_gate(
            manifest,
            root,
        )

        print_gate_result(gate_result)

        if args.json:
            payload = {
                "passed": gate_result.passed,
                "policy": {
                    "passed": gate_result.policy.passed,
                    "required_checks": (gate_result.policy.required_checks),
                    "required_evaluations": (gate_result.policy.required_evaluations),
                    "human_approval_required": (gate_result.policy.human_approval_required),
                    "failures": gate_result.policy.failures,
                },
                "checks": [
                    {
                        "name": check.name,
                        "passed": check.passed,
                        "returncode": check.returncode,
                        "output": check.output,
                    }
                    for check in gate_result.checks
                ],
                "evaluations": [
                    {
                        "name": evaluation.name,
                        "status": evaluation.status,
                        "passed": evaluation.passed,
                    }
                    for evaluation in gate_result.evaluations
                ],
                "unsupported_checks": gate_result.unsupported_checks,
            }

            print()
            print(json.dumps(payload, indent=2, sort_keys=True))

        if args.evidence:
            gate_path = root / "artifacts" / "gate.json"
            run_path = root / "artifacts" / "run.json"

            write_gate_evidence(
                gate_result,
                gate_path,
            )
            write_run_manifest(
                root,
                run_path,
            )

            target_path = root / "artifacts" / "target.json"

            if gate_result.passed:
                target = create_execution_target(
                    root,
                    gate_result="PASS",
                )
                write_execution_target(
                    target,
                    target_path,
                )

            print()
            print(f"Gate evidence: {gate_path}")
            print(f"Run evidence: {run_path}")

            if gate_result.passed:
                print(f"Execution target: {target_path}")

        if not gate_result.passed:
            raise SystemExit(1)

        return

    if args.command == "approve":
        gate_path = root / "artifacts" / "gate.json"
        approval_path = root / "artifacts" / "approval.json"

        if not gate_path.exists():
            print("Approval rejected: gate evidence does not exist.")
            raise SystemExit(1)

        gate_data = json.loads(gate_path.read_text(encoding="utf-8"))

        if not gate_data.get("passed", False):
            print("Approval rejected: quality gate did not pass.")
            raise SystemExit(1)

        target_path = root / "artifacts" / "target.json"

        if not target_path.exists():
            print("Approval rejected: execution target does not exist.")
            raise SystemExit(1)

        target = load_execution_target(target_path)

        if target.gate_result != "PASS":
            print("Approval rejected: execution target is not valid.")
            raise SystemExit(1)

        approval = create_approval(
            approver=args.approver,
            scope=args.scope,
            reason=args.reason,
            commit_sha=target.commit_sha,
            gate_result="PASS",
        )

        write_approval(
            approval,
            approval_path,
        )

        print("AI Engineering Platform")
        print("======================")
        print()
        print("Human approval:")
        print("  Result: APPROVED")
        print(f"  Approver: {approval.approver}")
        print(f"  Scope: {approval.scope}")
        print(f"  Commit: {approval.commit_sha}")
        print(f"  Gate: {approval.gate_result}")
        print(f"  Approval evidence: {approval_path}")
        return

    if args.command == "authorize":
        authorization_result = authorize(
            root,
            scope=args.scope,
            allowed_scopes=(
                "production_changes",
                "security_changes",
                "data_schema_changes",
                "deployment_changes",
            ),
        )

        print("AI Engineering Platform")
        print("======================")
        print()
        print("Authorization:")
        print(f"  Result: {'AUTHORIZED' if authorization_result.authorized else 'DENIED'}")
        print(f"  Scope: {authorization_result.scope}")
        print(f"  Commit: {authorization_result.commit_sha}")

        if authorization_result.failures:
            print()
            print("Failures:")
            for failure in authorization_result.failures:
                print(f"  ✗ {failure}")

        if not authorization_result.authorized:
            raise SystemExit(1)

        return

    if args.command == "execute":
        execution_result = execute(
            root,
            scope=args.scope,
            action=args.action,
        )

        provenance = build_execution_provenance(
            root,
            execution_result,
        )

        write_execution_provenance(
            provenance,
            root / "artifacts" / "execution.json",
        )

        print("AI Engineering Platform")
        print("======================")
        print()
        print("Execution:")
        print(f"  Result: {'EXECUTED' if execution_result.executed else 'DENIED'}")
        print(f"  Scope: {execution_result.scope}")
        print(f"  Action: {execution_result.action}")
        print(f"  Operation ID: {provenance.operation_id}")

        if execution_result.failures:
            print()
            print("Failures:")
            for failure in execution_result.failures:
                print(f"  ✗ {failure}")

        if not execution_result.executed:
            raise SystemExit(1)

        return


if __name__ == "__main__":
    main()
