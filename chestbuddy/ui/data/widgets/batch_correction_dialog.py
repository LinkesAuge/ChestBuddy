"""
batch_correction_dialog.py

A dialog for displaying and selecting batch corrections.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QLabel,
    QScrollArea,
    QWidget,
    QGridLayout,
    QFrame,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from typing import Dict, List, Tuple, Any, Optional
import logging

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionItem:
    """Represents a single correction item with original and suggested values."""

    def __init__(
        self,
        row: int,
        col: int,
        column_name: str,
        original: str,
        corrected: str,
        suggestion: Any = None,
    ):
        self.row = row
        self.col = col
        self.column_name = column_name
        self.original_value = original
        self.corrected_value = corrected
        self.suggestion = (
            suggestion  # The original suggestion object, may contain additional metadata
        )

    def __str__(self):
        return f'Row {self.row}, {self.column_name}: "{self.original_value}" → "{self.corrected_value}"'


class BatchCorrectionDialog(QDialog):
    """
    Dialog for selecting and applying multiple corrections at once.

    Displays a list of available corrections with checkboxes for selection.
    Users can select all, deselect all, and apply selected corrections.

    Signals:
        corrections_applied: Emitted when corrections are applied with a list of selected corrections.
    """

    # Signal emitted when corrections are applied
    corrections_applied = Signal(list)  # List of selected CorrectionItems

    def __init__(
        self, correction_items: List[CorrectionItem], parent=None, title="Batch Correction"
    ):
        """
        Initialize the batch correction dialog.

        Args:
            correction_items: List of CorrectionItem objects to display
            parent: Parent widget
            title: Dialog title
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.correction_items = correction_items
        self.checkboxes = []  # To track the checkboxes for each item

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the dialog UI."""
        main_layout = QVBoxLayout(self)

        # Header label
        header_label = QLabel(f"Found {len(self.correction_items)} cells that can be corrected:")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_label)

        # Create a scrollable area for the corrections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Add each correction as a row with a checkbox
        for item in self.correction_items:
            # Create a frame for each item
            item_frame = QFrame()
            item_frame.setFrameShape(QFrame.StyledPanel)
            item_frame.setFrameShadow(QFrame.Raised)
            item_layout = QHBoxLayout(item_frame)

            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to checked
            self.checkboxes.append(checkbox)
            item_layout.addWidget(checkbox)

            # Label with correction text
            label_text = str(item)
            label = QLabel(label_text)
            item_layout.addWidget(label, 1)  # Stretch factor of 1

            scroll_layout.addWidget(item_frame)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Selection control buttons
        selection_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        selection_layout.addWidget(select_all_btn)
        selection_layout.addWidget(deselect_all_btn)
        selection_layout.addStretch(1)
        main_layout.addLayout(selection_layout)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.apply_btn = QPushButton("Apply Selected")
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        # Store references to buttons for signal connections
        self.select_all_btn = select_all_btn
        self.deselect_all_btn = deselect_all_btn
        self.cancel_btn = cancel_btn

    def _connect_signals(self):
        """Connect button signals to slots."""
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.apply_btn.clicked.connect(self._apply_selected)
        self.cancel_btn.clicked.connect(self.reject)

    @Slot()
    def _select_all(self):
        """Select all correction items."""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    @Slot()
    def _deselect_all(self):
        """Deselect all correction items."""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    @Slot()
    def _apply_selected(self):
        """Apply the selected corrections."""
        selected_items = []

        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked() and i < len(self.correction_items):
                selected_items.append(self.correction_items[i])

        logger.info(f"Applying {len(selected_items)} selected corrections")
        self.corrections_applied.emit(selected_items)
        self.accept()

    @staticmethod
    def show_dialog(
        correction_items: List[CorrectionItem], parent=None
    ) -> Tuple[List[CorrectionItem], bool]:
        """
        Static method to create, show the dialog, and return selected corrections.

        Args:
            correction_items: List of CorrectionItem objects to display
            parent: Parent widget

        Returns:
            Tuple of (selected_items, accepted)
        """
        if not correction_items:
            logger.warning("No correction items provided to BatchCorrectionDialog")
            return [], False

        dialog = BatchCorrectionDialog(correction_items, parent)
        selected_items = []

        # Connect to capture selected items before dialog closes
        dialog.corrections_applied.connect(lambda items: selected_items.extend(items))

        result = dialog.exec()
        return selected_items, result == QDialog.Accepted
