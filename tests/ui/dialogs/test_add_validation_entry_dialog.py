"""
Tests for the AddValidationEntryDialog.
"""

import pytest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QDialogButtonBox, QListWidget, QComboBox, QLabel
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# Assume conftest.py provides qapp fixture
# from ..conftest import qapp

from chestbuddy.ui.dialogs.add_validation_entry_dialog import AddValidationEntryDialog


# --- Fixtures ---


@pytest.fixture
def dialog(qtbot):
    """Fixture to create an instance of the dialog with default values."""
    test_values = ["ValueA", "ValueB"]
    dlg = AddValidationEntryDialog(values_to_add=test_values)
    qtbot.addWidget(dlg)  # Register dialog with qtbot for event processing
    return dlg


# --- Tests ---


def test_dialog_initialization(dialog):
    """Test the initial state of the dialog widgets."""
    assert dialog.windowTitle() == "Add to Validation List"
    assert dialog.findChild(QLabel).text().startswith("Add the following 2 value(s)")

    list_widget = dialog.findChild(QListWidget)
    assert list_widget is not None
    assert list_widget.count() == 2
    assert list_widget.item(0).text() == "ValueA"
    assert list_widget.item(1).text() == "ValueB"

    combo_box = dialog.findChild(QComboBox)
    assert combo_box is not None
    assert combo_box.count() >= 3  # Check if default items are present
    assert combo_box.currentText() == "Player"  # Check default selection

    button_box = dialog.findChild(QDialogButtonBox)
    assert button_box is not None
    assert button_box.button(QDialogButtonBox.Ok) is not None
    assert button_box.button(QDialogButtonBox.Cancel) is not None


def test_initialization_empty_values():
    """Test that initializing with an empty list raises ValueError."""
    with pytest.raises(ValueError, match="empty values list"):
        AddValidationEntryDialog(values_to_add=[])


@patch.object(AddValidationEntryDialog, "exec", return_value=AddValidationEntryDialog.Accepted)
def test_get_validation_details_accept(mock_exec, qtbot):
    """Test getting details when the dialog is accepted."""
    test_values = ["Val1", "Val2"]
    list_type = "Chest Type"
    dialog = AddValidationEntryDialog(values_to_add=test_values)
    qtbot.addWidget(dialog)

    # Change the combo box selection
    combo_box = dialog.findChild(QComboBox)
    combo_index = combo_box.findText(list_type)
    if combo_index >= 0:
        combo_box.setCurrentIndex(combo_index)
    else:
        # Add it if not found (for robustness, though ideally it should exist)
        combo_box.addItem(list_type)
        combo_box.setCurrentText(list_type)

    # Manually call accept() to populate _result before calling get_validation_details
    # because mocking exec bypasses the signal that would normally call accept.
    dialog.accept()

    details = dialog.get_validation_details()

    assert details is not None
    assert details["values"] == test_values
    assert details["list_type"] == list_type
    mock_exec.assert_called_once()  # Ensure exec was called


@patch.object(AddValidationEntryDialog, "exec", return_value=AddValidationEntryDialog.Rejected)
def test_get_validation_details_reject(mock_exec, qtbot):
    """Test getting details when the dialog is rejected."""
    test_values = ["Val1"]
    dialog = AddValidationEntryDialog(values_to_add=test_values)
    qtbot.addWidget(dialog)

    details = dialog.get_validation_details()

    assert details is None
    mock_exec.assert_called_once()


def test_dialog_interaction_accept(dialog, qtbot):
    """Simulate clicking the OK button."""
    # We need to interact with the dialog shown via exec_() or show()
    # Patching exec_ is easier for testing the result directly.
    # Here we can test the accept slot triggers correctly.
    button_box = dialog.findChild(QDialogButtonBox)
    ok_button = button_box.button(QDialogButtonBox.Ok)

    # Check initial result is None
    assert dialog._result is None

    # Simulate click
    qtbot.mouseClick(ok_button, Qt.LeftButton)

    # Check result is populated
    assert dialog._result is not None
    assert dialog._result["values"] == ["ValueA", "ValueB"]
    assert dialog._result["list_type"] == "Player"  # Default value


def test_dialog_interaction_cancel(dialog, qtbot):
    """Simulate clicking the Cancel button."""
    button_box = dialog.findChild(QDialogButtonBox)
    cancel_button = button_box.button(QDialogButtonBox.Cancel)

    # Patch reject to prevent dialog closing during test if needed
    with patch.object(dialog, "reject") as mock_reject:
        qtbot.mouseClick(cancel_button, Qt.LeftButton)
        mock_reject.assert_called_once()

    # Result should remain None
    assert dialog._result is None
