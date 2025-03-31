---
title: ChestBuddy Testing Framework
date: 2024-06-29
---

# ChestBuddy Testing Framework

## Overview

This document outlines the comprehensive testing framework implemented for the ChestBuddy application. The framework provides a structured approach to testing different components and interactions within the application, ensuring code quality and reliability.

## Test Directory Structure

The test organization follows the application structure:

```
tests/
├── conftest.py                  # Global pytest fixtures and configuration
├── data/                        # Test data and data generation utilities
│   ├── test_data_factory.py     # Factory for generating test data
│   └── ...
├── integration/                 # Integration tests
│   ├── test_workflow_a.py       # Tests for workflow A
│   ├── test_workflow_b.py       # Tests for workflow B
│   └── ...
├── unit/                        # Unit tests (matches app structure)
│   ├── core/
│   │   ├── controllers/         # Tests for controllers
│   │   │   ├── test_controller_a.py
│   │   │   └── ...
│   │   ├── models/              # Tests for models
│   │   │   ├── test_model_a.py
│   │   │   └── ...
│   │   └── services/            # Tests for services
│   │       ├── test_service_a.py
│   │       └── ...
│   └── ui/                      # Tests for UI components
│       ├── dialogs/
│       │   ├── test_dialog_a.py
│       │   └── ...
│       ├── views/
│       │   ├── test_view_a.py
│       │   └── ...
│       └── widgets/
│           ├── test_widget_a.py
│           └── ...
└── utils/                       # Test utilities and helpers
    ├── helpers.py               # Common test helper functions
    └── ...
```

## Test Types

- **Unit Tests**: Focus on testing individual components in isolation
- **Integration Tests**: Test interaction between multiple components
- **UI Tests**: Test UI components functionality and interactions
- **Functional Tests**: Test application workflows end-to-end
- **Performance Tests**: Test application performance under load

## Running Tests

To run all tests:
```bash
python -m pytest
```

To run a specific test file:
```bash
python -m pytest tests/unit/core/models/test_model_a.py
```

To run tests with code coverage:
```bash
python -m pytest --cov=chestbuddy
```

To generate a coverage report:
```bash
python -m pytest --cov=chestbuddy --cov-report=html
```

## Key Testing Tools & Frameworks

- **pytest**: Main testing framework
- **pytest-qt**: Testing Qt applications
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Code coverage reports
- **SignalSpy**: Custom utility for testing Qt signals

## Special Test Features

For UI testing, use the enhanced_qtbot fixture which provides extra capabilities:
```python
def test_some_ui_component(enhanced_qtbot):
    # enhanced_qtbot has additional methods beyond standard qtbot
    widget = SomeWidget()
    enhanced_qtbot.add_widget(widget)
    enhanced_qtbot.wait_until(lambda: widget.is_ready)
```

## Common Test Fixtures

- **enhanced_qtbot**: Extended QtBot for UI testing
- **sample_data_small**: Small dataset for most tests
- **sample_data_large**: Large dataset for performance tests
- **temp_data_dir**: Temporary directory for file I/O tests
- **mock_config_manager**: Mock ConfigManager for tests

## Test Patterns

### Service Testing
```python
def test_service_method(mock_dependency):
    # Setup
    service = ServiceUnderTest(mock_dependency)
    mock_dependency.some_method.return_value = expected_value
    
    # Exercise
    result = service.method_to_test()
    
    # Verify
    assert result == expected_value
    mock_dependency.some_method.assert_called_once_with(expected_args)
```

### UI Component Testing
```python
def test_ui_component(enhanced_qtbot):
    # Setup
    widget = WidgetUnderTest()
    enhanced_qtbot.add_widget(widget)
    
    # Exercise
    enhanced_qtbot.mouseClick(widget.button, Qt.LeftButton)
    
    # Verify
    assert widget.result_label.text() == "Expected Text"
```

### Controller Testing
```python
def test_controller_action(mock_service, mock_view):
    # Setup
    controller = ControllerUnderTest(mock_service, mock_view)
    
    # Exercise
    controller.handle_action(input_data)
    
    # Verify
    mock_service.process_data.assert_called_once_with(input_data)
    mock_view.update_display.assert_called_once_with(expected_output)
```

## Specialized Test Cases

### Testing Background Processing
```python
def test_background_task(enhanced_qtbot, mock_dependency):
    # Setup
    task = BackgroundTaskUnderTest(mock_dependency)
    spy = SignalSpy(task.finished)
    
    # Exercise
    task.start()
    
    # Verify - wait for async completion
    spy.wait()
    assert spy.count == 1
    assert spy.signal_args[0] == expected_result
```

### Testing File Operations
```python
def test_file_operation(temp_data_dir):
    # Setup
    test_file = temp_data_dir / "test.csv"
    test_file.write_text("test,data")
    
    # Exercise
    service = FileServiceUnderTest()
    result = service.process_file(test_file)
    
    # Verify
    assert result == expected_result
```

## Common Test Scenarios

### Testing Data Loading
```python
def test_data_loading(sample_data_small, enhanced_qtbot):
    # Setup
    model = DataModelUnderTest()
    
    # Exercise
    model.load_data(sample_data_small)
    
    # Verify
    assert model.row_count() == len(sample_data_small)
    assert model.data(model.index(0, 0)) == sample_data_small[0]["column1"]
```

### Testing UI Update on Data Change
```python
def test_ui_update_on_data_change(enhanced_qtbot):
    # Setup
    model = DataModelUnderTest()
    view = ViewUnderTest(model)
    enhanced_qtbot.add_widget(view)
    
    # Exercise
    model.update_data(new_data)
    
    # Verify
    assert view.display_item.text() == expected_display_text
```

## Best Practices

1. **Isolate Tests**: Each test should be independent and not rely on state from other tests
2. **Follow AAA Pattern**: Arrange, Act, Assert (Setup, Exercise, Verify)
3. **Mock Dependencies**: Use mocks to isolate the component under test
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Keep Tests Fast**: Tests should run quickly to encourage frequent running
6. **Use Meaningful Assertions**: Assert exactly what you expect, with clear failure messages
7. **Don't Test Implementation Details**: Focus on behavior, not implementation

# Qt UI Testing Best Practices

Based on our experience improving the ValidationTabView tests, here are best practices for testing Qt UI components:

## Signal Mocking

When testing Qt UI components, one common challenge is handling signals. We've developed a `MockSignal` class that avoids many of the issues with real Qt signals in test environments:

```python
class MockSignal:
    """Mock for Qt signals to avoid PySide6 Signal issues"""

    def __init__(self, *args):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def disconnect(self, callback=None):
        if callback:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
        else:
            self.callbacks = []

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)
```

Use this class when mocking services or models that emit signals:

```python
mock_service = MagicMock()
mock_service.validation_changed = MockSignal()
```

## Widget Testing Techniques

For testing widgets and UI components, use a combination of real Qt components and mocks:

1. **Basic Widget Testing**: For simple widget property testing, use mocks:

```python
def test_widget_property(validation_tab_view):
    validation_tab_view._status_bar = MagicMock()
    validation_tab_view._set_status_message("Test message")
    validation_tab_view._status_bar.showMessage.assert_called_once_with("Test message")
```

2. **Widget Styling/Rendering**: When testing styling or rendering that involves Qt's property system, use real widgets:

```python
def test_widget_styling(validation_tab_view):
    from PySide6.QtWidgets import QPushButton
    test_button = QPushButton("Test")
    with patch.object(validation_tab_view, 'findChildren', return_value=[test_button]):
        validation_tab_view._ensure_widget_styling()
        # Simply test that the method doesn't crash
        assert True
```

## Status Messages and Multiple Method Calls

When a method makes multiple calls to the same mock method (like status bar updates), use `assert_any_call` instead of `assert_called_with`:

```python
def test_method_with_multiple_status_updates(validation_tab_view):
    validation_tab_view._status_bar.showMessage.reset_mock()
    validation_tab_view._on_validate_clicked()
    validation_tab_view._status_bar.showMessage.assert_any_call("Validating data...")
```

## Preventing Method Side Effects

Sometimes a method under test calls other methods that modify state or interfere with assertions. Mock these methods:

```python
def test_method_with_side_effects(validation_tab_view):
    with patch.object(validation_tab_view, '_update_validation_stats'):
        validation_tab_view._on_validate_clicked()
        # Now we can assert on status messages without _update_validation_stats
        # overriding them
```

## Exception Testing

For methods that catch exceptions internally and don't propagate them, test that the method handles the exception gracefully:

```python
def test_method_with_internal_exception_handling(validation_tab_view):
    with patch('some.dependency', side_effect=Exception("Test error")):
        # No exception should propagate from this call
        result = validation_tab_view._some_method()
        # Verify appropriate error handling behavior
        assert result is not None
```

## Signal Spy Usage

For testing that signals are emitted correctly, use SignalSpy:

```python
def test_signal_emission(validation_tab_view):
    spy = SignalSpy(validation_tab_view.validation_changed)
    validation_tab_view._on_validate_clicked()
    assert spy.count == 1
```

## Model Testing

When testing UI components that interact with data models:

```python
def test_ui_with_model(validation_tab_view):
    # Create a test model with specific properties
    test_model = MagicMock()
    test_model.entries = [MagicMock(is_invalid=True), MagicMock(is_invalid=False)]
    
    # Assign to component
    validation_tab_view._list_view.model.return_value = test_model
    
    # Test method that uses the model
    validation_tab_view._update_validation_stats()
    
    # Verify correct behavior
    expected_message = "Validation: 50% valid, 50% invalid, 0% missing"
    validation_tab_view._status_bar.showMessage.assert_called_with(expected_message)
```

## PySide6 Version Compatibility

We found that PySide6 version 6.6.0 works better with our test setup than newer versions (6.8.3), which had import issues with QObject. If you encounter errors like:

```
ImportError: cannot import name 'QObject' from 'PySide6.QtCore'
```

Consider downgrading to 6.6.0:

```bash
uv add pyside6==6.6.0
```

## Configuration System Test Plan

## Overview

This test plan focuses on ensuring the reliability and correctness of the ChestBuddy configuration management system after recent enhancements. The test plan covers settings persistence, export/import functionality, reset behavior, error handling, and UI component synchronization.

## Test Categories

### 1. Settings Persistence

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| SP-01 | Basic settings persistence | 1. Change a setting (e.g., theme)<br>2. Close application<br>3. Restart application | Setting should retain the changed value | Manual |
| SP-02 | Boolean settings persistence | 1. Toggle validation settings (case_sensitive, validate_on_import, auto_save)<br>2. Close application<br>3. Restart application | Boolean settings should retain their state | Manual |
| SP-03 | Path settings persistence | 1. Change a path setting (validation_lists_dir)<br>2. Close application<br>3. Restart application | Path setting should be preserved correctly | Manual |
| SP-04 | Window size persistence | 1. Resize application window<br>2. Close application<br>3. Restart application | Window size should be preserved | Manual |
| SP-05 | Multiple settings changes persistence | 1. Change multiple settings across different sections<br>2. Close application<br>3. Restart application | All setting changes should be preserved | Manual |

### 2. Configuration Export/Import

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| EI-01 | Basic configuration export | 1. Configure application with specific settings<br>2. Export configuration to a file | Export should complete successfully and create a valid JSON file | Manual |
| EI-02 | Basic configuration import | 1. Export configuration<br>2. Change settings<br>3. Import the exported configuration | All settings should revert to the exported state | Manual |
| EI-03 | Partial configuration import | 1. Create a JSON file with only some config sections<br>2. Import this partial configuration | Only the specified sections should be updated; others should remain unchanged | Manual |
| EI-04 | Invalid JSON import | Attempt to import an invalid JSON file | Application should show appropriate error and maintain current settings | Manual |
| EI-05 | Export with special characters | Configure paths with non-ASCII characters, then export | Special characters should be correctly preserved in export file | Manual |

### 3. Reset Functionality

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| RF-01 | Reset all settings | 1. Change multiple settings<br>2. Use "Reset all settings" feature | All settings should revert to default values | Manual |
| RF-02 | Reset specific section | 1. Change settings in multiple sections<br>2. Reset only one section | Only settings in the reset section should revert to defaults | Manual |
| RF-03 | Validation list preservation during reset | 1. Modify validation lists<br>2. Reset validation settings | Validation list content should be preserved unless specifically reset | Manual |
| RF-04 | UI update after reset | Perform settings reset | UI components should immediately reflect the reset values | Manual |
| RF-05 | Reset confirmation | Initiate settings reset | User should be prompted with confirmation dialog before reset occurs | Manual |

### 4. Error Handling

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| EH-01 | Missing config file recovery | 1. Delete config.ini<br>2. Start application | Application should create default config.ini and start normally | Automated |
| EH-02 | Corrupted config file recovery | 1. Corrupt config.ini with invalid content<br>2. Start application | Application should restore default settings and log warning | Automated |
| EH-03 | Permission issues | 1. Make config.ini read-only<br>2. Attempt to change settings | Application should show appropriate error message but continue functioning | Manual |
| EH-04 | Invalid settings values | Manually edit config.ini to contain invalid values | Application should use default values for invalid settings and log warnings | Automated |
| EH-05 | Missing validation lists recovery | Delete validation list files and start application | Application should recreate lists with default content | Automated |

### 5. Settings Synchronization

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| SS-01 | Validation tab to Settings tab sync | 1. Change settings in ValidationTabView<br>2. Switch to SettingsTabView | Changes should be reflected in SettingsTabView | Manual |
| SS-02 | Settings tab to Validation tab sync | 1. Change validation settings in SettingsTabView<br>2. Switch to ValidationTabView | Changes should be reflected in ValidationTabView | Manual |
| SS-03 | Real-time synchronization | 1. Arrange both views to be visible (e.g., using separate windows)<br>2. Change settings in one view | Other view should update immediately | Manual |
| SS-04 | Multiple view-model synchronization | Change settings that affect multiple UI components | All dependent components should update correctly | Manual |
| SS-05 | ValidationService signal emission | Change validation settings in SettingsTabView | ValidationService should emit validation_preferences_changed signal | Automated |

### 6. ValidationService Integration

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| VS-01 | ValidationService initialization | Initialize ValidationService with ConfigManager | Service should load settings from config | Automated |
| VS-02 | validate_on_import setting effect | 1. Set validate_on_import to false<br>2. Import data | Validation should not run automatically | Manual |
| VS-03 | case_sensitive setting effect | 1. Change case_sensitive setting<br>2. Validate data with case differences | Validation should respect case sensitivity setting | Automated |
| VS-04 | auto_save setting effect | 1. Set auto_save to true<br>2. Modify validation list<br>3. Check if file was updated | File should be automatically updated when auto_save is true | Automated |
| VS-05 | ValidationListModel reload | Change validation list file externally | ValidationListModel should properly reload changes | Automated |

### 7. ConfigManager API Tests

| ID | Test Case | Steps | Expected Result | Type |
|----|-----------|-------|----------------|------|
| CM-01 | get/set methods | Set values using set() and retrieve with get() | get() should return the value set by set() | Automated |
| CM-02 | get_bool method | Test get_bool with various values ("True", "False", "1", "0") | Should correctly convert strings to boolean values | Automated |
| CM-03 | get_path method | Test get_path with relative and absolute paths | Should correctly resolve paths | Automated |
| CM-04 | get_int method | Test get_int with various values | Should correctly convert strings to integers | Automated |
| CM-05 | save method | 1. Set values<br>2. Call save()<br>3. Examine config file | File should contain updated values in correct format | Automated |
| CM-06 | load method | 1. Modify config file<br>2. Call load()<br>3. Check values with get() | Values should reflect changes in file | Automated |
| CM-07 | has_section / has_option | Test with existing and non-existing sections/options | Should correctly report existence | Automated |
| CM-08 | validate_config method | Test with valid and invalid configurations | Should correctly identify problems | Automated |
| CM-09 | migration methods | Test with outdated config format | Should successfully migrate to new format | Automated |
| CM-10 | performance | Test with large configuration | Operations should complete within reasonable time | Automated |

## Implementation Approach

The test plan should be implemented using a combination of automated and manual testing:

### Automated Tests

For core ConfigManager functionality and ValidationService integration, create pytest test classes:

```python
class TestConfigManager:
    def test_get_set_values(self):
        # Test the get/set methods of ConfigManager
        
    def test_boolean_handling(self):
        # Test handling of boolean values
        
    # Additional test methods...
```

### Manual Tests

For UI-related tests and complex scenarios, create a manual test script with detailed steps and expected results. The tester should follow the script and report any deviations from expected behavior.

## Test Environment Setup

For automated tests:
1. Create a test fixture that sets up a temporary configuration directory
2. Initialize ConfigManager with this test directory
3. Perform test operations
4. Clean up temporary directory after test

Example:
```python
@pytest.fixture
def temp_config_manager():
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    # Initialize ConfigManager with test directory
    config_manager = ConfigManager(config_dir=temp_dir)
    
    yield config_manager
    
    # Cleanup
    shutil.rmtree(temp_dir)
```

For manual tests:
1. Create a testing build of the application
2. Document the initial state requirements
3. Provide clear steps to reproduce each test case
4. Include screenshots of expected results where appropriate

## Test Data Requirements

1. Sample validation lists with known content
2. Corrupted configuration files for error handling tests
3. Configuration files with various settings combinations
4. Large configuration files for performance testing

## Test Schedule

The testing should be conducted in the following order:

1. Automated tests for ConfigManager API (CM-01 to CM-10)
2. Automated tests for error handling (EH-01, EH-02, EH-04, EH-05)
3. Automated tests for ValidationService integration (VS-01, VS-03, VS-04, VS-05)
4. Manual tests for settings persistence (SP-01 to SP-05)
5. Manual tests for export/import (EI-01 to EI-05)
6. Manual tests for reset functionality (RF-01 to RF-05)
7. Manual tests for settings synchronization (SS-01 to SS-05)
8. Manual tests for remaining scenarios (EH-03, VS-02)

## Test Reporting

For each test case, record:
1. Test ID and name
2. Test date and tester
3. Result (Pass/Fail)
4. Actual behavior if different from expected
5. Screenshots or logs for failures
6. Notes or observations

## Success Criteria

The configuration system enhancements will be considered successfully tested when:
1. All automated tests pass
2. At least 90% of manual tests pass
3. Any failures are documented and assessed for severity
4. Critical functionality (persistence, reset, error recovery) works as expected 