"""
Tests for the ContextMenuFactory.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QWidget, QMenu

from chestbuddy.ui.data.menus.context_menu_factory import ContextMenuFactory
from chestbuddy.ui.data.context.action_context import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel  # Assume real model

# --- Test Fixtures ---


@pytest.fixture
def mock_model():
    """Creates a mock DataViewModel."""
    model = MagicMock(spec=DataViewModel)
    model.rowCount.return_value = 5
    model.columnCount.return_value = 4
    model.headerData.side_effect = (
        lambda col, orient: f"Column {col}" if orient == Qt.Horizontal else None
    )
    return model


@pytest.fixture
def mock_widget():
    """Creates a mock parent QWidget."""
    return MagicMock(spec=QWidget)


@pytest.fixture
def mock_table_state_manager():
    """Creates a mock table state manager."""
    return MagicMock()


@pytest.fixture
def mock_context_factory(mocker, mock_table_state_manager):
    """Factory to create mock ActionContext instances."""

    def _factory(
        model=None,
        clicked_index=QModelIndex(),
        selection=None,
        parent_widget=None,
        state_manager=mock_table_state_manager,  # Default to mock
        correction_service=None,
        validation_service=None,
    ):
        return ActionContext(
            clicked_index=clicked_index,
            selection=selection
            if selection is not None
            else ([clicked_index] if clicked_index.isValid() else []),
            model=model or mocker.MagicMock(spec=DataViewModel),
            parent_widget=parent_widget or mocker.MagicMock(spec=QWidget),
            state_manager=state_manager,  # Use provided or default mock
            correction_service=correction_service,
            validation_service=validation_service,
        )

    return _factory


@pytest.fixture
def base_context(mock_model, mock_table_state_manager):
    """Creates a base ActionContext."""
    return ActionContext(
        clicked_index=QModelIndex(),
        selection=[],
        model=mock_model,
        parent_widget=None,
        state_manager=mock_table_state_manager,
    )


@pytest.fixture
def single_cell_context(mock_model, mock_table_state_manager):
    """Creates an ActionContext for a single cell click."""
    clicked_index = mock_model.index(1, 1)
    return ActionContext(
        clicked_index=clicked_index,
        selection=[clicked_index],
        model=mock_model,
        parent_widget=None,
        state_manager=mock_table_state_manager,
    )


@pytest.fixture
def date_column_context(mock_model, mock_table_state_manager):
    """Creates context for clicking a 'Date' column."""
    mock_model.headerData.side_effect = (
        lambda col, orient: "Date Column"
        if col == 3 and orient == Qt.Horizontal
        else f"Column {col}"
    )
    clicked_index = mock_model.index(1, 3)
    return ActionContext(
        clicked_index=clicked_index,
        selection=[clicked_index],
        model=mock_model,
        parent_widget=None,
        state_manager=mock_table_state_manager,
    )


@pytest.fixture
def score_column_context(mock_model, mock_table_state_manager):
    """Creates context for clicking a 'Score' column."""
    mock_model.headerData.side_effect = (
        lambda col, orient: "Score Column"
        if col == 2 and orient == Qt.Horizontal
        else f"Column {col}"
    )
    clicked_index = mock_model.index(1, 2)
    return ActionContext(
        clicked_index=clicked_index,
        selection=[clicked_index],
        model=mock_model,
        parent_widget=None,
        state_manager=mock_table_state_manager,
    )


# --- Test Cases ---


class TestContextMenuFactoryIntegration:  # Example class name
    def test_create_context_menu_basic_actions(self, base_context):
        menu, actions = ContextMenuFactory.create_context_menu(base_context)

        assert isinstance(menu, QMenu)
        # Check standard actions (Copy, Paste, Cut, Delete might be disabled but present)
        assert "copy" in actions
        assert "paste" in actions
        assert "cut" in actions
        assert "delete" in actions
        assert "edit_cell" not in actions  # Requires single selection
        assert "show_edit_dialog" not in actions  # Requires single selection

    def test_create_context_menu_single_selection(self, single_cell_context):
        menu, actions = ContextMenuFactory.create_context_menu(single_cell_context)

        assert "copy" in actions
        assert "paste" in actions
        assert "cut" in actions
        assert "delete" in actions
        assert "edit_cell" in actions
        assert "show_edit_dialog" in actions
        assert "add_correction" in actions  # Assuming AddToCorrectionListAction is applicable

        # Check that cell-type specific placeholders are NOT present for a generic column
        action_texts = [a.text() for a in menu.actions()]
        assert not any("Format Date" in text for text in action_texts)
        assert not any("Number Format" in text for text in action_texts)

    def test_create_context_menu_date_column(self, date_column_context):
        menu, actions = ContextMenuFactory.create_context_menu(date_column_context)

        assert "copy" in actions
        assert "edit_cell" in actions

        action_texts = [a.text() for a in menu.actions()]
        assert any("Format Date (DATE)" in text for text in action_texts)
        assert not any("Number Format" in text for text in action_texts)

        # Verify the placeholder action is disabled
        date_action = next((a for a in menu.actions() if "Format Date" in a.text()), None)
        assert date_action is not None
        assert not date_action.isEnabled()

    def test_create_context_menu_score_column(self, score_column_context):
        menu, actions = ContextMenuFactory.create_context_menu(score_column_context)

        assert "copy" in actions
        assert "edit_cell" in actions

        action_texts = [a.text() for a in menu.actions()]
        assert not any("Format Date" in text for text in action_texts)
        assert any("Number Format (SCORE)" in text for text in action_texts)

        # Verify the placeholder action is disabled
        num_action = next((a for a in menu.actions() if "Number Format" in a.text()), None)
        assert num_action is not None
        assert not num_action.isEnabled()

    def test_create_context_menu_no_model(self, mock_table_state_manager):
        """Test menu creation when no model is provided."""
        context_no_model = ActionContext(
            clicked_index=QModelIndex(),
            selection=[],
            model=None,
            parent_widget=None,
            state_manager=mock_table_state_manager,
        )
        menu, actions = ContextMenuFactory.create_context_menu(context_no_model)
        assert len(menu.actions()) == 0
        assert len(actions) == 0


# TODO: Add tests for other actions (ViewError, ApplyCorrection, AddToCorrectionList)
#       These will depend on the specific context (e.g., cell state) provided in ActionContext.
#       We need to mock the is_applicable and is_enabled methods of these actions
#       or provide more detailed ActionContext fixtures.
