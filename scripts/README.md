# ChestBuddy Scripts

This directory contains utility scripts for testing, maintenance, and operation of the ChestBuddy application.

## Testing Scripts

### All Tests

* **run_all_tests.py** - Comprehensive script to run all tests with coverage options

  ```bash
  # Run all tests
  python scripts/run_all_tests.py
  
  # Run only unit tests
  python scripts/run_all_tests.py --unit
  
  # Run only integration tests
  python scripts/run_all_tests.py --integration
  
  # Generate a coverage report
  python scripts/run_all_tests.py --coverage
  
  # Run tests for a specific module
  python scripts/run_all_tests.py --module chestbuddy/utils
  
  # Generate XML report for CI integration
  python scripts/run_all_tests.py --xml
  ```

### Integration Tests

* **run_integration_tests.py** - Versatile script to run integration tests

  ```bash
  # Run all integration tests
  python scripts/run_integration_tests.py
  
  # Run only validation service integration tests
  python scripts/run_integration_tests.py --validation
  
  # Run only core component integration tests
  python scripts/run_integration_tests.py --core
  
  # Run specific test files
  python scripts/run_integration_tests.py --files test_file1.py test_file2.py
  ```

* **run_validation_integration_tests.py** - Script to run validation service integration tests

  ```bash
  python scripts/run_validation_integration_tests.py
  ```

## Running Scripts

All scripts in this directory are designed to be run from the project root directory. They include shebang lines for Unix-like systems to make them executable.

On Windows:
```
python scripts/script_name.py [arguments]
```

On Unix-like systems (after making them executable):
```
chmod +x scripts/script_name.py
./scripts/script_name.py [arguments]
```

## Adding New Scripts

When adding new scripts to this directory, please:

1. Include appropriate shebang lines (`#!/usr/bin/env python`)
2. Add docstrings explaining the script's purpose
3. Implement proper command-line argument handling if needed
4. Update this README.md with information about the new script 