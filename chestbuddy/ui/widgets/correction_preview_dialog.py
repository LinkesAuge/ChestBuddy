"""
correction_preview_dialog.py

Dialog to preview proposed data corrections before applying them.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from PySide6.QtCore import Qt, QModelIndex
from typing import List, Tuple, Any


class CorrectionPreviewDialog(QDialog):
    """
    A dialog that displays a preview of proposed corrections.

    Allows the user to review changes before confirming or canceling.
    """

    def __init__(self, changes: List[Tuple[QModelIndex, Any, Any]], parent=None):
        """
        Initialize the CorrectionPreviewDialog.

        Args:
            changes (List[Tuple[QModelIndex, Any, Any]]): A list of tuples,
                each containing (index, original_value, corrected_value).
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Correction Preview")
        self.setMinimumSize(500, 300)  # Adjust size as needed

        self._changes = changes
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)

        label = QLabel(f"Review the following {len(self._changes)} proposed correction(s):")
        layout.addWidget(label)

        self._table = QTableWidget()
        self._table.setColumnCount(4)  # Location, Column Name, Original, Corrected
        self._table.setHorizontalHeaderLabels(
            ["Row", "Column", "Original Value", "Corrected Value"]
        )
        self._table.setRowCount(len(self._changes))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only

        for row, (index, original, corrected) in enumerate(self._changes):
            row_item = QTableWidgetItem(str(index.row()))
            # Try to get column name from model header if index is valid and has model
            col_name = f"Col {index.column()}"
            if index.model() and index.isValid():
                header_data = index.model().headerData(
                    index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
                )
                if header_data:
                    col_name = str(header_data)

            col_item = QTableWidgetItem(col_name)
            original_item = QTableWidgetItem(str(original))
            corrected_item = QTableWidgetItem(str(corrected))

            # Set read-only flags
            for item in [row_item, col_item, original_item, corrected_item]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self._table.setItem(row, 0, row_item)
            self._table.setItem(row, 1, col_item)
            self._table.setItem(row, 2, original_item)
            self._table.setItem(row, 3, corrected_item)

        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)


# Example usage (for testing or demonstration)
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    from PySide6.QtCore import QAbstractItemModel

    # Minimal mock model index for testing display
    class MockModelIndex:
        def __init__(self, row, col):
            self._row = row
            self._col = col

        def row(self):
            return self._row

        def column(self):
            return self._col

        def isValid(self):
            return True

        def model(self):
            return None  # No model for basic test

    app = QApplication(sys.argv)
    test_changes = [
        (MockModelIndex(2, 0), "JohnSmiht", "John Smith"),
        (MockModelIndex(5, 1), "siver", "Silver"),
        (MockModelIndex(10, 2), 123, "CorrectedValue"),
    ]
    dialog = CorrectionPreviewDialog(test_changes)
    if dialog.exec():
        print("Corrections Accepted")
    else:
        print("Corrections Rejected")
    sys.exit()
