"""
Tests for the DataViewModel class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QColor
from unittest.mock import MagicMock

from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import TableStateManager
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Fixtures like mock_chest_data_model and mock_table_state_manager
# are now expected to be loaded from tests/ui/data/conftest.py


class TestDataViewModel:
    """Tests for the DataViewModel class."""

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_initialization(self, mock_chest_data_model):
        """Test that the DataViewModel initializes correctly."""
        model = DataViewModel(mock_chest_data_model)
        assert model.source_model() == mock_chest_data_model

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_row_count(self, mock_chest_data_model):
        """Test rowCount returns the correct number of rows."""
        model = DataViewModel(mock_chest_data_model)
        # Call rowCount on our model, which delegates to the mock
        result = model.rowCount()
        # Assert the result is correct
        assert result == 10  # Expected return value from mock
        # Assert the mock was called exactly once by our model's method
        mock_chest_data_model.rowCount.assert_called_once()

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_column_count(self, mock_chest_data_model):
        """Test columnCount returns the correct number of columns."""
        model = DataViewModel(mock_chest_data_model)
        # Call columnCount on our model
        result = model.columnCount()
        # Assert the result
        assert result == 5  # Expected return value from mock
        # Assert the mock was called exactly once
        mock_chest_data_model.columnCount.assert_called_once()

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_data_for_display_role(self, mock_chest_data_model):
        """Test data returns the correct value for DisplayRole."""
        model = DataViewModel(mock_chest_data_model)
        # QAbstractTableModel provides createIndex
        test_index = model.createIndex(0, 0)
        assert model.data(test_index, Qt.DisplayRole) == "test_data"
        # Verify the call was delegated correctly
        mock_chest_data_model.data.assert_called_with(test_index, Qt.DisplayRole)

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_data_for_validation_state_role(self, mock_chest_data_model, mock_table_state_manager):
        """Test data returns the correct validation state."""
        mock_table_state_manager.get_cell_state.return_value = "INVALID"

        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)

        test_index = model.createIndex(0, 0)
        assert model.data(test_index, DataViewModel.ValidationStateRole) == "INVALID"
        mock_table_state_manager.get_cell_state.assert_called_with(0, 0)

    def test_data_for_background_role_invalid(
        self, mock_chest_data_model, mock_table_state_manager
    ):
        """Test data returns the correct background color for INVALID state."""
        mock_table_state_manager.get_cell_state.return_value = "INVALID"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(1, 1)
        background_color = model.data(test_index, Qt.BackgroundRole)
        assert isinstance(background_color, QColor)
        assert background_color.name() == "#ffb6b6"
        mock_table_state_manager.get_cell_state.assert_called_with(1, 1)

    def test_data_for_background_role_correctable(
        self, mock_chest_data_model, mock_table_state_manager
    ):
        """Test data returns the correct background color for CORRECTABLE state."""
        mock_table_state_manager.get_cell_state.return_value = "CORRECTABLE"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(2, 2)
        background_color = model.data(test_index, Qt.BackgroundRole)
        assert isinstance(background_color, QColor)
        assert background_color.name() == "#fff3b6"
        mock_table_state_manager.get_cell_state.assert_called_with(2, 2)

    def test_data_for_background_role_normal(self, mock_chest_data_model, mock_table_state_manager):
        """Test data returns None for background color for NORMAL state."""
        # Default return value is NORMAL, no need to set
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(3, 3)
        background_color = model.data(test_index, Qt.BackgroundRole)
        assert background_color is None
        mock_table_state_manager.get_cell_state.assert_called_with(3, 3)

    def test_header_data(self, mock_chest_data_model):
        """Test headerData retrieves header from source model."""
        mock_chest_data_model.headerData.return_value = "Test Header"
        model = DataViewModel(mock_chest_data_model, None)  # No state manager needed
        assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Test Header"
        mock_chest_data_model.headerData.assert_called_with(0, Qt.Horizontal, Qt.DisplayRole)

    def test_flags(self, mock_chest_data_model):
        """Test flags includes default flags plus editable."""
        mock_chest_data_model.flags.return_value = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        model = DataViewModel(mock_chest_data_model, None)
        index = model.index(0, 0)
        flags = model.flags(index)
        assert flags & Qt.ItemIsSelectable
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsEditable  # Should be added by default
        mock_chest_data_model.flags.assert_called_with(index)

    def test_set_data_success(self, mock_chest_data_model, qtbot):
        """Test setData successfully updates source model and emits signal."""
        mock_chest_data_model.setData.return_value = True
        model = DataViewModel(mock_chest_data_model, None)
        index = model.index(0, 0)

        with qtbot.waitSignal(model.dataChanged) as blocker:
            success = model.setData(index, "new_value", Qt.EditRole)

        assert success
        mock_chest_data_model.setData.assert_called_with(index, "new_value", Qt.EditRole)
        assert blocker.args == [index, index, [Qt.EditRole]]

    def test_set_data_failure(self, mock_chest_data_model, qtbot):
        """Test setData returns False if source model fails."""
        mock_chest_data_model.setData.return_value = False
        model = DataViewModel(mock_chest_data_model, None)
        index = model.index(0, 0)

        with qtbot.assertNotEmitted(model.dataChanged):
            success = model.setData(index, "new_value", Qt.EditRole)

        assert not success
        mock_chest_data_model.setData.assert_called_with(index, "new_value", Qt.EditRole)

    def test_set_data_invalid_role(self, mock_chest_data_model, qtbot):
        """Test setData returns False for roles other than EditRole."""
        model = DataViewModel(mock_chest_data_model, None)
        index = model.index(0, 0)

        with qtbot.assertNotEmitted(model.dataChanged):
            success = model.setData(index, "new_value", Qt.DisplayRole)

        assert not success
        mock_chest_data_model.setData.assert_not_called()

    # --- Sorting Tests --- #

    def test_sort_delegates_to_source(self, mock_chest_data_model, qtbot):
        """Test sort calls source model's sort_data method."""
        mock_chest_data_model.headerData.return_value = "ColumnA"  # Mock header name
        # Ensure source model has the sort_data method
        mock_chest_data_model.sort_data = MagicMock()

        model = DataViewModel(mock_chest_data_model, None)

        with qtbot.waitSignals([model.layoutAboutToBeChanged, model.layoutChanged]):
            model.sort(0, Qt.AscendingOrder)

        mock_chest_data_model.sort_data.assert_called_once_with("ColumnA", True)
        assert model.current_sort_column() == 0
        assert model.current_sort_order() == Qt.AscendingOrder

    def test_sort_descending(self, mock_chest_data_model, qtbot):
        """Test sort with descending order."""
        mock_chest_data_model.headerData.return_value = "ColumnB"
        mock_chest_data_model.sort_data = MagicMock()
        model = DataViewModel(mock_chest_data_model, None)

        with qtbot.waitSignals([model.layoutAboutToBeChanged, model.layoutChanged]):
            model.sort(1, Qt.DescendingOrder)

        mock_chest_data_model.sort_data.assert_called_once_with("ColumnB", False)
        assert model.current_sort_column() == 1
        assert model.current_sort_order() == Qt.DescendingOrder

    def test_sort_invalid_column(self, mock_chest_data_model, qtbot):
        """Test sort does nothing if header data is not found."""
        mock_chest_data_model.headerData.return_value = None  # Simulate header not found
        mock_chest_data_model.sort_data = MagicMock()
        model = DataViewModel(mock_chest_data_model, None)

        with qtbot.assertNotEmitted(model.layoutAboutToBeChanged):
            with qtbot.assertNotEmitted(model.layoutChanged):
                model.sort(99, Qt.AscendingOrder)  # Invalid column index

        mock_chest_data_model.sort_data.assert_not_called()
        assert model.current_sort_column() == -1  # Should remain default

    def test_sort_no_source_method(self, mock_chest_data_model, qtbot):
        """Test sort does nothing if source model lacks sort_data method."""
        mock_chest_data_model.headerData.return_value = "ColumnA"
        # Ensure source model *does not* have sort_data
        if hasattr(mock_chest_data_model, "sort_data"):
            del mock_chest_data_model.sort_data

        model = DataViewModel(mock_chest_data_model, None)

        with qtbot.assertNotEmitted(model.layoutAboutToBeChanged):
            with qtbot.assertNotEmitted(model.layoutChanged):
                model.sort(0, Qt.AscendingOrder)

        assert model.current_sort_column() == -1  # Should remain default

    def test_data_for_edit_role(self, mock_chest_data_model):
        """Test data returns the correct value for EditRole (delegated)."""
        model = DataViewModel(mock_chest_data_model)
        test_index = model.createIndex(0, 0)
        # Assuming EditRole should return the same as DisplayRole for basic types initially
        mock_chest_data_model.data.return_value = "editable_data"
        assert model.data(test_index, Qt.EditRole) == "editable_data"
        # Verify delegation happened for EditRole
        mock_chest_data_model.data.assert_called_with(test_index, Qt.EditRole)

    def test_data_for_tooltip_role_invalid(self, mock_chest_data_model, mock_table_state_manager):
        """Test data returns the correct tooltip for INVALID state."""
        mock_table_state_manager.get_cell_state.return_value = "INVALID"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(1, 2)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip == "Invalid data in cell (1, 2)"
        mock_table_state_manager.get_cell_state.assert_called_with(1, 2)

    def test_data_for_tooltip_role_correctable(
        self, mock_chest_data_model, mock_table_state_manager
    ):
        """Test data returns the correct tooltip for CORRECTABLE state."""
        mock_table_state_manager.get_cell_state.return_value = "CORRECTABLE"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(2, 3)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip == "Correctable data in cell (2, 3)"
        mock_table_state_manager.get_cell_state.assert_called_with(2, 3)

    def test_data_for_tooltip_role_normal(self, mock_chest_data_model, mock_table_state_manager):
        """Test data returns None for tooltip for NORMAL state."""
        # Default state is NORMAL
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(4, 4)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip is None
        mock_table_state_manager.get_cell_state.assert_called_with(4, 4)

    def test_data_for_unknown_role(self, mock_chest_data_model):
        """Test data returns None for unhandled roles."""
        model = DataViewModel(mock_chest_data_model)
        test_index = model.createIndex(0, 0)
        assert model.data(test_index, Qt.UserRole + 100) is None  # Some arbitrary role
        # Check that the source model wasn't called for this unknown role (optional)
        # mock_chest_data_model.data.assert_called_with(test_index, Qt.UserRole + 100) # Should NOT have been called

    def test_data_invalid_index(self, mock_chest_data_model):
        """Test data returns None for an invalid index."""
        model = DataViewModel(mock_chest_data_model)
        invalid_index = QModelIndex()  # Default constructor creates an invalid index
        assert model.data(invalid_index, Qt.DisplayRole) is None
