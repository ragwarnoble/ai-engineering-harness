from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    returncode: int
    output: str


CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("format", ("ruff", "format", "--check", ".")),
    ("lint", ("ruff", "check", ".")),
    ("typecheck", ("mypy", "src")),
    ("tests", ("pytest", "--cov", "--cov-report=term-missing")),
)


def inspect_repository(root: Path) -> dict[str, object]:
    return {
        "root": str(root),
        "has_agents": (root / "AGENTS.md").exists(),
        "has_readme": (root / "README.md").exists(),
        "has_pyproject": (root / "pyproject.toml").exists(),
        "has_makefile": (root / "Makefile").exists(),
        "has_tests": (root / "tests").is_dir(),
        "has_ci": (root / ".github" / "workflows").is_dir(),
    }


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


def print_check_results(results: list[CheckResult]) -> None:
    print("AI Engineering Harness")
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
        description="AI Engineering Harness",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "inspect",
        help="Inspect repository structure and engineering controls.",
    )

    subparsers.add_parser(
        "check",
        help="Run deterministic engineering checks.",
    )

    args = parser.parse_args()
    root = Path.cwd()

    if args.command == "inspect":
        result = inspect_repository(root)

        print("AI Engineering Harness")
        print("======================")
        print(f"Repository: {result['root']}")
        print()
        print("Engineering controls:")

        controls = {
            "AGENTS.md": result["has_agents"],
            "README.md": result["has_readme"],
            "pyproject.toml": result["has_pyproject"],
            "Makefile": result["has_makefile"],
            "tests/": result["has_tests"],
            ".github/workflows/": result["has_ci"],
        }

        for name, exists in controls.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {name}")

    elif args.command == "check":
        results = run_checks(root)
        print_check_results(results)

        if not all(result.passed for result in results):
            raise SystemExit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
