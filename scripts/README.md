# ChestBuddy Scripts

This directory contains utility scripts for development, testing, and maintenance of the ChestBuddy application.

## Available Scripts

### `update_mainwindow_tests.py`

A utility script to help analyze and update MainWindow tests to support the new view-based architecture.

#### Usage

```bash
# Analyze a test file without making changes
python scripts/update_mainwindow_tests.py --analyze tests/ui/test_mainwindow.py

# Analyze all test files in a directory
python scripts/update_mainwindow_tests.py --analyze tests/ui/

# Update a test file with necessary changes
python scripts/update_mainwindow_tests.py --update tests/ui/test_mainwindow.py

# Update all test files in a directory
python scripts/update_mainwindow_tests.py --update tests/ui/
```

#### Features

- Detects and analyzes test methods that need updates for the new view-based architecture
- Identifies test methods that use tab references which need to be updated
- Identifies controller methods that need to be used in tests
- Automatically adds necessary fixtures for controllers
- Updates main_window fixture to include controller dependencies
- Marks tests as skipped with a reason if they need major updates
- Fixes common issues like method name inconsistencies and menu text changes
- Adds required imports
- Creates backups of original files before making changes

#### Report Example

```
Found 42 test methods:

File Operations (Total: 8):
  - test_open_file (line 158) - Issues: Uses 'open_files' instead of 'open_file'
  - test_save_file (line 172)
  - test_export_csv (line 185)
  - ...

Menu Actions (Total: 12):
  - test_open_action (line 201) - Issues: Menu text may need update: '&Open' to '&Open...'
  - test_save_action (line 215)
  - ...

View Navigation (Total: 6):
  - test_switch_to_tab (line 230) - Issues: Uses tab references instead of views
  - ...

Needed Controllers:
  - file_operations_controller
  - view_state_controller
```

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