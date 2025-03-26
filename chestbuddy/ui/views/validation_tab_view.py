"""
validation_tab_view.py

Description: Tab view for validation management
"""

import logging
from typing import Optional, Dict

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QLabel,
    QFrame,
    QTabWidget,
)

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.views.validation_list_view import ValidationListView
from chestbuddy.ui.views.validation_preferences_view import ValidationPreferencesView

logger = logging.getLogger(__name__)


class ValidationTabView(QWidget):
    """
    Tab view for validation management.

    This view provides a unified interface for managing validation lists
    and preferences. It includes three validation list views (players,
    chest types, and sources) and a preferences panel.

    Attributes:
        validation_updated (Signal): Signal emitted when validation lists or preferences are updated
    """

    validation_updated = Signal()

    def __init__(
        self, validation_service: ValidationService, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the ValidationTabView.

        Args:
            validation_service (ValidationService): Service for validation
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.validation_service = validation_service

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Create validation list views
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Players list view
        self.player_list_view = ValidationListView(
            "Players", self.validation_service.get_player_list_model(), self
        )

        # Chest types list view
        self.chest_type_list_view = ValidationListView(
            "Chest Types", self.validation_service.get_chest_type_list_model(), self
        )

        # Sources list view
        self.source_list_view = ValidationListView(
            "Sources", self.validation_service.get_source_list_model(), self
        )

        # Preferences view
        self.preferences_view = ValidationPreferencesView(self.validation_service, self)

        # Add views to splitter
        splitter.addWidget(self.player_list_view)
        splitter.addWidget(self.chest_type_list_view)
        splitter.addWidget(self.source_list_view)

        # Set splitter sizes
        splitter.setSizes([1, 1, 1])  # Equal sizes

        # Add splitter to main layout
        main_layout.addWidget(splitter, 1)  # Stretch factor 1

        # Add horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # Add preferences view
        main_layout.addWidget(self.preferences_view, 0)  # No stretch

        # Add button panel
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 5, 10, 10)

        # Add validate now button
        self.validate_now_button = QPushButton("Validate Now")
        self.validate_now_button.setToolTip("Validate all data against current validation lists")
        self.validate_now_button.clicked.connect(self._on_validate_now)
        button_layout.addWidget(self.validate_now_button)

        # Add reset button
        self.reset_button = QPushButton("Reset Lists")
        self.reset_button.setToolTip("Reload all validation lists from disk")
        self.reset_button.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Connect signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Connect validation list view status signals
        self.player_list_view.status_changed.connect(self._on_status_changed)
        self.chest_type_list_view.status_changed.connect(self._on_status_changed)
        self.source_list_view.status_changed.connect(self._on_status_changed)

        # Connect preferences signals
        self.preferences_view.preferences_changed.connect(self._on_preferences_changed)

    @Slot(str, int)
    def _on_status_changed(self, category: str, count: int) -> None:
        """
        Handle status changes in validation lists.

        Args:
            category (str): Validation list category
            count (int): Number of entries
        """
        logger.debug(f"Validation list '{category}' status changed: {count} entries")
        self.validation_updated.emit()

    @Slot(dict)
    def _on_preferences_changed(self, preferences: Dict) -> None:
        """
        Handle preferences changes.

        Args:
            preferences (Dict): Updated preferences
        """
        logger.debug(f"Validation preferences changed: {preferences}")
        self.validation_updated.emit()

    @Slot()
    def _on_validate_now(self) -> None:
        """Handle validate now button click."""
        self.validation_service.validate_data()
        logger.info("Manual validation triggered")
        self.validation_updated.emit()

    @Slot()
    def _on_reset(self) -> None:
        """Handle reset button click."""
        # Refresh all validation lists
        self.player_list_view.refresh()
        self.chest_type_list_view.refresh()
        self.source_list_view.refresh()

        # Refresh preferences
        self.preferences_view.refresh()

        logger.info("Validation lists and preferences reset")
        self.validation_updated.emit()

    def refresh(self) -> None:
        """Refresh the validation tab view."""
        self._on_reset()
