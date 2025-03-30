"""
Tests for AddEditRuleDialog.

This module contains test cases for the AddEditRuleDialog class, which provides
a dialog for adding or editing correction rules.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLineEdit, QComboBox, QRadioButton, QSpinBox

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.ui.dialogs.add_edit_rule_dialog import AddEditRuleDialog


@pytest.fixture
def mock_validation_service():
    """Create a mock ValidationService."""
    service = MagicMock()
    service.get_validation_lists.return_value = {
        "player": ["Player1", "Player2"],
        "chest_type": ["Weapon", "Shield"],
        "source": ["Dungeon", "Cave"],
    }
    return service


@pytest.fixture
def new_rule_dialog(qtbot, mock_validation_service):
    """Create an AddEditRuleDialog instance for adding a new rule."""
    dialog = AddEditRuleDialog(mock_validation_service)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def edit_rule_dialog(qtbot, mock_validation_service):
    """Create an AddEditRuleDialog instance for editing an existing rule."""
    existing_rule = CorrectionRule(
        to_value="corrected", from_value="test", category="player", status="enabled", order=5
    )
    dialog = AddEditRuleDialog(mock_validation_service, rule=existing_rule)
    qtbot.addWidget(dialog)
    return dialog


class TestAddEditRuleDialog:
    """Test cases for the AddEditRuleDialog class."""

    def test_initialization_new_rule(self, new_rule_dialog, mock_validation_service):
        """Test initialization when adding a new rule."""
        # Check that the dialog title is correct
        assert new_rule_dialog.windowTitle() == "Add Correction Rule"

        # Check that input fields are empty or have defaults
        assert new_rule_dialog._from_value.text() == ""
        assert new_rule_dialog._to_value.text() == ""
        assert new_rule_dialog._category_combo.currentText() == "general"
        assert new_rule_dialog._enabled_radio.isChecked()
        assert not new_rule_dialog._disabled_radio.isChecked()
        assert new_rule_dialog._order.value() == 0

    def test_initialization_edit_rule(self, edit_rule_dialog):
        """Test initialization when editing an existing rule."""
        # Check that the dialog title is correct
        assert edit_rule_dialog.windowTitle() == "Edit Correction Rule"

        # Check that input fields are populated with rule data
        assert edit_rule_dialog._from_value.text() == "test"
        assert edit_rule_dialog._to_value.text() == "corrected"
        assert edit_rule_dialog._category_combo.currentText() == "player"
        assert edit_rule_dialog._enabled_radio.isChecked()
        assert not edit_rule_dialog._disabled_radio.isChecked()
        assert edit_rule_dialog._order.value() == 5

    def test_get_rule(self, qtbot, new_rule_dialog):
        """Test that get_rule returns a correctly configured rule."""
        # Set the input values
        qtbot.keyClicks(new_rule_dialog._from_value, "test_from")
        qtbot.keyClicks(new_rule_dialog._to_value, "test_to")
        new_rule_dialog._category_combo.setCurrentText("chest_type")
        new_rule_dialog._disabled_radio.setChecked(True)
        new_rule_dialog._order.setValue(10)

        # Get the rule
        rule = new_rule_dialog.get_rule()

        # Check that the rule has the correct values
        assert rule.from_value == "test_from"
        assert rule.to_value == "test_to"
        assert rule.category == "chest_type"
        assert rule.status == "disabled"
        assert rule.order == 10

    def test_validation(self, qtbot, new_rule_dialog):
        """Test that validation prevents empty values."""
        # Both fields empty should fail validation
        assert not new_rule_dialog._validate_inputs()

        # Set from_value but leave to_value empty
        qtbot.keyClicks(new_rule_dialog._from_value, "test_from")
        assert not new_rule_dialog._validate_inputs()

        # Clear from_value and set to_value
        new_rule_dialog._from_value.clear()
        qtbot.keyClicks(new_rule_dialog._to_value, "test_to")
        assert not new_rule_dialog._validate_inputs()

        # Set both values
        qtbot.keyClicks(new_rule_dialog._from_value, "test_from")
        assert new_rule_dialog._validate_inputs()

    def test_accept_rejects_invalid(self, qtbot, new_rule_dialog):
        """Test that accept() rejects invalid inputs."""
        # Mock validate_inputs to return False and QDialog.accept
        with patch.object(new_rule_dialog, "_validate_inputs", return_value=False) as mock_validate:
            with patch.object(QDialog, "accept") as mock_accept:
                # Try to accept
                new_rule_dialog.accept()

                # Validate should be called but accept should not
                mock_validate.assert_called_once()
                mock_accept.assert_not_called()

    def test_accept_with_valid_inputs(self, qtbot, new_rule_dialog):
        """Test that accept() works with valid inputs."""
        # Set valid inputs
        qtbot.keyClicks(new_rule_dialog._from_value, "test_from")
        qtbot.keyClicks(new_rule_dialog._to_value, "test_to")

        # Mock QDialog.accept
        with patch.object(QDialog, "accept") as mock_accept:
            # Try to accept
            new_rule_dialog.accept()

            # Accept should be called
            mock_accept.assert_called_once()

    def test_to_validation_list_button(self, qtbot, new_rule_dialog, mock_validation_service):
        """Test that the 'Add to Validation List' button works."""
        # Set valid inputs
        qtbot.keyClicks(new_rule_dialog._from_value, "test_from")
        qtbot.keyClicks(new_rule_dialog._to_value, "test_to")
        new_rule_dialog._category_combo.setCurrentText("player")

        # Click the button
        qtbot.mouseClick(new_rule_dialog._add_to_validation_button, Qt.LeftButton)

        # Check that the validation service method was called
        mock_validation_service.add_validation_entry.assert_called_once_with("player", "test_to")

    def test_category_change_updates_validation_button(self, qtbot, new_rule_dialog):
        """Test that changing category updates the validation button state."""
        # Initially the button should be enabled for general category
        assert not new_rule_dialog._add_to_validation_button.isEnabled()

        # Change to a specific category
        new_rule_dialog._category_combo.setCurrentText("player")

        # Button should be enabled
        assert new_rule_dialog._add_to_validation_button.isEnabled()

        # Change back to general
        new_rule_dialog._category_combo.setCurrentText("general")

        # Button should be disabled again
        assert not new_rule_dialog._add_to_validation_button.isEnabled()

    def test_order_spinner_limits(self, new_rule_dialog):
        """Test that the order spinner has appropriate limits."""
        assert new_rule_dialog._order.minimum() == 0
        assert new_rule_dialog._order.maximum() >= 1000  # Should have a reasonable upper limit

    def test_cancel_button(self, qtbot, new_rule_dialog):
        """Test that the cancel button calls reject()."""
        with patch.object(QDialog, "reject") as mock_reject:
            # Click the cancel button (lookup by text)
            cancel_button = None
            for button in new_rule_dialog.findChildren(object):
                if hasattr(button, "text") and button.text() == "Cancel":
                    cancel_button = button
                    break

            assert cancel_button is not None
            qtbot.mouseClick(cancel_button, Qt.LeftButton)

            # Reject should be called
            mock_reject.assert_called_once()

    def test_status_radio_buttons(self, qtbot, new_rule_dialog):
        """Test that the status radio buttons work correctly."""
        # Default should be enabled
        assert new_rule_dialog._enabled_radio.isChecked()
        assert not new_rule_dialog._disabled_radio.isChecked()

        # Directly set disabled radio to checked, which should trigger signal handlers
        new_rule_dialog._disabled_radio.setChecked(True)

        # Disabled should be checked
        assert not new_rule_dialog._enabled_radio.isChecked()
        assert new_rule_dialog._disabled_radio.isChecked()

        # Directly set enabled radio to checked
        new_rule_dialog._enabled_radio.setChecked(True)

        # Enabled should be checked
        assert new_rule_dialog._enabled_radio.isChecked()
        assert not new_rule_dialog._disabled_radio.isChecked()

    def test_dialog_size(self, new_rule_dialog):
        """Test that the dialog has a reasonable size."""
        # Dialog should have a reasonable minimum size
        assert new_rule_dialog.minimumWidth() >= 400
        assert new_rule_dialog.minimumHeight() >= 200
