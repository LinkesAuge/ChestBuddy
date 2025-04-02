# DataView Refactoring - Unit Testing Strategy

## Overview

This document outlines the unit testing strategy for the DataView refactoring project. Following a test-driven development (TDD) approach, unit tests will be written before implementing the features. The goal is to achieve at least 95% code coverage across all components of the refactored DataView.

## Test-Driven Development Approach

The development process will follow these TDD steps:

1. **Write Tests First**: Before implementing any feature, write tests that define the expected behavior.
2. **Run Tests (Watch Them Fail)**: Ensure the tests fail initially, confirming they're testing something meaningful.
3. **Implement Minimal Code**: Write just enough code to make the tests pass.
4. **Run Tests Again**: Verify the implementation meets the requirements.
5. **Refactor**: Clean up the code while keeping tests passing.
6. **Repeat**: Continue this cycle for each feature or component.

## Testing Framework and Tools

The testing will utilize the following tools:

- **pytest**: Core testing framework
- **pytest-cov**: For measuring test coverage
- **pytest-qt**: For testing Qt GUI components
- **pytest-mock**: For mocking dependencies
- **pytest-xvfb**: For headless GUI testing

## Test Directory Structure

The test directory structure will mirror the implementation structure:

```
tests/ui/data/
├── __init__.py
├── conftest.py                      # Common fixtures and utilities
├── models/
│   ├── __init__.py
│   ├── test_data_view_model.py
│   ├── test_selection_model.py
│   ├── test_filter_model.py
│   └── test_sort_model.py
├── views/
│   ├── __init__.py
│   ├── test_data_table_view.py
│   └── test_data_header_view.py
├── delegates/
│   ├── __init__.py
│   ├── test_cell_display_delegate.py
│   └── test_cell_edit_delegate.py
├── menus/
│   ├── __init__.py
│   ├── test_data_context_menu.py
│   └── test_menu_factory.py
├── adapters/
│   ├── __init__.py
│   ├── test_validation_adapter.py
│   └── test_correction_adapter.py
└── utils/
    ├── __init__.py
    ├── test_cell_state_utils.py
    └── test_selection_utils.py
```

## Common Test Fixtures

The `conftest.py` file will contain common fixtures needed across multiple test files:

```python
# conftest.py
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    
@pytest.fixture
def mock_chest_data_model(mocker):
    """Create a mock ChestDataModel for testing."""
    model = mocker.MagicMock()
    # Setup default behavior
    model.data.return_value = "test_data"
    model.rowCount.return_value = 10
    model.columnCount.return_value = 5
    return model

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame({
        'A': ['A1', 'A2', 'A3', 'A4', 'A5'],
        'B': ['B1', 'B2', 'B3', 'B4', 'B5'],
        'C': [1, 2, 3, 4, 5],
        'D': [10.1, 20.2, 30.3, 40.4, 50.5],
        'E': [True, False, True, False, True]
    })
    return df

@pytest.fixture
def mock_validation_service(mocker):
    """Create a mock ValidationService for testing."""
    service = mocker.MagicMock()
    return service

@pytest.fixture
def mock_correction_service(mocker):
    """Create a mock CorrectionService for testing."""
    service = mocker.MagicMock()
    return service
```

## Test Categories

### Model Tests

Tests for model components will focus on:

1. **Data Access**: Verify data is correctly retrieved from the underlying model.
2. **Data Transformation**: Test data transformation and formatting.
3. **Sorting and Filtering**: Validate sorting and filtering functionality.
4. **Selection Handling**: Test selection state management.
5. **Signal Emission**: Verify signals are emitted correctly.

Example test structure for `DataViewModel`:

```python
# test_data_view_model.py
import pytest
from PySide6.QtCore import Qt, QModelIndex
from chestbuddy.ui.data.models.data_view_model import DataViewModel

class TestDataViewModel:
    """Tests for the DataViewModel class."""
    
    def test_initialization(self, mock_chest_data_model):
        """Test that the DataViewModel initializes correctly."""
        model = DataViewModel(mock_chest_data_model)
        assert model.source_model() == mock_chest_data_model
        
    def test_row_count(self, mock_chest_data_model):
        """Test rowCount returns the correct number of rows."""
        model = DataViewModel(mock_chest_data_model)
        assert model.rowCount() == mock_chest_data_model.rowCount()
        
    def test_column_count(self, mock_chest_data_model):
        """Test columnCount returns the correct number of columns."""
        model = DataViewModel(mock_chest_data_model)
        assert model.columnCount() == mock_chest_data_model.columnCount()
        
    def test_data_for_display_role(self, mock_chest_data_model):
        """Test data returns the correct value for DisplayRole."""
        model = DataViewModel(mock_chest_data_model)
        index = model.index(0, 0)
        assert model.data(index, Qt.DisplayRole) == "test_data"
        
    def test_data_for_validation_state_role(self, mock_chest_data_model, mocker):
        """Test data returns the correct validation state."""
        mock_table_state_manager = mocker.MagicMock()
        mock_table_state_manager.get_cell_state.return_value = "INVALID"
        
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        
        index = model.index(0, 0)
        assert model.data(index, DataViewModel.ValidationStateRole) == "INVALID"
```

### View Tests

Tests for view components will focus on:

1. **Rendering**: Verify cells are rendered correctly.
2. **User Interaction**: Test mouse and keyboard interaction.
3. **Selection Behavior**: Validate selection handling.
4. **Scrolling**: Test scrolling behavior.
5. **Signal Handling**: Verify signal connections.

Example test structure for `DataTableView`:

```python
# test_data_table_view.py
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from chestbuddy.ui.data.views.data_table_view import DataTableView

class TestDataTableView:
    """Tests for the DataTableView class."""
    
    def test_initialization(self, qapp, mock_chest_data_model):
        """Test that the DataTableView initializes correctly."""
        model = DataViewModel(mock_chest_data_model)
        view = DataTableView()
        view.setModel(model)
        
        assert view.model() == model
        
    def test_cell_click(self, qapp, mock_chest_data_model, mocker):
        """Test that clicking a cell emits the correct signal."""
        model = DataViewModel(mock_chest_data_model)
        view = DataTableView()
        view.setModel(model)
        
        # Mock the signal handler
        mock_handler = mocker.Mock()
        view.cell_clicked.connect(mock_handler)
        
        # Click on a cell
        cell_rect = view.visualRect(model.index(1, 1))
        QTest.mouseClick(view.viewport(), Qt.LeftButton, 
                         pos=cell_rect.center())
        
        # Check the signal was emitted with correct parameters
        mock_handler.assert_called_once()
        args = mock_handler.call_args[0]
        assert args[0] == 1  # row
        assert args[1] == 1  # column
```

### Delegate Tests

Tests for delegate components will focus on:

1. **Rendering**: Verify different cell states are rendered correctly.
2. **Editing**: Test cell editing behavior.
3. **State Handling**: Validate state representation.
4. **Event Handling**: Test event processing.

Example test structure for `CellDisplayDelegate`:

```python
# test_cell_display_delegate.py
import pytest
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPixmap
from chestbuddy.ui.data.delegates.cell_display_delegate import CellDisplayDelegate
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestCellDisplayDelegate:
    """Tests for the CellDisplayDelegate class."""
    
    def test_initialization(self):
        """Test that the CellDisplayDelegate initializes correctly."""
        delegate = CellDisplayDelegate()
        assert delegate is not None
        
    def test_paint_valid_cell(self, qapp, mocker):
        """Test painting a valid cell."""
        delegate = CellDisplayDelegate()
        
        # Create mock objects
        painter = mocker.MagicMock(spec=QPainter)
        option = mocker.MagicMock()
        option.rect = QRect(0, 0, 100, 30)
        index = mocker.MagicMock()
        
        # Configure index to return VALID validation state
        index.data.return_value = ValidationStatus.VALID
        
        # Call paint method
        delegate.paint(painter, option, index)
        
        # Verify background color was not changed
        painter.fillRect.assert_not_called()
        
    def test_paint_invalid_cell(self, qapp, mocker):
        """Test painting an invalid cell."""
        delegate = CellDisplayDelegate()
        
        # Create mock objects
        painter = mocker.MagicMock(spec=QPainter)
        option = mocker.MagicMock()
        option.rect = QRect(0, 0, 100, 30)
        index = mocker.MagicMock()
        
        # Configure index to return INVALID validation state
        index.data.return_value = ValidationStatus.INVALID
        
        # Call paint method
        delegate.paint(painter, option, index)
        
        # Verify background color was changed to red
        painter.fillRect.assert_called_once()
        # Check that the color argument was red
        args = painter.fillRect.call_args[0]
        assert args[1].name() == "#ffb6b6"  # light red
```

### Context Menu Tests

Tests for menu components will focus on:

1. **Menu Structure**: Verify menu items are created correctly.
2. **Action Triggering**: Test action execution.
3. **Dynamic Content**: Validate context-sensitive content generation.
4. **Signal Connections**: Test signals from actions.

Example test structure for `DataContextMenu`:

```python
# test_data_context_menu.py
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu
from chestbuddy.ui.data.menus.data_context_menu import DataContextMenu

class TestDataContextMenu:
    """Tests for the DataContextMenu class."""
    
    def test_initialization(self, qapp):
        """Test that the DataContextMenu initializes correctly."""
        menu = DataContextMenu()
        assert isinstance(menu, QMenu)
        
    def test_menu_for_single_selection(self, qapp, mocker):
        """Test menu structure for single cell selection."""
        menu = DataContextMenu()
        cell_indexes = [(0, 0)]  # Single cell at row 0, col 0
        
        # Mock selection info
        selection_info = mocker.MagicMock()
        selection_info.get_selected_cells.return_value = cell_indexes
        
        # Create menu for this selection
        menu.build_for_selection(selection_info)
        
        # Verify standard actions are present
        assert menu.actions()[0].text() == "Copy"
        assert menu.actions()[1].text() == "Paste"
        assert menu.actions()[2].text() == "Cut"
        assert menu.actions()[3].text() == "Delete"
        
    def test_menu_for_invalid_cell(self, qapp, mocker):
        """Test menu structure for invalid cell."""
        menu = DataContextMenu()
        cell_indexes = [(0, 0)]  # Single cell at row 0, col 0
        
        # Mock selection info
        selection_info = mocker.MagicMock()
        selection_info.get_selected_cells.return_value = cell_indexes
        
        # Mock validation state
        validation_state = mocker.MagicMock()
        validation_state.get_cell_validation_status.return_value = ValidationStatus.INVALID
        
        # Create menu with validation state
        menu.build_for_selection(selection_info, validation_state)
        
        # Find validation error action
        validation_actions = [a for a in menu.actions() 
                              if a.text() == "View Validation Error"]
        assert len(validation_actions) == 1
```

### Adapter Tests

Tests for adapter components will focus on:

1. **Data Conversion**: Verify correct data transformation.
2. **Signal Propagation**: Test signal forwarding.
3. **State Mapping**: Validate state transformation.
4. **Error Handling**: Test error cases.

Example test structure for `ValidationAdapter`:

```python
# test_validation_adapter.py
import pytest
import pandas as pd
from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestValidationAdapter:
    """Tests for the ValidationAdapter class."""
    
    def test_initialization(self, mock_validation_service):
        """Test that the ValidationAdapter initializes correctly."""
        adapter = ValidationAdapter(mock_validation_service)
        assert adapter.validation_service == mock_validation_service
        
    def test_on_validation_complete(self, mock_validation_service, mocker):
        """Test handling of validation results."""
        adapter = ValidationAdapter(mock_validation_service)
        
        # Create mock validation results
        validation_df = pd.DataFrame({
            'A_status': [ValidationStatus.VALID, ValidationStatus.INVALID],
            'B_status': [ValidationStatus.CORRECTABLE, ValidationStatus.VALID]
        })
        
        # Mock the signal handler
        mock_handler = mocker.Mock()
        adapter.validation_state_changed.connect(mock_handler)
        
        # Emit validation complete
        adapter.on_validation_complete(validation_df)
        
        # Check the signal was emitted
        mock_handler.assert_called_once()
        
        # Check the validation state is correct
        validation_state = adapter.get_validation_state()
        assert validation_state.get_cell_validation_status(0, 0) == ValidationStatus.VALID
        assert validation_state.get_cell_validation_status(0, 1) == ValidationStatus.CORRECTABLE
        assert validation_state.get_cell_validation_status(1, 0) == ValidationStatus.INVALID
        assert validation_state.get_cell_validation_status(1, 1) == ValidationStatus.VALID
```

### Utils Tests

Tests for utility functions will focus on:

1. **Functionality**: Verify correct behavior.
2. **Edge Cases**: Test boundary conditions.
3. **Error Handling**: Validate error responses.
4. **Performance**: Test with large inputs.

Example test structure for cell state utilities:

```python
# test_cell_state_utils.py
import pytest
from chestbuddy.ui.data.utils.cell_state_utils import map_validation_status_to_color
from chestbuddy.core.enums.validation_enums import ValidationStatus
from PySide6.QtGui import QColor

class TestCellStateUtils:
    """Tests for the cell state utilities."""
    
    def test_map_validation_status_to_color_valid(self):
        """Test mapping VALID status to color."""
        color = map_validation_status_to_color(ValidationStatus.VALID)
        assert color == QColor("#ffffff")  # white
        
    def test_map_validation_status_to_color_invalid(self):
        """Test mapping INVALID status to color."""
        color = map_validation_status_to_color(ValidationStatus.INVALID)
        assert color == QColor("#ffb6b6")  # light red
        
    def test_map_validation_status_to_color_correctable(self):
        """Test mapping CORRECTABLE status to color."""
        color = map_validation_status_to_color(ValidationStatus.CORRECTABLE)
        assert color == QColor("#fff3b6")  # light yellow
        
    def test_map_validation_status_to_color_unknown(self):
        """Test mapping unknown status to color."""
        color = map_validation_status_to_color("UNKNOWN")
        assert color == QColor("#ffffff")  # default to white
```

## Code Coverage Strategy

To achieve the 95% test coverage goal:

1. **Use Coverage Reports**: Run pytest with coverage reports to identify untested code.
   ```bash
   pytest --cov=chestbuddy.ui.data tests/ui/data/ --cov-report=html
   ```

2. **Target Critical Components First**: Prioritize testing of core functionality:
   - Data model and view classes
   - Cell rendering delegates
   - State management components

3. **Test All Code Paths**: Ensure tests cover:
   - Normal execution paths
   - Error handling paths
   - Edge cases
   - Boundary conditions

4. **Coverage Thresholds**: Configure pytest to fail if coverage drops below the target:
   ```bash
   pytest --cov=chestbuddy.ui.data tests/ui/data/ --cov-fail-under=95
   ```

5. **Incremental Improvement**: Track coverage metrics throughout development:
   - Start with core components
   - Add tests for missing coverage
   - Review and improve test quality

## Test Data Management

Test data will be managed through:

1. **Fixtures**: Reusable test data defined in pytest fixtures.
2. **Factory Methods**: Methods that generate test data with specific properties.
3. **Test Datasets**: Small, representative datasets for comprehensive testing.

Example test data factory:

```python
def create_test_validation_results(rows=5, columns=5):
    """Create test validation results DataFrame with various statuses."""
    import pandas as pd
    from chestbuddy.core.enums.validation_enums import ValidationStatus
    
    # Create column names with _status suffix
    columns = [f"Col{i}_status" for i in range(columns)]
    
    # Create data with mixed validation statuses
    data = []
    status_options = [ValidationStatus.VALID, ValidationStatus.INVALID, 
                      ValidationStatus.CORRECTABLE]
    
    for _ in range(rows):
        row = [status_options[i % len(status_options)] for i in range(len(columns))]
        data.append(row)
    
    return pd.DataFrame(data, columns=columns)
```

## Testing Qt UI Components

Testing Qt UI components requires special consideration:

1. **Use pytest-qt**: Leverage the pytest-qt plugin for interacting with Qt widgets.
2. **Mock Qt Components**: Use mocker to mock complex Qt components.
3. **Test Event Handling**: Use QTest to simulate user interactions.
4. **Visual Testing**: Consider screenshot-based testing for visual elements.

Example of a Qt UI test:

```python
def test_dataview_keyboard_navigation(qtbot, mock_chest_data_model):
    """Test keyboard navigation in DataTableView."""
    model = DataViewModel(mock_chest_data_model)
    view = DataTableView()
    view.setModel(model)
    
    # Add view to qtbot for event handling
    qtbot.addWidget(view)
    
    # Select first cell
    view.setCurrentIndex(model.index(0, 0))
    assert view.currentIndex().row() == 0
    assert view.currentIndex().column() == 0
    
    # Press down arrow to move to row 1
    qtbot.keyClick(view, Qt.Key_Down)
    assert view.currentIndex().row() == 1
    assert view.currentIndex().column() == 0
    
    # Press right arrow to move to column 1
    qtbot.keyClick(view, Qt.Key_Right)
    assert view.currentIndex().row() == 1
    assert view.currentIndex().column() == 1
```

## Mocking and Dependency Isolation

To isolate components during testing:

1. **Use pytest-mock**: Mock dependencies to isolate the component under test.
2. **Create Interface Adapters**: Use adapter classes that can be easily mocked.
3. **Use Dependency Injection**: Constructor injection for better testability.

Example of mocking dependencies:

```python
def test_data_view_model_with_mocked_dependencies(mocker):
    """Test DataViewModel with mocked dependencies."""
    # Mock ChestDataModel
    mock_data_model = mocker.MagicMock()
    mock_data_model.rowCount.return_value = 10
    mock_data_model.columnCount.return_value = 5
    mock_data_model.data.return_value = "test_data"
    
    # Mock TableStateManager
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.get_cell_state.return_value = "NORMAL"
    
    # Create DataViewModel with mocked dependencies
    model = DataViewModel(data_model=mock_data_model)
    model.set_table_state_manager(mock_state_manager)
    
    # Test interaction with mocked dependencies
    assert model.rowCount() == 10
    assert model.columnCount() == 5
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "test_data"
    
    # Verify interaction with mock
    mock_state_manager.get_cell_state.assert_called_with(0, 0)
```

## Test Execution and Continuous Integration

Tests will be integrated into the continuous integration (CI) workflow:

1. **Automated Testing**: Tests run automatically on each commit.
2. **Coverage Reporting**: Coverage reports generated and tracked.
3. **Test Results Reporting**: Test results reported and visualized.
4. **Pre-commit Hooks**: Run critical tests before allowing commits.

CI configuration will include:

```yaml
# Example GitHub Actions workflow
name: Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        
    - name: Install Qt dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
        
    - name: Run tests with coverage
      run: |
        xvfb-run --auto-servernum pytest tests/ui/data/ --cov=chestbuddy.ui.data --cov-report=xml --cov-fail-under=95
        
    - name: Upload coverage report
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

## Best Practices

### Writing Maintainable Tests

1. **Follow AAA Pattern**:
   - Arrange: Set up test environment and data
   - Act: Execute the code under test
   - Assert: Verify the results

2. **One Assertion Per Test**: Focus on testing one aspect per test method.

3. **Descriptive Test Names**: Name tests to describe what they're testing.

4. **Avoid Test Interdependence**: Tests should be independent of each other.

### Testing for Future Changes

1. **Black Box Testing**: Test behavior, not implementation details.

2. **Parameterized Tests**: Use pytest's parameterization for multiple test cases.

3. **Test Boundary Conditions**: Test at and around boundary values.

4. **Refactoring Safety Net**: Tests should enable safe refactoring.

## Conclusion

This unit testing strategy provides a comprehensive approach to testing the refactored DataView component. By following test-driven development principles and targeting 95% code coverage, the strategy ensures high-quality, maintainable code that meets the requirements. The tests will serve as both a specification and a safety net for future changes and enhancements. 