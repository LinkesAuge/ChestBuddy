"""
Tests for the DataViewController class.

This module contains tests for the DataViewController class, which manages data view
operations in the ChestBuddy application.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QCheckBox, QLabel, QTableView

from chestbuddy.core.controllers.data_view_controller import DataViewController


class MockDataModel(QObject):
    """Mock data model for testing."""

    data_changed = Signal()
    data_cleared = Signal()

    def __init__(self, with_data=True):
        """Initialize the mock data model."""
        super().__init__()
        self.is_empty = not with_data
        if with_data:
            data = {
                "Player Name": ["Player1", "Player2", "Player3"],
                "Value": [100, 200, 300],
                "Team": ["Team1", "Team2", "Team3"],
            }
            self.data = pd.DataFrame(data)
            self.column_names = list(data.keys())
        else:
            self.data = pd.DataFrame()
            self.column_names = []
        self.data_hash = "test_hash" if with_data else ""
        self.filtered_data = None

    def filter_data(self, column, value, mode, case_sensitive):
        """Mock filter_data method."""
        if column not in self.column_names:
            return None

        if not value:
            self.filtered_data = self.data
        else:
            if mode == "Contains":
                if case_sensitive:
                    self.filtered_data = self.data[self.data[column].str.contains(value)]
                else:
                    self.filtered_data = self.data[
                        self.data[column].str.contains(value, case=False)
                    ]
            elif mode == "Equals":
                if case_sensitive:
                    self.filtered_data = self.data[self.data[column] == value]
                else:
                    self.filtered_data = self.data[self.data[column].str.lower() == value.lower()]

        return self.filtered_data


class MockDataView(QWidget):
    """Mock data view for testing."""

    def __init__(self):
        """Initialize mock view."""
        super().__init__()
        self._filter_column = QComboBox()
        self._filter_column.addItems(["Player Name", "Date", "Quantity"])
        self._filter_text = QLineEdit()
        self._filter_mode = QComboBox()
        self._filter_mode.addItems(["Contains", "Equals", "Starts with", "Ends with"])
        self._case_sensitive = QCheckBox()
        self._status_label = QLabel()
        self._table_view = MagicMock()

        # Toolbar mocks
        self._action_toolbar = MagicMock()
        apply_filter_button = MagicMock()
        clear_filter_button = MagicMock()
        self._action_toolbar.get_button_by_name.side_effect = lambda name: {
            "apply_filter": apply_filter_button,
            "clear_filter": clear_filter_button,
        }.get(name)

        # Track method calls
        self.updated = False
        self.filtered_data = None
        self.populated = False
        self.refreshed = False

    def _update_view(self):
        """Mock _update_view method."""
        self.updated = True

    def _update_view_with_filtered_data(self, filtered_data):
        """Mock _update_view_with_filtered_data method."""
        self.filtered_data = filtered_data
        self.updated = True

    def populate_table(self):
        """Mock populate_table method."""
        self.populated = True

    def refresh(self):
        """Mock refresh method."""
        self.refreshed = True


@pytest.fixture
def mock_data_model():
    """Fixture for mock data model."""
    return MockDataModel()


@pytest.fixture
def mock_empty_data_model():
    """Fixture for mock empty data model."""
    return MockDataModel(with_data=False)


@pytest.fixture
def mock_view():
    """Fixture for mock view."""
    return MockDataView()


@pytest.fixture
def mock_signal_manager():
    """Fixture for mock signal manager."""
    from chestbuddy.utils.signal_manager import SignalManager

    return SignalManager()


@pytest.fixture
def controller(mock_data_model, mock_signal_manager):
    """Fixture for controller with data model."""
    return DataViewController(mock_data_model, mock_signal_manager)


@pytest.fixture
def controller_with_view(mock_data_model, mock_view, mock_signal_manager):
    """Fixture for controller with data model and view."""
    controller = DataViewController(mock_data_model, mock_signal_manager)
    controller.set_view(mock_view)
    return controller


class TestDataViewController:
    """Tests for the DataViewController class."""

    def test_initialization(self, controller, mock_data_model):
        """Test controller initialization."""
        assert controller._data_model == mock_data_model
        assert not hasattr(controller, "_view") or controller._view is None
        assert controller._current_filters == {}
        assert controller._current_sort_column is None
        assert controller._current_sort_ascending is True

    def test_set_view(self, controller, mock_view):
        """Test setting the view."""
        controller.set_view(mock_view)
        assert controller._view == mock_view

    def test_filter_data_success(self, controller_with_view, mock_view, mock_data_model):
        """Test filtering data successfully."""
        # Setup signal tracking
        filter_applied_called = False
        filter_params = None

        def on_filter_applied(params):
            nonlocal filter_applied_called, filter_params
            filter_applied_called = True
            filter_params = params

        controller_with_view.filter_applied.connect(on_filter_applied)

        # Call filter_data
        result = controller_with_view.filter_data("Player Name", "Player1", "Equals", False)

        # Assert results
        assert result is True
        assert filter_applied_called is True
        assert filter_params["column"] == "Player Name"
        assert filter_params["text"] == "Player1"
        assert filter_params["mode"] == "Equals"
        assert filter_params["case_sensitive"] is False
        assert mock_view.filtered_data is not None
        assert len(mock_view.filtered_data) == 1
        assert mock_view.filtered_data.iloc[0]["Player Name"] == "Player1"
        assert "column" in controller_with_view._current_filters
        assert controller_with_view._current_filters["column"] == "Player Name"
        assert controller_with_view._current_filters["text"] == "Player1"

    def test_filter_data_invalid_column(self, controller_with_view):
        """Test filtering with invalid column."""
        # Setup signal tracking
        error_called = False
        error_message = None

        def on_error(message):
            nonlocal error_called, error_message
            error_called = True
            error_message = message

        controller_with_view.operation_error.connect(on_error)

        # Call filter_data with invalid column
        result = controller_with_view.filter_data("InvalidColumn", "Value", "Contains", False)

        # Assert results
        assert result is False
        assert error_called is True
        assert "Invalid filter column" in error_message

    def test_filter_data_empty_model(self, mock_empty_data_model, mock_view):
        """Test filtering with empty data model."""
        controller = DataViewController(mock_empty_data_model)
        controller.set_view(mock_view)

        # Call filter_data
        result = controller.filter_data("Player Name", "Value", "Contains", False)

        # Assert results
        assert result is False

    def test_clear_filter(self, controller_with_view, mock_view):
        """Test clearing filter."""
        # First apply a filter
        controller_with_view.filter_data("Player Name", "Player1", "Equals", False)

        # Setup signal tracking
        filter_applied_called = False
        filter_params = None

        def on_filter_applied(params):
            nonlocal filter_applied_called, filter_params
            filter_applied_called = True
            filter_params = params

        controller_with_view.filter_applied.connect(on_filter_applied)

        # Call clear_filter
        result = controller_with_view.clear_filter()

        # Assert results
        assert result is True
        assert filter_applied_called is True
        assert filter_params == {}
        assert mock_view.updated is True
        assert mock_view._filter_text.text() == ""
        assert controller_with_view._current_filters == {}

    def test_sort_data(self, controller_with_view, mock_view):
        """Test sorting data."""
        # Setup signal tracking
        sort_applied_called = False
        sort_column = None
        sort_ascending = None

        def on_sort_applied(column, ascending):
            nonlocal sort_applied_called, sort_column, sort_ascending
            sort_applied_called = True
            sort_column = column
            sort_ascending = ascending

        controller_with_view.sort_applied.connect(on_sort_applied)

        # Call sort_data
        result = controller_with_view.sort_data("Player Name", True)

        # Assert results
        assert result is True
        assert sort_applied_called is True
        assert sort_column == "Player Name"
        assert sort_ascending is True
        assert controller_with_view._current_sort_column == "Player Name"
        assert controller_with_view._current_sort_ascending is True
        mock_view._table_view.sortByColumn.assert_called_once_with(0, 0)  # First column, ascending

    def test_sort_data_invalid_column(self, controller_with_view):
        """Test sorting with invalid column."""
        # Setup signal tracking
        error_called = False
        error_message = None

        def on_error(message):
            nonlocal error_called, error_message
            error_called = True
            error_message = message

        controller_with_view.operation_error.connect(on_error)

        # Call sort_data with invalid column
        result = controller_with_view.sort_data("InvalidColumn", True)

        # Assert results
        assert result is False
        assert error_called is True
        assert "Invalid sort column" in error_message

    def test_populate_table(self, controller_with_view, mock_view):
        """Test populating table."""
        # Setup signal tracking
        table_populated_called = False
        row_count = None

        def on_table_populated(count):
            nonlocal table_populated_called, row_count
            table_populated_called = True
            row_count = count

        controller_with_view.table_populated.connect(on_table_populated)

        # Call populate_table
        result = controller_with_view.populate_table()

        # Assert results
        assert result is True
        assert table_populated_called is True
        assert row_count == 3  # 3 rows in mock data
        assert mock_view.populated is True

    def test_needs_refresh_true(self, controller_with_view, mock_data_model):
        """Test needs_refresh when refresh is needed."""
        # Set up mock state that's different from current
        controller_with_view._last_data_state["row_count"] = 0

        # Call needs_refresh
        result = controller_with_view.needs_refresh()

        # Assert results
        assert result is True

    def test_needs_refresh_false(self, controller_with_view, mock_data_model):
        """Test needs_refresh when refresh is not needed."""
        # Set up mock state that matches current
        controller_with_view._last_data_state = {
            "row_count": 3,
            "column_count": 3,
            "data_hash": "test_hash",
            "last_update_time": 0,
        }

        # Call needs_refresh
        result = controller_with_view.needs_refresh()

        # Assert results
        assert result is False

    def test_refresh_data(self, controller_with_view, mock_view):
        """Test refreshing data."""
        # Force needs_refresh to return True
        controller_with_view.needs_refresh = MagicMock(return_value=True)

        # Call refresh_data
        result = controller_with_view.refresh_data()

        # Assert results
        assert result is True
        assert mock_view.refreshed is True

    def test_refresh_data_not_needed(self, controller_with_view, mock_view):
        """Test refreshing data when not needed."""
        # Force needs_refresh to return False
        controller_with_view.needs_refresh = MagicMock(return_value=False)

        # Call refresh_data
        result = controller_with_view.refresh_data()

        # Assert results
        assert result is True
        assert mock_view.refreshed is False  # Should not refresh

    def test_handle_filter_button_clicked(self, controller_with_view):
        """Test handling filter button click."""
        # Mock filter_data to track calls
        controller_with_view.filter_data = MagicMock(return_value=True)

        # Set up mock view's filter controls
        controller_with_view._view._filter_column.setCurrentText("Player Name")
        controller_with_view._view._filter_text.setText("Player1")
        controller_with_view._view._filter_mode.setCurrentText("Contains")
        controller_with_view._view._case_sensitive.setChecked(False)

        # Call _handle_filter_button_clicked
        controller_with_view._handle_filter_button_clicked()

        # Assert results
        controller_with_view.filter_data.assert_called_once_with(
            "Player Name", "Player1", "Contains", False
        )

    def test_handle_clear_filter_button_clicked(self, controller_with_view):
        """Test handling clear filter button click."""
        # Mock clear_filter to track calls
        controller_with_view.clear_filter = MagicMock(return_value=True)

        # Call _handle_clear_filter_button_clicked
        controller_with_view._handle_clear_filter_button_clicked()

        # Assert results
        controller_with_view.clear_filter.assert_called_once()
