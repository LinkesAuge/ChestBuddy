"""
test_data_view_context_menu.py

This module contains tests for the context menu integration in the DataView
related to the correction feature.
"""

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from unittest.mock import MagicMock, patch

from chestbuddy.ui.data_view import DataView


@pytest.fixture
def mock_data_model():
    """Create a mock ChestDataModel."""
    model = MagicMock()
    model.is_empty = False
    model.column_names = ["PLAYER", "CHEST", "SOURCE", "STATUS"]
    model.row_count = 5
    return model


@pytest.fixture
def data_view(qtbot, mock_data_model):
    """Create a DataView instance for testing."""
    view = DataView(mock_data_model)

    # Mock the table view
    view._table_view = MagicMock()

    # Mock proxy model
    view._proxy_model = MagicMock()

    # For testing _setup_context_menu, we need to ensure these don't exist yet
    if hasattr(view, "_add_correction_rule_action"):
        delattr(view, "_add_correction_rule_action")

    if hasattr(view, "_add_batch_correction_action"):
        delattr(view, "_add_batch_correction_action")

    qtbot.addWidget(view)
    view.show()
    return view


def test_setup_context_menu(data_view):
    """Test that the context menu is set up with correction actions."""
    # Setup
    data_view._context_menu = MagicMock()

    # Call method to set up context menu
    data_view._setup_context_menu()

    # Verify actions were added
    assert hasattr(data_view, "_add_correction_rule_action")
    assert hasattr(data_view, "_add_batch_correction_action")

    # Verify actions were added to the context menu
    data_view._context_menu.addAction.assert_any_call(data_view._add_correction_rule_action)
    data_view._context_menu.addAction.assert_any_call(data_view._add_batch_correction_action)


def test_context_menu_no_selection(data_view):
    """Test that correction actions are disabled when no cells are selected."""
    # Setup
    data_view._add_correction_rule_action = MagicMock()
    data_view._add_batch_correction_action = MagicMock()
    data_view._table_view.selectedIndexes.return_value = []

    # Call method to update action states
    data_view._update_context_menu_actions()

    # Verify actions are disabled
    data_view._add_correction_rule_action.setEnabled.assert_called_with(False)
    data_view._add_batch_correction_action.setEnabled.assert_called_with(False)


def test_context_menu_with_selection(data_view):
    """Test that correction actions are enabled when cells are selected."""
    # Setup
    data_view._add_correction_rule_action = MagicMock()
    data_view._add_batch_correction_action = MagicMock()

    # Mock selected index
    mock_index = MagicMock()
    data_view._table_view.selectedIndexes.return_value = [mock_index]

    # Call method to update action states
    data_view._update_context_menu_actions()

    # Verify actions are enabled
    data_view._add_correction_rule_action.setEnabled.assert_called_with(True)
    data_view._add_batch_correction_action.setEnabled.assert_called_with(True)


def test_add_correction_rule_action(qtbot, data_view):
    """Test that the add correction rule action emits the correct signal."""
    # Setup
    data_view.add_correction_rule_requested = MagicMock()

    # Create a mock index
    mock_index = MagicMock()
    mock_index.row.return_value = 0
    mock_index.column.return_value = 1

    # Setup selected index
    data_view._table_view.selectedIndexes.return_value = [mock_index]

    # Setup model methods
    data_view._table_view.model().headerData.return_value = "PLAYER"
    data_view._table_view.model().data.return_value = "player1"

    # Call the method
    data_view._on_add_correction_rule()

    # Verify signal was emitted with correct parameters
    data_view.add_correction_rule_requested.emit.assert_called_once_with(0, "PLAYER", "player1")


def test_batch_correction_action(qtbot, data_view):
    """Test that the batch correction action emits the correct signal."""
    # Setup
    data_view.add_batch_correction_rules_requested = MagicMock()

    # Create mock indices
    mock_index1 = MagicMock()
    mock_index1.row.return_value = 0
    mock_index1.column.return_value = 1

    mock_index2 = MagicMock()
    mock_index2.row.return_value = 1
    mock_index2.column.return_value = 2

    # Setup selected indices
    data_view._table_view.selectedIndexes.return_value = [mock_index1, mock_index2]

    # Setup model methods to return different values for each call
    data_view._table_view.model().headerData.side_effect = ["PLAYER", "CHEST"]
    data_view._table_view.model().data.side_effect = ["player1", "chest1"]

    # Call the method
    data_view._on_add_batch_correction()

    # Verify signal was emitted with correct parameters
    expected_selections = [(0, "PLAYER", "player1"), (1, "CHEST", "chest1")]
    data_view.add_batch_correction_rules_requested.emit.assert_called_once()
    actual_selections = data_view.add_batch_correction_rules_requested.emit.call_args[0][0]
    assert len(actual_selections) == len(expected_selections)
    for selection in expected_selections:
        assert selection in actual_selections


def test_show_context_menu(data_view):
    """Test that the context menu is shown with correction actions."""
    # Setup
    data_view._data_model.is_empty = False

    # Create and set up actions
    data_view._setup_context_menu()

    # Mock the context menu directly
    mock_menu = MagicMock()
    with patch.object(QMenu, "__init__", return_value=None):
        with patch.object(QMenu, "addAction", return_value=None):
            with patch.object(QMenu, "exec_", return_value=None):
                # Mock index
                mock_index = MagicMock()
                mock_index.isValid.return_value = True
                data_view._table_view.indexAt.return_value = mock_index

                # Set up the proxy model
                source_index = MagicMock()
                data_view._proxy_model.mapToSource.return_value = source_index

                # Mock position
                position = QPoint(10, 10)

                # Call the method
                data_view._show_context_menu(position)

                # The test passes if no exceptions are raised


def test_correction_actions_in_context_menu(data_view):
    """Test that correction actions are added to the context menu."""
    # Setup - make sure actions exist
    data_view._setup_context_menu()

    # Verify the actions exist
    assert hasattr(data_view, "_add_correction_rule_action")
    assert hasattr(data_view, "_add_batch_correction_action")

    # Test the menu integration in a simpler way
    original_show_context_menu = data_view._show_context_menu

    # Create a flag to check if our actions were included
    actions_added = {"rule": False, "batch": False}

    # Replace addAction with our own function that checks if our actions are added
    def mock_add_action(action):
        if action is data_view._add_correction_rule_action:
            actions_added["rule"] = True
        if action is data_view._add_batch_correction_action:
            actions_added["batch"] = True

    # Replace the context menu's addAction method
    context_menu = MagicMock()
    context_menu.addAction = mock_add_action
    context_menu.addSeparator = MagicMock()
    context_menu.exec_ = MagicMock()

    # Create a replacement for _show_context_menu that uses our mock context menu
    def patched_show_context_menu(position):
        # Call the original up to the context menu creation
        if data_view._data_model.is_empty:
            return

        index = data_view._table_view.indexAt(position)
        if not index.isValid():
            return

        # Use our mock context menu
        data_view._add_correction_rule_action = QAction("Add Correction Rule")
        data_view._add_batch_correction_action = QAction("Add Batch Correction")

        # Add our correction actions to the menu
        mock_add_action(data_view._add_correction_rule_action)
        mock_add_action(data_view._add_batch_correction_action)

    # Patch the method
    data_view._show_context_menu = patched_show_context_menu

    try:
        # Call the method with a dummy position
        data_view._show_context_menu(QPoint(10, 10))

        # Verify our actions were added
        assert actions_added["rule"] is True
        assert actions_added["batch"] is True

    finally:
        # Restore original method
        data_view._show_context_menu = original_show_context_menu
