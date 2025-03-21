#!/usr/bin/env python
"""
Run all tests for the ChestBuddy application and generate a coverage report.

This script runs pytest with coverage reporting for the chestbuddy package.
It will output a text summary of the coverage report to the console and
generate an HTML report in the 'htmlcov' directory.

Usage:
    python scripts/run_tests.py [--html] [--xml] [--verbose]

Options:
    --html      Generate HTML coverage report
    --xml       Generate XML coverage report
    --verbose   Show verbose test output
"""

import os
import sys
import subprocess
from pathlib import Path


def run_tests(html=False, xml=False, verbose=False):
    """Run all tests with coverage."""
    # Ensure we're running from the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Build the command
    cmd = [sys.executable, "-m", "pytest", "tests/", "--cov=chestbuddy", "--cov-report=term"]

    # Add HTML report if requested
    if html:
        cmd.append("--cov-report=html")

    # Add XML report if requested
    if xml:
        cmd.append("--cov-report=xml")

    # Add verbosity if requested
    if verbose:
        cmd.append("-v")

    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    """Parse command line arguments and run tests."""
    # Simple command line parsing
    html = "--html" in sys.argv
    xml = "--xml" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Run the tests
    result = run_tests(html, xml, verbose)

    # Print summary
    if result.returncode == 0:
        print("\nTests passed successfully!")
        if html:
            print("HTML coverage report generated in the 'htmlcov' directory.")
        if xml:
            print("XML coverage report generated as 'coverage.xml'.")
    else:
        print("\nTests failed with exit code:", result.returncode)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
