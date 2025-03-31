#!/usr/bin/env python
"""
update_tests.py

A utility script to help update and run tests for the ChestBuddy application.
This script helps to identify and update tests from tab-based architecture to view-based architecture.
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
import re

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def find_tests(pattern=None):
    """
    Find test files matching the provided pattern.

    Args:
        pattern (str): Optional regex pattern to filter test files

    Returns:
        list: List of test file paths matching the pattern
    """
    test_dir = project_root / "tests"
    all_tests = list(test_dir.glob("test_*.py"))

    if pattern:
        compiled_pattern = re.compile(pattern)
        return [test for test in all_tests if compiled_pattern.search(test.name)]

    return all_tests


def run_single_test(test_path, verbose=False):
    """
    Run a single test file.

    Args:
        test_path (Path): Path to the test file
        verbose (bool): Whether to show verbose output

    Returns:
        int: Return code from pytest
    """
    cmd = ["pytest", str(test_path)]
    if verbose:
        cmd.append("-v")

    print(f"Running test: {test_path.name}")
    result = subprocess.run(cmd, capture_output=not verbose)

    if result.returncode != 0 and not verbose:
        print("Test failed. Error output:")
        print(result.stderr.decode())

    return result.returncode


def find_tab_based_patterns(test_path):
    """
    Scan a test file for patterns indicating tab-based UI testing.

    Args:
        test_path (Path): Path to the test file

    Returns:
        list: List of line numbers and patterns found
    """
    tab_patterns = [
        r"_tab_widget",
        r"currentIndex\(\)",
        r"setCurrentIndex",
        r"tabBar\(\)",
        r"addTab",
        r"QTabWidget",
    ]

    findings = []
    with open(test_path, "r") as f:
        for i, line in enumerate(f.readlines(), 1):
            for pattern in tab_patterns:
                if re.search(pattern, line):
                    findings.append((i, line.strip(), pattern))

    return findings


def analyze_test_file(test_path):
    """
    Analyze a test file for tab-based patterns and suggest updates.

    Args:
        test_path (Path): Path to the test file

    Returns:
        tuple: (findings, suggested_updates)
    """
    findings = find_tab_based_patterns(test_path)

    suggested_updates = {
        r"_tab_widget": "Use view_state_controller.set_active_view() instead of _tab_widget",
        r"currentIndex\(\)": "Check active view name instead of tab index",
        r"setCurrentIndex": "Use _on_navigation_changed() to switch views",
        r"tabBar\(\)": "Access UI elements through view controllers",
        r"addTab": "Views are now created in controllers, not directly in MainWindow",
        r"QTabWidget": "TabWidget is replaced with view-based architecture",
    }

    return findings, suggested_updates


def create_backup(test_path):
    """
    Create a backup of a test file.

    Args:
        test_path (Path): Path to the test file

    Returns:
        Path: Path to the backup file
    """
    backup_path = test_path.with_suffix(".py.bak")
    with open(test_path, "r") as src:
        with open(backup_path, "w") as dst:
            dst.write(src.read())
    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Update and run ChestBuddy tests")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Find command
    find_parser = subparsers.add_parser("find", help="Find tests matching a pattern")
    find_parser.add_argument("pattern", nargs="?", help="Regex pattern to match test files")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run tests")
    run_parser.add_argument("pattern", nargs="?", help="Regex pattern to match test files")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze tests for tab-based patterns")
    analyze_parser.add_argument("pattern", nargs="?", help="Regex pattern to match test files")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backups of test files")
    backup_parser.add_argument("pattern", nargs="?", help="Regex pattern to match test files")

    args = parser.parse_args()

    if args.command == "find":
        tests = find_tests(args.pattern)
        print(f"Found {len(tests)} test files:")
        for test in tests:
            print(f"  {test.relative_to(project_root)}")

    elif args.command == "run":
        tests = find_tests(args.pattern)
        print(f"Running {len(tests)} test files...")

        failures = 0
        for test in tests:
            ret_code = run_single_test(test, args.verbose)
            if ret_code != 0:
                failures += 1

        if failures > 0:
            print(f"{failures} test files failed")
            sys.exit(1)
        else:
            print("All tests passed")

    elif args.command == "analyze":
        tests = find_tests(args.pattern)
        print(f"Analyzing {len(tests)} test files for tab-based patterns...")

        for test in tests:
            findings, suggested_updates = analyze_test_file(test)

            if findings:
                print(f"\n{test.relative_to(project_root)}:")
                for line_num, line, pattern in findings:
                    print(f"  Line {line_num}: {line}")
                    print(f"    Suggestion: {suggested_updates.get(pattern, 'Update needed')}")
            else:
                print(f"\n{test.relative_to(project_root)}: No tab-based patterns found")

    elif args.command == "backup":
        tests = find_tests(args.pattern)
        print(f"Creating backups for {len(tests)} test files...")

        for test in tests:
            backup_path = create_backup(test)
            print(f"  Created backup: {backup_path.relative_to(project_root)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
