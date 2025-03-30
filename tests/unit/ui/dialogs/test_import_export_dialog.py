"""
Tests for ImportExportDialog.

This module contains test cases for the ImportExportDialog class, which provides
a dialog for importing and exporting correction rules.
"""

import pytest
from unittest.mock import MagicMock, patch
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QComboBox, QFileDialog, QMessageBox

from chestbuddy.ui.dialogs.import_export_dialog import ImportExportDialog


@pytest.fixture
def mock_file_dialog():
    """Mock QFileDialog to avoid actual file operations during tests."""
    with patch("chestbuddy.ui.dialogs.import_export_dialog.QFileDialog") as mock_dialog:
        # Configure getOpenFileName to return a file path
        mock_dialog.getOpenFileName.return_value = ("/fake/path/rules.csv", "CSV Files (*.csv)")
        # Configure getSaveFileName to return a file path
        mock_dialog.getSaveFileName.return_value = (
            "/fake/path/export_rules.csv",
            "CSV Files (*.csv)",
        )
        yield mock_dialog


@pytest.fixture
def import_dialog(qtbot):
    """Create an ImportExportDialog instance for testing importing."""
    dialog = ImportExportDialog(mode="import")
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def export_dialog(qtbot):
    """Create an ImportExportDialog instance for testing exporting."""
    dialog = ImportExportDialog(mode="export")
    qtbot.addWidget(dialog)
    return dialog


class TestImportExportDialog:
    """Test cases for the ImportExportDialog class."""

    def test_import_initialization(self, import_dialog):
        """Test that the import dialog initializes correctly."""
        # Check title and mode
        assert import_dialog.windowTitle() == "Import Correction Rules"
        assert import_dialog._mode == "import"

        # Check UI components for import mode
        assert import_dialog._file_path_edit is not None
        assert import_dialog._browse_button is not None
        assert import_dialog._format_combo is not None

        # Default format should be CSV
        assert import_dialog._format_combo.currentText() == "CSV"

    def test_export_initialization(self, export_dialog):
        """Test that the export dialog initializes correctly."""
        # Check title and mode
        assert export_dialog.windowTitle() == "Export Correction Rules"
        assert export_dialog._mode == "export"

        # Check UI components for export mode
        assert export_dialog._file_path_edit is not None
        assert export_dialog._browse_button is not None
        assert export_dialog._format_combo is not None

        # Default format should be CSV
        assert export_dialog._format_combo.currentText() == "CSV"

        # Format combo items should include CSV and JSON
        formats = [
            export_dialog._format_combo.itemText(i)
            for i in range(export_dialog._format_combo.count())
        ]
        assert "CSV" in formats
        assert "JSON" in formats

    def test_browse_button_import(self, qtbot, import_dialog, mock_file_dialog):
        """Test that browse button works correctly in import mode."""
        # Click browse button
        qtbot.mouseClick(import_dialog._browse_button, Qt.LeftButton)

        # File dialog should be called with open mode
        mock_file_dialog.getOpenFileName.assert_called_once()

        # File path should be updated
        assert import_dialog._file_path_edit.text() == "/fake/path/rules.csv"

    def test_browse_button_export(self, qtbot, export_dialog, mock_file_dialog):
        """Test that browse button works correctly in export mode."""
        # Click browse button
        qtbot.mouseClick(export_dialog._browse_button, Qt.LeftButton)

        # File dialog should be called with save mode
        mock_file_dialog.getSaveFileName.assert_called_once()

        # File path should be updated
        assert export_dialog._file_path_edit.text() == "/fake/path/export_rules.csv"

    def test_format_change(self, qtbot, import_dialog):
        """Test that changing format updates file dialog filter."""
        # Initially it should be CSV
        assert import_dialog._format_combo.currentText() == "CSV"

        # Change to JSON
        import_dialog._format_combo.setCurrentText("JSON")

        # File filter should update
        assert import_dialog._file_filter == "JSON Files (*.json)"

    def test_get_file_path(self, import_dialog):
        """Test that get_file_path returns the correct file path."""
        # Set a file path
        import_dialog._file_path_edit.setText("/test/path/rules.csv")

        # Get the file path
        path = import_dialog.get_file_path()

        # Should be what we set
        assert path == "/test/path/rules.csv"

    def test_get_format(self, import_dialog):
        """Test that get_format returns the correct format."""
        # Initially it should be CSV
        assert import_dialog.get_format() == "CSV"

        # Change to JSON
        import_dialog._format_combo.setCurrentText("JSON")

        # Should now be JSON
        assert import_dialog.get_format() == "JSON"

    def test_accept_rejects_with_no_file_path(self, import_dialog):
        """Test that accept() rejects if no file path is specified."""
        # Clear file path
        import_dialog._file_path_edit.clear()

        # Mock QDialog.accept
        with patch.object(QDialog, "accept") as mock_accept:
            # Try to accept
            import_dialog.accept()

            # Accept should not be called
            mock_accept.assert_not_called()

    def test_accept_with_valid_file_path(self, import_dialog):
        """Test that accept() works with a valid file path."""
        # Set a file path
        import_dialog._file_path_edit.setText("/test/path/rules.csv")

        # Mock QDialog.accept
        with patch.object(QDialog, "accept") as mock_accept:
            # Try to accept
            import_dialog.accept()

            # Accept should be called
            mock_accept.assert_called_once()

    def test_cancel_button(self, qtbot, import_dialog):
        """Test that the cancel button exists and has the right properties."""
        # Directly access the cancel button property
        cancel_button = import_dialog._cancel_button

        assert cancel_button is not None
        assert cancel_button.text() == "Cancel"
        assert cancel_button.isEnabled()
        assert not cancel_button.isDefault()

    def test_import_button(self, qtbot, import_dialog):
        """Test that the Import button exists and has the right properties."""
        # Set a file path
        import_dialog._file_path_edit.setText("/test/path/rules.csv")

        # Directly access the action button property
        action_button = import_dialog._action_button

        assert action_button is not None
        assert action_button.text() == "Import"
        assert action_button.isEnabled()
        assert action_button.isDefault()

    def test_export_button(self, qtbot, export_dialog):
        """Test that the Export button exists and has the right properties."""
        # Set a file path
        export_dialog._file_path_edit.setText("/test/path/export_rules.csv")

        # Directly access the action button property
        action_button = export_dialog._action_button

        assert action_button is not None
        assert action_button.text() == "Export"
        assert action_button.isEnabled()
        assert action_button.isDefault()

    def test_validate_file_path(self, import_dialog):
        """Test file path validation logic."""
        # Empty path should fail
        import_dialog._file_path_edit.clear()
        assert not import_dialog._validate_file_path()

        # Valid path should pass
        import_dialog._file_path_edit.setText("/test/path/rules.csv")
        assert import_dialog._validate_file_path()

    def test_path_with_incorrect_extension_import(self, import_dialog):
        """Test handling of incorrect file extension in import mode."""
        # Set format to CSV
        import_dialog._format_combo.setCurrentText("CSV")

        # Set path with wrong extension
        import_dialog._file_path_edit.setText("/test/path/rules.json")

        # Mock QMessageBox.question to return Yes
        with patch("PySide6.QtWidgets.QMessageBox.question", return_value=QMessageBox.Yes):
            # Mock _update_extension
            with patch.object(import_dialog, "_update_extension") as mock_update:
                import_dialog._validate_file_path()
                mock_update.assert_called_once()

    def test_update_extension(self, import_dialog):
        """Test updating file extension based on selected format."""
        # Set format to CSV
        import_dialog._format_combo.setCurrentText("CSV")

        # Set path with wrong extension (using OS-specific path format)
        test_path = str(Path("/test/path/rules.json"))
        import_dialog._file_path_edit.setText(test_path)

        # Update extension
        import_dialog._update_extension()

        # Path should be updated (with OS-specific path format)
        expected_path = str(Path("/test/path/rules.csv"))
        assert import_dialog._file_path_edit.text() == expected_path

    def test_dialog_size(self, import_dialog):
        """Test that the dialog has a reasonable size."""
        # Dialog should have a reasonable minimum size
        assert import_dialog.minimumWidth() >= 400
        assert import_dialog.minimumHeight() >= 200
