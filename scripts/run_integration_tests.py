#!/usr/bin/env python
"""
Run ChestBuddy integration tests.

This script runs integration tests in the project, providing a convenient
way to verify the integration between different components of the application.

Usage:
    python run_integration_tests.py             # Run all integration tests
    python run_integration_tests.py --all       # Run all integration tests
    python run_integration_tests.py --validation # Run only validation integration tests
    python run_integration_tests.py --core       # Run only core component integration tests
    python run_integration_tests.py --files test_file1.py test_file2.py  # Run specific test files
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run ChestBuddy integration tests.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all integration tests")
    group.add_argument(
        "--validation", action="store_true", help="Run only validation service integration tests"
    )
    group.add_argument(
        "--core", action="store_true", help="Run only core component integration tests"
    )
    group.add_argument("--files", nargs="+", help="Run specific test files (provide file names)")

    return parser.parse_args()


def main():
    """Run integration tests based on command line arguments."""
    args = parse_args()

    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Ensure we're running from the project root
    os.chdir(project_root)

    # Determine which tests to run
    if args.validation:
        test_path = "tests/integration/test_validation_service_config_integration.py"
        desc = "ValidationService integration tests"
    elif args.core:
        test_path = "tests/integration/test_simple_integration.py"
        desc = "core component integration tests"
    elif args.files:
        test_path = [f"tests/integration/{file}" for file in args.files]
        desc = f"specific integration test files: {', '.join(args.files)}"
    else:  # default or --all
        test_path = "tests/integration/"
        desc = "all ChestBuddy integration tests"

    # Build the pytest command
    pytest_cmd = [
        "pytest",
    ]

    # Add test paths to command
    if isinstance(test_path, str):
        pytest_cmd.append(test_path)
    else:
        pytest_cmd.extend(test_path)

    # Add pytest options
    pytest_cmd.extend(
        [
            "-v",  # Verbose output
            "--no-header",  # Skip pytest header
            "--tb=native",  # Use native traceback formatting
        ]
    )

    print(f"Running {desc}...")
    print(f"Command: {' '.join(pytest_cmd)}")
    print("-" * 80)

    # Run the tests
    result = subprocess.run(pytest_cmd)

    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
