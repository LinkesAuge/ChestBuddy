"""Tests for the BatchCorrectionDialog widget."""

import pytest
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.data.widgets.batch_correction_dialog import BatchCorrectionDialog, CorrectionItem


class TestBatchCorrectionDialog:
    """Test cases for the BatchCorrectionDialog."""

    def test_dialog_initialization(self, qtbot):
        """Test that the dialog initializes correctly."""
        # Create sample correction items
        items = [
            CorrectionItem(1, 1, "Player", "JohnSmiht", "John Smith"),
            CorrectionItem(2, 1, "Player", "MaryJhonson", "Mary Johnson"),
            CorrectionItem(3, 2, "Clan", "GoldenMafia", "Golden Mafia"),
        ]

        # Create the dialog
        dialog = BatchCorrectionDialog(items)
        qtbot.addWidget(dialog)

        # Verify dialog properties
        assert dialog.windowTitle() == "Batch Correction"
        assert len(dialog.correction_items) == 3
        assert len(dialog.checkboxes) == 3

        # Verify checkboxes are all checked by default
        for checkbox in dialog.checkboxes:
            assert checkbox.isChecked()

    def test_select_deselect_all(self, qtbot):
        """Test the select all and deselect all functionality."""
        # Create sample correction items
        items = [
            CorrectionItem(1, 1, "Player", "JohnSmiht", "John Smith"),
            CorrectionItem(2, 1, "Player", "MaryJhonson", "Mary Johnson"),
        ]

        # Create the dialog
        dialog = BatchCorrectionDialog(items)
        qtbot.addWidget(dialog)

        # Test deselect all
        qtbot.mouseClick(dialog.deselect_all_btn, Qt.LeftButton)
        for checkbox in dialog.checkboxes:
            assert not checkbox.isChecked()

        # Test select all
        qtbot.mouseClick(dialog.select_all_btn, Qt.LeftButton)
        for checkbox in dialog.checkboxes:
            assert checkbox.isChecked()

    def test_apply_selected(self, qtbot):
        """Test that the dialog emits the correct signals when applying corrections."""
        # Create sample correction items
        items = [
            CorrectionItem(1, 1, "Player", "JohnSmiht", "John Smith"),
            CorrectionItem(2, 1, "Player", "MaryJhonson", "Mary Johnson"),
        ]

        # Create the dialog
        dialog = BatchCorrectionDialog(items)
        qtbot.addWidget(dialog)

        # Setup signal capture
        received_items = []
        dialog.corrections_applied.connect(lambda items: received_items.extend(items))

        # Deselect the second item
        dialog.checkboxes[1].setChecked(False)

        # Click apply button and check if correctly emitted signal
        qtbot.mouseClick(dialog.apply_btn, Qt.LeftButton)

        # Verify only the first item was included
        assert len(received_items) == 1
        assert received_items[0].original_value == "JohnSmiht"
        assert received_items[0].corrected_value == "John Smith"

    def test_static_show_method(self, qtbot, monkeypatch):
        """Test the static show_dialog method functionality."""
        # Create sample correction items
        items = [
            CorrectionItem(1, 1, "Player", "JohnSmiht", "John Smith"),
            CorrectionItem(2, 1, "Player", "MaryJhonson", "Mary Johnson"),
        ]

        # Mock the dialog.exec method to return Accepted and select the second item
        def mock_exec():
            # Emit the signal with just the second item
            dialog = monkeypatch._dialogue_instance
            selected = [dialog.correction_items[1]]
            dialog.corrections_applied.emit(selected)
            return BatchCorrectionDialog.Accepted

        # Store the dialog instance for access in the mock
        def mock_init(self, *args, **kwargs):
            monkeypatch._dialogue_instance = self
            original_init(self, *args, **kwargs)
            # Deselect first item, keep second item
            self.checkboxes[0].setChecked(False)

        # Apply monkeypatches
        original_init = BatchCorrectionDialog.__init__
        monkeypatch.setattr(BatchCorrectionDialog, "__init__", mock_init)
        monkeypatch.setattr(BatchCorrectionDialog, "exec", mock_exec)

        # Call the static method
        selected_items, accepted = BatchCorrectionDialog.show_dialog(items)

        # Verify results
        assert accepted is True
        assert len(selected_items) == 1
        assert selected_items[0].original_value == "MaryJhonson"
        assert selected_items[0].corrected_value == "Mary Johnson"
