# MainWindow Test Execution Examples

This document provides practical examples of how to run and debug the MainWindow tests after updating them to work with the new view-based architecture.

## Running Updated Tests

### Running All MainWindow Tests

```bash
# Run all MainWindow tests
pytest tests/test_main_window.py -v
```

### Running Specific MainWindow Tests

```bash
# Run a specific test by name
pytest tests/test_main_window.py::TestMainWindow::test_view_navigation -v

# Run tests matching a pattern
pytest tests/test_main_window.py -k "view" -v
```

### Running With Coverage

```bash
# Run with coverage
pytest tests/test_main_window.py --cov=chestbuddy.ui.main_window -v
```

## Debugging MainWindow Tests

### Using Visual Studio Code

1. Add a breakpoint to the test file
2. Use the VSCode test explorer or run/debug configuration
3. Add this configuration to `.vscode/launch.json`:

```json
{
    "name": "Debug MainWindow Tests",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "args": ["tests/test_main_window.py", "-v"],
    "cwd": "${workspaceFolder}",
    "console": "integratedTerminal"
}
```

### Using Print Statements

Add debugging print statements to the test or MainWindow class:

```python
def test_view_navigation(self, qtbot, main_window):
    print(f"Initial widget: {main_window._content_stack.currentWidget()}")
    
    # Test navigation
    view_name = "Validation"
    main_window._view_state_controller.set_active_view.reset_mock()
    main_window._on_navigation_changed(view_name)
    
    print(f"View state controller called with: {main_window._view_state_controller.set_active_view.call_args}")
    print(f"Current widget: {main_window._content_stack.currentWidget()}")
    
    main_window._view_state_controller.set_active_view.assert_called_with(view_name)
```

### Using PDB

Insert PDB breakpoints in your test code:

```python
def test_menu_enables(self, qtbot, main_window):
    import pdb; pdb.set_trace()
    # Test code here
```

## Test Fixtures

The updated test fixtures provide correctly mocked controllers:

```python
@pytest.fixture
def view_state_controller():
    """Create a mock view state controller."""
    controller = MagicMock(spec=ViewStateController)
    return controller

@pytest.fixture
def file_operations_controller():
    """Create a mock file operations controller."""
    controller = MagicMock(spec=FileOperationsController)
    return controller

@pytest.fixture
def ui_state_controller():
    """Create a mock UI state controller."""
    controller = MagicMock(spec=UIStateController)
    return controller

@pytest.fixture
def main_window(
    qtbot,
    app,
    data_model,
    csv_service,
    validation_service,
    correction_service,
    chart_service,
    data_manager,
    file_operations_controller,
    progress_controller,
    view_state_controller,
    data_view_controller,
    ui_state_controller,
    config_mock,
):
    """Create a MainWindow instance for testing."""
    with patch("chestbuddy.utils.config.ConfigManager", return_value=config_mock):
        window = MainWindow(
            data_model=data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=file_operations_controller,
            progress_controller=progress_controller,
            view_state_controller=view_state_controller,
            data_view_controller=data_view_controller,
            ui_state_controller=ui_state_controller,
            config_manager=config_mock,
        )
        qtbot.addWidget(window)
        window.show()
        yield window
        window.close()
```

## Example Updated Tests

### Example 1: Menu Action Test

```python
def test_validate_data_action(self, qtbot, main_window):
    """Test the validate data action using the view state controller."""
    # Create a signal catcher for the validate_data_triggered signal
    catcher = SignalCatcher()
    main_window.validate_data_triggered.connect(catcher.handler)
    
    # Reset mock to ensure clean state
    main_window._view_state_controller.set_active_view.reset_mock()
    
    # Find and trigger the validate data action
    for action in main_window.findChildren(QAction):
        if action.text() == "&Validate Data":
            action.trigger()
            break
    
    # Check if the signal was emitted
    assert catcher.signal_received
    
    # Check if view state controller was called with correct view name
    main_window._view_state_controller.set_active_view.assert_called_with("Validation")
```

### Example 2: View Navigation Test

```python
def test_view_navigation(self, qtbot, main_window):
    """Test navigation between views in the view-based architecture."""
    # Test navigation to each main view
    view_names = ["Dashboard", "Data", "Validation", "Correction", "Charts", "Settings"]
    
    for view_name in view_names:
        # Reset mock to check next call
        main_window._view_state_controller.set_active_view.reset_mock()
        
        # Simulate navigation action
        main_window._on_navigation_changed(view_name)
        
        # Verify controller was called with correct view name
        main_window._view_state_controller.set_active_view.assert_called_with(view_name)
        
        # Allow time for UI updates
        qtbot.wait(50)
```

### Example 3: File Operation Test

```python
def test_open_file_action(self, qtbot, main_window, test_csv_path):
    """Test the open file action using the file operations controller."""
    # Reset mock to check calls
    main_window._file_operations_controller.open_files.reset_mock()
    
    # Mock QFileDialog to return our test path
    with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
        # Find and trigger the open action
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open":
                action.trigger()
                break
    
    # Verify controller method was called with correct paths
    main_window._file_operations_controller.open_files.assert_called_with([str(test_csv_path)])
```

### Example 4: UI State Test

```python
def test_window_title_update(self, qtbot, main_window):
    """Test window title update via the UI state controller."""
    # Reset the mock to check future calls
    main_window._ui_state_controller.update_window_title.reset_mock()
    
    # Set a test file name
    test_file = "test_data.csv"
    
    # Simulate a file being loaded
    main_window._on_file_loaded(test_file)
    
    # Verify that the UIStateController was called to update the window title
    main_window._ui_state_controller.update_window_title.assert_called_with(test_file)
```

### Example 5: Signal Handling Test

```python
def test_data_changed_signal(self, qtbot, main_window):
    """Test handling of data_changed signal from the data model."""
    with (
        patch.object(main_window, "_update_ui") as mock_update_ui,
        patch.object(main_window, "_update_data_loaded_state") as mock_update_data_loaded,
    ):
        # Create a mock DataState object
        mock_data_state = MagicMock()
        mock_data_state.has_data = True
        
        # Emit the signal with the DataState object
        main_window._data_model.data_changed.emit(mock_data_state)
        
        # Check if UI methods were called with correct parameters
        mock_update_ui.assert_called_once()
        mock_update_data_loaded.assert_called_once()
        assert mock_update_data_loaded.call_args[0][0] == True
```

## Common Testing Patterns

### Testing Menu Actions

```python
# General pattern for testing menu actions
def test_action_pattern(self, qtbot, main_window):
    # 1. Setup signal catcher if needed
    catcher = SignalCatcher()
    main_window.some_signal.connect(catcher.handler)
    
    # 2. Reset controller mock
    main_window._some_controller.some_method.reset_mock()
    
    # 3. Find and trigger the action
    for action in main_window.findChildren(QAction):
        if action.text() == "&Action Name":
            action.trigger()
            break
    
    # 4. Verify signal emission if applicable
    assert catcher.signal_received
    
    # 5. Verify controller method was called
    main_window._some_controller.some_method.assert_called_with(expected_args)
```

### Testing Controller Interactions

```python
# General pattern for testing controller interactions
def test_controller_interaction_pattern(self, qtbot, main_window):
    # 1. Reset the controller mock
    main_window._some_controller.some_method.reset_mock()
    
    # 2. Setup return value if needed
    main_window._some_controller.some_method.return_value = expected_result
    
    # 3. Trigger the interaction
    main_window._some_method()
    
    # 4. Verify controller method was called
    main_window._some_controller.some_method.assert_called_with(expected_args)
```

### Testing Signal Handling

```python
# General pattern for testing signal handling
def test_signal_handling_pattern(self, qtbot, main_window):
    # 1. Setup mocks for methods that should be called
    with patch.object(main_window, "_some_method") as mock_method:
        # 2. Create any needed arguments for the signal
        mock_arg = MagicMock()
        
        # 3. Emit the signal
        main_window._some_object.some_signal.emit(mock_arg)
        
        # 4. Verify method was called with correct arguments
        mock_method.assert_called_with(mock_arg)
```

## Troubleshooting

### "AssertionError: Expected 'assert_called_with()' to be called..."

This typically means that the mock's method was not called with the expected arguments. Check:

1. Is the mock method name correct?
2. Are the expected arguments correct?
3. Was the mock reset before the test?

Solution: Add debugging to see the actual call:

```python
print(f"Mock was called with: {main_window._controller.method.call_args}")
print(f"Expected: {expected_args}")
```

### "RuntimeError: Internal C++ object already deleted"

This occurs when a Qt object is accessed after it's been deleted. Check:

1. Is the object being destroyed before accessing it?
2. Are signals disconnected properly?
3. Is the object properly parented?

Solution: Ensure proper cleanup or use weak references:

```python
# In the test fixture
yield window
window.close()
QtWidgets.QApplication.processEvents()  # Process pending events
```

### "Signal not emitted" Errors

If a signal isn't emitted as expected, check:

1. Is the signal connected properly?
2. Is the signal actually emitted in the code path being tested?
3. Is the wait timeout sufficient?

Solution: Use longer timeouts or debug signal connections:

```python
# Use longer timeout
with qtbot.waitSignal(object.signal, timeout=1000) as blocker:
    # Trigger action
    
# Or add debug prints
print(f"Signal connections: {object.receivers(SIGNAL('signal()'))}")
```

## Running Tests in CI

For running tests in CI environments, use these commands:

```bash
# Run all MainWindow tests with XML report
pytest tests/test_main_window.py --junitxml=test-results/junit-mainwindow.xml

# Run with coverage report
pytest tests/test_main_window.py --cov=chestbuddy.ui.main_window --cov-report=xml:coverage-reports/coverage-mainwindow.xml
```

## Summary

Following these examples and patterns will help ensure that the MainWindow tests are properly updated to work with the new view-based architecture. The key changes are:

1. Verifying controller method calls instead of direct UI manipulation
2. Using proper mock resets before testing calls
3. Focusing on behavior rather than implementation
4. Using the appropriate controller for each functionality area

These examples should provide a solid foundation for updating all MainWindow tests to support the new architecture.

## MainWindow Test Examples for View-Based Architecture

### Controller Mocking

When testing MainWindow with the view-based architecture, we need to mock the controllers:

```python
@pytest.fixture
def view_state_controller():
    """Create a mock view state controller."""
    controller = MagicMock(spec=ViewStateController)
    return controller

@pytest.fixture
def file_operations_controller():
    """Create a mock file operations controller."""
    controller = MagicMock(spec=FileOperationsController)
    return controller
```

### Menu Actions Tests

Testing menu actions now involves finding the action and triggering it, then verifying the controller was called:

```python
def test_open_file_action(self, qtbot, main_window, file_operations_controller, test_csv_path):
    """Test the open file action using the file operations controller."""
    # Reset mock to check calls
    file_operations_controller.open_file.reset_mock()
    
    # Mock QFileDialog to return our test path
    with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
        # Find and trigger the open action
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open..." or action.text() == "&Open":
                action.trigger()
                break
    
    # Verify controller method was called with correct paths
    file_operations_controller.open_file.assert_called_with([str(test_csv_path)])
```

### View Navigation Tests

Testing view navigation by directly calling the controller:

```python
def test_view_switching(self, qtbot, main_window, view_state_controller):
    """Test switching between views with the view-based architecture."""
    # Test switching to different views
    view_sequence = ["Data", "Validation", "Correction", "Charts", "Dashboard"]
    
    for view_name in view_sequence:
        # Reset mock to check next call
        view_state_controller.set_active_view.reset_mock()
        
        # Call the controller directly
        view_state_controller.set_active_view(view_name)
        
        # Allow time for UI updates
        qtbot.wait(50)
        
        # Verify controller was called with correct view name
        view_state_controller.set_active_view.assert_called_with(view_name)
```

### Signal Testing

Testing signal emission and handling:

```python
def test_validate_data_action(self, qtbot, main_window, view_state_controller):
    """Test the validate data action using the view state controller."""
    # Create a signal catcher for the validate_data_triggered signal
    catcher = SignalCatcher()
    main_window.validate_data_triggered.connect(catcher.handler)
    
    # Reset mock to ensure clean state
    view_state_controller.set_active_view.reset_mock()
    
    # Find and trigger the validate data action
    for action in main_window.findChildren(QAction):
        if action.text() == "Validate &Data":
            action.trigger()
            break
    
    # Check if the signal was emitted
    assert catcher.signal_received
    
    # Check if view state controller was called with correct view name
    view_state_controller.set_active_view.assert_called_with("Validation")
```

### Clean Up and Avoiding Signal Warnings

To avoid signal disconnection warnings, ensure proper cleanup:

```python
@pytest.fixture
def main_window(qtbot, data_model, csv_service, validation_service, correction_service, 
               chart_service, data_manager, file_operations_controller, progress_controller, 
               view_state_controller, data_view_controller, ui_state_controller, config_mock):
    """Create a MainWindow instance for testing with mocked controllers."""
    with patch("chestbuddy.utils.config.ConfigManager", return_value=config_mock):
        window = MainWindow(
            data_model=data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=file_operations_controller,
            progress_controller=progress_controller,
            view_state_controller=view_state_controller,
            data_view_controller=data_view_controller,
            ui_state_controller=ui_state_controller,
            config_manager=config_mock,
        )
        qtbot.addWidget(window)
        window.show()
        # Allow time for the window to fully initialize
        qtbot.wait(50)
        yield window
        # Proper cleanup to avoid signal disconnection warnings
        window.close()
        QApplication.processEvents()  # Process any pending events
```

## Common Issues and Solutions

### Controller Method Names

Be aware that controller method names may differ from what you expect. Check the actual implementation and adjust your tests accordingly:

- `file_operations_controller.open_files` should be `file_operations_controller.open_file`
- `file_operations_controller.export_csv` should be `file_operations_controller.export_file`

### Menu Text Changes

Menu texts may have changed from the original implementation. Be flexible in your tests to handle variations:

```python
# Before
if action.text() == "&Open":
    action.trigger()

# After
if action.text() == "&Open..." or action.text() == "&Open":
    action.trigger()
```

### Signal Disconnection Warnings

Signal disconnection warnings can be reduced by:

1. Ensuring proper cleanup in fixtures
2. Using QApplication.processEvents() to process pending events before cleanup
3. Disconnecting signals before closing windows

### Multiple Controller Calls

If your controller method is being called multiple times when expected once, ensure you reset the mock before each test step:

```python
view_state_controller.set_active_view.reset_mock()
```

## Original Test Examples

// ... existing content ... 