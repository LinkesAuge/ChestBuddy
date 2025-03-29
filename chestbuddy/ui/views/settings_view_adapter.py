"""
settings_view_adapter.py

Description: Adapter to integrate the SettingsTabView with the BaseView structure
Usage:
    settings_view = SettingsViewAdapter(config_manager)
    main_window.add_view(settings_view)
"""

import logging
from typing import Any, Optional, Dict

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.views.settings_tab_view import SettingsTabView
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class SettingsViewAdapter(BaseView):
    """
    Adapter that wraps the SettingsTabView component to integrate with the BaseView structure.

    This view provides a user interface for managing application settings, including
    theme, language, validation options, UI preferences, and configuration backup/restore.

    Signals:
        settings_changed: Emitted when a setting is changed
        config_reset: Emitted when configuration is reset
        config_imported: Emitted when configuration is imported
        config_exported: Emitted when configuration is exported
    """

    # Define signals
    settings_changed = Signal(str, str, str)  # Section, option, value
    config_reset = Signal(str)  # Section or "all"
    config_imported = Signal(str)  # Import path
    config_exported = Signal(str)  # Export path

    def __init__(
        self,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the SettingsViewAdapter.

        Args:
            config_manager (ConfigManager): The application configuration manager
            parent (Optional[QWidget]): Parent widget
            debug_mode (bool): Enable debug mode for signal connections
        """
        # Store references
        self._config_manager = config_manager

        # Create the underlying SettingsTabView
        self._settings_tab = SettingsTabView(config_manager=config_manager)

        # Initialize the base view
        super().__init__(
            title="Settings",
            parent=parent,
            debug_mode=debug_mode,
        )
        self.setObjectName("SettingsViewAdapter")

        # Set the lightContentView property to true for proper theme inheritance
        self._settings_tab.setProperty("lightContentView", True)

        # Connect signals
        self._connect_tab_signals()

        logger.info("Initialized SettingsViewAdapter")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add header action buttons
        self._add_header_action("refresh", "Refresh", "refresh")

        # Add the SettingsTabView to the content widget
        self.get_content_layout().addWidget(self._settings_tab)

    def _connect_tab_signals(self):
        """Connect signals from the SettingsTabView."""
        # Connect settings changed signal
        self._settings_tab.settings_changed.connect(self._on_settings_changed)

        # Connect backup/restore signals
        self._settings_tab.settings_exported.connect(self._on_settings_exported)
        self._settings_tab.settings_imported.connect(self._on_settings_imported)
        self._settings_tab.settings_reset.connect(self._on_settings_reset)

    def _add_header_action(self, name: str, tooltip: str, icon_name: str) -> None:
        """
        Add an action button to the header.

        Args:
            name (str): Button name
            tooltip (str): Button tooltip
            icon_name (str): Icon name
        """
        self._header.add_action_button(name, tooltip, icon_name)
        button = self._header.get_action_button(name)
        if button:
            button.clicked.connect(lambda: self._on_action_clicked(name))

    def _on_action_clicked(self, action_id: str) -> None:
        """
        Handle action button clicks.

        Args:
            action_id (str): The ID of the clicked action
        """
        if action_id == "refresh":
            self._on_refresh_clicked()

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        self._settings_tab.refresh()
        self._set_header_status("Settings refreshed")
        logger.debug("Settings refreshed from config")

    def _on_settings_changed(self, section: str, option: str, value: str) -> None:
        """
        Handle settings changed event.

        Args:
            section (str): Configuration section
            option (str): Configuration option
            value (str): New value
        """
        # Update header status
        self._set_header_status(f"Setting updated: [{section}] {option}")

        # Apply setting immediately if it's a UI setting
        if section == "UI":
            self._apply_ui_setting(option, value)

        # Emit our own signal
        self.settings_changed.emit(section, option, value)
        logger.info(f"Setting changed: [{section}] {option} = {value}")

    def _on_settings_exported(self, file_path: str) -> None:
        """
        Handle settings exported event.

        Args:
            file_path (str): Path to the exported file
        """
        self._set_header_status(f"Settings exported to: {file_path}")
        self.config_exported.emit(file_path)
        logger.info(f"Configuration exported to: {file_path}")

    def _on_settings_imported(self, file_path: str) -> None:
        """
        Handle settings imported event.

        Args:
            file_path (str): Path to the imported file
        """
        self._set_header_status(f"Settings imported from: {file_path}")
        self.config_imported.emit(file_path)
        logger.info(f"Configuration imported from: {file_path}")

        # Apply UI settings after import
        self._apply_all_ui_settings()

    def _on_settings_reset(self, section: str) -> None:
        """
        Handle settings reset event.

        Args:
            section (str): The section that was reset, or "all"
        """
        self._set_header_status(f"Settings reset: {section}")
        self.config_reset.emit(section)
        logger.info(f"Configuration reset: {section}")

        # Apply UI settings after reset
        if section == "all" or section == "UI":
            self._apply_all_ui_settings()

    def _apply_ui_setting(self, option: str, value: str) -> None:
        """
        Apply a UI setting immediately.

        Args:
            option (str): UI option
            value (str): New value
        """
        # These settings typically require application restart to take full effect,
        # but we can make some immediate adjustments

        # For now, just log that this would be applied
        logger.debug(f"Would apply UI setting: {option} = {value}")

    def _apply_all_ui_settings(self) -> None:
        """Apply all UI settings from the configuration."""
        # Get all UI settings
        width = self._config_manager.get_int("UI", "window_width", 1024)
        height = self._config_manager.get_int("UI", "window_height", 768)
        page_size = self._config_manager.get_int("UI", "table_page_size", 100)

        # Apply settings (with minimal implementation for now)
        logger.debug(
            f"Would apply UI settings: width={width}, height={height}, page_size={page_size}"
        )

    def _set_header_status(self, message: str) -> None:
        """
        Set the header status message.

        Args:
            message (str): Status message
        """
        if hasattr(self._header, "set_status"):
            self._header.set_status(message)
        else:
            logger.debug(f"Header status: {message}")

    def refresh(self) -> None:
        """Refresh the settings view."""
        self._settings_tab.refresh()
        logger.debug("Settings view refreshed")
