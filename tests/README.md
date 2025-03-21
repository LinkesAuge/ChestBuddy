# ChestBuddy Tests

This directory contains tests for the ChestBuddy application. The tests are written using pytest and cover various aspects of the application, including core utilities, models, services, and UI components.

## Test Structure

The tests are organized as follows:

- `test_config_manager.py`: Tests for the ConfigManager class.
- `test_chest_data_model.py`: Tests for the ChestDataModel class.
- `test_services.py`: Tests for the service classes (CSVService, ValidationService, CorrectionService).
- `test_ui_components.py`: Tests for the UI components (DataView, ValidationTab, CorrectionTab).
- `test_app.py`: Tests for the ChestBuddyApp class.

## Default Files

The application uses several default files that are also used in testing:

### Input Data
- **Location**: `data/input/Chests_input_test.csv`
- **Format**: CSV with columns (DATE, PLAYER, SOURCE, CHEST, SCORE, CLAN)
- **Purpose**: Sample data for testing and default data for the application

### Validation Lists
- **Location**: `data/validation/`
- **Files**:
  - `chest_types.txt`: List of valid chest types, one per line
  - `players.txt`: List of valid player names, one per line
  - `sources.txt`: List of valid source/location names, one per line
- **Purpose**: Used to validate the input data

### Correction Lists
- **Location**: `data/corrections/standard_corrections.csv`
- **Format**: CSV with columns (From, To, Category, enabled)
- **Purpose**: Used to apply automatic corrections to invalid data

## Running the Tests

To run the tests, you will need to have pytest installed. You can install it using:

```bash
uv add pytest --dev
```

Then, from the project root directory, run:

```bash
python -m pytest tests/
```

To run a specific test file:

```bash
python -m pytest tests/test_config_manager.py
```

To run a specific test function:

```bash
python -m pytest tests/test_config_manager.py::test_singleton_pattern
```

## Test Coverage

To generate a test coverage report, install pytest-cov:

```bash
uv add pytest-cov --dev
```

Then run:

```bash
python -m pytest tests/ --cov=chestbuddy
```

## UI Tests

The UI component tests require a QApplication instance to be created. This is handled automatically by the fixtures in the test files. Note that these tests do not actually display any UI, they just test that the components initialize correctly and respond appropriately to method calls.

## Data Format

The tests expect data to have the following structure:

1. **ChestDataModel Expected Columns**:
   - Date: Date of the chest drop (YYYY-MM-DD format)
   - Player Name: Name of the player
   - Source/Location: Where the chest was obtained
   - Chest Type: Type of chest
   - Value: Numeric value of the chest
   - Clan: Clan name

2. **Validation Status DataFrame**:
   - Contains columns named after data columns with "_valid" suffix
   - For example: "Date_valid", "Player Name_valid", etc.
   - Boolean values indicating validity

3. **Correction Status DataFrame**:
   - Contains columns named after data columns with "_corrected" suffix
   - For example: "Date_corrected", "Player Name_corrected", etc.
   - Boolean values indicating if corrections were applied
   - Also contains "_original" columns to store original values

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create a new test file in the tests directory.
2. Use pytest fixtures for common setup code.
3. Follow the naming convention: `test_*` for test files and test functions.
4. Group related tests into classes.
5. Add docstrings to explain what each test does.
6. Clean up any temporary files or resources created during tests.
7. Use the default files for testing when possible.

## Example

Here's an example of how to add a new test:

```python
import pytest
from chestbuddy.some_module import SomeClass

@pytest.fixture
def some_object():
    """Create a SomeClass instance for testing."""
    return SomeClass()

def test_some_functionality(some_object):
    """Test that some functionality works correctly."""
    result = some_object.some_method()
    assert result == expected_value
``` 