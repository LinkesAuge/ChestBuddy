#!/usr/bin/env python
"""
Run all ChestBuddy tests.

This script runs all tests in the project, including unit tests and integration tests.
It provides options to run specific test categories and generate coverage reports.

Usage:
    python run_all_tests.py             # Run all tests
    python run_all_tests.py --unit      # Run only unit tests
    python run_all_tests.py --integration # Run only integration tests
    python run_all_tests.py --coverage  # Generate a coverage report
    python run_all_tests.py --module chestbuddy/utils  # Run tests for a specific module
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run ChestBuddy tests.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all tests")
    group.add_argument("--unit", action="store_true", help="Run only unit tests")
    group.add_argument("--integration", action="store_true", help="Run only integration tests")
    group.add_argument("--module", help="Run tests for a specific module or path")

    parser.add_argument("--coverage", action="store_true", help="Generate a coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Show minimal output")
    parser.add_argument("--xml", action="store_true", help="Generate XML report for CI")

    return parser.parse_args()


def main():
    """Run tests based on command line arguments."""
    args = parse_args()

    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Ensure we're running from the project root
    os.chdir(project_root)

    # Base pytest command
    pytest_cmd = ["pytest"]

    # Determine which tests to run
    if args.unit:
        test_path = "tests/unit/"
        desc = "unit tests"
    elif args.integration:
        test_path = "tests/integration/"
        desc = "integration tests"
    elif args.module:
        # If a module is specified, run tests for that module
        # This will match test paths based on the module path
        module_path = args.module
        test_path = f"tests/"
        pytest_cmd.extend(["-k", f"{module_path.replace('/', '.')}"])
        desc = f"tests for module {module_path}"
    else:  # --all or default
        test_path = "tests/"
        desc = "all tests"

    # Add the test path
    pytest_cmd.append(test_path)

    # Add options based on command line arguments
    if args.verbose:
        pytest_cmd.append("-v")
    if args.quiet:
        pytest_cmd.append("-q")

    # Add coverage if requested
    if args.coverage:
        # Use pytest-cov plugin for coverage reporting
        pytest_cmd.extend(
            ["--cov=chestbuddy", "--cov-report=term", "--cov-report=html:reports/coverage"]
        )
        desc = f"{desc} with coverage"

    # Add XML reporting if requested (useful for CI)
    if args.xml:
        pytest_cmd.extend(
            [
                "--junitxml=reports/test-results.xml",
            ]
        )

    print(f"Running {desc}...")
    print(f"Command: {' '.join(pytest_cmd)}")
    print("-" * 80)

    # Create reports directory if it doesn't exist
    if args.coverage or args.xml:
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

    # Run the tests
    result = subprocess.run(pytest_cmd)

    # Print summary if coverage was generated
    if args.coverage and result.returncode == 0:
        print()
        print("Coverage report generated:")
        print(f"  HTML report: {project_root}/reports/coverage/index.html")
        print()

    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
