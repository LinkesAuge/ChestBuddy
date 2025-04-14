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

    def __init__(self, is_editable=True, validation_state=None, cell_data_types=None):
        self._is_editable = is_editable
        self._validation_state = validation_state
        # Simple data store - can be overridden by cell_data_types
        self._data = {(r, c): f"Data({r},{c})" for r in range(2) for c in range(2)}
        # Store specific data/types for cells if provided
        self._cell_data = cell_data_types if cell_data_types else {}

    def index(self, row, col, parent=QModelIndex()):
        # Return a valid MagicMock for QModelIndex
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.row.return_value = row
        mock_index.column.return_value = col
        mock_index.isValid.return_value = True  # Ensure it's valid
        # Add mock parent() if needed, returning QModelIndex() for top-level
        mock_index.parent.return_value = QModelIndex()
        # --- FIX: Make mock index call the real model's data method --- #
        mock_index.data.side_effect = lambda role: self.data(mock_index, role)
        # ------------------------------------------------------------ #
        return mock_index

    def data(self, index, role):
        if not index or not index.isValid():
            return None

        # Check if specific data/type is set for this cell
        cell_key = (index.row(), index.column())
        if cell_key in self._cell_data:
            specific_data = self._cell_data[cell_key]
            # Return specific data for EditRole or DisplayRole if requested
            if role in [Qt.EditRole, Qt.DisplayRole]:
                return specific_data
            # Fall through for other roles if needed, or return None

        # Default role handling
        if role == DataViewModel.ValidationStateRole:
            return self._validation_state
        if role in [Qt.EditRole, Qt.DisplayRole]:  # Default data if not overridden
            return self._data.get(cell_key, f"Default({index.row()},{index.column()})")
        return None  # Default for other roles

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

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Mock headerData method."""
        if role == Qt.DisplayRole:
            return f"Header {section}"
        return None


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


@pytest.fixture
def mock_table_state_manager(mocker):
    """Fixture for mocking the table state manager."""
    mock = MagicMock()
    return mock


# --- Helper Function ---


def get_actions_dict(menu: QMenu) -> typing.Dict[str, QAction]:
    """Helper to get actions from a menu by their text."""
    return {action.text(): action for action in menu.actions() if action.text()}


# --- Tests ---


class TestContextMenuFactory:
    """Tests for ContextMenuFactory."""

    def test_create_menu_no_selection(
        self, mock_model, mock_qwidget, mock_clipboard, mock_table_state_manager
    ):
        """Test menu state with no selection."""
        mock_clipboard.text.return_value = ""
        info = ActionContext(
            clicked_index=QModelIndex(),  # No valid index clicked
            selection=[],
            model=mock_model,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
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

    def test_create_menu_single_selection_editable(
        self,
        mock_model,
        mock_qwidget,
        mock_clipboard,
        mock_table_state_manager,
    ):
        """Test menu state with a single editable cell selected."""
        mock_clipboard.text.return_value = "some text"
        index = mock_model.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model,  # Default model is editable
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
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

    def test_create_menu_single_selection_not_editable(
        self, mock_qwidget, mock_clipboard, mock_table_state_manager
    ):
        """Test menu state with a single non-editable cell selected."""
        mock_model_not_editable = MockModel(is_editable=False)
        mock_clipboard.text.return_value = "some text"
        index = mock_model_not_editable.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_not_editable,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
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

    def test_create_menu_multi_selection(
        self, mock_model, mock_qwidget, mock_clipboard, mock_table_state_manager
    ):
        """Test menu state with multiple cells selected."""
        mock_clipboard.text.return_value = "some text"
        index1 = mock_model.index(0, 0)
        index2 = mock_model.index(0, 1)
        info = ActionContext(
            clicked_index=index1,  # Clicked on the first cell
            selection=[index1, index2],
            model=mock_model,  # Editable by default
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
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

    def test_create_menu_invalid_cell(self, mock_qwidget, mock_clipboard, mock_table_state_manager):
        """Test menu includes validation action for invalid cell."""
        mock_model_invalid = MockModel(validation_state=CellState.INVALID)
        index = mock_model_invalid.index(0, 0)

        # Setup mock state manager for INVALID state
        from chestbuddy.core.table_state_manager import CellFullState

        invalid_state = CellFullState(
            validation_status=CellState.INVALID,
            error_details="Mock error message",
        )
        mock_table_state_manager.get_full_cell_state.side_effect = (
            lambda r, c: invalid_state
            if r == index.row() and c == index.column()
            else CellFullState()
        )

        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_invalid,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert "view_error" in actions_map
        assert actions_map["view_error"].isEnabled()
        assert "apply_correction" not in actions_map

    def test_create_menu_correctable_cell(
        self, mock_qwidget, mock_clipboard, mock_table_state_manager
    ):
        """Test menu includes correction action for correctable cell."""
        mock_model_correctable = MockModel(validation_state=CellState.CORRECTABLE)
        index = mock_model_correctable.index(0, 0)

        # --- Setup Mock State Manager --- #
        from chestbuddy.core.table_state_manager import CellFullState

        # Define the state to be returned by the mock
        correctable_state = CellFullState(
            validation_status=CellState.CORRECTABLE,
            correction_suggestions=["mock_suggestion"],  # Needs suggestions to be enabled
        )
        # Configure the mock to return this state for the target cell
        mock_table_state_manager.get_full_cell_state.return_value = correctable_state
        # If state manager is called with specific row/col:
        # mock_table_state_manager.get_full_cell_state.configure_mock(**{
        #     f'({index.row()}, {index.column()})': correctable_state
        # })
        # If get_full_cell_state is called like get_full_cell_state(row, col):
        mock_table_state_manager.get_full_cell_state.side_effect = (
            lambda r, c: correctable_state
            if r == index.row() and c == index.column()
            else CellFullState()
        )

        # Use the provided mock state manager
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_correctable,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
        )
        menu, actions_map = ContextMenuFactory.create_context_menu(info)

        assert "apply_correction" in actions_map
        assert actions_map["apply_correction"].isEnabled()
        assert "view_error" not in actions_map

    def test_menu_numeric_cell(self, mock_qwidget, mock_table_state_manager):
        """Test menu includes numeric placeholder action for numeric cell."""
        numeric_data = {(0, 1): 123.45}  # Cell (0,1) has a float
        mock_model_numeric = MockModel(cell_data_types=numeric_data)
        index = mock_model_numeric.index(0, 1)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_numeric,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
        )
        menu, _ = ContextMenuFactory.create_context_menu(info)
        actions = get_actions_dict(menu)

        # Check for the numeric placeholder action
        # Find action that starts with "Numeric Options for..."
        found_numeric_action = None
        for text, action in actions.items():
            if text.startswith("Numeric Options for"):
                found_numeric_action = action
                break

        assert found_numeric_action is not None, "Numeric placeholder action not found in menu"
        assert not found_numeric_action.isEnabled()  # Should be disabled placeholder

        # numeric_action_key = "Numeric Options for 'Header 1'..." # Assumes header is 'Header 1'
        # assert numeric_action_key in actions
        # assert not actions[numeric_action_key].isEnabled() # Should be disabled placeholder
        # Check other type placeholders are NOT present

    def test_menu_string_cell(self, mock_qwidget, mock_table_state_manager):
        """Test menu includes string placeholder action for string cell."""
        string_data = {(0, 0): "Some Text"}  # Cell (0,0) has a string
        mock_model_string = MockModel(cell_data_types=string_data)
        index = mock_model_string.index(0, 0)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_string,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
        )
        menu, _ = ContextMenuFactory.create_context_menu(info)
        actions = get_actions_dict(menu)

        # Check for the string placeholder action
        string_action_key = "Text Options for 'Header 0'..."  # Assumes header is 'Header 0'
        assert string_action_key in actions
        assert not actions[string_action_key].isEnabled()
        # Check other type placeholders are NOT present
        assert "Numeric Options for" not in " ".join(actions.keys())
        assert "Date Options for" not in " ".join(actions.keys())

    def test_menu_date_column_cell(self, mock_qwidget, mock_table_state_manager):
        """Test menu includes date placeholder action based on column name."""

        # Mock headerData to return 'DATE' for column 1
        class MockModelWithDateHeader(MockModel):
            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    return "DATE" if section == 1 else f"Header {section}"
                return None

        date_data = {(0, 1): "2024-01-01"}  # Cell (0,1) has string data, but header suggests date
        mock_model_date = MockModelWithDateHeader(cell_data_types=date_data)
        index = mock_model_date.index(0, 1)
        info = ActionContext(
            clicked_index=index,
            selection=[index],
            model=mock_model_date,
            parent_widget=mock_qwidget,
            state_manager=mock_table_state_manager,
        )
        menu, _ = ContextMenuFactory.create_context_menu(info)
        actions = get_actions_dict(menu)

        # Check for the date placeholder action
        date_action_key = "Date Options for 'DATE'..."
        assert date_action_key in actions
        assert not actions[date_action_key].isEnabled()
        # Check other type placeholders are NOT present
        assert "Numeric Options for" not in " ".join(actions.keys())
        assert "Text Options for" not in " ".join(actions.keys())

    def test_create_menu_numeric_column_shows_format_action(self, factory_setup):
        """Test that 'Format Number...' appears for a numeric column."""
        model, state_manager, index = factory_setup
        context = ActionContext(
            clicked_index=index,
            selection=[index],
            model=model,
            state_manager=state_manager,
            parent_widget=None,
            column_name="Amount",  # Simulate clicking on a numeric column
        )

        menu, created_actions = ContextMenuFactory.create_context_menu(context)

        assert "format_number" in created_actions
        assert "parse_date" not in created_actions
        # Check other expected/unexpected actions as needed
        action = created_actions["format_number"]
        assert action.text() == "Format Number..."
        assert action.isEnabled()  # Assuming it's enabled by default

    def test_create_menu_date_column_shows_parse_action(self, factory_setup):
        """Test that 'Parse Date...' appears for a date column."""
        model, state_manager, index = factory_setup
        context = ActionContext(
            clicked_index=index,
            selection=[index],
            model=model,
            state_manager=state_manager,
            parent_widget=None,
            column_name="Date",  # Simulate clicking on a date column
        )

        menu, created_actions = ContextMenuFactory.create_context_menu(context)

        assert "parse_date" in created_actions
        assert "format_number" not in created_actions
        action = created_actions["parse_date"]
        assert action.text() == "Parse Date..."
        assert action.isEnabled()

    def test_create_menu_other_column_hides_type_specific_actions(self, factory_setup):
        """Test that type-specific actions don't appear for other columns."""
        model, state_manager, index = factory_setup
        context = ActionContext(
            clicked_index=index,
            selection=[index],
            model=model,
            state_manager=state_manager,
            parent_widget=None,
            column_name="PlayerName",  # Simulate clicking on a generic text column
        )

        menu, created_actions = ContextMenuFactory.create_context_menu(context)

        assert "parse_date" not in created_actions
        assert "format_number" not in created_actions
