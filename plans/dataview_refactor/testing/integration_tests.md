# DataView Refactoring - Integration Testing Strategy

## Overview

This document outlines the integration testing strategy for the DataView refactoring project. While unit tests focus on individual components in isolation, integration tests ensure that these components work together correctly. The goal is to verify the interactions between different parts of the system and identify issues that might not be apparent when testing components in isolation.

## Integration Testing Approach

The integration testing strategy follows these principles:

1. **Progressive Integration**: Start with small component groups and gradually expand.
2. **Focus on Interfaces**: Test the boundaries between components.
3. **End-to-End Workflows**: Test complete user workflows.
4. **State Verification**: Verify system state changes correctly during interactions.
5. **Signal/Slot Connections**: Ensure signals and slots are correctly connected.

## Testing Scope

The integration tests will cover the following key integrations:

### 1. DataView Component Integration

- **Model-View Integration**: How DataViewModel interacts with DataTableView
- **Delegate Integration**: How delegates integrate with the view
- **Selection Integration**: How selection changes propagate through the system
- **Context Menu Integration**: How context menus respond to different selection states

### 2. Validation System Integration

- **Validation Service to TableStateManager**: How validation results flow to state management
- **TableStateManager to DataViewModel**: How state information is provided to the model
- **DataViewModel to CellDisplayDelegate**: How validation state affects cell rendering
- **User Interaction with Validation**: How users interact with validation indicators

### 3. Correction System Integration

- **Correction Service to UI**: How correction options are displayed
- **UI to Correction Application**: How corrections are applied from UI actions
- **Correction to Validation**: How applied corrections affect validation state
- **Batch Correction Workflows**: How batch corrections work end-to-end

### 4. Import/Export Integration

- **Import Dialog to Data Model**: How imported data flows into the system
- **Data Model to Export**: How data is exported from the system
- **Validation during Import**: How validation is applied during import
- **Selection to Export**: How selection affects export operations

## Test Environment and Setup

### Environment

Integration tests will run in a controlled environment with:

- **In-Memory Database**: For data persistence testing
- **Mock Services**: For external service dependencies
- **Full Qt Application**: For UI component testing
- **Controlled Time**: For time-dependent operations

### Test Fixtures

Common test fixtures will include:

```python
# integration_conftest.py

import pytest
from PySide6.QtWidgets import QApplication
import pandas as pd
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService, CorrectionService
from chestbuddy.ui.data.models import DataViewModel
from chestbuddy.ui.data.views import DataTableView
from chestbuddy.ui.data.adapters import ValidationAdapter, CorrectionAdapter
from chestbuddy.core.managers import TableStateManager

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def test_data():
    """Create test data for integration tests."""
    return pd.DataFrame({
        'Player': ['Player1', 'Player2', 'JohnSmiht', 'Player4', 'Player5'],
        'Chest': ['Gold', 'Silver', 'siver', 'Diamond', 'Bronze'],
        'Score': [100, 200, 'abc', 400, 500],
        'Date': ['2023-01-01', '2023-02-01', '2023-13-45', '2023-04-01', '2023-05-01']
    })

@pytest.fixture
def chest_data_model(test_data):
    """Create a ChestDataModel with test data."""
    model = ChestDataModel()
    model.update_data(test_data)
    return model

@pytest.fixture
def validation_service():
    """Create a real ValidationService."""
    return ValidationService()

@pytest.fixture
def correction_service():
    """Create a real CorrectionService."""
    return CorrectionService()

@pytest.fixture
def table_state_manager():
    """Create a real TableStateManager."""
    return TableStateManager()

@pytest.fixture
def integrated_system(chest_data_model, validation_service, correction_service, 
                      table_state_manager, qapp):
    """Create an integrated system with all components."""
    # Create adapters
    validation_adapter = ValidationAdapter(validation_service)
    correction_adapter = CorrectionAdapter(correction_service)
    
    # Create view model
    data_view_model = DataViewModel(chest_data_model)
    
    # Create view
    data_table_view = DataTableView()
    data_table_view.setModel(data_view_model)
    
    # Connect components
    validation_service.validation_complete.connect(
        validation_adapter.on_validation_complete)
    validation_adapter.validation_state_changed.connect(
        table_state_manager.update_cell_states_from_validation)
    table_state_manager.cell_states_changed.connect(
        data_view_model.on_cell_states_changed)
    
    correction_service.correction_available.connect(
        correction_adapter.on_correction_available)
    correction_adapter.correction_state_changed.connect(
        table_state_manager.update_cell_states_from_correction)
    
    # Return all components
    return {
        'data_model': chest_data_model,
        'validation_service': validation_service,
        'correction_service': correction_service,
        'table_state_manager': table_state_manager,
        'validation_adapter': validation_adapter,
        'correction_adapter': correction_adapter,
        'data_view_model': data_view_model,
        'data_table_view': data_table_view
    }
```

## Test Categories

### Model-View Integration Tests

These tests verify that the model correctly provides data to the view and that the view correctly displays it.

```python
# test_model_view_integration.py

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

class TestModelViewIntegration:
    """Tests for model-view integration."""
    
    def test_data_propagation(self, integrated_system):
        """Test that data changes in the model propagate to the view."""
        model = integrated_system['data_model']
        view = integrated_system['data_table_view']
        
        # Change data in model
        test_value = "TestValue"
        model.setData(model.index(0, 0), test_value)
        
        # Verify view displays the new value
        view_index = view.model().index(0, 0)
        assert view.model().data(view_index, Qt.DisplayRole) == test_value
        
    def test_selection_propagation(self, integrated_system, qtbot):
        """Test that selection in view propagates to model."""
        view = integrated_system['data_table_view']
        
        # Select a cell in the view
        view_index = view.model().index(1, 1)
        view.setCurrentIndex(view_index)
        
        # Verify selection was updated
        assert view.currentIndex() == view_index
        
        # Test programmatic selection signal propagation
        mock_handler = qtbot.createSignalSpy(view.selectionModel().selectionChanged)
        
        # Change selection
        view.setCurrentIndex(view.model().index(2, 2))
        
        # Verify signal was emitted
        assert mock_handler.count() == 1
```

### Validation Integration Tests

These tests verify that validation results correctly propagate through the system and affect cell rendering.

```python
# test_validation_integration.py

import pytest
from PySide6.QtCore import Qt, QPoint
from chestbuddy.core.enums.validation_enums import ValidationStatus
import pandas as pd

class TestValidationIntegration:
    """Tests for validation system integration."""
    
    def test_validation_result_propagation(self, integrated_system, qtbot):
        """Test that validation results propagate through the system."""
        validation_service = integrated_system['validation_service']
        table_state_manager = integrated_system['table_state_manager']
        data_view_model = integrated_system['data_view_model']
        
        # Create validation results
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.INVALID],
            'Chest_status': [ValidationStatus.CORRECTABLE, ValidationStatus.VALID]
        })
        
        # Monitor cell states changed signal
        state_changed_spy = qtbot.createSignalSpy(table_state_manager.cell_states_changed)
        model_changed_spy = qtbot.createSignalSpy(data_view_model.dataChanged)
        
        # Emit validation complete
        validation_service.validation_complete.emit(validation_df)
        
        # Verify signals were emitted
        assert state_changed_spy.count() == 1
        assert model_changed_spy.count() >= 1
        
        # Verify cell states were updated
        assert table_state_manager.get_cell_state(0, 0) == ValidationStatus.VALID
        assert table_state_manager.get_cell_state(0, 1) == ValidationStatus.CORRECTABLE
        assert table_state_manager.get_cell_state(1, 0) == ValidationStatus.INVALID
        assert table_state_manager.get_cell_state(1, 1) == ValidationStatus.VALID
        
    def test_validation_rendering(self, integrated_system, qtbot, mocker):
        """Test that validation states affect cell rendering."""
        validation_service = integrated_system['validation_service']
        data_table_view = integrated_system['data_table_view']
        
        # Create validation results
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.INVALID],
            'Chest_status': [ValidationStatus.CORRECTABLE, ValidationStatus.VALID]
        })
        
        # Spy on the paint method of the delegate
        delegate = data_table_view.itemDelegate()
        paint_spy = mocker.spy(delegate, 'paint')
        
        # Emit validation complete
        validation_service.validation_complete.emit(validation_df)
        
        # Force repaint
        data_table_view.viewport().update()
        qtbot.wait(100)  # Give time for paint events
        
        # Verify paint was called
        assert paint_spy.call_count > 0
        
        # For proper verification, we'd need to check the rendering result
        # This is difficult to do directly, but we can check delegate behavior
        # in the unit tests and trust that the integration works if signals
        # are connected correctly
```

### Correction Integration Tests

These tests verify that correction suggestions correctly propagate through the system and affect cell rendering and correction actions.

```python
# test_correction_integration.py

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest

class TestCorrectionIntegration:
    """Tests for correction system integration."""
    
    def test_correction_suggestion_propagation(self, integrated_system, qtbot):
        """Test that correction suggestions propagate through the system."""
        correction_service = integrated_system['correction_service']
        table_state_manager = integrated_system['table_state_manager']
        
        # Create correction suggestions
        corrections = {
            (2, 0): [{"original": "JohnSmiht", "corrected": "John Smith"}],
            (2, 2): [{"original": "siver", "corrected": "Silver"}]
        }
        
        # Monitor cell states changed signal
        state_changed_spy = qtbot.createSignalSpy(table_state_manager.cell_states_changed)
        
        # Emit correction available
        correction_service.correction_available.emit(corrections)
        
        # Verify signal was emitted
        assert state_changed_spy.count() == 1
        
        # Verify cell states were updated (CORRECTABLE state)
        # The exact representation depends on implementation
        assert table_state_manager.get_cell_correction_status(2, 0) is not None
        assert table_state_manager.get_cell_correction_status(2, 2) is not None
        
    def test_correction_application(self, integrated_system, qtbot):
        """Test applying a correction through UI."""
        correction_service = integrated_system['correction_service']
        data_model = integrated_system['data_model']
        data_table_view = integrated_system['data_table_view']
        
        # Create correction suggestions
        corrections = {
            (2, 0): [{"original": "JohnSmiht", "corrected": "John Smith"}]
        }
        
        # Emit correction available
        correction_service.correction_available.emit(corrections)
        
        # Get the current value
        original_value = data_model.data(data_model.index(2, 0), Qt.DisplayRole)
        assert original_value == "JohnSmiht"
        
        # Simulate correction application
        # This depends on the exact UI implementation
        # Here we directly call the correction service
        correction_service.apply_correction(2, 0, corrections[(2, 0)][0])
        
        # Verify the value was corrected
        corrected_value = data_model.data(data_model.index(2, 0), Qt.DisplayRole)
        assert corrected_value == "John Smith"
```

### Context Menu Integration Tests

These tests verify that context menus are correctly generated based on selection and cell state, and that menu actions correctly affect the system.

```python
# test_context_menu_integration.py

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMenu

class TestContextMenuIntegration:
    """Tests for context menu integration."""
    
    def test_context_menu_generation(self, integrated_system, qtbot, monkeypatch):
        """Test context menu generation based on selection."""
        data_table_view = integrated_system['data_table_view']
        
        # Monkeypatch QMenu.exec to prevent actual menu display
        monkeypatch.setattr(QMenu, 'exec', lambda self, *args: None)
        
        # Spy on the context menu method
        context_menu_spy = qtbot.createSignalSpy(data_table_view.customContextMenuRequested)
        
        # Select a cell
        view_index = data_table_view.model().index(1, 1)
        data_table_view.setCurrentIndex(view_index)
        
        # Simulate right-click
        right_click_pos = data_table_view.visualRect(view_index).center()
        QTest.mouseClick(data_table_view.viewport(), Qt.RightButton, pos=right_click_pos)
        
        # Verify context menu signal was emitted
        assert context_menu_spy.count() == 1
        
        # For full testing, we'd need to check the menu content and actions
        # This depends on the specific implementation of the context menu system
        
    def test_copy_action(self, integrated_system, qtbot, monkeypatch, mocker):
        """Test copy action from context menu."""
        data_table_view = integrated_system['data_table_view']
        data_model = integrated_system['data_model']
        
        # Mock clipboard
        mock_clipboard = mocker.MagicMock()
        monkeypatch.setattr(data_table_view, 'clipboard', mock_clipboard)
        
        # Select a cell with known value
        row, col = 0, 0
        test_value = data_model.data(data_model.index(row, col), Qt.DisplayRole)
        data_table_view.setCurrentIndex(data_table_view.model().index(row, col))
        
        # Find copy action in the view
        copy_action = None
        for action in data_table_view.actions():
            if action.text() == "Copy":
                copy_action = action
                break
                
        assert copy_action is not None, "Copy action not found in view actions"
        
        # Trigger copy action
        copy_action.trigger()
        
        # Verify clipboard was set with the correct value
        # The exact format depends on implementation
        mock_clipboard.setText.assert_called_once()
        assert test_value in str(mock_clipboard.setText.call_args)
```

### End-to-End Workflow Tests

These tests verify complete user workflows that span multiple components.

```python
# test_end_to_end_workflows.py

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
import pandas as pd
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestEndToEndWorkflows:
    """Tests for end-to-end user workflows."""
    
    def test_validation_correction_workflow(self, integrated_system, qtbot, monkeypatch):
        """Test the complete workflow of validation and correction."""
        validation_service = integrated_system['validation_service']
        correction_service = integrated_system['correction_service']
        data_model = integrated_system['data_model']
        data_table_view = integrated_system['data_table_view']
        
        # 1. Initial data state
        original_value = data_model.data(data_model.index(2, 0), Qt.DisplayRole)
        assert original_value == "JohnSmiht"
        
        # 2. Run validation
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                             ValidationStatus.CORRECTABLE, ValidationStatus.VALID, 
                             ValidationStatus.VALID],
            'Chest_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID],
            'Score_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.INVALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID],
            'Date_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                           ValidationStatus.INVALID, ValidationStatus.VALID, 
                           ValidationStatus.VALID]
        })
        
        validation_service.validation_complete.emit(validation_df)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # 3. Generate correction suggestions
        corrections = {
            (2, 0): [{"original": "JohnSmiht", "corrected": "John Smith"}]
        }
        
        correction_service.correction_available.emit(corrections)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # 4. Apply correction
        correction_service.apply_correction(2, 0, corrections[(2, 0)][0])
        qtbot.wait(100)  # Wait for changes to apply
        
        # 5. Verify corrected state
        corrected_value = data_model.data(data_model.index(2, 0), Qt.DisplayRole)
        assert corrected_value == "John Smith"
        
        # 6. Run validation again
        validation_df_after = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                             ValidationStatus.VALID, ValidationStatus.VALID, 
                             ValidationStatus.VALID],
            'Chest_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID],
            'Score_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                            ValidationStatus.INVALID, ValidationStatus.VALID, 
                            ValidationStatus.VALID],
            'Date_status': [ValidationStatus.VALID, ValidationStatus.VALID, 
                           ValidationStatus.INVALID, ValidationStatus.VALID, 
                           ValidationStatus.VALID]
        })
        
        validation_service.validation_complete.emit(validation_df_after)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # 7. Verify the cell is now valid
        # This depends on how validation status is accessed from the view
        cell_state = integrated_system['table_state_manager'].get_cell_state(2, 0)
        assert cell_state == ValidationStatus.VALID
    
    def test_import_validation_workflow(self, integrated_system, qtbot, monkeypatch):
        """Test the workflow of importing data and validating it."""
        data_model = integrated_system['data_model']
        validation_service = integrated_system['validation_service']
        
        # 1. Initial row count
        initial_row_count = data_model.rowCount()
        
        # 2. Import new data
        new_data = pd.DataFrame({
            'Player': ['NewPlayer1', 'NewPlayer2'],
            'Chest': ['Gold', 'InvalidChest'],
            'Score': [100, 'abc'],
            'Date': ['2023-01-01', '2023-13-45']
        })
        
        data_model.update_data(new_data)
        qtbot.wait(100)  # Wait for model update
        
        # 3. Verify row count changed
        assert data_model.rowCount() == 2  # New data replaced old
        
        # 4. Run validation
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.VALID],
            'Chest_status': [ValidationStatus.VALID, ValidationStatus.INVALID],
            'Score_status': [ValidationStatus.VALID, ValidationStatus.INVALID],
            'Date_status': [ValidationStatus.VALID, ValidationStatus.INVALID]
        })
        
        validation_service.validation_complete.emit(validation_df)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # 5. Verify invalid cells are marked
        cell_states = integrated_system['table_state_manager']
        assert cell_states.get_cell_state(1, 1) == ValidationStatus.INVALID  # Chest
        assert cell_states.get_cell_state(1, 2) == ValidationStatus.INVALID  # Score
        assert cell_states.get_cell_state(1, 3) == ValidationStatus.INVALID  # Date
```

## Performance and Stress Testing

Integration tests will also include performance and stress tests to verify that the system performs well under load:

```python
# test_performance_integration.py

import pytest
import time
import pandas as pd
import numpy as np
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestPerformanceIntegration:
    """Performance and stress tests for the integrated system."""
    
    def test_large_dataset_rendering(self, integrated_system, qtbot):
        """Test rendering performance with large datasets."""
        data_model = integrated_system['data_model']
        data_table_view = integrated_system['data_table_view']
        
        # Create large dataset
        rows = 10000
        large_data = pd.DataFrame({
            'Player': [f'Player{i}' for i in range(rows)],
            'Chest': [f'Chest{i % 5}' for i in range(rows)],
            'Score': np.random.randint(1, 1000, rows),
            'Date': [f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}' for i in range(rows)]
        })
        
        # Measure time to update model
        start_time = time.time()
        data_model.update_data(large_data)
        model_update_time = time.time() - start_time
        
        # Give UI time to update
        qtbot.wait(500)
        
        # Measure scrolling performance
        start_time = time.time()
        for i in range(0, 1000, 100):
            data_table_view.scrollTo(data_table_view.model().index(i, 0))
            qtbot.wait(10)  # Small delay to simulate user scrolling
        scroll_time = time.time() - start_time
        
        # Assertions depend on performance targets
        # These are example thresholds and should be adjusted based on
        # actual performance requirements and testing environment
        assert model_update_time < 5.0, f"Model update took {model_update_time:.2f}s"
        assert scroll_time < 2.0, f"Scrolling took {scroll_time:.2f}s"
    
    def test_large_validation_performance(self, integrated_system, qtbot):
        """Test validation performance with large datasets."""
        data_model = integrated_system['data_model']
        validation_service = integrated_system['validation_service']
        table_state_manager = integrated_system['table_state_manager']
        
        # Create large dataset
        rows = 10000
        large_data = pd.DataFrame({
            'Player': [f'Player{i}' for i in range(rows)],
            'Chest': [f'Chest{i % 5}' for i in range(rows)],
            'Score': np.random.randint(1, 1000, rows),
            'Date': [f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}' for i in range(rows)]
        })
        
        # Update model
        data_model.update_data(large_data)
        qtbot.wait(500)  # Give UI time to update
        
        # Create large validation results
        # Add some invalid cells randomly
        validation_data = {}
        for col in ['Player', 'Chest', 'Score', 'Date']:
            col_status = [ValidationStatus.VALID] * rows
            # Make ~5% invalid
            invalid_indices = np.random.choice(rows, size=rows//20)
            for idx in invalid_indices:
                col_status[idx] = ValidationStatus.INVALID
            validation_data[f'{col}_status'] = col_status
        
        validation_df = pd.DataFrame(validation_data)
        
        # Measure time to process validation results
        start_time = time.time()
        validation_service.validation_complete.emit(validation_df)
        qtbot.wait(500)  # Give time for signals to propagate
        validation_time = time.time() - start_time
        
        # Count updated cells
        invalid_count = sum(1 for row in range(rows) for col in range(4)
                          if table_state_manager.get_cell_state(row, col) == ValidationStatus.INVALID)
        
        # Assertion depends on performance targets
        assert validation_time < 10.0, f"Validation took {validation_time:.2f}s"
        assert invalid_count > 0, "No invalid cells found"
```

## Edge Case Testing

Integration tests will also cover edge cases that might occur during component interactions:

```python
# test_edge_cases_integration.py

import pytest
import pandas as pd
import numpy as np
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestEdgeCasesIntegration:
    """Tests for edge cases in component integration."""
    
    def test_empty_dataset(self, integrated_system, qtbot):
        """Test behavior with empty dataset."""
        data_model = integrated_system['data_model']
        data_table_view = integrated_system['data_table_view']
        
        # Update with empty data
        empty_data = pd.DataFrame()
        data_model.update_data(empty_data)
        qtbot.wait(100)  # Wait for model update
        
        # Verify view handles empty data properly
        assert data_table_view.model().rowCount() == 0
        assert data_table_view.model().columnCount() == 0
        
    def test_mismatched_validation_results(self, integrated_system, qtbot):
        """Test behavior when validation results don't match data."""
        data_model = integrated_system['data_model']
        validation_service = integrated_system['validation_service']
        
        # Set up data
        test_data = pd.DataFrame({
            'Player': ['Player1', 'Player2'],
            'Chest': ['Gold', 'Silver']
        })
        
        data_model.update_data(test_data)
        qtbot.wait(100)  # Wait for model update
        
        # Create validation results with more rows
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.VALID, ValidationStatus.INVALID],
            'Chest_status': [ValidationStatus.VALID, ValidationStatus.VALID, ValidationStatus.INVALID]
        })
        
        # This should not crash the system
        validation_service.validation_complete.emit(validation_df)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # Create validation results with more columns
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.VALID],
            'Chest_status': [ValidationStatus.VALID, ValidationStatus.VALID],
            'Extra_status': [ValidationStatus.INVALID, ValidationStatus.INVALID]
        })
        
        # This should not crash the system
        validation_service.validation_complete.emit(validation_df)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # The test passes if no exceptions are raised
        
    def test_concurrent_operations(self, integrated_system, qtbot):
        """Test behavior with concurrent validation and correction."""
        validation_service = integrated_system['validation_service']
        correction_service = integrated_system['correction_service']
        
        # Emit validation and correction signals in quick succession
        validation_df = pd.DataFrame({
            'Player_status': [ValidationStatus.VALID, ValidationStatus.CORRECTABLE],
            'Chest_status': [ValidationStatus.INVALID, ValidationStatus.VALID]
        })
        
        corrections = {
            (0, 1): [{"original": "Gold", "corrected": "Golden"}]
        }
        
        # Emit both signals
        validation_service.validation_complete.emit(validation_df)
        correction_service.correction_available.emit(corrections)
        qtbot.wait(100)  # Wait for signals to propagate
        
        # The test passes if no race conditions or exceptions occur
```

## Test Reporting and Metrics

Integration test results will be reported with:

1. **Test Coverage**: How much of the integration points are covered.
2. **Test Success Rate**: Percentage of passing tests.
3. **Performance Metrics**: Timing data from performance tests.
4. **Issue Categorization**: Classification of any issues found.

## Integration with CI/CD

Integration tests will be included in the CI/CD pipeline:

1. **Nightly Runs**: Full integration test suite run nightly.
2. **Selective Tests**: Critical integration tests run on each commit.
3. **Performance Tests**: Performance tests run on scheduled basis.

## Best Practices

### Writing Robust Integration Tests

1. **Manage Test State**: Ensure each test starts with a clean environment.
2. **Handle Asynchronous Operations**: Use appropriate waiting mechanisms for signal propagation.
3. **Test Real Components**: Use real components where possible rather than mocks.
4. **Isolate Test Cases**: Make tests independent of each other.

### Debugging Integration Issues

1. **Logging**: Add detailed logging to track component interactions.
2. **Signal Tracing**: Use signal spy to verify signal emissions.
3. **State Inspection**: Check component state at each step of the test.
4. **Divide and Conquer**: Break complex tests into smaller, more focused tests.

## Conclusion

This integration testing strategy provides a comprehensive approach to verifying the correct interaction between components of the refactored DataView. By focusing on component boundaries, workflows, and edge cases, the strategy ensures that the system works correctly as a whole, even when individual components pass their unit tests.

The integration tests serve as an important safety net for refactoring, helping to catch issues that might arise from changes to component interactions while allowing flexibility in the implementation of individual components. 