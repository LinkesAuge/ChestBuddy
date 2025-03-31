#!/usr/bin/env python
"""
run_controller_tests.py

Description: Script to run controller interaction tests
Usage:
    python scripts/run_controller_tests.py
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def main():
    """Run the controller interaction tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run controller interaction tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--capture", "-s", action="store_true", help="Disable output capture")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--view", "-V", action="store_true", help="Run only view interaction tests")
    parser.add_argument(
        "--controller", "-C", action="store_true", help="Run only controller interaction tests"
    )
    parser.add_argument(
        "--signal", "-S", action="store_true", help="Run only signal disconnection tests"
    )
    parser.add_argument("--all", "-a", action="store_true", help="Run all main window tests")
    args = parser.parse_args()

    # Find the project root directory (contains pyproject.toml or setup.py)
    root_dir = find_project_root()
    if not root_dir:
        print("Error: Could not find project root directory.")
        return 1

    # Change to the root directory
    os.chdir(root_dir)

    # Build the command
    cmd = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add output capture
    if args.capture:
        cmd.append("-s")

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=chestbuddy", "--cov-report=term", "--cov-report=html"])

    # Determine which tests to run
    if args.all:
        cmd.append("tests/ui/")
    elif args.view:
        cmd.append("tests/ui/test_main_window_view_interaction.py")
    elif args.controller:
        cmd.append("tests/ui/test_main_window_controller_interaction.py")
    elif args.signal:
        cmd.append("tests/ui/test_signal_disconnection.py")
    else:
        # Default to run all specific tests
        cmd.extend(
            [
                "tests/ui/test_main_window_view_interaction.py",
                "tests/ui/test_main_window_controller_interaction.py",
                "tests/ui/test_signal_disconnection.py",
            ]
        )

    # Print the command
    print(f"Running: {' '.join(cmd)}")

    # Run the tests
    result = subprocess.run(cmd)

    return result.returncode


def find_project_root():
    """
    Find the project root directory by looking for pyproject.toml or setup.py.

    Returns:
        Path: Path to the project root directory or None if not found
    """
    current_dir = Path.cwd()

    # Walk up the directory tree looking for project root markers
    while current_dir != current_dir.parent:
        if (current_dir / "pyproject.toml").exists() or (current_dir / "setup.py").exists():
            return current_dir
        current_dir = current_dir.parent

    return None


if __name__ == "__main__":
    sys.exit(main())
