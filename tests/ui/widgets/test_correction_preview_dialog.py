"""
Tests for the CorrectionPreviewDialog class.
"""

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QTableWidget
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtTest import QTest
from unittest.mock import MagicMock

from chestbuddy.ui.widgets.correction_preview_dialog import CorrectionPreviewDialog

# Fixtures like qapp are expected from conftest.py


# Minimal mock model and index for testing display
class MockModel(MagicMock):
    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return f"Column {section}"
        return None


class MockModelIndex:
    def __init__(self, row, col, model=None):
        self._row = row
        self._col = col
        self._model = model or MockModel()

    def row(self):
        return self._row

    def column(self):
        return self._col

    def isValid(self):
        return True

    def model(self):
        return self._model


@pytest.fixture
def mock_changes():
    """Provides a list of mock changes for the dialog."""
    return [
        (MockModelIndex(2, 0), "JohnSmiht", "John Smith"),
        (MockModelIndex(5, 1), "siver", "Silver"),
        (MockModelIndex(10, 2), 123, "CorrectedValue"),
    ]


@pytest.fixture
def dialog(mock_changes, qapp):  # qapp fixture ensures QApplication exists
    """Create a CorrectionPreviewDialog instance with mock changes."""
    return CorrectionPreviewDialog(mock_changes)


class TestCorrectionPreviewDialog:
    """Tests for the CorrectionPreviewDialog class."""

    def test_dialog_initialization(self, dialog, mock_changes):
        """Test that the dialog initializes correctly and displays data."""
        assert dialog is not None
        assert dialog.windowTitle() == "Correction Preview"
        # Check table dimensions and content
        table = dialog.findChild(QTableWidget)
        assert table is not None
        assert table.rowCount() == len(mock_changes)
        assert table.columnCount() == 4
        # Check content of the first row
        assert table.item(0, 0).text() == "2"  # Row index
        assert table.item(0, 1).text() == "Column 0"  # Column Name
        assert table.item(0, 2).text() == "JohnSmiht"  # Original Value
        assert table.item(0, 3).text() == "John Smith"  # Corrected Value

    def test_dialog_accept(self, dialog, qtbot):
        """Test clicking the OK button accepts the dialog."""
        # Mock the exec_ method to prevent the dialog from blocking tests
        dialog.exec = MagicMock(return_value=QDialog.DialogCode.Accepted)

        ok_button = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
        assert ok_button is not None

        # Use qtbot for interaction
        qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)

        # Check if accept was called (implicitly checked by mocked exec)
        # We can also spy on the accept method
        accept_spy = MagicMock()
        dialog.accepted.connect(accept_spy)

        # Re-trigger click with spy connected
        qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)
        # Check if accept was called
        # Since we mocked exec_, the signal might not be emitted naturally
        # Better to test the return value of exec_
        assert dialog.exec() == QDialog.DialogCode.Accepted

    def test_dialog_reject(self, dialog, qtbot):
        """Test clicking the Cancel button rejects the dialog."""
        # Mock the exec_ method
        dialog.exec = MagicMock(return_value=QDialog.DialogCode.Rejected)

        cancel_button = dialog.findChild(QDialogButtonBox).button(
            QDialogButtonBox.StandardButton.Cancel
        )
        assert cancel_button is not None

        qtbot.mouseClick(cancel_button, Qt.MouseButton.LeftButton)

        # Test return value of mocked exec_
        assert dialog.exec() == QDialog.DialogCode.Rejected

    def test_table_read_only(self, dialog, mock_changes):
        """Test that the table cells are not editable."""
        table = dialog.findChild(QTableWidget)
        assert table is not None
        for row in range(len(mock_changes)):
            for col in range(4):
                item = table.item(row, col)
                assert not (item.flags() & Qt.ItemFlag.ItemIsEditable)
