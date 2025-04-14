"""
Tests for CorrectionPreviewDialog.
"""

import pytest
from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QDialog, QDialogButtonBox
from PySide6.QtCore import Qt

from chestbuddy.ui.dialogs import CorrectionPreviewDialog


@pytest.fixture
def preview_data():
    """Provides sample preview data for the dialog."""
    return [
        (10, "ColumnA", "old_value1", "new_value1"),
        (25, "ColumnB", 123, 456),  # Test with integer data
        (5, "ColumnC", True, False),  # Test with boolean data
        (100, "ColumnD", None, "Something"),  # Test with None
    ]


@pytest.fixture
def preview_dialog(qtbot, preview_data):
    """Creates an instance of CorrectionPreviewDialog."""
    dialog = CorrectionPreviewDialog(preview_data)
    qtbot.addWidget(dialog)
    return dialog


class TestCorrectionPreviewDialog:
    """Test cases for the CorrectionPreviewDialog."""

    def test_initialization(self, preview_dialog, preview_data):
        """Test dialog initialization and basic properties."""
        assert preview_dialog.windowTitle() == "Correction Rule Preview"
        assert isinstance(preview_dialog.table_widget, QTableWidget)
        assert preview_dialog.table_widget.rowCount() == len(preview_data)
        assert preview_dialog.table_widget.columnCount() == 4
        assert (
            preview_dialog.table_widget.editTriggers()
            == QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Check headers
        headers = [preview_dialog.table_widget.horizontalHeaderItem(i).text() for i in range(4)]
        assert headers == ["Row", "Column", "Original Value", "Corrected Value"]

        # Check OK button exists and is connected
        button_box = preview_dialog.findChild(QDialogButtonBox)
        assert button_box is not None
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok_button is not None

    def test_table_population(self, preview_dialog, preview_data):
        """Test that the table is populated correctly."""
        table = preview_dialog.table_widget
        assert table.rowCount() == len(preview_data)

        for i, (row_idx, col_name, old_val, new_val) in enumerate(preview_data):
            assert table.item(i, 0).text() == str(row_idx + 1)  # Check 1-based row index
            assert table.item(i, 0).textAlignment() == (
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            assert table.item(i, 1).text() == str(col_name)
            assert table.item(i, 2).text() == str(old_val)
            assert table.item(i, 3).text() == str(new_val)

    def test_ok_button(self, qtbot, preview_dialog):
        """Test clicking the OK button closes the dialog."""
        button_box = preview_dialog.findChild(QDialogButtonBox)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)

        # Use qtbot.clickAndAccept to simulate click and check result code
        with qtbot.waitSignal(preview_dialog.accepted, timeout=500):
            qtbot.mouseClick(ok_button, Qt.LeftButton)

        # Alternatively, check the result code if exec() was called externally
        # preview_dialog.open()
        # qtbot.mouseClick(ok_button, Qt.LeftButton)
        # assert preview_dialog.result() == QDialog.Accepted
        # preview_dialog.close() # Close manually if not using qtbot.clickAndAccept
