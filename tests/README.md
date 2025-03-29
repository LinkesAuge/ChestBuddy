# ChestBuddy Testing Framework

This directory contains all the tests for the ChestBuddy application.

## Directory Structure

- **tests/**
  - **unit/**: Unit tests for individual components
  - **integration/**: Tests for interactions between components
  - **ui/**: Tests for UI components and interactions
  - **e2e/**: End-to-end workflow tests
  - **data/**: Test data factories and datasets
  - **utils/**: Testing utilities and helpers
  - **resources/**: Test resources and assets
  - **conftest.py**: Common test fixtures
  - **README.md**: This file

## Running Tests

You can run tests using `pytest` directly or using the Makefile:

```bash
# Run all tests
make test-all

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run only UI tests
make test-ui

# Run only end-to-end tests
make test-e2e

# Run tests with coverage
make test-coverage

# Run a specific test file
make test-file file=tests/unit/test_example.py
```

## Current Test Status

- **Unit Tests**: Working correctly
- **UI Tests**: Working correctly
- **Integration Tests**: Experiencing recursion issues with signal handling (Work in progress)
- **End-to-End Tests**: Experiencing issues with test execution (Work in progress)

## Testing Categories

### Unit Tests
- Test individual components in isolation
- Fast execution
- Use mocks for dependencies
- Located in the `tests/unit/` directory

### Integration Tests
- Test interactions between components
- Medium execution speed
- Minimal mocking
- Located in the `tests/integration/` directory

### UI Tests
- Test UI components and interactions
- Use QtBot and widget tests
- Located in the `tests/ui/` directory

### End-to-End Tests
- Test complete application workflows
- Slower execution
- No mocking of core components
- Located in the `tests/e2e/` directory

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These include:

- **Sample Data**: Pre-generated test datasets
- **Temporary Files/Directories**: For file I/O tests
- **Enhanced QtBot**: Improved QtBot with additional helper methods
- **Main Window**: Common QMainWindow for UI tests

## Markers

The following pytest markers are available:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.ui`: UI tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.slow`: Tests that take a long time to run
- `@pytest.mark.model`: Tests for data models
- `@pytest.mark.service`: Tests for service components
- `@pytest.mark.controller`: Tests for controller components
- `@pytest.mark.utility`: Tests for utility functions

## Test Data

Test data is generated using the `TestDataFactory` class in the `tests/data/` directory. You can use it to create:

- Empty datasets
- Small datasets (10 rows)
- Medium datasets (100 rows)
- Large datasets (1000 rows)
- Very large datasets (10,000 rows)
- Datasets with specific errors

## Testing Utilities

The `tests/utils/` directory contains helper functions and classes for testing:

- File I/O helpers (temporary files and directories)
- Qt testing helpers (enhanced QtBot, signal spies, etc.)
- Waiting utilities (wait for conditions, signals, etc.)
- Widget finding utilities

## Known Issues and Limitations

- **Recursion Issues with Qt Signals**: Some tests may experience recursion issues when using PySide6 signals with complex data structures like pandas DataFrames.
- **Enhancement Ideas**: 
  - Use simpler data structures for integration tests
  - Add disconnect logic to properly clean up signal connections
  - Implement better handling of Qt's event loop in tests 