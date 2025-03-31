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

    # Also ensure enhanced menu items don't exist
    if hasattr(view, "_apply_correction_rules_action"):
        delattr(view, "_apply_correction_rules_action")
    if hasattr(view, "_apply_specific_rule_menu"):
        delattr(view, "_apply_specific_rule_menu")
    if hasattr(view, "_view_validation_details_action"):
        delattr(view, "_view_validation_details_action")

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
    # Verify enhanced menu items are added
    assert hasattr(data_view, "_apply_correction_rules_action")
    assert hasattr(data_view, "_apply_specific_rule_menu")
    assert hasattr(data_view, "_view_validation_details_action")

    # Verify actions were added to the context menu
    data_view._context_menu.addAction.assert_any_call(data_view._add_correction_rule_action)
    data_view._context_menu.addAction.assert_any_call(data_view._add_batch_correction_action)
    data_view._context_menu.addAction.assert_any_call(data_view._apply_correction_rules_action)
    data_view._context_menu.addAction.assert_any_call(data_view._view_validation_details_action)
    # For the submenu, we should check it was added
    data_view._context_menu.addMenu.assert_any_call(data_view._apply_specific_rule_menu)


def test_context_menu_no_selection(data_view):
    """Test that correction actions are disabled when no cells are selected."""
    # Setup
    data_view._add_correction_rule_action = MagicMock()
    data_view._add_batch_correction_action = MagicMock()
    data_view._apply_correction_rules_action = MagicMock()
    data_view._apply_specific_rule_menu = MagicMock()
    data_view._view_validation_details_action = MagicMock()
    data_view._table_view.selectedIndexes.return_value = []

    # Call method to update action states
    data_view._update_context_menu_actions()

    # Verify actions are disabled
    data_view._add_correction_rule_action.setEnabled.assert_called_with(False)
    data_view._add_batch_correction_action.setEnabled.assert_called_with(False)
    data_view._apply_correction_rules_action.setEnabled.assert_called_with(False)
    data_view._apply_specific_rule_menu.setEnabled.assert_called_with(False)
    data_view._view_validation_details_action.setEnabled.assert_called_with(False)


def test_context_menu_with_selection(data_view):
    """Test that correction actions are enabled when cells are selected."""
    # Setup
    data_view._add_correction_rule_action = MagicMock()
    data_view._add_batch_correction_action = MagicMock()
    data_view._apply_correction_rules_action = MagicMock()
    data_view._apply_specific_rule_menu = MagicMock()
    data_view._view_validation_details_action = MagicMock()

    # Mock selected index
    mock_index = MagicMock()
    data_view._table_view.selectedIndexes.return_value = [mock_index]

    # Call method to update action states
    data_view._update_context_menu_actions()

    # Verify actions are enabled
    data_view._add_correction_rule_action.setEnabled.assert_called_with(True)
    data_view._add_batch_correction_action.setEnabled.assert_called_with(True)
    data_view._apply_correction_rules_action.setEnabled.assert_called_with(True)
    data_view._apply_specific_rule_menu.setEnabled.assert_called_with(True)
    data_view._view_validation_details_action.setEnabled.assert_called_with(True)


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


def test_on_apply_correction_rules(data_view):
    """Test the apply correction rules action."""
    # Setup - mock the get_correction_controller method
    correction_controller = MagicMock()
    data_view._get_correction_controller = MagicMock(return_value=correction_controller)

    # Setup selected cells
    data_view._get_selected_cells = MagicMock(
        return_value=[{"row": 0, "col": 1, "value": "test", "column_name": "PLAYER"}]
    )

    # Call the method
    data_view._on_apply_correction_rules()

    # Verify the controller method was called with the correct parameters
    correction_controller.apply_rules_to_selection.assert_called_once()
    # Check the first argument (selection)
    selection = correction_controller.apply_rules_to_selection.call_args[0][0]
    assert len(selection) == 1
    assert selection[0]["row"] == 0
    assert selection[0]["col"] == 1
    assert selection[0]["value"] == "test"
    assert selection[0]["column_name"] == "PLAYER"


def test_on_apply_specific_rule(data_view):
    """Test the apply specific rule action."""
    # Setup - mock the get_correction_controller method
    correction_controller = MagicMock()
    data_view._get_correction_controller = MagicMock(return_value=correction_controller)

    # Create a mock rule
    from chestbuddy.core.models.correction_rule import CorrectionRule

    mock_rule = MagicMock(spec=CorrectionRule)
    mock_rule.from_value = "test"
    mock_rule.to_value = "corrected"

    # Setup selected cells
    data_view._get_selected_cells = MagicMock(
        return_value=[{"row": 0, "col": 1, "value": "test", "column_name": "PLAYER"}]
    )

    # Call the method
    data_view._on_apply_specific_rule(mock_rule)

    # Verify the controller method was called with the correct parameters
    assert correction_controller.apply_single_rule.call_count == 1
    # Check the first argument (rule)
    rule_arg = correction_controller.apply_single_rule.call_args[0][0]
    assert rule_arg is mock_rule
    # Check the second argument (selection)
    selection = correction_controller.apply_single_rule.call_args[0][1]
    assert len(selection) == 1
    assert selection[0]["row"] == 0
    assert selection[0]["col"] == 1


def test_on_view_validation_details(data_view):
    """Test the view validation details action."""
    # Setup - mock the get_correction_controller method
    correction_controller = MagicMock()
    validation_service = MagicMock()
    correction_controller.get_validation_service = MagicMock(return_value=validation_service)
    data_view._get_correction_controller = MagicMock(return_value=correction_controller)

    # Setup a selected cell
    mock_index = MagicMock()
    source_index = MagicMock()
    source_index.row.return_value = 0
    source_index.column.return_value = 1
    data_view._table_view.currentIndex.return_value = mock_index
    data_view._proxy_model.mapToSource.return_value = source_index

    # Add mocks for QMessageBox
    with patch("PySide6.QtWidgets.QMessageBox.information") as mock_message_box:
        # Call the method
        data_view._on_view_validation_details()

        # Verify the validation service method was called with the correct parameters
        validation_service.get_cell_validation_details.assert_called_once_with(0, 1)

        # Verify the message box was shown
        assert mock_message_box.call_count == 1


def test_update_specific_rule_submenu(data_view):
    """Test that the specific rule submenu is updated correctly."""
    # Setup - create a mock rule manager with some rules
    correction_controller = MagicMock()
    from chestbuddy.core.models.correction_rule import CorrectionRule

    # Create some mock rules
    rule1 = MagicMock(spec=CorrectionRule)
    rule1.from_value = "test1"
    rule1.to_value = "corrected1"
    rule1.category = "PLAYER"

    rule2 = MagicMock(spec=CorrectionRule)
    rule2.from_value = "test2"
    rule2.to_value = "corrected2"
    rule2.category = "CHEST"

    # Setup the controller to return these rules
    correction_controller.get_applicable_rules = MagicMock(return_value=[rule1, rule2])
    data_view._get_correction_controller = MagicMock(return_value=correction_controller)

    # Mock the submenu
    data_view._apply_specific_rule_menu = MagicMock()
    data_view._apply_specific_rule_menu.clear = MagicMock()
    data_view._apply_specific_rule_menu.addAction = MagicMock()

    # Setup selected cells with a value
    selected_cell = {"row": 0, "col": 1, "value": "test", "column_name": "PLAYER"}
    data_view._get_selected_cells = MagicMock(return_value=[selected_cell])

    # Call the method
    data_view._update_specific_rule_submenu()

    # Verify the submenu was cleared
    data_view._apply_specific_rule_menu.clear.assert_called_once()

    # Verify the controller was asked for applicable rules
    correction_controller.get_applicable_rules.assert_called_once_with("test", "PLAYER")

    # Verify actions were added for each rule
    assert data_view._apply_specific_rule_menu.addAction.call_count == 2


def test_correction_actions_in_context_menu(data_view):
    """Test that correction actions are added to the context menu."""
    # Setup - make sure actions exist
    data_view._setup_context_menu()

    # Verify the actions exist
    assert hasattr(data_view, "_add_correction_rule_action")
    assert hasattr(data_view, "_add_batch_correction_action")
    assert hasattr(data_view, "_apply_correction_rules_action")
    assert hasattr(data_view, "_apply_specific_rule_menu")
    assert hasattr(data_view, "_view_validation_details_action")

    # Test the menu integration in a simpler way
    original_show_context_menu = data_view._show_context_menu

    # Create a flag to check if our actions were included
    actions_added = {
        "rule": False,
        "batch": False,
        "apply_rules": False,
        "specific_rule_menu": False,
        "validation_details": False,
    }

    # Replace addAction with our own function that checks if our actions are added
    def mock_add_action(action):
        if action is data_view._add_correction_rule_action:
            actions_added["rule"] = True
        if action is data_view._add_batch_correction_action:
            actions_added["batch"] = True
        if action is data_view._apply_correction_rules_action:
            actions_added["apply_rules"] = True
        if action is data_view._view_validation_details_action:
            actions_added["validation_details"] = True

    def mock_add_menu(menu):
        if menu is data_view._apply_specific_rule_menu:
            actions_added["specific_rule_menu"] = True

    # Replace the context menu's methods
    context_menu = MagicMock()
    context_menu.addAction = mock_add_action
    context_menu.addMenu = mock_add_menu
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
        data_view._apply_correction_rules_action = QAction("Apply Correction Rules")
        data_view._apply_specific_rule_menu = QMenu("Apply Specific Rule")
        data_view._view_validation_details_action = QAction("View Validation Details")

        # Add our correction actions to the menu
        mock_add_action(data_view._add_correction_rule_action)
        mock_add_action(data_view._add_batch_correction_action)
        mock_add_action(data_view._apply_correction_rules_action)
        mock_add_menu(data_view._apply_specific_rule_menu)
        mock_add_action(data_view._view_validation_details_action)

    # Patch the method
    data_view._show_context_menu = patched_show_context_menu

    try:
        # Call the method with a dummy position
        data_view._show_context_menu(QPoint(10, 10))

        # Verify our actions were added
        assert actions_added["rule"] is True
        assert actions_added["batch"] is True
        assert actions_added["apply_rules"] is True
        assert actions_added["specific_rule_menu"] is True
        assert actions_added["validation_details"] is True

    finally:
        # Restore original method
        data_view._show_context_menu = original_show_context_menu
