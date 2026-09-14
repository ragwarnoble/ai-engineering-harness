from __future__ import annotations

import argparse
from pathlib import Path


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

    args = parser.parse_args()

    if args.command == "inspect":
        root = Path.cwd()
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
