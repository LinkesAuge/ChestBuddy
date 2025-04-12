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
from PySide6.QtWidgets import QTableView, QMenu
from PySide6.QtTest import QTest
from unittest.mock import MagicMock, patch

from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from PySide6.QtCore import QAbstractItemModel
from chestbuddy.core.table_state_manager import TableStateManager
from chestbuddy.ui.data.delegates.cell_delegate import CellDelegate

# Fixtures like qapp and mock_chest_data_model are expected from conftest.py


class MockDelegate(CellDelegate):
    """Mock delegate to emit signals for testing."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def emit_validation_failed(self, index, message):
        self.validationFailed.emit(index, message)


class TestDataTableView:
    """Tests for the DataTableView class."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock TableStateManager."""
        return MagicMock(spec=TableStateManager)

    @pytest.fixture
    def view_model(self, mock_chest_data_model, mock_state_manager):
        """Create a DataViewModel instance for view tests."""
        # Now we can use the actual DataViewModel
        return DataViewModel(mock_chest_data_model, mock_state_manager)

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

    def test_context_menu_basic(self, qapp, view_model, qtbot, monkeypatch, mocker):
        """Test that a basic context menu is shown on right-click."""
        view = DataTableView()
        view.setModel(view_model)
        view.show()
        qtbot.addWidget(view)

        # Spy on the slot that creates the menu
        show_menu_spy = mocker.spy(view, "_show_context_menu")

        # Mock the exec_ method on the QMenu class globally initially,
        # just to prevent it from blocking if the spy doesn't work as expected.
        monkeypatch.setattr("PySide6.QtWidgets.QMenu.exec_", lambda *args: None)

        # Simulate right-click by directly emitting the signal
        index_to_click = view.model().index(0, 0)
        click_pos = view.visualRect(index_to_click).center()
        # qtbot.mouseClick(view.viewport(), Qt.RightButton, pos=click_pos) # Don't simulate click
        view.customContextMenuRequested.emit(click_pos)  # Emit signal directly

        # Check that our slot was called
        assert show_menu_spy.call_count == 1, "_show_context_menu slot was not called."

        # Get the menu that was created and returned by the slot
        returned_menu = show_menu_spy.spy_return
        assert isinstance(returned_menu, QMenu), "_show_context_menu did not return a QMenu."

        # Check the actions on the actual returned menu
        menu_actions = [action.text() for action in returned_menu.actions() if action.text()]
        assert len(menu_actions) > 0, "Context menu had no actions."
        assert "Copy" in menu_actions

    def test_set_model(self, qapp):
        """Test setting the model on the view."""
        mock_model = MagicMock(spec=QAbstractItemModel)
        view = DataTableView()
        view.setModel(mock_model)
        assert view.model() == mock_model
        mock_model.setParent.assert_called_once_with(view.table_view)  # Parent should be table_view

    # --- Column Visibility Tests --- #

    def test_column_visibility_methods(self, qapp, mock_chest_data_model):
        """Test setColumnVisible and isColumnVisible methods."""
        model = DataViewModel(mock_chest_data_model, None)
        view = DataTableView()
        view.setModel(model)

        # Verify initial visibility
        assert view.isColumnVisible(1) is True
        assert not view.table_view.isColumnHidden(1)

        # Hide column 1
        view.setColumnVisible(1, False)
        assert view.isColumnVisible(1) is False
        assert view.table_view.isColumnHidden(1)

        # Show column 1 again
        view.setColumnVisible(1, True)
        assert view.isColumnVisible(1) is True
        assert not view.table_view.isColumnHidden(1)

    def test_header_context_menu_shows(self, qapp, mock_chest_data_model, qtbot, monkeypatch):
        """Test that right-clicking the header shows the context menu."""
        model = DataViewModel(mock_chest_data_model, None)
        view = DataTableView()
        view.setModel(model)
        qtbot.addWidget(view)

        header = view.table_view.horizontalHeader()

        # Mock QMenu.exec to prevent actual menu display and track it
        menu_shown = False

        def mock_exec(*args, **kwargs):
            nonlocal menu_shown
            menu_shown = True
            return None  # Don't return an action

        monkeypatch.setattr(QMenu, "exec", mock_exec)

        # Simulate right-click on header (section 0)
        header_pos = header.sectionViewportPosition(0)
        click_point = QPoint(header_pos + 5, header.height() // 2)
        qtbot.mouseClick(header, Qt.RightButton, pos=click_point)

        # Verify the menu was triggered
        assert menu_shown

    def test_header_context_menu_content(self, qapp, mock_chest_data_model, qtbot, monkeypatch):
        """Test the content of the header context menu."""
        mock_chest_data_model.columnCount.return_value = 3
        mock_chest_data_model.headerData.side_effect = (
            lambda sec, orient, role: f"Col {sec}" if role == Qt.DisplayRole else None
        )
        model = DataViewModel(mock_chest_data_model, None)
        view = DataTableView()
        view.setModel(model)
        qtbot.addWidget(view)

        header = view.table_view.horizontalHeader()
        menu_actions = []

        # Mock QMenu.exec to capture actions
        def mock_exec(self, *args, **kwargs):
            nonlocal menu_actions
            menu_actions = self.actions()
            return None

        monkeypatch.setattr(QMenu, "exec", mock_exec)

        # Simulate right-click on header
        qtbot.mouseClick(header, Qt.RightButton, pos=QPoint(10, 10))

        # Verify actions for each column exist
        assert len(menu_actions) >= 3  # At least 3 column actions + separator + resize
        col_action_texts = {a.text() for a in menu_actions if a.isCheckable()}
        assert "Col 0" in col_action_texts
        assert "Col 1" in col_action_texts
        assert "Col 2" in col_action_texts
        assert "Resize Columns to Contents" in {
            a.text() for a in menu_actions if not a.isSeparator()
        }

        # Verify actions are checkable and checked initially
        for action in menu_actions:
            if action.isCheckable():
                assert action.isCheckable()
                assert action.isChecked()

    def test_header_context_menu_toggle_visibility(
        self, qapp, mock_chest_data_model, qtbot, monkeypatch
    ):
        """Test toggling column visibility via the header context menu."""
        model = DataViewModel(mock_chest_data_model, None)
        view = DataTableView()
        view.setModel(model)
        qtbot.addWidget(view)

        header = view.table_view.horizontalHeader()
        captured_actions = []

        # Mock QMenu.exec to capture actions
        def mock_exec(self, *args, **kwargs):
            nonlocal captured_actions
            captured_actions = self.actions()
            return None

        monkeypatch.setattr(QMenu, "exec", mock_exec)

        # Show the menu
        qtbot.mouseClick(header, Qt.RightButton, pos=QPoint(10, 10))

        # Find the action for column 1 (assuming it exists)
        action_col1 = None
        for action in captured_actions:
            if action.text() == mock_chest_data_model.headerData(
                1, Qt.Horizontal
            ):  # Use mocked header data
                action_col1 = action
                break

        assert action_col1 is not None
        assert action_col1.isChecked()  # Should be visible initially
        assert view.isColumnVisible(1) is True

        # Simulate unchecking the action to hide the column
        # Directly trigger the action with checked=False
        action_col1.triggered.emit(False)
        qtbot.wait(50)  # Wait for potential UI updates

        # Verify column is now hidden
        assert view.isColumnVisible(1) is False

        # Show the menu again
        qtbot.mouseClick(header, Qt.RightButton, pos=QPoint(10, 10))

        # Find the action again and verify it's unchecked
        action_col1_updated = None
        for action in captured_actions:
            if action.text() == mock_chest_data_model.headerData(1, Qt.Horizontal):
                action_col1_updated = action
                break
        assert action_col1_updated is not None
        assert not action_col1_updated.isChecked()

        # Simulate checking the action to show the column
        action_col1_updated.triggered.emit(True)
        qtbot.wait(50)

        # Verify column is visible again
        assert view.isColumnVisible(1) is True

    def test_column_reordering(self, qapp, mock_chest_data_model, qtbot):
        """Test that columns can be reordered by dragging header."""
        model = DataViewModel(mock_chest_data_model, None)
        view = DataTableView()
        view.setModel(model)
        qtbot.addWidget(view)

        header = view.table_view.horizontalHeader()

        # Initial visual order: 0, 1, 2, ...
        assert header.visualIndex(0) == 0
        assert header.visualIndex(1) == 1
        assert header.visualIndex(2) == 2

        # Simulate dragging header section 0 to position 2
        source_pos = header.sectionViewportPosition(0)
        target_pos = header.sectionViewportPosition(2)
        center_y = header.height() // 2

        # Press on header 0
        qtbot.mousePress(header, Qt.LeftButton, pos=QPoint(source_pos + 5, center_y))
        # Drag to position 2
        qtbot.mouseMove(header, pos=QPoint(target_pos + 5, center_y))
        # Release
        qtbot.mouseRelease(header, Qt.LeftButton, pos=QPoint(target_pos + 5, center_y))
        qtbot.wait(100)  # Allow time for move

        # Verify new visual order (e.g., 1, 2, 0)
        # The exact order depends on Qt's handling, but 0 should not be at index 0
        assert header.visualIndex(0) != 0
        # It's hard to predict exact final order reliably in tests, but we know 0 moved
        assert header.logicalIndex(0) != 0  # Check that logical 0 is no longer visual 0

    # --- Tests for Validation Failure Handling --- #

    def test_on_validation_failed_shows_messagebox(self, qapp, view_model, qtbot, mocker):
        """Test that the _on_validation_failed slot shows a QMessageBox."""
        model = view_model  # Use the fixture which now includes state manager
        view = DataTableView()
        view.setModel(model)
        qtbot.addWidget(view)

        # Mock QMessageBox.warning
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        # Get the delegate instance set by the view
        delegate = view.table_view.itemDelegate()
        assert delegate is not None

        # Emit the validationFailed signal from the delegate
        test_index = model.index(1, 1)
        error_message = "Invalid data entered"

        # Ensure the signal is connected
        # Need to manually trigger signal emission if using MagicMock delegate
        # If using a real delegate instance, we can emit its signal
        if hasattr(delegate, "validationFailed"):
            delegate.validationFailed.emit(test_index, error_message)
        else:
            # If the delegate doesn't have the signal (maybe base class test?),
            # manually call the slot to test its logic
            view._on_validation_failed(test_index, error_message)

        # Verify QMessageBox.warning was called
        mock_warning.assert_called_once()
        # Check arguments (optional, but good practice)
        args, kwargs = mock_warning.call_args
        assert args[0] == view  # Parent
        assert args[1] == "Validation Failed"  # Title
        assert error_message in args[2]  # Message content
        assert f"cell ({test_index.row()}, {test_index.column()})" in args[2]

    def test_delegate_reconnection_on_set_model(self, qapp, mock_chest_data_model, qtbot, mocker):
        """Test that delegate signals are disconnected and reconnected when model changes."""
        # ... existing code ...

    # --- Other Tests ---
