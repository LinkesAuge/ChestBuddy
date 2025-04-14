"""
correction_preview_dialog.py

Description:
    Dialog to display the potential changes a specific correction rule would make.

Usage:
    preview_data = [
        (10, 'ColumnA', 'old_value1', 'new_value1'),
        (25, 'ColumnB', 'old_value2', 'new_value2')
    ]
    dialog = CorrectionPreviewDialog(preview_data)
    dialog.exec()
"""

import logging
from typing import List, Tuple, Any, Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QDialogButtonBox,
    QHeaderView,
    QWidget,
)
from PySide6.QtCore import Qt

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionPreviewDialog(QDialog):
    """
    A dialog to preview the effects of a single correction rule.

    Displays a table showing which cells would be changed, their original
    values, and their proposed new values.

    Attributes:
        preview_data (List[Tuple[int, str, Any, Any]]): Data containing potential changes.
            Each tuple represents a change: (row_index, column_name, old_value, new_value)
    """

    def __init__(
        self, preview_data: List[Tuple[int, str, Any, Any]], parent: Optional[QWidget] = None
    ):
        """
        Initialize the CorrectionPreviewDialog.

        Args:
            preview_data (List[Tuple[int, str, Any, Any]]): The list of potential changes.
            parent (Optional[QWidget]): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.preview_data = preview_data
        self._setup_ui()
        self._populate_table()
        self.setWindowTitle("Correction Rule Preview")
        self.setMinimumSize(600, 400)  # Set a reasonable minimum size
        logger.debug(f"CorrectionPreviewDialog initialized with {len(preview_data)} items.")

    def _setup_ui(self):
        """Set up the UI elements of the dialog."""
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Row", "Column", "Original Value", "Corrected Value"]
        )
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Read-only
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.verticalHeader().setVisible(False)  # Hide row numbers

        # Resize columns to fit content
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Stretch Value columns
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table_widget)

        # Standard OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _populate_table(self):
        """Fill the table widget with the preview data."""
        self.table_widget.setRowCount(len(self.preview_data))

        for row_idx, (data_row, col_name, old_val, new_val) in enumerate(self.preview_data):
            # Create QTableWidgetItem for each cell
            row_item = QTableWidgetItem(str(data_row + 1))  # Display 1-based index
            col_item = QTableWidgetItem(str(col_name))
            old_val_item = QTableWidgetItem(str(old_val))
            new_val_item = QTableWidgetItem(str(new_val))

            # Set alignment for row number (optional)
            row_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Add items to the table
            self.table_widget.setItem(row_idx, 0, row_item)
            self.table_widget.setItem(row_idx, 1, col_item)
            self.table_widget.setItem(row_idx, 2, old_val_item)
            self.table_widget.setItem(row_idx, 3, new_val_item)

        logger.debug("Preview table populated.")
