"""
Tests for the DataTableView class.
"""

import pytest
from PySide6.QtCore import (
    Qt,
    QPoint,
    QAbstractTableModel,
    QModelIndex,
    QItemSelection,
    QItemSelectionModel,
)
from PySide6.QtWidgets import QTableView
from PySide6.QtTest import QTest

from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.models.data_view_model import DataViewModel

# Fixtures like qapp and mock_chest_data_model are expected from conftest.py


class TestDataTableView:
    """Tests for the DataTableView class."""

    @pytest.fixture
    def view_model(self, mock_chest_data_model):
        """Create a DataViewModel instance for view tests."""
        # Now we can use the actual DataViewModel
        return DataViewModel(mock_chest_data_model)

    def test_initialization(self, qapp, view_model):
        """Test that the DataTableView initializes correctly."""
        view = DataTableView()
        view.setModel(view_model)

        assert view.model() == view_model
        # Basic properties set in _setup_ui
        assert view.alternatingRowColors() is True
        assert view.showGrid() is True
        assert view.isSortingEnabled() is True
        assert view.selectionBehavior() == QTableView.SelectItems
        assert view.selectionMode() == QTableView.ExtendedSelection
        assert view.horizontalHeader().stretchLastSection() is True
        assert view.verticalHeader().isVisible() is False
        assert view.contextMenuPolicy() == Qt.CustomContextMenu

    def test_cell_click_signal(self, qapp, view_model, qtbot):
        """Test that clicking a cell emits the clicked signal (from QTableView)."""
        view = DataTableView()
        view.setModel(view_model)
        view.show()  # View needs to be visible for interactions
        qtbot.addWidget(view)

        # QTableView itself has a clicked signal(QModelIndex)
        with qtbot.waitSignal(
            view.clicked, timeout=100
        ) as blocker:  # Use view.clicked which takes QModelIndex
            # Need a valid index from the model
            # Use index method from QAbstractItemModel which DataViewModel inherits
            index_to_click = view.model().index(1, 1)

            cell_rect = view.visualRect(index_to_click)
            # Ensure viewport exists and is valid
            assert view.viewport() is not None
            QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=cell_rect.center())

        assert blocker.signal_triggered
        # The clicked signal emits the QModelIndex
        assert len(blocker.args) == 1
        clicked_index = blocker.args[0]
        assert isinstance(clicked_index, QModelIndex)
        assert clicked_index.row() == 1
        assert clicked_index.column() == 1

    def test_model_setting(self, qapp, view_model):
        """Test setting and retrieving the model."""
        view = DataTableView()
        assert view.model() is None  # Should be None initially

        # Use the view_model fixture instead of dummy QAbstractTableModel
        view.setModel(view_model)
        assert view.model() == view_model

    def test_custom_selection_changed_signal(self, qapp, view_model, qtbot):
        """Test that the custom selection_changed signal emits correctly."""
        view = DataTableView()
        view.setModel(view_model)
        view.show()
        qtbot.addWidget(view)

        # Assuming DataTableView will have a custom signal like this:
        # selection_changed = Signal(list) # Emitting list of QModelIndex

        # Spy on the custom signal
        with qtbot.waitSignal(view.selection_changed, timeout=100) as blocker:
            # Programmatically change the selection
            index1 = view.model().index(0, 0)
            index2 = view.model().index(1, 1)
            # Create a selection object
            selection = QItemSelection()
            selection.select(index1, index1)
            selection.select(index2, index2)
            # Apply the selection
            view.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)

        assert blocker.signal_triggered
        assert len(blocker.args) == 1
        selected_indices = blocker.args[0]
        assert isinstance(selected_indices, list)
        assert len(selected_indices) == 2
        # Check if the correct indices are in the list (order might vary)
        rows_cols = sorted([(idx.row(), idx.column()) for idx in selected_indices])
        assert rows_cols == [(0, 0), (1, 1)]
