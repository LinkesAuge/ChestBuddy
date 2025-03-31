# MainWindow Tests Update Plan

## Overview

The ChestBuddy application is transitioning from a tab-based UI architecture to a modern view-based architecture. This plan outlines how to update the MainWindow tests to align with these architectural changes.

## Understanding the Architectural Changes

### From Tab-Based to View-Based

**Previous Architecture:**
- MainWindow contained a QTabWidget with tabs for different functions
- Tabs were directly referenced (e.g., _validation_tab, _correction_tab)
- Tab switching was done through QTabWidget.setCurrentIndex()

**New Architecture:**
- MainWindow contains a QStackedWidget with different view components
- Views are managed through dedicated controllers (ViewStateController)
- Navigation is handled through signals/slots and controllers
- Each view is a self-contained component with its own functionality

### Controller-Based Coordination

**Previous Architecture:**
- MainWindow handled most operations directly
- Direct method calls between components
- Limited separation of concerns

**New Architecture:**
- Operations delegated to specialized controllers:
  - FileOperationsController: Handles file operations
  - ViewStateController: Manages active view
  - DataViewController: Coordinates data operations
  - UIStateController: Manages UI state updates
  - ProgressController: Handles progress feedback

### Signal Flow Changes

**Previous Architecture:**
- Signals directly connected between components
- MainWindow coordinated most signal connections

**New Architecture:**
- Controllers mediate signal connections
- Components communicate through controller interfaces
- Cleaner signal flow with better separation

### Menu Structure Updates

**Previous Architecture:**
- Menus directly referenced tabs
- Actions directly called MainWindow methods

**New Architecture:**
- Menus organized by function, not by tab
- Actions trigger controller methods
- New menu structure with reorganized commands

## Test Update Strategy

### Test Types

1. **Tests Needing Minor Updates:**
   - Tests that verify signals still being emitted
   - Tests checking basic window properties
   - Tests verifying menu existence

2. **Tests Needing Major Rework:**
   - Tests that directly reference tabs
   - Tests that assume specific UI structure
   - Tests that rely on direct method calls

3. **Tests Needing Replacement:**
   - Tests that validate behavior fundamentally changed in the new architecture
   - Tests tightly coupled to implementation details

### Update Patterns

1. **Controller Call Verification:**
   - Instead of checking UI state directly, verify controller methods are called
   - Use `assert_called_with()` to check controller invocation

2. **Signal Verification:**
   - Keep verifying signals when appropriate
   - Update signal expectations to match new architecture

3. **Mock Updates:**
   - Ensure mocks reflect new controller interfaces
   - Add new mock behaviors for controller responses

4. **Component Initialization:**
   - Update test fixtures to initialize controllers correctly
   - Ensure proper component initialization order

## Specific Test Categories

### Menu Action Tests

Tests that verify menu actions trigger appropriate behavior:

**Update Approach:**
- Keep verifying that actions exist
- Update expectations to verify controller methods are called
- Maintain signal verification where appropriate

**Example Test Update:**

```python
# BEFORE
def test_validate_data_action(self, qtbot, main_window):
    catcher = SignalCatcher()
    main_window.validate_data_triggered.connect(catcher.handler)
    for action in main_window.findChildren(QAction):
        if action.text() == "&Validate Data":
            action.trigger()
            break
    assert catcher.signal_received
    assert main_window._tab_widget.currentWidget() == main_window._validation_tab

# AFTER
def test_validate_data_action(self, qtbot, main_window):
    catcher = SignalCatcher()
    main_window.validate_data_triggered.connect(catcher.handler)
    main_window._view_state_controller.set_active_view.reset_mock()
    for action in main_window.findChildren(QAction):
        if action.text() == "&Validate Data":
            action.trigger()
            break
    assert catcher.signal_received
    main_window._view_state_controller.set_active_view.assert_called_with("Validation")
```

### View Navigation Tests

Tests that verify proper navigation between views:

**Update Approach:**
- Replace tab switching tests with view navigation tests
- Verify controller methods called with correct view names
- Check signal propagation for navigation events

**Example Test Update:**

```python
# BEFORE
def test_tab_switching(self, qtbot, main_window):
    assert main_window._tab_widget.currentIndex() == 0
    main_window._tab_widget.setCurrentIndex(1)
    assert main_window._tab_widget.currentIndex() == 1
    main_window._tab_widget.setCurrentIndex(2)
    assert main_window._tab_widget.currentIndex() == 2
    main_window._tab_widget.setCurrentIndex(0)
    assert main_window._tab_widget.currentIndex() == 0

# AFTER
def test_view_navigation(self, qtbot, main_window):
    # Verify initial view (typically Dashboard)
    initial_view = main_window._content_stack.currentWidget()
    
    # Test navigation to each main view
    view_names = ["Dashboard", "Data", "Validation", "Correction", "Charts", "Settings"]
    
    for view_name in view_names:
        main_window._view_state_controller.set_active_view.reset_mock()
        
        # Simulate navigation action
        main_window._on_navigation_changed(view_name)
        
        # Verify controller was called with correct view name
        main_window._view_state_controller.set_active_view.assert_called_with(view_name)
        qtbot.wait(50)  # Allow time for UI updates
```

### File Operation Tests

Tests that verify file operations:

**Update Approach:**
- Update to verify FileOperationsController methods are called
- Check signal propagation for file operations
- Verify UI updates based on file operation results

**Example Test Update:**

```python
# BEFORE
def test_open_file_action(self, qtbot, main_window, test_csv_path):
    catcher = SignalCatcher()
    main_window.load_csv_triggered.connect(catcher.handler)
    with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open":
                action.trigger()
                break
    assert catcher.signal_received
    assert catcher.signal_args[0][0] == str(test_csv_path)

# AFTER
def test_open_file_action(self, qtbot, main_window, test_csv_path):
    # Reset mock to check calls
    main_window._file_operations_controller.open_files.reset_mock()
    
    with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open":
                action.trigger()
                break
    
    # Verify controller method was called with correct paths
    main_window._file_operations_controller.open_files.assert_called_with([str(test_csv_path)])
```

### UI State Tests

Tests that verify UI state updates:

**Update Approach:**
- Verify UIStateController methods are called with correct parameters
- Check that UI responds correctly to controller signals
- Focus on behavior rather than implementation details

**Example Test Update:**

```python
# BEFORE
def test_window_title_update(self, qtbot, main_window, config_mock):
    assert "ChestBuddy" in main_window.windowTitle()
    test_file = "test_data.csv"
    config_mock.get.return_value = test_file
    main_window._update_window_title()
    assert test_file in main_window.windowTitle()

# AFTER
def test_window_title_update(self, qtbot, main_window):
    assert "ChestBuddy" in main_window.windowTitle()
    
    # Reset mock to check calls
    main_window._ui_state_controller.update_window_title.reset_mock()
    
    # Set a test file name
    test_file = "test_data.csv"
    
    # Simulate a file being loaded
    main_window._on_file_loaded(test_file)
    
    # Verify the controller was called to update window title
    main_window._ui_state_controller.update_window_title.assert_called_with(test_file)
```

### Signal Handling Tests

Tests that verify signal connections and handling:

**Update Approach:**
- Update signal expectations to match controller-based architecture
- Verify signals are connected to appropriate controller methods
- Check signals propagate through the system correctly

**Example Test Update:**

```python
# BEFORE
def test_data_changed_signal(self, qtbot, main_window):
    with patch.object(main_window, "_update_ui") as mock_update_ui:
        main_window._data_model.data_changed.emit()
        mock_update_ui.assert_called_once()

# AFTER
def test_data_changed_signal(self, qtbot, main_window):
    with (
        patch.object(main_window, "_update_ui") as mock_update_ui,
        patch.object(main_window, "_update_data_loaded_state") as mock_update_data_loaded,
    ):
        # Create a mock DataState object for the signal
        mock_data_state = MagicMock()
        mock_data_state.has_data = True
        
        # Emit the data_changed signal with DataState object
        main_window._data_model.data_changed.emit(mock_data_state)
        
        # Check if UI update methods were called
        mock_update_ui.assert_called_once()
        mock_update_data_loaded.assert_called_once()
        assert mock_update_data_loaded.call_args[0][0] == True
```

## Implementation Plan

### Phase 1: Basic Test Fixes

1. **Update Test Fixtures:**
   - Update fixtures to create mocked controllers
   - Ensure MainWindow initialization uses proper controllers
   - Fix basic assertion failures

2. **Update Simple Tests:**
   - Fix menu existence tests
   - Update simple signal tests
   - Fix basic property tests

### Phase 1 Implementation Results and Findings

After implementing the first phase of MainWindow test updates, several important issues were identified:

1. **Controller Method Names**:
   - Some controller method names in the actual implementation differ from our assumptions:
     - `file_operations_controller.open_files` should be `file_operations_controller.open_file`
     - `file_operations_controller.export_csv` doesn't exist, need to identify the correct method

2. **View Navigation Communication**:
   - Direct calls to `_on_navigation_changed("Charts")` don't trigger `view_state_controller.set_active_view`
   - Tests need to be updated to either mock the signal chain or call the controller directly

3. **Menu Text Changes**:
   - Menu item texts have changed slightly:
     - `&Open` is now `&Open...`
     - Menu structure might need more detailed inspection

4. **Signal Disconnection Warnings**:
   - Many warnings about failed signal disconnections
   - This confirms the need for the cleanup improvements we planned

5. **Multiple Calls to Single-Call Methods**:
   - Several mock methods are called multiple times when expected to be called once
   - May need to add reset_mock() calls in more places or check for specific parameters instead

These findings will help refine the implementation of the remaining test updates and guide the next phases.

### Phase 2: Core Functionality Tests

1. **Update Navigation Tests:**
   - Replace tab switching tests with view navigation tests
   - Verify view activation through controllers

2. **Update File Operation Tests:**
   - Rewrite to use FileOperationsController
   - Verify proper signal handling

3. **Update Action Tests:**
   - Update to verify controller interactions
   - Fix menu action tests

### Phase 2 Planning Updates

Based on these findings, Phase 2 implementation will need to:

1. Update controller method names to match actual implementation
2. Fix view navigation testing by using the correct controller methods
3. Update menu text assertions to match actual menu text
4. Focus on improving signal connection/disconnection
5. Add proper mock resets between test steps

### Phase 3: Advanced Tests

1. **Update Complex Interaction Tests:**
   - Update tests with multiple component interactions
   - Fix state persistence tests

2. **Add New Architecture Tests:**
   - Add tests specific to the new architecture
   - Test controller coordination

### Phase 4: Final Review

1. **Cleanup Skipped Tests:**
   - Remove or update all skipped tests
   - Ensure no legacy architecture references

2. **Comprehensive Testing:**
   - Verify all tests pass with the new architecture
   - Ensure test coverage remains high

## Best Practices

1. **Focus on Behavior:**
   - Test what the application does, not how it's implemented
   - Minimize implementation coupling

2. **Use Controllers Appropriately:**
   - Test through controller interfaces
   - Avoid direct UI manipulation

3. **Mock Effectively:**
   - Mock at the appropriate level
   - Verify interactions, not implementation

4. **Maintain Signal Verification:**
   - Continue to verify signal emissions
   - Update signal parameters as needed

5. **Document Changes:**
   - Comment on architectural differences
   - Explain test approach changes

## Test Cases To Update

The following tests need specific updates:

1. **test_validate_data_action:**
   - Replace tab checks with ViewStateController verification
   - Maintain signal verification

2. **test_apply_corrections_action:**
   - Replace tab checks with ViewStateController verification
   - Maintain signal verification

3. **test_tab_switching:**
   - Replace with view navigation test
   - Verify controller calls and view changes

4. **test_window_title_update:**
   - Update to verify UIStateController calls
   - Check window title updates via controller

5. **test_open_file_action:**
   - Update to verify FileOperationsController calls
   - Maintain signal verification

6. **test_save_file_action:**
   - Update to verify FileOperationsController calls
   - Maintain signal verification

7. **test_open_multiple_files:**
   - Rewrite to use FileOperationsController
   - Verify proper handling of multiple files

8. **test_recent_files_menu:**
   - Update to match new menu structure
   - Verify controller interactions

## Future-Proofing

1. **Avoid Implementation Coupling:**
   - Test behavior, not implementation
   - Use abstractions when possible

2. **Controller-Based Testing:**
   - Test through controller interfaces
   - Minimize direct UI testing

3. **Signal-Based Verification:**
   - Focus on signal flow
   - Verify correct signal parameters

4. **Componentized Testing:**
   - Test each component in isolation
   - Use integration tests for component interaction

By following this plan, we can successfully update the MainWindow tests to support the new view-based architecture while maintaining good test coverage and ensuring the application functions correctly. 