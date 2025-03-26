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
    QStatusBar,
    QToolBar,
)

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.views.validation_list_view import ValidationListView
from chestbuddy.ui.views.validation_preferences_view import ValidationPreferencesView
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons

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
        self.validation_stats = {"players": 0, "chest_types": 0, "sources": 0}

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Create the central content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Add title label
        title_label = QLabel("Validation Lists")
        title_label.setStyleSheet(
            f"font-weight: bold; font-size: 16px; color: {Colors.TEXT_LIGHT};"
        )
        content_layout.addWidget(title_label)

        # Create three-column splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

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

        # Add views to splitter
        self.splitter.addWidget(self.player_list_view)
        self.splitter.addWidget(self.chest_type_list_view)
        self.splitter.addWidget(self.source_list_view)

        # Set splitter sizes
        self.splitter.setSizes([1, 1, 1])  # Equal sizes

        # Add splitter to content layout
        content_layout.addWidget(self.splitter, 1)  # Stretch factor 1

        # Create bottom toolbar
        self.toolbar = QToolBar("Validation Actions")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Add save all button
        self.save_all_button = QPushButton("Save All")
        self.save_all_button.setIcon(Icons.get_icon(Icons.SAVE))
        self.save_all_button.setToolTip("Save all validation lists")
        self.save_all_button.clicked.connect(self._on_save_all)
        self.toolbar.addWidget(self.save_all_button)

        # Add spacer
        self.toolbar.addSeparator()

        # Add reload all button
        self.reload_all_button = QPushButton("Reload All")
        self.reload_all_button.setToolTip("Reload all validation lists from disk")
        self.reload_all_button.clicked.connect(self._on_reset)
        self.toolbar.addWidget(self.reload_all_button)

        # Add validate now button
        self.validate_now_button = QPushButton("Validate Now")
        self.validate_now_button.setIcon(Icons.get_icon(Icons.VALIDATE))
        self.validate_now_button.setToolTip("Validate all data against current validation lists")
        self.validate_now_button.clicked.connect(self._on_validate_now)
        self.toolbar.addWidget(self.validate_now_button)

        # Add preferences button
        self.preferences_button = QPushButton("Preferences")
        self.preferences_button.setIcon(Icons.get_icon(Icons.SETTINGS))
        self.preferences_button.setToolTip("Configure validation preferences")
        self.preferences_button.clicked.connect(self._on_show_preferences)
        self.toolbar.addWidget(self.preferences_button)

        # Add toolbar to content layout
        content_layout.addWidget(self.toolbar)

        # Add horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Add preferences view (initially hidden)
        self.preferences_view = ValidationPreferencesView(self.validation_service, self)
        self.preferences_view.setVisible(False)
        content_layout.addWidget(self.preferences_view, 0)  # No stretch

        # Add status bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self._update_status_bar()
        content_layout.addWidget(self.status_bar)

        # Add content widget to main layout
        main_layout.addWidget(content_widget)

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

        # Update validation stats
        if category == "Players":
            self.validation_stats["players"] = count
        elif category == "Chest Types":
            self.validation_stats["chest_types"] = count
        elif category == "Sources":
            self.validation_stats["sources"] = count

        # Update status bar
        self._update_status_bar()

        # Emit validation updated signal
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

    @Slot()
    def _on_save_all(self) -> None:
        """Handle save all button click."""
        # Save all validation lists
        player_model = self.validation_service.get_player_list_model()
        chest_type_model = self.validation_service.get_chest_type_list_model()
        source_model = self.validation_service.get_source_list_model()

        player_model.save()
        chest_type_model.save()
        source_model.save()

        logger.info("All validation lists saved")
        self.status_bar.showMessage("All validation lists saved", 3000)

    @Slot()
    def _on_show_preferences(self) -> None:
        """Handle preferences button click."""
        # Toggle preferences view visibility
        self.preferences_view.setVisible(not self.preferences_view.isVisible())

        # Update button text
        if self.preferences_view.isVisible():
            self.preferences_button.setText("Hide Preferences")
        else:
            self.preferences_button.setText("Preferences")

    def _update_status_bar(self) -> None:
        """Update the status bar with validation statistics."""
        total_entries = sum(self.validation_stats.values())
        status_text = (
            f"Total Entries: {total_entries} | "
            f"Players: {self.validation_stats['players']} | "
            f"Chest Types: {self.validation_stats['chest_types']} | "
            f"Sources: {self.validation_stats['sources']}"
        )
        self.status_bar.showMessage(status_text)

    def refresh(self) -> None:
        """Refresh the validation tab view."""
        self._on_reset()
