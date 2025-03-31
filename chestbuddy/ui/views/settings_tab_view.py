"""
settings_tab_view.py

Description: View for managing application settings
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal, QSize

from chestbuddy.utils.config import ConfigManager
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.utils.icon_provider import IconProvider
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.core.services.validation_service import ValidationService

# Set up logger
logger = logging.getLogger(__name__)


class SettingsTabView(QWidget):
    """
    View for managing application settings.

    Signals:
        settings_changed: Emitted when settings are changed
        settings_exported: Emitted when settings are exported
        settings_imported: Emitted when settings are imported
        settings_reset: Emitted when settings are reset
    """

    settings_changed = Signal(str, str, str)  # Section, option, value
    settings_exported = Signal(str)  # Export path
    settings_imported = Signal(str)  # Import path
    settings_reset = Signal(str)  # Section or "all"

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        """
        Initialize the settings tab view.

        Args:
            config_manager (ConfigManager): Application configuration manager
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self._config_manager = config_manager
        self._settings_widgets = {}

        # Try to get ValidationService from ServiceLocator
        self._validation_service = None
        try:
            self._validation_service = ServiceLocator.get("validation_service")
            logger.info("Retrieved ValidationService from ServiceLocator")
        except KeyError:
            logger.warning("ValidationService not found in ServiceLocator")

        self._setup_ui()
        self._load_settings()
        self._connect_signals()
        logger.info("Initialized SettingsTabView")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.North)
        self._tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.DARK_BORDER};
                background-color: {Colors.DARK_CONTENT_BG};
                border-top-color: {Colors.SECONDARY};
            }}
            QTabBar::tab {{
                background-color: {Colors.PRIMARY_DARK};
                color: {Colors.TEXT_LIGHT};
                padding: 10px 15px;
                border: 1px solid {Colors.DARK_BORDER};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom: none;
                min-width: 100px;
                margin-right: 2px;
                margin-bottom: 0;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.DARK_CONTENT_BG};
                border-bottom-color: {Colors.DARK_CONTENT_BG};
                border-top: 2px solid {Colors.SECONDARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.PRIMARY};
            }}
        """)

        # Create settings tabs
        self._setup_general_tab()
        self._setup_validation_tab()
        self._setup_correction_tab()
        self._setup_ui_tab()
        self._setup_backup_tab()

        # Add tab widget to main layout
        main_layout.addWidget(self._tab_widget)

    def _create_scrollable_content(self) -> tuple:
        """
        Create a scrollable content widget.

        Returns:
            tuple: (scroll_area, content_widget, content_layout)
        """
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.DARK_CONTENT_BG};
                border: none;
            }}
        """)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {Colors.DARK_CONTENT_BG};")

        # Create content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Set content widget as scroll area widget
        scroll_area.setWidget(content_widget)

        return scroll_area, content_widget, content_layout

    def _setup_general_tab(self) -> None:
        """Set up the general settings tab."""
        # Create scrollable content
        scroll_area, content_widget, layout = self._create_scrollable_content()

        # Create general settings group
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        # Create form layout for settings
        general_layout = QFormLayout(general_group)
        general_layout.setContentsMargins(16, 24, 16, 16)
        general_layout.setSpacing(12)
        general_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        general_layout.setLabelAlignment(Qt.AlignRight)

        # Theme dropdown
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        theme_combo = QComboBox()
        theme_combo.addItems(["Dark", "Light"])
        theme_combo.setObjectName("theme")
        theme_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 25px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                border-left: 1px solid {Colors.DARK_BORDER};
                width: 20px;
            }}
        """)

        # Language dropdown
        language_label = QLabel("Language:")
        language_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        language_combo = QComboBox()
        language_combo.addItems(["English", "German", "Spanish"])
        language_combo.setObjectName("language")
        language_combo.setStyleSheet(theme_combo.styleSheet())

        # Config version (display only)
        version_label = QLabel("Config Version:")
        version_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        version_display = QLineEdit()
        version_display.setReadOnly(True)
        version_display.setObjectName("config_version")
        version_display.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.PRIMARY_DARK};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 25px;
            }}
            QLineEdit:disabled {{
                background-color: {Colors.PRIMARY_DARK};
                color: {Colors.TEXT_MUTED};
            }}
        """)

        # Add fields to layout
        general_layout.addRow(theme_label, theme_combo)
        general_layout.addRow(language_label, language_combo)
        general_layout.addRow(version_label, version_display)

        # Save widget references
        self._settings_widgets["General"] = {
            "theme": theme_combo,
            "language": language_combo,
            "config_version": version_display,
        }

        # Connect signals
        theme_combo.currentTextChanged.connect(
            lambda value: self._on_setting_changed("General", "theme", value)
        )
        language_combo.currentTextChanged.connect(
            lambda value: self._on_setting_changed("General", "language", value)
        )

        # Add group to layout
        layout.addWidget(general_group)

        # Add spacer at the bottom
        layout.addStretch(1)

        # Add tab
        self._tab_widget.addTab(scroll_area, "General")

    def _setup_validation_tab(self) -> None:
        """Set up the validation settings tab."""
        # Create scrollable content
        scroll_area, content_widget, layout = self._create_scrollable_content()

        # Create validation settings group
        validation_group = QGroupBox("Validation Settings")
        validation_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        # Create form layout for settings
        validation_layout = QFormLayout(validation_group)
        validation_layout.setContentsMargins(16, 24, 16, 16)
        validation_layout.setSpacing(12)
        validation_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        validation_layout.setLabelAlignment(Qt.AlignRight)

        # Checkboxes
        validate_label = QLabel("Validate on Import:")
        validate_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        validate_checkbox = QCheckBox()
        validate_checkbox.setObjectName("validate_on_import")
        validate_checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 2px;
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            QCheckBox::indicator:checked {{
                image: url(:/icons/check.svg);
                background-color: {Colors.SECONDARY};
            }}
        """)

        case_sensitive_label = QLabel("Case Sensitive:")
        case_sensitive_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        case_sensitive_checkbox = QCheckBox()
        case_sensitive_checkbox.setObjectName("case_sensitive")
        case_sensitive_checkbox.setStyleSheet(validate_checkbox.styleSheet())

        auto_save_label = QLabel("Auto-save Lists:")
        auto_save_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        auto_save_checkbox = QCheckBox()
        auto_save_checkbox.setObjectName("auto_save")
        auto_save_checkbox.setStyleSheet(validate_checkbox.styleSheet())

        # Validation lists directory input
        dir_label = QLabel("Validation Lists Directory:")
        dir_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        dir_layout = QHBoxLayout()
        dir_input = QLineEdit()
        dir_input.setObjectName("validation_lists_dir")
        dir_input.setReadOnly(True)
        dir_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 25px;
            }}
        """)

        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                min-height: 25px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SECONDARY_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Colors.SECONDARY_DARK};
            }}
        """)

        dir_layout.addWidget(dir_input)
        dir_layout.addWidget(browse_button)

        # Add fields to layout
        validation_layout.addRow(validate_label, validate_checkbox)
        validation_layout.addRow(case_sensitive_label, case_sensitive_checkbox)
        validation_layout.addRow(auto_save_label, auto_save_checkbox)
        validation_layout.addRow(dir_label, dir_layout)

        # Save widget references
        self._settings_widgets["Validation"] = {
            "validate_on_import": validate_checkbox,
            "case_sensitive": case_sensitive_checkbox,
            "auto_save": auto_save_checkbox,
            "validation_lists_dir": dir_input,
        }

        # Connect signals
        validate_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "Validation", "validate_on_import", str(bool(state))
            )
        )
        case_sensitive_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed("Validation", "case_sensitive", str(bool(state)))
        )
        auto_save_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed("Validation", "auto_save", str(bool(state)))
        )
        browse_button.clicked.connect(self._browse_validation_lists_dir)

        # Add validation group to layout
        layout.addWidget(validation_group)

        # Create correction settings group
        correction_group = QGroupBox("Correction Settings")
        correction_group.setStyleSheet(validation_group.styleSheet())

        # Create layout for correction settings
        correction_layout = QFormLayout(correction_group)
        correction_layout.setContentsMargins(16, 24, 16, 16)
        correction_layout.setSpacing(12)
        correction_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        correction_layout.setLabelAlignment(Qt.AlignRight)

        # Auto-correct on validation checkbox
        auto_correct_validation_label = QLabel("Auto-correct after Validation:")
        auto_correct_validation_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        auto_correct_validation_checkbox = QCheckBox()
        auto_correct_validation_checkbox.setObjectName("auto_correct_on_validation")
        auto_correct_validation_checkbox.setStyleSheet(validate_checkbox.styleSheet())

        # Auto-correct on import checkbox
        auto_correct_import_label = QLabel("Auto-correct on Import:")
        auto_correct_import_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        auto_correct_import_checkbox = QCheckBox()
        auto_correct_import_checkbox.setObjectName("auto_correct_on_import")
        auto_correct_import_checkbox.setStyleSheet(validate_checkbox.styleSheet())

        # Add fields to correction layout
        correction_layout.addRow(auto_correct_validation_label, auto_correct_validation_checkbox)
        correction_layout.addRow(auto_correct_import_label, auto_correct_import_checkbox)

        # Save widget references
        self._settings_widgets["Correction"] = {
            "auto_correct_on_validation": auto_correct_validation_checkbox,
            "auto_correct_on_import": auto_correct_import_checkbox,
        }

        # Connect signals
        auto_correct_validation_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "Correction", "auto_correct_on_validation", str(bool(state))
            )
        )
        auto_correct_import_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "Correction", "auto_correct_on_import", str(bool(state))
            )
        )

        # Add correction group to layout
        layout.addWidget(correction_group)

        # Add spacer at the bottom
        layout.addStretch(1)

        # Add tab
        self._tab_widget.addTab(scroll_area, "Validation")

    def _setup_correction_tab(self) -> None:
        """Set up the correction settings tab."""
        # Create scrollable content
        scroll_area, content_widget, layout = self._create_scrollable_content()

        # Create correction settings group
        correction_group = QGroupBox("Correction Settings")
        correction_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        # Create form layout for settings
        correction_layout = QFormLayout(correction_group)
        correction_layout.setContentsMargins(16, 24, 16, 16)
        correction_layout.setSpacing(12)
        correction_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        correction_layout.setLabelAlignment(Qt.AlignRight)

        # Auto-correction on validation
        auto_correct_validation_label = QLabel("Auto-correct after validation:")
        auto_correct_validation_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        auto_correct_validation_checkbox = QCheckBox()
        auto_correct_validation_checkbox.setObjectName("auto_correct_on_validation")
        auto_correct_validation_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_LIGHT};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 3px;
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.SECONDARY};
                image: url(:/icons/check.png);
            }}
        """)

        # Auto-correction on import
        auto_correct_import_label = QLabel("Auto-correct after import:")
        auto_correct_import_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        auto_correct_import_checkbox = QCheckBox()
        auto_correct_import_checkbox.setObjectName("auto_correct_on_import")
        auto_correct_import_checkbox.setStyleSheet(auto_correct_validation_checkbox.styleSheet())

        # Add fields to layout
        correction_layout.addRow(auto_correct_validation_label, auto_correct_validation_checkbox)
        correction_layout.addRow(auto_correct_import_label, auto_correct_import_checkbox)

        # Save widget references
        self._settings_widgets["Correction"] = {
            "auto_correct_on_validation": auto_correct_validation_checkbox,
            "auto_correct_on_import": auto_correct_import_checkbox,
        }

        # Connect signals
        auto_correct_validation_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "Correction", "auto_correct_on_validation", str(bool(state))
            )
        )
        auto_correct_import_checkbox.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "Correction", "auto_correct_on_import", str(bool(state))
            )
        )

        # Add group to layout
        layout.addWidget(correction_group)

        # Add spacer at the bottom
        layout.addStretch(1)

        # Add tab
        self._tab_widget.addTab(scroll_area, "Correction")

    def _setup_ui_tab(self) -> None:
        """Set up the UI settings tab."""
        # Create scrollable content
        scroll_area, content_widget, layout = self._create_scrollable_content()

        # Create UI settings group
        ui_group = QGroupBox("UI Settings")
        ui_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        # Create form layout for settings
        ui_layout = QFormLayout(ui_group)
        ui_layout.setContentsMargins(16, 24, 16, 16)
        ui_layout.setSpacing(12)
        ui_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ui_layout.setLabelAlignment(Qt.AlignRight)

        # Window width
        width_label = QLabel("Window Width:")
        width_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        width_spinner = QSpinBox()
        width_spinner.setObjectName("window_width")
        width_spinner.setRange(800, 3840)
        width_spinner.setSingleStep(10)
        width_spinner.setStyleSheet(f"""
            QSpinBox {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 25px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {Colors.PRIMARY_DARK};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 2px;
            }}
        """)

        # Window height
        height_label = QLabel("Window Height:")
        height_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        height_spinner = QSpinBox()
        height_spinner.setObjectName("window_height")
        height_spinner.setRange(600, 2160)
        height_spinner.setSingleStep(10)
        height_spinner.setStyleSheet(width_spinner.styleSheet())

        # Table page size
        page_size_label = QLabel("Table Page Size:")
        page_size_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        page_size_spinner = QSpinBox()
        page_size_spinner.setObjectName("table_page_size")
        page_size_spinner.setRange(10, 1000)
        page_size_spinner.setSingleStep(10)
        page_size_spinner.setStyleSheet(width_spinner.styleSheet())

        # Add fields to layout
        ui_layout.addRow(width_label, width_spinner)
        ui_layout.addRow(height_label, height_spinner)
        ui_layout.addRow(page_size_label, page_size_spinner)

        # Save widget references
        self._settings_widgets["UI"] = {
            "window_width": width_spinner,
            "window_height": height_spinner,
            "table_page_size": page_size_spinner,
        }

        # Connect signals
        width_spinner.valueChanged.connect(
            lambda value: self._on_setting_changed("UI", "window_width", str(value))
        )
        height_spinner.valueChanged.connect(
            lambda value: self._on_setting_changed("UI", "window_height", str(value))
        )
        page_size_spinner.valueChanged.connect(
            lambda value: self._on_setting_changed("UI", "table_page_size", str(value))
        )

        # Add group to layout
        layout.addWidget(ui_group)

        # Add spacer at the bottom
        layout.addStretch(1)

        # Add tab
        self._tab_widget.addTab(scroll_area, "UI")

    def _setup_backup_tab(self) -> None:
        """Set up the backup/restore tab."""
        # Create scrollable content
        scroll_area, content_widget, layout = self._create_scrollable_content()

        # Create backup/restore group
        backup_group = QGroupBox("Configuration Backup and Restore")
        backup_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        # Create backup layout
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setContentsMargins(16, 24, 16, 16)
        backup_layout.setSpacing(16)

        # Description label
        description = QLabel(
            "These functions allow you to back up and restore your configuration settings."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")

        # Export config button
        export_button = QPushButton("Export Configuration")
        export_button.setIcon(IconProvider.get_icon("export"))
        export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARK};
            }}
        """)

        # Import config button
        import_button = QPushButton("Import Configuration")
        import_button.setIcon(IconProvider.get_icon("import"))
        import_button.setStyleSheet(export_button.styleSheet())

        # Reset section
        reset_group = QGroupBox("Reset to Defaults")
        reset_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.PRIMARY_DARK};
                border-radius: 6px;
                border: 1px solid {Colors.DARK_BORDER};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px;
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
            }}
        """)

        reset_layout = QVBoxLayout(reset_group)
        reset_layout.setContentsMargins(16, 24, 16, 16)
        reset_layout.setSpacing(12)

        reset_warning = QLabel(
            "Warning: Resetting will overwrite your current settings with default values."
        )
        reset_warning.setWordWrap(True)
        reset_warning.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")

        # Reset buttons layout
        reset_buttons_layout = QHBoxLayout()
        reset_buttons_layout.setContentsMargins(0, 8, 0, 0)
        reset_buttons_layout.setSpacing(8)

        # Reset all button
        reset_all_button = QPushButton("Reset All Settings")
        reset_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER_BG};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DANGER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.DANGER_ACTIVE};
            }}
        """)

        # Reset specific section buttons
        reset_general_button = QPushButton("Reset General")
        reset_general_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY_DARK};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER_BG};
                border-color: {Colors.DANGER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.DANGER};
            }}
        """)

        reset_validation_button = QPushButton("Reset Validation")
        reset_validation_button.setStyleSheet(reset_general_button.styleSheet())

        reset_ui_button = QPushButton("Reset UI")
        reset_ui_button.setStyleSheet(reset_general_button.styleSheet())

        # Add buttons to layout
        reset_buttons_layout.addWidget(reset_general_button)
        reset_buttons_layout.addWidget(reset_validation_button)
        reset_buttons_layout.addWidget(reset_ui_button)

        # Add widgets to reset layout
        reset_layout.addWidget(reset_warning)
        reset_layout.addLayout(reset_buttons_layout)
        reset_layout.addWidget(reset_all_button)

        # Add widgets to backup layout
        backup_layout.addWidget(description)
        backup_layout.addWidget(export_button)
        backup_layout.addWidget(import_button)
        backup_layout.addWidget(reset_group)

        # Connect signals
        export_button.clicked.connect(self._on_export_config)
        import_button.clicked.connect(self._on_import_config)
        reset_all_button.clicked.connect(lambda: self._on_reset_config(None))
        reset_general_button.clicked.connect(lambda: self._on_reset_config("General"))
        reset_validation_button.clicked.connect(lambda: self._on_reset_config("Validation"))
        reset_ui_button.clicked.connect(lambda: self._on_reset_config("UI"))

        # Add group to layout
        layout.addWidget(backup_group)

        # Add spacer at the bottom
        layout.addStretch(1)

        # Add tab
        self._tab_widget.addTab(scroll_area, "Backup & Reset")

    def _load_settings(self) -> None:
        """Load current settings into UI controls."""
        # Load General settings
        general_widgets = self._settings_widgets.get("General", {})
        theme_combo = general_widgets.get("theme")
        if theme_combo:
            theme = self._config_manager.get("General", "theme", "dark")
            theme_combo.setCurrentText(theme.capitalize())

        language_combo = general_widgets.get("language")
        if language_combo:
            language = self._config_manager.get("General", "language", "en")
            # Map language code to display name
            language_map = {"en": "English", "de": "German", "es": "Spanish"}
            language_combo.setCurrentText(language_map.get(language, "English"))

        version_display = general_widgets.get("config_version")
        if version_display:
            version = self._config_manager.get("General", "config_version", "1.0")
            version_display.setText(version)

        # Load Validation settings
        validation_widgets = self._settings_widgets.get("Validation", {})
        validate_checkbox = validation_widgets.get("validate_on_import")
        if validate_checkbox:
            validate_on_import = self._config_manager.get_bool(
                "Validation", "validate_on_import", True
            )
            validate_checkbox.setChecked(validate_on_import)

        case_sensitive_checkbox = validation_widgets.get("case_sensitive")
        if case_sensitive_checkbox:
            case_sensitive = self._config_manager.get_bool("Validation", "case_sensitive", False)
            case_sensitive_checkbox.setChecked(case_sensitive)

        auto_save_checkbox = validation_widgets.get("auto_save")
        if auto_save_checkbox:
            auto_save = self._config_manager.get_bool("Validation", "auto_save", True)
            auto_save_checkbox.setChecked(auto_save)

        validation_dir_input = validation_widgets.get("validation_lists_dir")
        if validation_dir_input:
            dir_path = self._config_manager.get("Validation", "validation_lists_dir", "")
            validation_dir_input.setText(dir_path)

        # Load Correction settings
        correction_widgets = self._settings_widgets.get("Correction", {})
        auto_correct_validation_checkbox = correction_widgets.get("auto_correct_on_validation")
        if auto_correct_validation_checkbox:
            auto_correct_validation = self._config_manager.get_auto_correct_on_validation()
            auto_correct_validation_checkbox.setChecked(auto_correct_validation)

        auto_correct_import_checkbox = correction_widgets.get("auto_correct_on_import")
        if auto_correct_import_checkbox:
            auto_correct_import = self._config_manager.get_auto_correct_on_import()
            auto_correct_import_checkbox.setChecked(auto_correct_import)

        # Load UI settings
        ui_widgets = self._settings_widgets.get("UI", {})
        width_spinner = ui_widgets.get("window_width")
        if width_spinner:
            width = self._config_manager.get_int("UI", "window_width", 1024)
            width_spinner.setValue(width)

        height_spinner = ui_widgets.get("window_height")
        if height_spinner:
            height = self._config_manager.get_int("UI", "window_height", 768)
            height_spinner.setValue(height)

        page_size_spinner = ui_widgets.get("table_page_size")
        if page_size_spinner:
            page_size = self._config_manager.get_int("UI", "table_page_size", 100)
            page_size_spinner.setValue(page_size)

        logger.debug("Loaded settings into UI controls")

    def _on_setting_changed(self, section: str, option: str, value: str) -> None:
        """
        Handle setting change.

        Args:
            section (str): Configuration section
            option (str): Configuration option
            value (str): New value
        """
        # Update config
        try:
            self._config_manager.set(section, option, value)
            self._config_manager.save()

            # If this is a validation setting and we have a validation service, update it directly
            if section == "Validation" and self._validation_service:
                if option == "validate_on_import":
                    # Convert string to boolean
                    bool_value = value.lower() in ["true", "1", "yes", "y", "on"]
                    self._validation_service.set_validate_on_import(bool_value)
                    logger.debug(f"Updated ValidationService validate_on_import to {bool_value}")

                elif option == "case_sensitive":
                    # Convert string to boolean
                    bool_value = value.lower() in ["true", "1", "yes", "y", "on"]
                    self._validation_service.set_case_sensitive(bool_value)
                    logger.debug(f"Updated ValidationService case_sensitive to {bool_value}")

                elif option == "auto_save":
                    # Convert string to boolean
                    bool_value = value.lower() in ["true", "1", "yes", "y", "on"]
                    self._validation_service.set_auto_save(bool_value)
                    logger.debug(f"Updated ValidationService auto_save to {bool_value}")

            # Emit signal
            self.settings_changed.emit(section, option, value)

            logger.debug(f"Setting changed: [{section}] {option} = {value}")
        except Exception as e:
            logger.error(f"Error updating setting [{section}] {option}: {e}")
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Error updating setting: {e}",
                QMessageBox.Ok,
            )

    def _on_validation_path_browse(self) -> None:
        """Handle validation path browse button click."""
        # Get current path
        current_path = self._config_manager.get("Validation", "validation_lists_dir", "")

        # Show directory dialog
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Validation Lists Directory",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if dir_path:
            # Update config
            self._config_manager.set("Validation", "validation_lists_dir", dir_path)
            self._config_manager.save()

            # Update UI
            validation_dir_input = self._settings_widgets.get("Validation", {}).get(
                "validation_lists_dir"
            )
            if validation_dir_input:
                validation_dir_input.setText(dir_path)

            # Emit signal
            self.settings_changed.emit("Validation", "validation_lists_dir", dir_path)

            logger.info(f"Updated validation lists directory: {dir_path}")

    def _on_export_config(self) -> None:
        """Handle export configuration button click."""
        try:
            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Configuration",
                str(Path.home()),
                "JSON Files (*.json)",
            )

            if not file_path:
                return

            # Make sure it has .json extension
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            # Export configuration to JSON
            config_data = {}
            for section in self._config_manager._config.sections():
                config_data[section] = {}
                for option in self._config_manager._config.options(section):
                    config_data[section][option] = self._config_manager.get(section, option)

            # Write to file
            with open(file_path, "w") as file:
                json.dump(config_data, file, indent=4)

            # Emit signal
            self.settings_exported.emit(file_path)

            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Configuration exported to:\n{file_path}",
                QMessageBox.Ok,
            )

            logger.info(f"Exported configuration to: {file_path}")
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting configuration: {e}",
                QMessageBox.Ok,
            )

    def _on_import_config(self) -> None:
        """Handle import configuration button click."""
        try:
            # Show warning
            result = QMessageBox.warning(
                self,
                "Import Configuration",
                "Importing will overwrite your current settings. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if result != QMessageBox.Yes:
                return

            # Show open dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Configuration",
                str(Path.home()),
                "JSON Files (*.json)",
            )

            if not file_path:
                return

            # Read config from JSON
            with open(file_path, "r") as file:
                config_data = json.load(file)

            # Apply to config
            for section, options in config_data.items():
                if not self._config_manager._config.has_section(section):
                    self._config_manager._config.add_section(section)

                for option, value in options.items():
                    self._config_manager.set(section, option, value)

            # Save changes
            self._config_manager.save()

            # If we have a validation service, sync its preferences with the imported settings
            if self._validation_service and "Validation" in config_data:
                validation_options = config_data.get("Validation", {})
                prefs = {}

                # Only include known preferences
                if "validate_on_import" in validation_options:
                    # Convert the value to a proper boolean
                    value = validation_options["validate_on_import"]
                    if isinstance(value, str):
                        prefs["validate_on_import"] = value.lower() in [
                            "true",
                            "1",
                            "yes",
                            "y",
                            "on",
                        ]
                    else:
                        prefs["validate_on_import"] = bool(value)

                if "case_sensitive" in validation_options:
                    # Convert the value to a proper boolean
                    value = validation_options["case_sensitive"]
                    if isinstance(value, str):
                        prefs["case_sensitive"] = value.lower() in ["true", "1", "yes", "y", "on"]
                    else:
                        prefs["case_sensitive"] = bool(value)

                if "auto_save" in validation_options:
                    # Convert the value to a proper boolean
                    value = validation_options["auto_save"]
                    if isinstance(value, str):
                        prefs["auto_save"] = value.lower() in ["true", "1", "yes", "y", "on"]
                    else:
                        prefs["auto_save"] = bool(value)

                # Update validation service if we have any preferences to set
                if prefs:
                    self._validation_service.set_validation_preferences(prefs)
                    logger.debug(f"Synced ValidationService preferences after import: {prefs}")

            # Reload UI
            self._load_settings()

            # Emit signal
            self.settings_imported.emit(file_path)

            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                "Configuration has been imported and applied.",
                QMessageBox.Ok,
            )

            logger.info(f"Imported configuration from: {file_path}")
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing configuration: {e}",
                QMessageBox.Ok,
            )

    def _on_reset_config(self, section: Optional[str]) -> None:
        """
        Handle reset configuration button click.

        Args:
            section (Optional[str]): Section to reset, or None for all sections
        """
        # Confirm reset
        if section:
            message = f"Reset {section} settings to defaults?"
        else:
            message = "Reset ALL settings to defaults?"

        result = QMessageBox.warning(
            self,
            "Reset Settings",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        try:
            # Reset config
            self._config_manager.reset_to_defaults(section)

            # If validation section was reset, sync ValidationService preferences
            if (section == "Validation" or section is None) and self._validation_service:
                # Get updated validation preferences from config
                validate_on_import = self._config_manager.get_bool(
                    "Validation", "validate_on_import", True
                )
                case_sensitive = self._config_manager.get_bool(
                    "Validation", "case_sensitive", False
                )
                auto_save = self._config_manager.get_bool("Validation", "auto_save", True)

                # Update validation service directly
                self._validation_service.set_validation_preferences(
                    {
                        "validate_on_import": validate_on_import,
                        "case_sensitive": case_sensitive,
                        "auto_save": auto_save,
                    }
                )

                logger.debug(
                    f"Synced ValidationService preferences after reset: validate_on_import={validate_on_import}, case_sensitive={case_sensitive}, auto_save={auto_save}"
                )

            # Reload UI
            self._load_settings()

            # Emit signal
            self.settings_reset.emit(section or "all")

            # Show success message
            QMessageBox.information(
                self,
                "Reset Successful",
                "Settings have been reset to defaults.",
                QMessageBox.Ok,
            )

            if section:
                logger.info(f"Reset {section} settings to defaults")
            else:
                logger.info("Reset all settings to defaults")
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            QMessageBox.critical(
                self,
                "Reset Error",
                f"Error resetting settings: {e}",
                QMessageBox.Ok,
            )

    def refresh(self) -> None:
        """Refresh settings from the configuration manager."""
        self._load_settings()
        logger.debug("Refreshed settings from config")

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect tab and button signals if they exist
        if hasattr(self._tab_widget, "currentChanged"):
            self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Connect to the validation_preferences_changed signal if we have a validation service
        if self._validation_service and hasattr(
            self._validation_service, "validation_preferences_changed"
        ):
            try:
                self._validation_service.validation_preferences_changed.disconnect(
                    self._on_validation_preferences_changed
                )
                logger.debug("Disconnected existing validation_preferences_changed signal.")
            except (TypeError, RuntimeError):
                logger.debug("No existing validation_preferences_changed signal to disconnect.")

            # Connect the signal
            self._validation_service.validation_preferences_changed.connect(
                self._on_validation_preferences_changed
            )
            logger.debug(
                "Connected validation_preferences_changed signal to _on_validation_preferences_changed."
            )
        else:
            logger.warning(
                "ValidationService or validation_preferences_changed signal not available."
            )

    def _on_validation_preferences_changed(self, preferences: dict) -> None:
        """
        Update UI when validation preferences change in the service.

        Args:
            preferences (dict): Updated preferences
        """
        logger.debug(
            f"SettingsTabView received validation_preferences_changed signal: {preferences}"
        )

        # Get the validation section widgets
        validation_widgets = self._settings_widgets.get("Validation", {})

        # Block signals to prevent loops
        try:
            # Update checkboxes for validation preferences
            case_sensitive_checkbox = validation_widgets.get("case_sensitive")
            validate_on_import_checkbox = validation_widgets.get("validate_on_import")
            auto_save_checkbox = validation_widgets.get("auto_save")

            if case_sensitive_checkbox and "case_sensitive" in preferences:
                case_sensitive_checkbox.blockSignals(True)
                case_sensitive_checkbox.setChecked(preferences["case_sensitive"])
                case_sensitive_checkbox.blockSignals(False)
                logger.debug(f"Updated case_sensitive checkbox to {preferences['case_sensitive']}")

            if validate_on_import_checkbox and "validate_on_import" in preferences:
                validate_on_import_checkbox.blockSignals(True)
                validate_on_import_checkbox.setChecked(preferences["validate_on_import"])
                validate_on_import_checkbox.blockSignals(False)
                logger.debug(
                    f"Updated validate_on_import checkbox to {preferences['validate_on_import']}"
                )

            if auto_save_checkbox and "auto_save" in preferences:
                auto_save_checkbox.blockSignals(True)
                auto_save_checkbox.setChecked(preferences["auto_save"])
                auto_save_checkbox.blockSignals(False)
                logger.debug(f"Updated auto_save checkbox to {preferences['auto_save']}")

        except Exception as e:
            logger.error(f"Error updating validation preferences in UI: {e}")

    def _on_tab_changed(self, index: int) -> None:
        """
        Handle tab change in settings view.

        Args:
            index (int): The index of the selected tab
        """
        logger.debug(f"Settings tab changed to index {index}")
        # Any additional logic for tab changes can be added here
