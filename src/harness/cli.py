from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
