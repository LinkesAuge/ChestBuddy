# UI Tests for ChestBuddy

This directory contains UI tests for the ChestBuddy application, focusing on the view-based architecture.

## Test Structure

The UI tests are organized into focused test files to isolate specific concerns:

- `test_main_window_view_interaction.py`: Tests for view switching, navigation, and view controller integration
- `test_main_window_controller_interaction.py`: Tests for controller interaction and signal handling
- `test_signal_disconnection.py`: Tests for proper signal connection and disconnection

## Running Tests

You can run these tests using the helper script provided:

```bash
# Run all UI tests
python scripts/run_controller_tests.py

# Run view interaction tests only
python scripts/run_controller_tests.py -V

# Run controller interaction tests only
python scripts/run_controller_tests.py -C

# Run signal disconnection tests only
python scripts/run_controller_tests.py -S

# Run all tests with coverage
python scripts/run_controller_tests.py -c

# Run with verbose output
python scripts/run_controller_tests.py -v
```

## Test Patterns

These tests demonstrate the following patterns for testing the view-based architecture:

### View Interaction
- Testing view switching via sidebar navigation
- Testing view switching via menu actions
- Testing view availability based on data state
- Testing history navigation (back/forward)

### Controller Interaction
- Testing action triggering
- Testing controller method calls
- Testing response to controller signals
- Testing controller signal connections

### Signal Management
- Tracking signal connections
- Verifying proper disconnection
- Testing controller disconnect interface
- Verifying MainWindow cleanup

## Extending Tests

When adding new tests, follow these guidelines:

1. Keep test files focused on specific concerns
2. Use the provided mock fixtures for controllers and views
3. Test both the UI interaction and the controller integration
4. Ensure signals are properly connected and disconnected
5. Check edge cases like empty data or error conditions

## Test Fixtures

Common fixtures are provided in each test file:

- `mock_data_model`: Mocked ChestDataModel
- `mock_view_state_controller`: Mocked ViewStateController
- `mock_file_operations_controller`: Mocked FileOperationsController
- `mock_data_view_controller`: Mocked DataViewController
- `mock_progress_controller`: Mocked ProgressController
- `mock_ui_state_controller`: Mocked UIStateController
- `main_window`: MainWindow instance with all controllers mocked

For signal testing, `test_signal_disconnection.py` provides:

- `signal_tracker`: For tracking signal connections and disconnections
- `mock_signal_manager`: Signal manager that uses the tracker 