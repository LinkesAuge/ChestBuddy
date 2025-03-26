"""
validation_preferences_view.py

Description: View for configuring validation preferences
"""

import logging
from typing import Optional, Dict, Callable

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QGroupBox,
    QFrame,
)

from chestbuddy.core.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class ValidationPreferencesView(QWidget):
    """
    View for configuring validation preferences.

    This widget allows users to configure validation settings such as
    case sensitivity and validation on import.

    Attributes:
        preferences_changed (Signal): Signal emitted when preferences are changed
    """

    preferences_changed = Signal(dict)  # Dict of preferences

    def __init__(
        self, validation_service: ValidationService, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the ValidationPreferencesView.

        Args:
            validation_service (ValidationService): Service for validation
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.validation_service = validation_service

        # Setup UI
        self._setup_ui()

        # Load initial settings
        self._load_preferences()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("Validation Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Group box for settings
        settings_group = QGroupBox("Preferences")
        settings_layout = QVBoxLayout(settings_group)

        # Case sensitivity checkbox
        self.case_sensitive_checkbox = QCheckBox("Case-sensitive validation")
        self.case_sensitive_checkbox.setToolTip(
            "When enabled, validation will be case-sensitive (e.g., 'Player' and 'player' are different)"
        )
        self.case_sensitive_checkbox.toggled.connect(self._on_case_sensitive_changed)
        settings_layout.addWidget(self.case_sensitive_checkbox)

        # Validate on import checkbox
        self.validate_on_import_checkbox = QCheckBox("Validate on import")
        self.validate_on_import_checkbox.setToolTip(
            "When enabled, validation will be performed automatically when importing data"
        )
        self.validate_on_import_checkbox.toggled.connect(self._on_validate_on_import_changed)
        settings_layout.addWidget(self.validate_on_import_checkbox)

        # Add group to main layout
        layout.addWidget(settings_group)

        # Add spacer
        layout.addStretch()

    def _load_preferences(self) -> None:
        """Load preferences from the validation service."""
        prefs = self.validation_service.get_validation_preferences()

        # Update checkboxes without triggering signals
        self.case_sensitive_checkbox.blockSignals(True)
        self.validate_on_import_checkbox.blockSignals(True)

        self.case_sensitive_checkbox.setChecked(prefs.get("case_sensitive", False))
        self.validate_on_import_checkbox.setChecked(prefs.get("validate_on_import", True))

        self.case_sensitive_checkbox.blockSignals(False)
        self.validate_on_import_checkbox.blockSignals(False)

        logger.debug(f"Loaded validation preferences: {prefs}")

    @Slot(bool)
    def _on_case_sensitive_changed(self, checked: bool) -> None:
        """
        Handle case sensitivity preference change.

        Args:
            checked (bool): Whether case sensitivity is enabled
        """
        self.validation_service.set_case_sensitive(checked)
        self._emit_preferences_changed()
        logger.info(f"Case sensitivity set to: {checked}")

    @Slot(bool)
    def _on_validate_on_import_changed(self, checked: bool) -> None:
        """
        Handle validate on import preference change.

        Args:
            checked (bool): Whether validation on import is enabled
        """
        self.validation_service.set_validate_on_import(checked)
        self._emit_preferences_changed()
        logger.info(f"Validate on import set to: {checked}")

    def _emit_preferences_changed(self) -> None:
        """Emit signal with current preferences."""
        prefs = self.validation_service.get_validation_preferences()
        self.preferences_changed.emit(prefs)

    def refresh(self) -> None:
        """Refresh the preferences view."""
        self._load_preferences()
