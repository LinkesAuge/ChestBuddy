"""
Tests for the ContextMenuFactory.
"""

import pytest
import typing
from unittest.mock import MagicMock

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMenu, QWidget
from PySide6.QtGui import QAction, QGuiApplication

from chestbuddy.ui.data.menus.context_menu_factory import ContextMenuFactory, ActionContext
from chestbuddy.core.table_state_manager import CellState
from chestbuddy.ui.data.models.data_view_model import DataViewModel

# --- Mock Objects ---


class MockModel:
    """Mock DataViewModel for testing."""

    def __init__(self, is_editable=True, validation_state=None):
        self._is_editable = is_editable
        self._validation_state = validation_state
        # Simple data store
        self._data = {(r, c): f"Data({r},{c})" for r in range(2) for c in range(2)}

    def index(self, row, col, parent=QModelIndex()):
        # Return a valid MagicMock for QModelIndex
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.row.return_value = row
        mock_index.column.return_value = col
        mock_index.isValid.return_value = True  # Ensure it's valid
        # Add mock parent() if needed, returning QModelIndex() for top-level
        mock_index.parent.return_value = QModelIndex()
        return mock_index

    def data(self, index, role):
        if not index or not index.isValid():
            return None
        if role == DataViewModel.ValidationStateRole:
            return self._validation_state
        return f"Data({index.row()},{index.column()})"  # Return something for data role

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._is_editable:
            flags |= Qt.ItemIsEditable
        return flags

    # Add mock get_correction_suggestions
    def get_correction_suggestions(self, row, col):
        # Return empty list by default for testing enablement
        if self._validation_state == CellState.CORRECTABLE:
            # Can return mock suggestions here if needed for specific tests
            return ["mock_suggestion"]  # Return something to enable the action
        return []


@pytest.fixture
def mock_qwidget(qapp):  # Need qapp for QWidget
    """Fixture for a mock parent QWidget."""
    return QWidget()


@pytest.fixture
def mock_model():
    """Fixture for a basic mock model."""
    return MockModel()


@pytest.fixture
def mock_clipboard(mocker):
    """Fixture for mocking the clipboard."""
    mock = MagicMock()
    mocker.patch.object(QGuiApplication, "clipboard", return_value=mock)
    return mock


# --- Helper Function ---


def get_actions_dict(menu: QMenu) -> typing.Dict[str, QAction]:
    """Helper to get actions from a menu by their text."""
    return {action.text(): action for action in menu.actions() if action.text()}


# --- Tests ---


class TestContextMenuFactory:
    """Tests for ContextMenuFactory."""

    def test_create_empty_menu_no_model(self, mock_qwidget):
        """Test creating a menu with no model in context."""
        info = ActionContext(
            clicked_index=QModelIndex(), selection=[], model=None, parent_widget=mock_qwidget
        )
        menu, actions = ContextMenuFactory.create_context_menu(info)
        assert isinstance(menu, QMenu)
        assert len(actions) == 0
        assert len(menu.actions()) == 0  # No actions should be added

    def test_create_menu_no_selection(self, mock_model, mock_qwidget, mock_clipboard):
        """Test menu state with no selection."""
        mock_clipboard.text.return_value = ""
        info = ActionContext(
            clicked_index=QModelIndex(),  # No valid index clicked
            selection=[],
            model=mock_model,
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)
        # actions = get_actions_dict(menu)

        assert isinstance(menu, QMenu)
        assert "copy" in actions_map
        assert "paste" in actions_map
        assert "cut" in actions_map
        assert "delete" in actions_map

        assert not actions_map["copy"].isEnabled()  # No selection
        assert not actions_map["paste"].isEnabled()  # No clipboard text & invalid target
        assert not actions_map["cut"].isEnabled()  # No selection
        assert not actions_map["delete"].isEnabled()  # No selection
        # Validation/Correction actions should not be present without valid index
        assert "view_error" not in actions_map
        assert "apply_correction" not in actions_map

    def test_create_menu_single_selection_editable(self, mock_model, mock_qwidget, mock_clipboard):
        """Test menu state with a single editable cell selected."""
        mock_clipboard.text.return_value = "some text"
        index = mock_model.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model,  # Default model is editable
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert actions_map["copy"].isEnabled()
        assert actions_map["paste"].isEnabled()  # Has clipboard text and target is editable
        assert actions_map["cut"].isEnabled()
        assert actions_map["delete"].isEnabled()
        assert "edit_cell" in actions_map
        assert "show_edit_dialog" in actions_map
        assert actions_map["edit_cell"].isEnabled()
        assert actions_map["show_edit_dialog"].isEnabled()

    def test_create_menu_single_selection_not_editable(self, mock_qwidget, mock_clipboard):
        """Test menu state with a single non-editable cell selected."""
        mock_model_not_editable = MockModel(is_editable=False)
        mock_clipboard.text.return_value = "some text"
        index = mock_model_not_editable.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_not_editable,
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert actions_map["copy"].isEnabled()  # Copy is always enabled with selection
        assert not actions_map["paste"].isEnabled()  # Target not editable
        assert not actions_map["cut"].isEnabled()  # Not editable
        assert not actions_map["delete"].isEnabled()  # Not editable
        assert "edit_cell" in actions_map
        assert "show_edit_dialog" in actions_map
        assert not actions_map["edit_cell"].isEnabled()
        assert not actions_map["show_edit_dialog"].isEnabled()

    def test_create_menu_multi_selection(self, mock_model, mock_qwidget, mock_clipboard):
        """Test menu state with multiple cells selected."""
        mock_clipboard.text.return_value = "some text"
        index1 = mock_model.index(0, 0)
        index2 = mock_model.index(0, 1)
        info = ActionContext(
            clicked_index=index1,  # Clicked on the first cell
            selection=[index1, index2],
            model=mock_model,  # Editable by default
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        # Edit actions should not be applicable/enabled for multi-selection
        assert actions_map["copy"].isEnabled()  # Standard actions can be enabled
        assert actions_map["delete"].isEnabled()

        assert "edit_cell" not in actions_map  # Or should be disabled if present
        assert "show_edit_dialog" not in actions_map  # Or should be disabled if present
        # Note: Depending on implementation, actions might be added but disabled.
        # Checking for presence OR disabled state might be more robust.
        # For now, assume is_applicable=False means they aren't added.

    def test_create_menu_invalid_cell(self, mock_qwidget, mock_clipboard):
        """Test menu includes validation action for invalid cell."""
        mock_model_invalid = MockModel(validation_state=CellState.INVALID)
        index = mock_model_invalid.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_invalid,
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert "view_error" in actions_map
        assert actions_map["view_error"].isEnabled()
        assert "apply_correction" not in actions_map

    def test_create_menu_correctable_cell(self, mock_qwidget, mock_clipboard):
        """Test menu includes correction action for correctable cell."""
        mock_model_correctable = MockModel(validation_state=CellState.CORRECTABLE)
        index = mock_model_correctable.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_correctable,
            parent_widget=mock_qwidget,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert "apply_correction" in actions_map
        assert actions_map["apply_correction"].isEnabled()
        assert "view_error" not in actions_map
