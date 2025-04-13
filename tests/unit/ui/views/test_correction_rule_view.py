"""
Tests for CorrectionRuleView.

This module contains test cases for the CorrectionRuleView class, which provides
a user interface for managing and applying correction rules.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from typing import List, Dict, Any, Optional

import pandas as pd
from PySide6.QtCore import Qt, Signal, QModelIndex, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QTableWidget,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QWidget,
    QMessageBox,
    QMenu,
    QAbstractItemView,
)

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.ui.views.correction_rule_view import CorrectionRuleView


@pytest.fixture
def mock_correction_controller():
    """Create a mock CorrectionController with necessary methods and properties."""
    controller = MagicMock()

    # Mock rule data
    rules = [
        CorrectionRule("test1", "corrected1", "general", "enabled"),
        CorrectionRule("test2", "corrected2", "player", "enabled"),
        CorrectionRule("test3", "corrected3", "chest_type", "disabled"),
    ]

    # Setup controller methods that the view will call
    controller.get_rules.return_value = rules
    controller.get_rules_by_category = MagicMock(return_value=rules)
    controller.add_rule.return_value = True
    controller.update_rule.return_value = True
    controller.delete_rule.return_value = True
    controller.reorder_rule.return_value = True
    controller.toggle_rule_status.return_value = True
    controller.move_rule_to_top.return_value = True
    controller.move_rule_to_bottom.return_value = True
    controller.apply_corrections.return_value = None
    controller.apply_single_rule.return_value = True
    controller.import_rules.return_value = True
    controller.export_rules.return_value = True

    return controller


@pytest.fixture
def correction_rule_view(qtbot, mock_correction_controller):
    """Create a CorrectionRuleView instance for testing."""
    view = CorrectionRuleView(mock_correction_controller)
    qtbot.addWidget(view)
    view.show()
    return view


class TestCorrectionRuleView:
    """Test cases for the CorrectionRuleView class."""

    def test_initialization(self, correction_rule_view, mock_correction_controller):
        """Test that the view initializes correctly with all components."""
        # Check that the controller is set
        assert correction_rule_view._controller == mock_correction_controller

        # Check that UI components are created
        assert correction_rule_view._rule_table is not None
        assert correction_rule_view._filter_controls is not None
        assert correction_rule_view._rule_controls is not None
        assert correction_rule_view._settings_panel is not None

        # Check that the title is set correctly
        assert correction_rule_view.windowTitle() == "Correction Rules"

    def test_ui_components_created(self, correction_rule_view):
        """Test that all UI components are created and laid out correctly."""
        # Check filter controls
        assert isinstance(correction_rule_view._category_filter, QComboBox)
        assert isinstance(correction_rule_view._status_filter, QComboBox)
        assert isinstance(correction_rule_view._search_edit, QLineEdit)

        # Check rule table
        assert isinstance(correction_rule_view._rule_table, QTableWidget)
        assert correction_rule_view._rule_table.model() is not None

        # Check rule controls
        assert correction_rule_view._add_button is not None
        assert correction_rule_view._edit_button is not None
        assert correction_rule_view._delete_button is not None
        assert correction_rule_view._move_up_button is not None
        assert correction_rule_view._move_down_button is not None
        assert correction_rule_view._move_top_button is not None
        assert correction_rule_view._move_bottom_button is not None
        assert correction_rule_view._toggle_status_button is not None

        # Check settings panel
        assert correction_rule_view._recursive_checkbox is not None
        assert correction_rule_view._correct_invalid_only_checkbox is not None
        assert correction_rule_view._apply_button is not None

    def test_header_actions(self, correction_rule_view):
        """Test that action buttons are added and connected."""
        # Check that the apply button exists
        assert correction_rule_view._apply_button is not None
        assert correction_rule_view._apply_button.text() == "Apply Corrections"

        # Check that Import/Export buttons exist in the header
        assert hasattr(correction_rule_view, "_import_button"), "Import button should exist"
        assert hasattr(correction_rule_view, "_export_button"), "Export button should exist"

        assert correction_rule_view._import_button is not None
        assert correction_rule_view._export_button is not None

        assert correction_rule_view._import_button.text() == "Import Rules"
        assert correction_rule_view._export_button.text() == "Export Rules"

    def test_rule_table_population(self, correction_rule_view, mock_correction_controller):
        """Test that the rule table is populated correctly with rules."""
        # Reset the mock to clear previous calls
        mock_correction_controller.get_rules.reset_mock()

        # Manually call refresh to ensure it's called only once
        correction_rule_view._refresh_rule_table()

        # Check that get_rules was called to populate the table
        mock_correction_controller.get_rules.assert_called_once_with(
            category="", status="", search_term=""
        )

        # Check that the table has the correct number of rows
        assert correction_rule_view._rule_table.rowCount() == 3

        # Check column headers
        headers = [
            correction_rule_view._rule_table.horizontalHeaderItem(i).text() for i in range(5)
        ]
        assert "Order" in headers
        assert "From" in headers
        assert "To" in headers
        assert "Category" in headers
        assert "Status" in headers

    def test_filter_controls(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test that filter controls work correctly."""
        # Reset the mock to clear previous calls
        mock_correction_controller.get_rules.reset_mock()

        # Directly call the filter changed method
        correction_rule_view._current_filter["category"] = "player"
        correction_rule_view._refresh_rule_table()

        # Verify controller was called with expected parameters
        mock_correction_controller.get_rules.assert_called()

        # Also verify that the filter controls exist and have the expected types
        assert isinstance(correction_rule_view._category_filter, QComboBox)
        assert isinstance(correction_rule_view._status_filter, QComboBox)
        assert isinstance(correction_rule_view._search_edit, QLineEdit)

    def test_add_rule(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test adding a new rule."""
        # Mock the add_rule_dialog to return a new rule
        new_rule = CorrectionRule("new", "corrected", "general", "enabled")
        with patch("chestbuddy.ui.views.correction_rule_view.AddEditRuleDialog") as MockDialog:
            mock_dialog = MockDialog.return_value
            mock_dialog.exec.return_value = True
            mock_dialog.get_rule.return_value = new_rule

            # Click the add button
            qtbot.mouseClick(correction_rule_view._add_button, Qt.LeftButton)

            # Check that the dialog was shown
            MockDialog.assert_called_once()

            # Check that add_rule was called with the new rule
            mock_correction_controller.add_rule.assert_called_once_with(new_rule)

            # Check that the table was refreshed
            mock_correction_controller.get_rules.assert_called()

    def test_edit_rule(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test editing an existing rule functionality exists."""
        # Verify the edit button exists
        assert correction_rule_view._edit_button is not None
        assert hasattr(correction_rule_view, "_on_edit_rule")

        # Set a row in the table
        correction_rule_view._rule_table.selectRow(1)

        # Force enable the button
        correction_rule_view._edit_button.setEnabled(True)

        # Directly call the edit method instead of clicking
        with patch("chestbuddy.ui.views.correction_rule_view.AddEditRuleDialog") as MockDialog:
            mock_dialog = MockDialog.return_value
            mock_dialog.exec.return_value = True
            mock_dialog.get_rule.return_value = CorrectionRule(
                "updated", "corrected", "general", "enabled"
            )

            # Call the method directly
            correction_rule_view._on_edit_rule()

            # Verify dialog was created
            MockDialog.assert_called_once()

    def test_delete_rule(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test deleting a rule functionality exists."""
        # Verify the delete button exists
        assert correction_rule_view._delete_button is not None
        assert hasattr(correction_rule_view, "_on_delete_rule")

        # Set a row in the table
        correction_rule_view._rule_table.selectRow(1)

        # Force enable the button
        correction_rule_view._delete_button.setEnabled(True)

        # Directly call the delete method with mocked confirmation
        with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes):
            # Call the method directly
            correction_rule_view._on_delete_rule()

            # Verify controller method was called
            mock_correction_controller.delete_rule.assert_called_once_with(1)

    def test_reorder_rule(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test reordering rules functionality exists."""
        # Verify the move buttons exist
        assert correction_rule_view._move_up_button is not None
        assert correction_rule_view._move_down_button is not None
        assert correction_rule_view._move_top_button is not None
        assert correction_rule_view._move_bottom_button is not None

        # Verify the handler methods exist
        assert hasattr(correction_rule_view, "_on_move_rule_up")
        assert hasattr(correction_rule_view, "_on_move_rule_down")
        assert hasattr(correction_rule_view, "_on_move_rule_to_top")
        assert hasattr(correction_rule_view, "_on_move_rule_to_bottom")

        # Set a row in the table
        correction_rule_view._rule_table.selectRow(1)

        # Directly call the reorder methods
        correction_rule_view._on_move_rule_up()

        # Verify controller method was called
        mock_correction_controller.reorder_rule.assert_called()

    def test_toggle_rule_status(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test toggling rule status functionality exists."""
        # Verify the toggle button exists
        assert correction_rule_view._toggle_status_button is not None
        assert hasattr(correction_rule_view, "_on_toggle_status")

        # Set a row in the table
        correction_rule_view._rule_table.selectRow(1)

        # Directly call the toggle method
        correction_rule_view._on_toggle_status()

        # Verify controller method was called
        mock_correction_controller.toggle_rule_status.assert_called()

    def test_apply_corrections(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test applying corrections."""
        # Click the apply button in the header actions
        correction_rule_view._on_action_clicked("apply")

        # Check that apply_corrections was called
        # By default, correct_invalid_only should be checked, so should pass True
        mock_correction_controller.apply_corrections.assert_called_once_with(only_invalid=True)

        # Uncheck the correct_invalid_only checkbox
        correction_rule_view._correct_invalid_only_checkbox.setChecked(False)

        # Click the apply button again
        correction_rule_view._on_action_clicked("apply")

        # Check that apply_corrections was called with only_invalid=False
        mock_correction_controller.apply_corrections.assert_called_with(only_invalid=False)

    def test_import_export_rules(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test importing and exporting rules."""
        # Store the original method
        original_method = correction_rule_view._show_import_export_dialog

        # Create a tracking function
        called = [False]

        def mock_show_import_export_dialog(export_mode=False):
            called[0] = True

        correction_rule_view._show_import_export_dialog = mock_show_import_export_dialog

        # Call the method directly
        correction_rule_view._on_action_clicked("import")

        # Check that the method was called
        assert called[0]

    def test_settings_panel(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test that settings panel controls work correctly."""
        # Test recursive checkbox
        assert correction_rule_view._recursive_checkbox is not None
        assert correction_rule_view._recursive_checkbox.isChecked() == True

        qtbot.mouseClick(correction_rule_view._recursive_checkbox, Qt.LeftButton)
        assert correction_rule_view._recursive_checkbox.isChecked() == False

        # Test only invalid cells checkbox
        assert correction_rule_view._correct_invalid_only_checkbox is not None
        assert correction_rule_view._correct_invalid_only_checkbox.isChecked() == True

        qtbot.mouseClick(correction_rule_view._correct_invalid_only_checkbox, Qt.LeftButton)
        assert correction_rule_view._correct_invalid_only_checkbox.isChecked() == False

    def test_update_status_bar(self, correction_rule_view, mock_correction_controller):
        """Test that the status bar is updated correctly with proper format."""
        # Mock the rule counts
        mock_correction_controller.get_rules.return_value = [
            CorrectionRule("test1", "corrected1", "general", "enabled"),
            CorrectionRule("test2", "corrected2", "player", "enabled"),
            CorrectionRule("test3", "corrected3", "chest_type", "disabled"),
            CorrectionRule("test4", "corrected4", "source", "disabled"),
        ]

        # Update the status bar
        correction_rule_view._update_status_bar()

        # Check that the status bar exists
        assert correction_rule_view._status_bar is not None

        # Check the content follows the expected format
        status_text = correction_rule_view._status_bar.currentMessage()
        assert "Total rules: 4" in status_text
        assert "Enabled: 2" in status_text
        assert "Disabled: 2" in status_text

        # Test updating counts with different data
        mock_correction_controller.get_rules.return_value = [
            CorrectionRule("test1", "corrected1", "general", "enabled"),
            CorrectionRule("test3", "corrected3", "chest_type", "disabled"),
        ]

        # Force update again
        correction_rule_view._update_status_bar()

        # Verify new counts
        status_text = correction_rule_view._status_bar.currentMessage()
        assert "Total rules: 2" in status_text
        assert "Enabled: 1" in status_text
        assert "Disabled: 1" in status_text

    def test_context_menu(self, qtbot, correction_rule_view, mock_correction_controller):
        """Test the rule table has expected structure for context menu."""
        # Verify the rule table exists
        assert correction_rule_view._rule_table is not None

        # Check basic properties needed for context menu to work
        assert correction_rule_view._rule_table.selectionBehavior() == QAbstractItemView.SelectRows
        assert correction_rule_view._rule_table.selectionMode() == QAbstractItemView.SingleSelection

    def test_selection_handling(self, qtbot, correction_rule_view):
        """Test that button states update based on selection."""
        # Initially, with no selection, editing buttons should be disabled
        assert not correction_rule_view._edit_button.isEnabled()
        assert not correction_rule_view._delete_button.isEnabled()
        assert not correction_rule_view._move_up_button.isEnabled()
        assert not correction_rule_view._move_down_button.isEnabled()
        assert not correction_rule_view._move_top_button.isEnabled()
        assert not correction_rule_view._move_bottom_button.isEnabled()
        assert not correction_rule_view._toggle_status_button.isEnabled()

        # Force an update of button states to simulate selection
        correction_rule_view._update_button_states()
