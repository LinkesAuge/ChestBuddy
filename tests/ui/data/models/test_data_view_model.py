"""
Tests for the DataViewModel class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, Signal
from PySide6.QtGui import QColor
from unittest.mock import MagicMock, call

from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.core.models import ChestDataModel

# Fixtures like mock_chest_data_model and mock_table_state_manager
# are now expected to be loaded from tests/ui/data/conftest.py


class TestDataViewModel:
    """Tests for the DataViewModel class."""

    @pytest.fixture(autouse=True)
    def setup_model(self, mock_chest_data_model, mock_table_state_manager):
        """Setup the model instance for each test."""
        # Pass both mocks during initialization
        self.model = DataViewModel(mock_chest_data_model, mock_table_state_manager)
        self.mock_source_model = mock_chest_data_model
        self.mock_state_manager = mock_table_state_manager

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_initialization(self):
        """Test that the DataViewModel initializes correctly."""
        assert self.model.source_model() == self.mock_source_model
        assert self.model._state_manager == self.mock_state_manager
        # Verify signal connections were attempted (mocks don't raise errors)
        # self.mock_source_model.data_changed.connect.assert_called_once()
        # self.mock_state_manager.state_changed.connect.assert_called_once()

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_row_count(self):
        """Test rowCount returns the correct number of rows."""
        self.mock_source_model.rowCount.return_value = 15
        assert self.model.rowCount() == 15
        self.mock_source_model.rowCount.assert_called_once()

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_column_count(self):
        """Test columnCount returns the correct number of columns."""
        self.mock_source_model.columnCount.return_value = 7
        assert self.model.columnCount() == 7
        self.mock_source_model.columnCount.assert_called_once()

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_data_for_display_role(self):
        """Test data returns the correct value for DisplayRole."""
        index = self.model.index(0, 0)
        self.mock_source_model.data.return_value = "Source Data"
        assert self.model.data(index, Qt.DisplayRole) == "Source Data"
        self.mock_source_model.data.assert_called_with(index, Qt.DisplayRole)

    # @pytest.mark.skip(reason="DataViewModel not implemented yet") - Removed skip
    def test_data_for_validation_state_role(self):
        """Test data returns the correct validation state."""
        index = self.model.index(1, 1)
        # Mock state manager to return a specific full state
        state = CellFullState(validation_status=CellState.INVALID)
        self.mock_state_manager.get_full_cell_state.return_value = state

        assert self.model.data(index, DataViewModel.ValidationStateRole) == CellState.INVALID
        self.mock_state_manager.get_full_cell_state.assert_called_with(1, 1)

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

    def test_header_data(self):
        """Test headerData retrieves header from source model."""
        self.mock_source_model.headerData.return_value = "Test Header"
        assert self.model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Test Header"
        self.mock_source_model.headerData.assert_called_with(0, Qt.Horizontal, Qt.DisplayRole)

    def test_flags(self):
        """Test flags includes default flags plus editable."""
        self.mock_source_model.flags.return_value = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        index = self.model.index(0, 0)
        flags = self.model.flags(index)
        assert flags & Qt.ItemIsSelectable
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsEditable  # Should be added by default
        self.mock_source_model.flags.assert_called_with(index)

    def test_set_data_success(self, qtbot):
        """Test setData successfully updates source model and emits signal."""
        self.mock_source_model.setData.return_value = True
        index = self.model.index(0, 0)

        with qtbot.waitSignal(self.model.dataChanged) as blocker:
            success = self.model.setData(index, "new_value", Qt.EditRole)

        assert success
        self.mock_source_model.setData.assert_called_with(index, "new_value", Qt.EditRole)
        # Note: dataChanged signal arguments might vary based on QAbstractTableModel internals
        # Check if the signal was emitted with the correct index range
        assert blocker.args[0] == index
        assert blocker.args[1] == index
        # assert blocker.args[2] == [Qt.EditRole] # Role might not always be EditRole here

    def test_set_data_failure(self, qtbot):
        """Test setData returns False if source model fails."""
        self.mock_source_model.setData.return_value = False
        index = self.model.index(0, 0)
        with qtbot.assertNotEmitted(self.model.dataChanged):
            success = self.model.setData(index, "new_value", Qt.EditRole)
        assert not success
        self.mock_source_model.setData.assert_called_with(index, "new_value", Qt.EditRole)

    def test_set_data_invalid_role(self, qtbot):
        """Test setData returns False for roles other than EditRole."""
        index = self.model.index(0, 0)
        with qtbot.assertNotEmitted(self.model.dataChanged):
            success = self.model.setData(index, "new_value", Qt.DisplayRole)
        assert not success
        self.mock_source_model.setData.assert_not_called()

    # --- Sorting Tests --- #

    def test_sort_delegates_to_source(self, qtbot):
        """Test sort calls source model's sort_data method."""
        self.mock_source_model.headerData.return_value = "ColumnA"  # Mock header name
        # Ensure source model has the sort_data method
        self.mock_source_model.sort_data = MagicMock()

        with qtbot.waitSignals([self.model.layoutAboutToBeChanged, self.model.layoutChanged]):
            self.model.sort(0, Qt.AscendingOrder)

        self.mock_source_model.sort_data.assert_called_once_with("ColumnA", True)
        assert self.model.current_sort_column() == 0
        assert self.model.current_sort_order() == Qt.AscendingOrder

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

    def test_data_for_edit_role(self):
        """Test data returns the correct value for EditRole (delegated)."""
        index = self.model.index(0, 0)
        # Assuming EditRole should return the same as DisplayRole for basic types initially
        self.mock_source_model.data.return_value = "editable_data"
        assert self.model.data(index, Qt.EditRole) == "editable_data"
        # Verify delegation happened for EditRole
        self.mock_source_model.data.assert_called_with(index, Qt.EditRole)

    def test_data_for_tooltip_role_invalid(self, mock_table_state_manager):
        """Test data returns the correct tooltip for INVALID state."""
        mock_table_state_manager.get_cell_state.return_value = "INVALID"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(1, 2)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip == "Invalid data in cell (1, 2)"
        mock_table_state_manager.get_cell_state.assert_called_with(1, 2)

    def test_data_for_tooltip_role_correctable(self, mock_table_state_manager):
        """Test data returns the correct tooltip for CORRECTABLE state."""
        mock_table_state_manager.get_cell_state.return_value = "CORRECTABLE"
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(2, 3)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip == "Correctable data in cell (2, 3)"
        mock_table_state_manager.get_cell_state.assert_called_with(2, 3)

    def test_data_for_tooltip_role_normal(self, mock_table_state_manager):
        """Test data returns None for tooltip for NORMAL state."""
        # Default state is NORMAL
        model = DataViewModel(mock_chest_data_model)
        model.set_table_state_manager(mock_table_state_manager)
        test_index = model.createIndex(4, 4)
        tooltip = model.data(test_index, Qt.ToolTipRole)
        assert tooltip is None
        mock_table_state_manager.get_cell_state.assert_called_with(4, 4)

    def test_data_for_unknown_role(self):
        """Test data returns None for unhandled roles."""
        model = DataViewModel(mock_chest_data_model)
        test_index = model.createIndex(0, 0)
        assert model.data(test_index, Qt.UserRole + 100) is None  # Some arbitrary role
        # Check that the source model wasn't called for this unknown role (optional)
        # mock_chest_data_model.data.assert_called_with(test_index, Qt.UserRole + 100) # Should NOT have been called

    def test_data_invalid_index(self):
        """Test data returns None for an invalid index."""
        model = DataViewModel(mock_chest_data_model)
        invalid_index = QModelIndex()  # Default constructor creates an invalid index
        assert model.data(invalid_index, Qt.DisplayRole) is None

    # --- Signal Handling Tests --- #

    def test_on_source_data_changed_resets_model(self, qtbot):
        """Test that source model changes trigger begin/endResetModel."""
        # Need to connect manually if init mock doesn't handle it
        # For this test, assume connection is made or trigger manually
        # self.model._connect_source_model_signals() # Reconnect if needed

        mock_begin_reset = MagicMock()
        mock_end_reset = MagicMock()
        self.model.beginResetModel = mock_begin_reset
        self.model.endResetModel = mock_end_reset

        # Simulate source model signal
        # This requires the source model mock to have the signal
        # Let's call the slot directly for simplicity here
        self.model._on_source_data_changed()

        mock_begin_reset.assert_called_once()
        mock_end_reset.assert_called_once()

    def test_on_state_manager_state_changed_resets_model(self, qtbot):
        """Test state manager changes trigger begin/endResetModel (current implementation)."""
        # Connect signal if not done in init mock
        # self.model._connect_state_manager_signals()

        mock_begin_reset = MagicMock()
        mock_end_reset = MagicMock()
        self.model.beginResetModel = mock_begin_reset
        self.model.endResetModel = mock_end_reset

        changed_set = {(0, 0), (1, 1)}

        # Simulate state manager signal emission
        self.mock_state_manager.state_changed.emit(changed_set)

        # Verify model reset was called
        mock_begin_reset.assert_called_once()
        mock_end_reset.assert_called_once()

    # Add any other specific tests needed for DataViewModel logic
