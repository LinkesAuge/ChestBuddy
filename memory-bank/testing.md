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

## Current Test Status

All core test types are now functioning correctly:
- Unit tests pass
- Integration tests pass with SimpleData
- UI tests pass with enhanced_qtbot
- End-to-end tests pass with improved signal handling

The main application test suite is still being updated to use the new testing patterns and fixtures. 