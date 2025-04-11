"""
Tests for the DataViewModel class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QColor

from chestbuddy.ui.data.models.data_view_model import DataViewModel

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
        """Test headerData delegates to the source model."""
        model = DataViewModel(mock_chest_data_model)
        assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Header"
        mock_chest_data_model.headerData.assert_called_with(0, Qt.Horizontal, Qt.DisplayRole)

    def test_flags(self, mock_chest_data_model):
        """Test flags returns editable flags combined with source flags."""
        model = DataViewModel(mock_chest_data_model)
        test_index = model.createIndex(0, 0)
        expected_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        assert model.flags(test_index) == expected_flags
        # Verify source model's flags was called
        mock_chest_data_model.flags.assert_called_with(test_index)

    def test_set_data(self, mock_chest_data_model, qtbot):
        """Test setData delegates to the source model and emits dataChanged."""
        model = DataViewModel(mock_chest_data_model)
        test_index = model.createIndex(0, 0)
        new_value = "new_data"

        # Use waitSignal to check if dataChanged is emitted
        # timeout=0 ensures it checks immediately if signal was emitted synchronously
        with qtbot.waitSignal(model.dataChanged, timeout=100, raising=True) as blocker:
            result = model.setData(test_index, new_value, Qt.EditRole)

        assert result is True
        mock_chest_data_model.setData.assert_called_with(test_index, new_value, Qt.EditRole)
        # Check that the signal was emitted correctly via the blocker
        assert blocker.signal_triggered
        # Arguments are emitted as a list within blocker.args
        assert len(blocker.args) == 3
        assert blocker.args[0] == test_index  # topLeft
        assert blocker.args[1] == test_index  # bottomRight
        assert blocker.args[2] == [Qt.EditRole]  # roles

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
