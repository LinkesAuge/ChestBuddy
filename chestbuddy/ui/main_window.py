"""
MainWindow class for the ChestBuddy application.

This module defines the MainWindow class, which is the main window of the ChestBuddy
application. It contains the menu bar, toolbar, and the main widget.
"""

import logging
import os
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTabWidget,
    QToolBar,
)

from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.utils.config import ConfigManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main window of the ChestBuddy application.

    This class represents the main window of the application and contains all the UI components.
    It also handles the menu actions and toolbar actions.

    Signals:
        load_csv_triggered: Signal emitted when the user wants to load a CSV file.
        save_csv_triggered: Signal emitted when the user wants to save a CSV file.
        validate_data_triggered: Signal emitted when the user wants to validate the data.
        apply_corrections_triggered: Signal emitted when the user wants to apply corrections.
        export_validation_issues_triggered: Signal emitted when the user wants to export validation issues.
    """

    # Signals to communicate with the application
    load_csv_triggered = Signal(str)
    save_csv_triggered = Signal(str)
    validate_data_triggered = Signal()
    apply_corrections_triggered = Signal()
    export_validation_issues_triggered = Signal(str)

    def __init__(self, data_model, validation_service, correction_service):
        """
        Initialize the MainWindow.

        Args:
            data_model: The data model to use.
            validation_service: The validation service to use.
            correction_service: The correction service to use.
        """
        super().__init__()

        # Store references to the model and services
        self._data_model = data_model
        self._validation_service = validation_service
        self._correction_service = correction_service
        self._config = ConfigManager()

        # Initialize the UI
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("ChestBuddy - Chest Tracker Correction Tool")
        self.setMinimumSize(1024, 768)

        # Create the menu bar
        self._create_menu_bar()

        # Create the toolbar
        self._create_toolbar()

        # Create the main widget
        self._create_main_widget()

        # Set the central widget
        self.setCentralWidget(self._tab_widget)

        # Restore window geometry
        geometry = self._config.get("Window", "geometry", "")
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open action
        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open a CSV file")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        # Recent files menu
        self._recent_files_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self._recent_files_menu)
        self._update_recent_files_menu()

        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current file")
        save_action.triggered.connect(self._on_save_file)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Save the current file with a new name")
        save_as_action.triggered.connect(self._on_save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export validation issues action
        export_validation_action = QAction("Export &Validation Issues...", self)
        export_validation_action.setStatusTip("Export validation issues to a CSV file")
        export_validation_action.triggered.connect(self._on_export_validation_issues)
        file_menu.addAction(export_validation_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Validate action
        validate_action = QAction("&Validate Data", self)
        validate_action.setStatusTip("Validate the data against rules")
        validate_action.triggered.connect(self._on_validate_data)
        tools_menu.addAction(validate_action)

        # Apply corrections action
        correct_action = QAction("Apply &Corrections", self)
        correct_action.setStatusTip("Apply corrections to the data")
        correct_action.triggered.connect(self._on_apply_corrections)
        tools_menu.addAction(correct_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show information about the application")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # Open action
        open_action = QAction(QIcon(":/icons/open.png"), "Open", self)
        open_action.setStatusTip("Open a CSV file")
        open_action.triggered.connect(self._on_open_file)
        toolbar.addAction(open_action)

        # Save action
        save_action = QAction(QIcon(":/icons/save.png"), "Save", self)
        save_action.setStatusTip("Save the current file")
        save_action.triggered.connect(self._on_save_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Validate action
        validate_action = QAction(QIcon(":/icons/validate.png"), "Validate", self)
        validate_action.setStatusTip("Validate the data against rules")
        validate_action.triggered.connect(self._on_validate_data)
        toolbar.addAction(validate_action)

        # Apply corrections action
        correct_action = QAction(QIcon(":/icons/correct.png"), "Correct", self)
        correct_action.setStatusTip("Apply corrections to the data")
        correct_action.triggered.connect(self._on_apply_corrections)
        toolbar.addAction(correct_action)

    def _create_main_widget(self):
        """Create the main widget."""
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._tab_widget.setMovable(True)

        # Data view
        self._data_view = DataView(self._data_model)
        self._tab_widget.addTab(self._data_view, "Data")

        # Validation tab
        self._validation_tab = ValidationTab(self._data_model, self._validation_service)
        self._tab_widget.addTab(self._validation_tab, "Validation")

        # Correction tab
        self._correction_tab = CorrectionTab(self._data_model, self._correction_service)
        self._tab_widget.addTab(self._correction_tab, "Correction")

    def _connect_signals(self):
        """Connect signals to slots."""
        # Connect data model signals
        self._data_model.data_changed.connect(self._on_data_changed)

    def _on_open_file(self):
        """Handle the open file action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            str(self._config.get_path("Files", "last_directory", Path.home())),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            self._config.set_path("Files", "last_directory", Path(file_path).parent)
            self._config.add_recent_file(file_path)
            self._update_recent_files_menu()
            self.load_csv_triggered.emit(file_path)

    def _on_open_recent_file(self, file_path):
        """Handle opening a recent file."""
        self.load_csv_triggered.emit(file_path)
        self._config.add_recent_file(file_path)
        self._update_recent_files_menu()

    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        self._recent_files_menu.clear()
        recent_files = self._config.get_recent_files()

        if not recent_files:
            no_recent_action = QAction("No Recent Files", self)
            no_recent_action.setEnabled(False)
            self._recent_files_menu.addAction(no_recent_action)
            return

        for file_path in recent_files:
            action = QAction(os.path.basename(file_path), self)
            action.setStatusTip(file_path)
            action.triggered.connect(
                lambda checked, path=file_path: self._on_open_recent_file(path)
            )
            self._recent_files_menu.addAction(action)

        self._recent_files_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._on_clear_recent_files)
        self._recent_files_menu.addAction(clear_action)

    def _on_clear_recent_files(self):
        """Clear the recent files list."""
        self._config.set_list("Files", "recent_files", [])
        self._update_recent_files_menu()

    def _on_save_file(self):
        """Handle the save file action."""
        current_file = self._config.get("Files", "current_file", "")
        if current_file and os.path.exists(current_file):
            self.save_csv_triggered.emit(current_file)
        else:
            self._on_save_file_as()

    def _on_save_file_as(self):
        """Handle the save file as action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            str(self._config.get_path("Files", "last_directory", Path.home())),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            # Ensure the file has a .csv extension
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"

            self._config.set("Files", "current_file", file_path)
            self._config.set_path("Files", "last_directory", Path(file_path).parent)
            self.save_csv_triggered.emit(file_path)

    def _on_export_validation_issues(self):
        """Handle the export validation issues action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Validation Issues",
            str(self._config.get_path("Files", "last_directory", Path.home())),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            # Ensure the file has a .csv extension
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"

            self._config.set_path("Files", "last_directory", Path(file_path).parent)
            self.export_validation_issues_triggered.emit(file_path)

    def _on_validate_data(self):
        """Handle the validate data action."""
        self.validate_data_triggered.emit()
        self._tab_widget.setCurrentWidget(self._validation_tab)

    def _on_apply_corrections(self):
        """Handle the apply corrections action."""
        self.apply_corrections_triggered.emit()
        self._tab_widget.setCurrentWidget(self._correction_tab)

    def _on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About ChestBuddy",
            "ChestBuddy - Chest Tracker Correction Tool\n\n"
            "Version: 0.1.0\n\n"
            "A tool for validating and correcting chest tracker data.\n\n"
            "© 2023 ChestBuddy Team",
        )

    def _on_data_changed(self):
        """Handle data model changes."""
        self.setWindowModified(True)
        self._update_window_title()

    def _update_window_title(self):
        """Update the window title to show the current file and modified status."""
        current_file = self._config.get("Files", "current_file", "")
        if current_file:
            file_name = os.path.basename(current_file)
            self.setWindowTitle(f"ChestBuddy - {file_name}[*]")
        else:
            self.setWindowTitle("ChestBuddy - Chest Tracker Correction Tool[*]")

    def closeEvent(self, event):
        """Handle the window close event."""
        # Save window geometry
        self._config.set("Window", "geometry", self.saveGeometry().hex())
        self._config.save()

        # Accept the event
        event.accept()
