#!/usr/bin/env python
"""
Run ValidationService integration tests.

This script runs the integration tests for the ValidationService and ConfigManager integration.
It provides a convenient way to run just these tests with verbose output.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run ValidationService integration tests."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Ensure we're running from the project root
    os.chdir(project_root)

    # Build the pytest command
    pytest_cmd = [
        "pytest",
        "tests/integration/test_validation_service_config_integration.py",
        "-v",  # Verbose output
        "--no-header",  # Skip pytest header
        "--tb=native",  # Use native traceback formatting
    ]

    print(f"Running ValidationService integration tests...")
    print(f"Command: {' '.join(pytest_cmd)}")
    print("-" * 80)

    # Run the tests
    result = subprocess.run(pytest_cmd)

    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
