---
title: ChestBuddy Testing Framework
date: 2024-06-29
---

# ChestBuddy Testing Framework

## Overview

This document outlines the comprehensive testing framework implemented for the ChestBuddy application. The framework provides a structured approach to testing different components and interactions within the application, ensuring code quality and reliability.

## Test Directory Structure

The testing framework follows a structured layout:

```
tests/
├── unit/               # Tests for individual components in isolation
├── integration/        # Tests for component interactions
├── ui/                 # Tests for UI components
├── e2e/                # End-to-end workflow tests
├── data/               # Test data factories and datasets
├── utils/              # Testing utilities and helpers
├── resources/          # Test resources and assets
├── conftest.py         # Common test fixtures
├── pytest.ini          # Pytest configuration
└── README.md           # Documentation
```

## Test Types

### Unit Tests
- Focus on testing individual components in isolation
- Fast execution with minimal dependencies
- Use mocks for external dependencies
- Current status: Working correctly with TestDataFactory

### Integration Tests
- Test interactions between multiple components
- Medium execution speed
- Less mocking, more real component interaction
- Current status: Working correctly after implementing SimpleData and improved signal handling

### UI Tests
- Test UI components and user interactions
- Use QtBot for widget testing
- Test both appearance and behavior
- Current status: Working correctly with enhanced_qtbot

### End-to-End Tests
- Test complete application workflows
- Slow execution, but comprehensive coverage
- Minimal mocking, focused on real usage scenarios
- Current status: Working correctly with improved signal management

## Key Testing Tools & Frameworks

### Core Testing Framework
- Pytest as the primary testing framework
- Pytest-qt for Qt widget testing
- Pytest-cov for test coverage reporting

### Special Test Features
- Custom SignalSpy for monitoring Qt signals with proper disconnection
- Enhanced QtBot for improved widget testing with signal tracking
- TestDataFactory for generating test datasets
- SimpleData for avoiding recursion in signal transmission
- wait_for_signal function for proper event loop handling

## Test Fixtures

The framework includes several fixtures defined in `conftest.py`:

1. **QtBot Enhanced**: Extended version of qtbot with additional helper methods:
   - Widget tracking and cleanup
   - Signal spy integration
   - Button click helpers
   - Wait for signal emission

2. **Signal Connections**: Fixture to track and clean up signal connections:
   - Automatic disconnection after test
   - Tracking of all connections
   - Prevents signal leakage between tests

3. **Sample Data**: Pre-generated datasets using SimpleData:
   - Various sizes and characteristics
   - Avoids recursion issues with Qt signals

4. **Temporary Files**: Fixtures for temporary file/directory management:
   - Auto-cleanup after tests
   - Path helpers for test data

5. **Mock Services**: Pre-configured service mocks for different testing scenarios

## Test Patterns

### Widget Testing Pattern
```python
def test_widget_functionality(enhanced_qtbot):
    # Create widget
    widget = SomeWidget()
    enhanced_qtbot.addWidget(widget)
    
    # Set up signal spy
    signal_spy = enhanced_qtbot.add_spy(widget.some_signal)
    
    # Perform action
    enhanced_qtbot.click_button(widget.button)
    
    # Verify results
    assert signal_spy.count() == 1
    assert widget.property("value") == expected_value
```

### Integration Testing Pattern
```python
def test_component_interaction(signal_connections):
    # Create components
    component_a = ComponentA()
    component_b = ComponentB()
    
    # Set up signal connections with tracking
    connection = signal_connections(component_a.signal, component_b.slot)
    
    # Create SimpleData for avoiding recursion
    test_data = SimpleData({"key": "value"})
    
    # Perform action
    component_a.process_data(test_data)
    process_events()  # Process Qt event loop
    
    # Verify results
    assert component_b.received_data.key == "value"
```

## Solutions to Common Issues

### 1. Recursion with Complex Data Structures

**Problem**: Integration tests experienced recursion issues when using PySide6 signals with pandas DataFrames, causing stack overflows during signal emission.

**Solution**:
- Implemented SimpleData class as a lightweight alternative to pandas DataFrames
- SimpleData uses basic Python data types (dicts, lists) that Qt can handle
- Added proper copy methods to avoid reference cycles
- Used clear construction/copying patterns to prevent recursion

Example implementation:
```python
class SimpleData:
    """Simple message container that won't cause recursion issues."""

    def __init__(self, data=None):
        """Initialize with simple data types."""
        self.data = data or {}

    def __repr__(self):
        """String representation for debugging."""
        return f"SimpleData({self.data})"
```

### 2. Signal Cleanup

**Problem**: Tests would leak signal connections, leading to unexpected behaviors in subsequent tests when signals were unexpectedly received.

**Solution**:
- Enhanced SignalSpy with proper disconnection:
  - Added connection tracking
  - Implemented disconnect() method
  - Added automatic cleanup in __del__
- Created signal_connections fixture for automatic cleanup
- Added connection tracking in Controller classes
- Implemented explicit QObject.disconnect() calls

Example implementation:
```python
class SignalSpy:
    def __init__(self, signal):
        self.signal = signal
        self.emissions = []
        self.connection = signal.connect(self._on_signal_emission)
        
    def disconnect(self):
        if self.connection:
            QObject.disconnect(self.connection)
            self.connection = None
            
    def __del__(self):
        self.disconnect()
```

### 3. Event Loop Management

**Problem**: Tests involving signal emissions had timing issues due to the Qt event loop not processing events properly.

**Solution**:
- Implemented wait_for_signal function with proper timeout handling
- Added process_events utility for consistent event processing
- Enhanced SignalSpy with wait_for_emission method
- Used QEventLoop with QTimer for proper timeout management

Example implementation:
```python
def wait_for_signal(signal, timeout=1000):
    """Wait for a signal to be emitted using an event loop."""
    result = {"received": False, "args": None}
    
    def handler(*args):
        result["received"] = True
        result["args"] = args
        loop.quit()
    
    loop = QEventLoop()
    connection = signal.connect(handler)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    QObject.disconnect(connection)
    
    return result
```

## Best Practices

1. **Isolated Tests**: Each test should be completely isolated and not depend on the state from previous tests.

2. **Clean Setup and Teardown**: Always clean up resources (files, connections, etc.) after tests.

3. **Meaningful Assertions**: Make assertions that verify the actual functionality, not just implementation details.

4. **Mock External Dependencies**: Use mocks for external services, I/O operations, and other dependencies.

5. **Test Data Management**: Use the TestDataFactory for consistent test data rather than creating ad-hoc data in each test.

6. **Signal Management**:
   - Always track signal connections
   - Use signal_connections fixture for automatic cleanup
   - Explicitly disconnect signals after use
   - Use wait_for_signal instead of manual timing

7. **Event Loop Handling**:
   - Always call process_events() after signal emissions
   - Use wait_for_signal for asynchronous operations
   - Avoid fixed time delays (time.sleep) in favor of event-based waiting

## Qt UI Testing Best Practices

1. **Widget Registration**: Always register widgets with enhanced_qtbot using `enhanced_qtbot.addWidget(widget)`.

2. **Signal Verification**: Use SignalSpy to verify signal emissions rather than relying on side effects.

3. **Event Processing**: Use `enhanced_qtbot.waitForWindowShown(widget)` before interacting with newly created widgets.

4. **Event Timing**: Use `enhanced_qtbot.waitUntil()` for asynchronous operations instead of fixed delays.

5. **Modal Dialog Testing**: Use `enhanced_qtbot.waitForWindow()` for testing modal dialogs.

6. **Signal Cleanup**: Always ensure signals are disconnected after testing.

7. **Use SimpleData**: When testing components that emit signals with complex data, use SimpleData instead of complex structures.

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

## Current Test Status

All core test types are now functioning correctly:
- Unit tests pass
- Integration tests pass with SimpleData
- UI tests pass with enhanced_qtbot
- End-to-end tests pass with improved signal handling

The main application test suite is still being updated to use the new testing patterns and fixtures.

## Test Runner Scripts

ChestBuddy includes several specialized test runner scripts to simplify test execution:

### 1. Run All Tests

The `scripts/run_all_tests.py` script provides a comprehensive way to run tests with various options:

```bash
python scripts/run_all_tests.py [options]
```

**Options:**
- `--all`: Run all tests (default if no category specified)
- `--unit`: Run only unit tests
- `--integration`: Run only integration tests
- `--module MODULE`: Run tests for a specific module (e.g., `tests/unit/utils/test_config_manager_unit.py`)
- `--coverage`: Generate a coverage report
- `--verbose`: Show verbose output
- `--quiet`: Show minimal output
- `--xml`: Generate an XML report for CI integration

**Example Uses:**
```bash
# Run all tests
python scripts/run_all_tests.py

# Run only unit tests with verbose output
python scripts/run_all_tests.py --unit --verbose

# Run only integration tests
python scripts/run_all_tests.py --integration

# Generate a coverage report
python scripts/run_all_tests.py --coverage

# Run tests for a specific module
python scripts/run_all_tests.py --module tests/unit/utils/test_config_manager_unit.py

# Generate XML reports for CI
python scripts/run_all_tests.py --xml
```

### 2. Run Integration Tests

The `scripts/run_integration_tests.py` script focuses on running integration tests:

```bash
python scripts/run_integration_tests.py
```

This script runs all tests in the `tests/integration/` directory.

### 3. Run Validation Integration Tests

The `scripts/run_validation_integration_tests.py` script runs the integration tests for the ValidationService:

```bash
python scripts/run_validation_integration_tests.py
```

This script specifically targets tests related to the integration between ValidationService and ConfigManager.

## Recent Test Improvements

### ConfigManager Testing Enhancements

1. **Boolean Value Handling**: 
   - Fixed the `get_bool()` method to properly recognize 'Y'/'y' as True values
   - Added comprehensive tests for various boolean string representations

2. **Configuration Migration**:
   - Added tests for migrating from older configuration versions
   - Ensured the auto_validate setting properly migrates to validate_on_import

3. **Error Handling**:
   - Added tests for permission errors during save operations
   - Improved handling of corrupted configuration files

4. **Integration Testing**:
   - Fixed all integration tests between ValidationService and ConfigManager
   - Added tests for validation list path resolution from configuration
   - Ensured proper handling of configuration resets
   - Added tests for auto-save behavior

### Skipping UI Tests in Headless Environments

For UI tests that require a graphical environment, we've added proper skip conditions:

```python
import pytest
import sys
from PySide6.QtWidgets import QApplication

# Skip if running in a headless environment
@pytest.mark.skipif(
    not QApplication.instance() or not hasattr(QApplication.instance(), "node"),
    reason="UI tests need a QApplication with a display"
)
def test_ui_component():
    # UI test code here
    pass
```

This ensures tests don't fail in CI environments that lack a display server. 