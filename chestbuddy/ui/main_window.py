"""
main_window.py

Description: Main window of the ChestBuddy application
Usage:
    window = MainWindow(data_model, services)
    window.show()
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Set, Tuple

from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QMenuBar,
    QStatusBar,
    QMenu,
    QFileDialog,
    QMessageBox,
    QApplication,
    QStackedWidget,
    QProgressDialog,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CSVService, ValidationService, CorrectionService, ChartService
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.resources.resource_manager import ResourceManager
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation, NavigationSection
from chestbuddy.ui.widgets.status_bar import StatusBar
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.views.dashboard_view import DashboardView
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.views.correction_view_adapter import CorrectionViewAdapter
from chestbuddy.ui.views.chart_view_adapter import ChartViewAdapter
from chestbuddy.ui.widgets import ProgressDialog, ProgressBar
from chestbuddy.ui.data_view import DataView
import pandas as pd

# Set up logger
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main window of the ChestBuddy application.

    Signals:
        file_opened (str): Signal emitted when a file is opened, with the file path.
        file_saved (str): Signal emitted when a file is saved, with the file path.
        validation_requested (): Signal emitted when data validation is requested.
        correction_requested (): Signal emitted when data correction is requested.
        load_csv_triggered (list): Signal emitted when a CSV file load is triggered.
        save_csv_triggered (str): Signal emitted when a CSV file save is triggered.
        validate_data_triggered (): Signal emitted when data validation is triggered.
        apply_corrections_triggered (): Signal emitted when corrections should be applied.
        export_validation_issues_triggered (str): Signal emitted when validation issues export is triggered.

    Attributes:
        data_model (ChestDataModel): The data model for the application.
        csv_service (CSVService): Service for CSV operations.
        validation_service (ValidationService): Service for data validation.
        correction_service (CorrectionService): Service for data correction.
        chart_service (ChartService): Service for chart generation.

    Implementation Notes:
        - Uses a sidebar navigation for app sections
        - Contains a stacked widget for content views
        - Provides a dashboard view as the main landing page
        - Manages the application's main actions and menus
        - Includes a status bar for application status
    """

    # Signals
    file_opened = Signal(str)
    file_saved = Signal(str)
    validation_requested = Signal()
    correction_requested = Signal()
    load_csv_triggered = Signal(list)
    save_csv_triggered = Signal(str)
    validate_data_triggered = Signal()
    apply_corrections_triggered = Signal()
    export_validation_issues_triggered = Signal(str)

    def __init__(
        self,
        data_model: ChestDataModel,
        csv_service: CSVService,
        validation_service: ValidationService,
        correction_service: CorrectionService,
        chart_service: ChartService,
        data_manager=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the MainWindow.

        Args:
            data_model: The data model to use.
            csv_service: Service for CSV operations.
            validation_service: Service for data validation.
            correction_service: Service for data correction.
            chart_service: Service for chart generation.
            data_manager: The data manager service (optional).
            parent: The parent widget.
        """
        super().__init__(parent)

        # Store references to services
        self._data_model = data_model
        self._csv_service = csv_service
        self._validation_service = validation_service
        self._correction_service = correction_service
        self._chart_service = chart_service
        self._data_manager = data_manager

        if self._data_manager:
            logger.debug("MainWindow initialized with data_manager")
        else:
            logger.error("MainWindow initialized WITHOUT data_manager")

        # Set window title and icon
        self.setWindowTitle("ChestBuddy - Chest Data Analysis Tool")
        self.setWindowIcon(Icons.get_icon(Icons.APP_ICON))

        # Set window size
        self.resize(1200, 800)

        # Initialize UI
        self._init_ui()

        # Create menus
        self._init_menus()

        # Connect signals
        self._connect_signals()

        # Load settings
        self._load_settings()

        # Initialize recent files
        self._recent_files: List[str] = []
        self._load_recent_files()

        # Don't set up progress dialog yet - it will be created when needed
        self._progress_dialog = None

        # State tracking for file loading progress
        self._loading_state = {
            "total_files": 0,  # Total number of files being loaded
            "current_file_index": 0,  # Current file being processed (1-based)
            "current_file": "",  # Path of current file
            "processed_files": [],  # List of processed file paths
            "total_rows": 0,  # Total rows processed so far
        }

        # Update UI
        self._update_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar navigation
        self._sidebar = SidebarNavigation()
        self._sidebar.navigation_changed.connect(self._on_navigation_changed)
        main_layout.addWidget(self._sidebar)

        # Create content stack
        self._content_stack = QStackedWidget()
        main_layout.addWidget(self._content_stack)

        # Set layout stretch
        main_layout.setStretch(0, 0)  # Sidebar doesn't stretch
        main_layout.setStretch(1, 1)  # Content area stretches

        # Create status bar
        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)

        # Create views
        self._create_views()

        # Set initial view to Dashboard
        self._set_active_view("Dashboard")

    def _create_views(self) -> None:
        """Create the views for the application."""
        # Dictionary to store views
        self._views: Dict[str, BaseView] = {}

        # Create Dashboard view
        dashboard_view = DashboardView(self._data_model)
        dashboard_view.action_triggered.connect(self._on_dashboard_action)
        dashboard_view.file_selected.connect(self._on_recent_file_selected)
        self._content_stack.addWidget(dashboard_view)
        self._views["Dashboard"] = dashboard_view

        # Create Data view
        data_view = DataViewAdapter(self._data_model)
        self._content_stack.addWidget(data_view)
        self._views["Data"] = data_view

        # Create Validation view
        validation_view = ValidationViewAdapter(self._data_model, self._validation_service)
        self._content_stack.addWidget(validation_view)
        self._views["Validation"] = validation_view

        # Create Correction view
        correction_view = CorrectionViewAdapter(self._data_model, self._correction_service)
        self._content_stack.addWidget(correction_view)
        self._views["Correction"] = correction_view

        # Create Analysis/Charts view
        chart_view = ChartViewAdapter(self._data_model, self._chart_service)
        self._content_stack.addWidget(chart_view)
        self._views["Charts"] = chart_view

        # TODO: Add placeholder views for other sections
        # For Reports, Settings, Help if needed

    def _init_menus(self) -> None:
        """Initialize the application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")

        # Open action
        self._open_action = QAction(Icons.get_icon(Icons.OPEN), "&Open...", self)
        self._open_action.setShortcut(QKeySequence.Open)
        self._open_action.setStatusTip("Open a CSV file")
        self._open_action.triggered.connect(self._open_file)
        file_menu.addAction(self._open_action)

        # Save action
        self._save_action = QAction(Icons.get_icon(Icons.SAVE), "&Save", self)
        self._save_action.setShortcut(QKeySequence.Save)
        self._save_action.setStatusTip("Save the current file")
        self._save_action.triggered.connect(self._save_file)
        file_menu.addAction(self._save_action)

        # Save As action
        self._save_as_action = QAction("Save &As...", self)
        self._save_as_action.setShortcut(QKeySequence.SaveAs)
        self._save_as_action.setStatusTip("Save the file with a new name")
        self._save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(self._save_as_action)

        file_menu.addSeparator()

        # Recent files submenu
        self._recent_files_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self._recent_files_menu)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Data menu
        data_menu = self.menuBar().addMenu("&Data")

        # Validate action
        self._validate_action = QAction(Icons.get_icon(Icons.VALIDATE), "&Validate", self)
        self._validate_action.setStatusTip("Validate the data")
        self._validate_action.triggered.connect(self._validate_data)
        data_menu.addAction(self._validate_action)

        # Correct action
        self._correct_action = QAction(Icons.get_icon(Icons.CORRECT), "&Correct", self)
        self._correct_action.setStatusTip("Apply corrections to the data")
        self._correct_action.triggered.connect(self._correct_data)
        data_menu.addAction(self._correct_action)

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Data manager signals
        self._data_manager.load_started.connect(self._on_load_started)
        self._data_manager.load_progress.connect(self._on_load_progress)
        self._data_manager.load_finished.connect(self._on_load_finished)
        self._data_manager.load_error.connect(self._on_load_error)
        self._data_manager.load_success.connect(self.refresh_ui)
        self._data_manager.populate_table_requested.connect(self._on_populate_table_requested)

        # Data model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect data model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect data manager signals for progress reporting
        if self._data_manager:
            logger.debug("Connecting data_manager signals in MainWindow")
            self._data_manager.load_started.connect(self._on_load_started)
            self._data_manager.load_progress.connect(self._on_load_progress)
            self._data_manager.load_finished.connect(self._on_load_finished)
            self._data_manager.load_success.connect(lambda msg: self._status_bar.set_status(msg))
            self._data_manager.load_error.connect(self._on_load_error)
            logger.debug("All data_manager signals connected successfully")
        else:
            logger.warning("No data_manager available, progress signals will not be connected")

    def _load_settings(self) -> None:
        """Load application settings."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _save_settings(self) -> None:
        """Save application settings."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        settings.setValue("geometry", self.saveGeometry())
        settings.sync()

    def _load_recent_files(self) -> None:
        """Load the list of recent files."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        self._recent_files = settings.value("recentFiles", [])
        if not isinstance(self._recent_files, list):
            self._recent_files = []
        self._update_recent_files_menu()

    def _save_recent_files(self) -> None:
        """Save the list of recent files."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        settings.setValue("recentFiles", self._recent_files)
        settings.sync()

    def _add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: The path of the file to add.
        """
        # Remove if already exists
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)

        # Add to the beginning of the list
        self._recent_files.insert(0, file_path)

        # Limit to 10 recent files
        if len(self._recent_files) > 10:
            self._recent_files = self._recent_files[:10]

        # Update menu and save
        self._update_recent_files_menu()
        self._save_recent_files()

        # Update dashboard
        dashboard_view = self._views.get("Dashboard")
        if dashboard_view and isinstance(dashboard_view, DashboardView):
            dashboard_view.set_recent_files(self._recent_files)

    def _update_recent_files_menu(self) -> None:
        """Update the recent files menu."""
        self._recent_files_menu.clear()

        for file_path in self._recent_files:
            action = QAction(os.path.basename(file_path), self)
            action.setData(file_path)
            action.triggered.connect(
                lambda checked=False, path=file_path: self._open_recent_file(path)
            )
            self._recent_files_menu.addAction(action)

        if not self._recent_files:
            no_files_action = QAction("No recent files", self)
            no_files_action.setEnabled(False)
            self._recent_files_menu.addAction(no_files_action)

    def _update_ui(self) -> None:
        """Update the UI based on the current state."""
        has_data = not self._data_model.is_empty

        # Update actions
        self._save_action.setEnabled(has_data)
        self._save_as_action.setEnabled(has_data)
        self._validate_action.setEnabled(has_data)
        self._correct_action.setEnabled(has_data)

        # Update status bar
        if has_data:
            row_count = len(self._data_model.data)
            self._status_bar.set_record_count(row_count)

            # Get the current file path
            try:
                current_file = self._data_model.file_path
                if current_file:
                    self._status_bar.set_status(f"Loaded: {os.path.basename(current_file)}")
                else:
                    self._status_bar.set_status("Data loaded (unsaved)")
            except Exception as e:
                logger.error(f"Error updating UI with file path: {e}")
                self._status_bar.set_status("Data loaded")
        else:
            self._status_bar.clear_all()
            self._status_bar.set_status("No data loaded")

    @Slot(str)
    def _set_active_view(self, view_name: str) -> None:
        """
        Set the active view.

        Args:
            view_name: The name of the view to activate.
        """
        try:
            logger.info(f"Setting active view to: {view_name}")
            view = self._views.get(view_name)
            if view:
                self._content_stack.setCurrentWidget(view)
                self._sidebar.set_active_item(view_name)
                logger.info(f"View '{view_name}' activated successfully")
            else:
                logger.warning(f"View '{view_name}' not found in available views")
        except Exception as e:
            logger.error(f"Error setting active view to {view_name}: {e}")

    # ===== Slots =====

    @Slot(str, str)
    def _on_navigation_changed(self, section: str, subsection: Optional[str] = None) -> None:
        """
        Handle navigation changes.

        Args:
            section: The selected section.
            subsection: The selected subsection, if any.
        """
        logger.debug(f"Navigation changed: {section} - {subsection}")

        if subsection:
            # Handle subsections
            if section == "Data":
                if subsection == "Import":
                    self._open_file()
                elif subsection == "Validate":
                    self._set_active_view("Validation")
                elif subsection == "Correct":
                    self._set_active_view("Correction")
                elif subsection == "Export":
                    self._save_file_as()
            elif section == "Analysis":
                if subsection == "Charts":
                    self._set_active_view("Charts")
                elif subsection == "Tables":
                    # TODO: Handle tables view
                    pass
            elif section == "Settings":
                # TODO: Handle settings subsections
                pass
        else:
            # Handle main sections
            if section == "Dashboard":
                self._set_active_view("Dashboard")
            elif section == "Data":
                self._set_active_view("Data")
            elif section == "Analysis":
                self._set_active_view("Charts")
            elif section == "Reports":
                # TODO: Handle reports view
                pass
            elif section == "Settings":
                # TODO: Handle settings view
                pass
            elif section == "Help":
                # TODO: Handle help view
                pass

    @Slot(str)
    def _on_dashboard_action(self, action: str) -> None:
        """
        Handle actions triggered from the dashboard.

        Args:
            action: The action name.
        """
        if action == "import":
            self._open_file()
        elif action == "validate":
            self._validate_data()
            self._set_active_view("Validation")
        elif action == "analyze":
            self._set_active_view("Charts")
        elif action == "report":
            # TODO: Handle report generation
            pass

    @Slot(str)
    def _on_recent_file_selected(self, file_path: str) -> None:
        """
        Handle selection of a recent file.

        Args:
            file_path: The path of the selected file.
        """
        self._open_recent_file(file_path)

    @Slot()
    def _on_data_changed(self) -> None:
        """Handle data model changes."""
        self._update_ui()

    @Slot(object)
    def _on_validation_changed(self, validation_status: Any) -> None:
        """
        Handle validation status changes.

        Args:
            validation_status: The new validation status.
        """
        if not validation_status.empty:
            issue_count = len(validation_status)
            self._status_bar.set_status(f"Found {issue_count} validation issues")
        else:
            self._status_bar.set_status("Validation completed: No issues found")

    @Slot(object)
    def _on_correction_applied(self, correction_status: Any) -> None:
        """
        Handle correction status changes.

        Args:
            correction_status: The new correction status.
        """
        if not correction_status.empty:
            row_count = len(correction_status)
            self._status_bar.set_status(f"Corrections applied to {row_count} rows")
        else:
            self._status_bar.set_status("No corrections were applied")

    @Slot()
    def _on_load_started(self) -> None:
        """Handle when a loading operation starts."""
        logger.debug("MainWindow._on_load_started called")

        # Initialize loading state
        self._loading_state = {
            "current_file": "",
            "current_file_index": 0,
            "processed_files": [],
            "total_files": 0,  # Will be set by the caller via total_files property
            "total_rows": 0,
        }

        # Get total files from data manager if available
        if self._data_manager and hasattr(self._data_manager, "total_files"):
            self._loading_state["total_files"] = self._data_manager.total_files
            logger.debug(
                f"Setting total files to {self._loading_state['total_files']} from data manager"
            )

        # Reset state flags
        self._total_rows_loaded = 0
        self._total_rows_estimated = 0
        self._last_progress_current = 0
        self._file_loading_complete = False
        self._table_population_complete = False
        self._table_population_in_progress = False

        # Close any existing progress dialog to avoid duplicates
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                # Disconnect any existing signals
                try:
                    self._progress_dialog.canceled.disconnect()
                except:
                    pass

                # Close the existing dialog
                self._progress_dialog.close()

                # Ensure it's deleted
                self._progress_dialog.deleteLater()
                self._progress_dialog = None

                # Process events to ensure UI updates
                QApplication.processEvents()

                logger.debug("Closed existing progress dialog")
            except Exception as e:
                logger.error(f"Error closing existing progress dialog: {e}")
                # Continue anyway

        # Flag to track if dialog was successfully created and shown
        progress_dialog_ready = False

        try:
            # Create a new progress dialog with our custom implementation
            self._progress_dialog = ProgressDialog(
                "Preparing to load data...", "Cancel", 0, 100, self
            )
            self._progress_dialog.setWindowTitle("CSV Import - ChestBuddy")

            # Set the dialog to modal to prevent interaction with the main window
            # but use Qt.ApplicationModal instead of Qt.WindowModal to ensure it stays on top
            self._progress_dialog.setWindowModality(Qt.ApplicationModal)

            # Connect cancel button
            self._progress_dialog.canceled.connect(self._cancel_loading)
            progress_dialog_ready = True

            # Make sure dialog is visible and activated
            self._progress_dialog.show()
            self._progress_dialog.raise_()
            self._progress_dialog.activateWindow()

            # Process events to ensure UI updates
            QApplication.processEvents()

        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            self._progress_dialog = None
            progress_dialog_ready = False
            # Show error message to user
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create progress dialog: {e}\nFile loading canceled.",
            )
            # Cancel the loading operation
            self._cancel_loading()

        # Only proceed if dialog is ready
        if not progress_dialog_ready:
            logger.warning("Progress dialog not ready, canceling loading operation")
            self._cancel_loading()

    def _on_load_finished(self, status_message: str) -> None:
        """
        Handle the completion of a loading operation.

        Args:
            status_message: Message indicating the status of the loading operation
        """
        logger.debug(f"Load finished: {status_message}")

        # Early return if progress dialog doesn't exist
        if not hasattr(self, "_progress_dialog") or not self._progress_dialog:
            logger.debug("No progress dialog to update")
            return

        try:
            # Check if this is a processing message (which means we're transitioning to table population)
            is_processing_message = (
                "processing" in status_message.lower() or "populating" in status_message.lower()
            )

            # Check if table population is already in progress or complete
            is_table_population = (
                self._table_population_in_progress or self._table_population_complete
            )

            # Check if this is an error message
            is_error = "error" in status_message.lower() or "failed" in status_message.lower()

            # If this is an intermediate processing message, we don't finalize the dialog yet
            if is_processing_message and not is_table_population and not is_error:
                # Set flag to indicate file loading is complete but table population is next
                self._file_loading_complete = True

                # Update progress dialog for transition to table population
                if hasattr(self._progress_dialog, "setStatusText"):
                    self._progress_dialog.setStatusText(status_message)

                # Set progress to 100% to indicate file loading is complete
                self._progress_dialog.setValue(100)

                # Make sure dialog is still responsive
                self._progress_dialog.setCancelButtonEnabled(True)

                # Force UI to process events to prevent dialog from appearing frozen
                QApplication.processEvents()

                # Early return as we don't want to finalize the dialog yet
                return

            # If we reach here, this is the final completion or an error

            # Update the dialog to indicate completion
            self._progress_dialog.setLabelText("Loading complete")

            # Set progress to max to indicate completion
            self._progress_dialog.setValue(self._progress_dialog.maximum())

            # Set status text if we have a status message
            if hasattr(self._progress_dialog, "setStatusText"):
                self._progress_dialog.setStatusText(status_message)

            # If message contains "error" or "failed", show error styling
            if is_error:
                # Error state - show confirmation to close
                logger.error(f"Load operation failed: {status_message}")
                self._progress_dialog.setButtonText("Close")

                # Set error state if the method exists
                if hasattr(self._progress_dialog, "setState") and hasattr(ProgressBar, "State"):
                    self._progress_dialog.setState(ProgressBar.State.ERROR)
            else:
                # Success state - show confirmation to continue
                logger.debug(f"Load operation completed successfully: {status_message}")
                self._progress_dialog.setButtonText("Close")

            # Disconnect previous signal connections to cancel loading
            try:
                self._progress_dialog.canceled.disconnect(self._cancel_loading)
            except:
                pass  # Ignore if not connected

            # Connect cancel button to close the dialog
            self._progress_dialog.canceled.connect(self._progress_dialog.close)

            # Enable the button to allow user to continue
            if hasattr(self._progress_dialog, "setCancelButtonEnabled"):
                self._progress_dialog.setCancelButtonEnabled(True)

            # Force UI to process events to keep dialog responsive
            QApplication.processEvents()

        except Exception as e:
            logger.error(f"Error updating progress dialog on load finished: {e}")
            # Try to ensure the dialog can be closed
            try:
                if self._progress_dialog and hasattr(self._progress_dialog, "_cancel_button"):
                    self._progress_dialog._cancel_button.setEnabled(True)
                    self._progress_dialog._cancel_button.setText("Close")
                    self._progress_dialog._cancel_button.clicked.disconnect()
                    self._progress_dialog._cancel_button.clicked.connect(
                        self._progress_dialog.close
                    )
            except Exception as inner_e:
                logger.error(f"Failed to recover progress dialog: {inner_e}")

    def _on_populate_table_requested(self, data: pd.DataFrame) -> None:
        """
        Handle request to populate table during data loading.
        This synchronizes table population with file import.

        Args:
            data: The data to populate in the table
        """
        logger.debug(f"Received request to populate table with {len(data):,} rows")

        # Set flags indicating we've reached table population phase
        self._file_loading_complete = True
        self._table_population_complete = False
        self._table_population_in_progress = True

        # Update progress dialog to show table population
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                # Make sure the dialog exists and is visible
                if not self._progress_dialog.isVisible():
                    logger.debug("Progress dialog not visible during table population, showing it")
                    # Don't create a new one, just make sure the existing one is visible
                    self._progress_dialog.show()

                # Reset the progress bar for table population phase
                self._progress_dialog.setLabelText(f"Populating table with {len(data):,} rows...")
                self._progress_dialog.setValue(0)  # Reset progress for table population
                self._progress_dialog.setStatusText("Building data table...")

                # Make cancel button show "Cancel" during table population
                self._progress_dialog.setCancelButtonText("Cancel")

                # Make sure cancel button is enabled to prevent dialog from appearing frozen
                if hasattr(self._progress_dialog, "setCancelButtonEnabled"):
                    self._progress_dialog.setCancelButtonEnabled(True)

                # Make sure dialog is in front
                self._progress_dialog.raise_()
                self._progress_dialog.activateWindow()

                # Force UI to process events to keep dialog responsive
                QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error updating progress dialog for table population: {e}")
                # Continue anyway

            # Set up a timer to update progress during table population
            if not hasattr(self, "_table_population_timer") or self._table_population_timer is None:
                self._table_population_timer = QTimer()
                self._table_population_timer.timeout.connect(self._update_table_population_progress)

            # Reset table population tracking variables
            self._table_population_start_time = datetime.now()
            self._table_population_progress = 0

            # Start the timer with a shorter interval for more responsive updates
            self._table_population_timer.start(50)  # Update every 50ms for smoother animation

        # Track if table was populated successfully
        table_populated = False

        # Get the data view
        if hasattr(self, "_content_stack"):
            # Find the data view
            for i in range(self._content_stack.count()):
                widget = self._content_stack.widget(i)
                if hasattr(widget, "_update_view"):
                    # Update the view with progress tracking
                    try:
                        # Call update view to populate table (it has its own chunking)
                        widget._update_view()
                        table_populated = True
                        break
                    except Exception as e:
                        logger.error(f"Error populating table: {e}")

        # Stop the progress timer
        if hasattr(self, "_table_population_timer") and self._table_population_timer is not None:
            if self._table_population_timer.isActive():
                self._table_population_timer.stop()

        # Update progress to 100% to ensure we show completion
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.setValue(100)
            QApplication.processEvents()

        # After table population is complete, finalize the progress dialog
        if table_populated:
            # Set flag to indicate completion
            self._table_population_complete = True
            self._table_population_in_progress = False

            # Call _on_load_finished with a completion message
            completion_message = f"Successfully loaded and populated table with {len(data):,} rows"
            self._on_load_finished(completion_message)
        else:
            # Handle failed table population
            self._table_population_complete = False
            self._table_population_in_progress = False
            self._on_load_finished("Error: Failed to populate data table")

    def _update_table_population_progress(self):
        """Update the progress dialog during table population."""
        if not hasattr(self, "_progress_dialog") or not self._progress_dialog:
            return

        # Only update if table population is in progress
        if not self._table_population_in_progress:
            return

        # Initialize tracking variables if needed
        if not hasattr(self, "_table_population_start_time"):
            self._table_population_start_time = datetime.now()
            self._table_population_progress = 0

        # Calculate elapsed time since table population started
        elapsed = (datetime.now() - self._table_population_start_time).total_seconds()
        if elapsed < 0.1:
            elapsed = 0.1

        # Use a realistic progress curve based on elapsed time
        # For most tables, population is quick at first then slows down
        # Progress from 0 to 99 (leave final 1% for completion)

        # For first 3 seconds, progress quickly to 60%
        if elapsed <= 3:
            target_progress = min(60, int(elapsed * 20))
        # For next 7 seconds, progress to 90%
        elif elapsed <= 10:
            target_progress = min(90, 60 + int((elapsed - 3) * 4.3))
        # For next 10 seconds, progress to 95%
        elif elapsed <= 20:
            target_progress = min(95, 90 + int((elapsed - 10) * 0.5))
        # For remaining time, creep to 99%
        else:
            # Slow asymptotic approach to 99%
            target_progress = min(99, 95 + int(min(4, (elapsed - 20) * 0.1)))

        # Update progress only if it's increased (never go backwards)
        if target_progress > self._table_population_progress:
            self._table_population_progress = target_progress

            # Update the progress dialog with current progress
            self._progress_dialog.setValue(self._table_population_progress)

            # Every 10% update the status text to show more detail
            if self._table_population_progress % 10 == 0:
                if elapsed > 5:
                    # After 5 seconds, show elapsed time
                    self._progress_dialog.setStatusText(
                        f"Building data table... ({int(elapsed)}s elapsed)"
                    )
                else:
                    # Just show the basic message initially
                    self._progress_dialog.setStatusText("Building data table...")

            # Process events only occasionally to avoid UI slowdown
            if self._table_population_progress % 5 == 0:
                QApplication.processEvents()

        # Stop the timer if we've reached max progress or table population is complete
        if self._table_population_progress >= 99 or self._table_population_complete:
            if hasattr(self, "_table_population_timer") and self._table_population_timer.isActive():
                self._table_population_timer.stop()

    def _on_load_progress(self, file_path: str, current: int, total: int) -> None:
        """
        Handle progress updates during loading.

        Args:
            file_path: Path of the file being processed (empty for overall progress)
            current: Current progress value
            total: Total progress value
        """
        # Ensure progress dialog exists
        if not hasattr(self, "_progress_dialog") or not self._progress_dialog:
            return

        try:
            # Skip progress updates if table population is complete
            if hasattr(self, "_table_population_complete") and self._table_population_complete:
                return

            # Update loading state based on signal type
            if file_path:
                # This is a file-specific progress update
                # If this is a new file, update the file index
                if file_path != self._loading_state["current_file"]:
                    # If we're moving to a new file, record the size of the completed file
                    if self._loading_state["current_file"]:
                        # Initialize file sizes tracking dictionary if it doesn't exist
                        if not hasattr(self, "_file_sizes"):
                            self._file_sizes = {}
                        # Store the actual size of the completed file
                        self._file_sizes[self._loading_state["current_file"]] = self._loading_state[
                            "total_rows"
                        ]

                    # Add new file to processed files if needed
                    if file_path not in self._loading_state["processed_files"]:
                        self._loading_state["current_file_index"] += 1
                        if file_path not in self._loading_state["processed_files"]:
                            self._loading_state["processed_files"].append(file_path)
                    self._loading_state["current_file"] = file_path

                # Update total rows for this file
                self._loading_state["total_rows"] = max(total, self._loading_state["total_rows"])

                # Track rows across all files
                if not hasattr(self, "_total_rows_loaded"):
                    self._total_rows_loaded = 0
                    self._total_rows_estimated = 0
                    self._last_progress_current = 0
                    self._file_sizes = {}

                # Increment total rows loaded by the increase since last update
                if hasattr(self, "_last_progress_current"):
                    # Only increment if current is greater than last value (to avoid counting backwards)
                    if current > self._last_progress_current:
                        self._total_rows_loaded += current - self._last_progress_current
                    self._last_progress_current = current
                else:
                    self._last_progress_current = current

                # Better row estimation based on known file sizes
                if hasattr(self, "_file_sizes"):
                    # Calculate known total from processed files
                    known_sizes = sum(self._file_sizes.values())
                    known_files = len(self._file_sizes)

                    # Current file's expected size
                    current_size = total

                    # Calculate average file size from known files
                    if known_files > 0:
                        avg_size = known_sizes / known_files
                    else:
                        avg_size = current_size  # Fall back to current file size

                    # Count remaining files
                    remaining_files = (
                        self._loading_state["total_files"] - known_files - 1
                    )  # -1 for current file
                    if remaining_files < 0:
                        remaining_files = 0

                    # Estimate total rows across all files
                    self._total_rows_estimated = (
                        known_sizes + current_size + (avg_size * remaining_files)
                    )
                else:
                    # Fall back to simpler estimation if we don't have file sizes yet
                    self._total_rows_estimated = max(
                        self._total_rows_estimated,
                        total * len(self._loading_state["processed_files"]),
                    )

            # Calculate progress percentage safely
            percentage = min(100, int((current * 100 / total) if total > 0 else 0))

            # Create a consistent progress message
            filename = (
                os.path.basename(self._loading_state["current_file"])
                if self._loading_state["current_file"]
                else "files"
            )

            # Standardized progress message format: "File X of Y - Z rows processed"
            if self._loading_state["total_files"] > 0:
                # Format file information
                # Always use total_files directly, not current_file_index
                total_files = self._loading_state["total_files"]
                current_file_index = self._loading_state["current_file_index"]

                file_info = f"File {current_file_index} of {total_files}"

                # Add filename
                file_info += f": {filename}"

                # Format rows with commas for readability
                if total > 0:
                    current_formatted = f"{current:,}"
                    total_formatted = f"{total:,}"
                    row_info = f"{current_formatted} of {total_formatted} rows"

                    # Create combined message with standardized format
                    message = f"{file_info} - {row_info}"

                    # Add total rows information as status text
                    if hasattr(self, "_total_rows_loaded") and self._total_rows_estimated > 0:
                        total_progress = f"Total: {self._total_rows_loaded:,} of ~{self._total_rows_estimated:,} rows"
                        self._progress_dialog.setStatusText(total_progress)
                    else:
                        self._progress_dialog.setStatusText("")
                else:
                    # If we don't have row information yet
                    message = file_info
                    self._progress_dialog.setStatusText("")
            else:
                # Fallback if we don't have file count yet
                message = f"Loading {filename}..."
                if total > 0:
                    message += f" ({current:,}/{total:,} rows)"

            # Update the dialog
            self._progress_dialog.setLabelText(message)
            self._progress_dialog.setValue(percentage)

            # Only make visibility adjustments if the dialog is not already visible
            # This prevents unnecessary UI updates that can make it appear like a new window
            if not self._progress_dialog.isVisible():
                self._progress_dialog.show()
                self._progress_dialog.raise_()
                self._progress_dialog.activateWindow()

            # Process events to ensure UI updates, but limit this to avoid excessive refreshing
            # Only process events if the percentage changes significantly
            if percentage % 5 == 0 or percentage >= 100:
                QApplication.processEvents()

        except Exception as e:
            # Add error handling to prevent crashes
            logger.error(f"Error updating progress dialog: {e}")
            # Don't crash the application if there's an error updating the progress

    def _on_load_error(self, message: str) -> None:
        """
        Handle errors during the loading process.

        Args:
            message: Error message
        """
        logger.error(f"Load error: {message}")

        # Update the status bar
        self._status_bar.set_status(f"Error: {message}")

        # If the progress dialog exists, update it to show the error
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                # Set error state
                self._progress_dialog.setState(ProgressBar.State.ERROR)

                # Update labels
                self._progress_dialog.setLabelText("Loading failed")
                self._progress_dialog.setStatusText(f"Error: {message}")

                # Change button to Close
                self._progress_dialog.setCancelButtonText("Close")

                # Disconnect previous signal connections
                try:
                    self._progress_dialog.canceled.disconnect()
                except:
                    pass

                # Connect cancel button to close the dialog
                self._progress_dialog.canceled.connect(self._progress_dialog.close)

                # Make sure dialog is visible
                if not self._progress_dialog.isVisible():
                    self._progress_dialog.show()
                    self._progress_dialog.raise_()
                    self._progress_dialog.activateWindow()

                # Process events to update the UI
                QApplication.processEvents()

                logger.debug("Progress dialog updated to show error")
            except Exception as e:
                logger.error(f"Error updating progress dialog for error state: {e}")

        # Reset loading state
        self._loading_state = {
            "total_files": 0,
            "current_file_index": 0,
            "current_file": "",
            "processed_files": [],
            "total_rows": 0,
        }

    # ===== Actions =====

    def _open_file(self) -> None:
        """Open one or more CSV files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open CSV Files", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_paths:
            try:
                for file_path in file_paths:
                    self._add_recent_file(file_path)
                    self.file_opened.emit(file_path)

                # Emit signal with all selected files
                self.load_csv_triggered.emit(file_paths)
                self._status_bar.set_status(f"Loaded: {len(file_paths)} files")
            except Exception as e:
                logger.error(f"Error opening files: {e}")
                QMessageBox.critical(self, "Error", f"Error opening files: {str(e)}")

    def _open_recent_file(self, file_path: str) -> None:
        """
        Open a recent file.

        Args:
            file_path: The path of the file to open.
        """
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file {file_path} does not exist.")
            # Remove from recent files
            if file_path in self._recent_files:
                self._recent_files.remove(file_path)
                self._update_recent_files_menu()
                self._save_recent_files()
            return

        try:
            # Add to recent files (will move to top of list)
            self._add_recent_file(file_path)

            # Emit signals
            self.file_opened.emit(file_path)
            self.load_csv_triggered.emit([file_path])

            # Update status
            self._status_bar.set_status(f"Loaded: {os.path.basename(file_path)}")

            # Update last modified timestamp
            modified_time = os.path.getmtime(file_path)
            self._status_bar.set_last_modified(modified_time)
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            QMessageBox.critical(self, "Error", f"Error opening file: {str(e)}")

    def _save_file(self) -> None:
        """Save the current file."""
        if self._data_model.is_empty:
            return

        file_path = self._data_model.file_path
        if not file_path:
            self._save_file_as()
            return

        try:
            self._csv_service.write_csv(file_path, self._data_model.data)
            self.file_saved.emit(file_path)
            self.save_csv_triggered.emit(file_path)
            self._status_bar.set_status(f"Saved: {os.path.basename(file_path)}")

            # Update last modified timestamp
            modified_time = os.path.getmtime(file_path)
            self._status_bar.set_last_modified(modified_time)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

    def _save_file_as(self) -> None:
        """Save the file with a new name."""
        if self._data_model.is_empty:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                self._csv_service.write_csv(file_path, self._data_model.data)
                self._add_recent_file(file_path)
                self.file_saved.emit(file_path)
                self._status_bar.set_status(f"Saved: {os.path.basename(file_path)}")

                # Update last modified timestamp
                modified_time = os.path.getmtime(file_path)
                self._status_bar.set_last_modified(modified_time)
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

    def _validate_data(self) -> None:
        """Validate the data."""
        if self._data_model.is_empty:
            return

        self.validation_requested.emit()
        self.validate_data_triggered.emit()
        self._set_active_view("Validation")

    def _correct_data(self) -> None:
        """Apply corrections to the data."""
        if self._data_model.is_empty:
            return

        self.correction_requested.emit()
        self.apply_corrections_triggered.emit()
        self._set_active_view("Correction")

    def _show_about(self) -> None:
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About ChestBuddy",
            """
            <h1>ChestBuddy</h1>
            <p>A data analysis tool for chest data.</p>
            <p>Version 1.0</p>
            <p>&copy; 2023 ChestBuddy Team</p>
            """,
        )

    def _export_validation_issues(self) -> None:
        """Export validation issues to a file."""
        if self._data_model.is_empty or not self._validation_service.has_validation_results():
            QMessageBox.warning(
                self, "No validation results", "There are no validation results to export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Validation Issues", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                # Get the issues from the validation service
                issues = self._validation_service.get_validation_results()
                if hasattr(issues, "to_csv"):
                    issues.to_csv(file_path, index=False)
                    self._status_bar.set_status(
                        f"Exported validation issues to {os.path.basename(file_path)}"
                    )
                    self.export_validation_issues_triggered.emit(file_path)
                else:
                    QMessageBox.warning(
                        self,
                        "Export Failed",
                        "The validation results are not in a format that can be exported.",
                    )
            except Exception as e:
                logger.error(f"Error exporting validation issues: {e}")
                QMessageBox.critical(self, "Error", f"Error exporting validation issues: {str(e)}")

    # ===== Events =====

    def closeEvent(self, event: Any) -> None:
        """
        Handle the window close event.

        Args:
            event: The close event.
        """
        # Cancel any ongoing data loading operations
        if hasattr(self, "_data_manager") and self._data_manager:
            try:
                logger.info("Cancelling any ongoing operations before closing")
                self._data_manager.cancel_loading()
            except Exception as e:
                logger.error(f"Error cancelling operations during shutdown: {e}")

        # Close progress dialog if it exists
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                self._progress_dialog.close()
            except Exception as e:
                logger.error(f"Error closing progress dialog during shutdown: {e}")

        # Save settings
        self._save_settings()
        self._save_recent_files()

        # Accept the event
        event.accept()

    def refresh_ui(self) -> None:
        """Refresh all UI components."""
        try:
            # Refresh the current tab if it exists
            if hasattr(self, "_content_stack") and self._content_stack is not None:
                current_index = self._content_stack.currentIndex()
                current_widget = self._content_stack.widget(current_index)

                # Call refresh or update method if available
                if hasattr(current_widget, "refresh"):
                    current_widget.refresh()
                elif hasattr(current_widget, "_update_view"):
                    current_widget._update_view()

            # Update other UI elements as needed (status bar, etc.)
            if hasattr(self, "_status_bar") and self._status_bar is not None:
                self._update_status_bar()
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error refreshing UI: {e}")

    def _update_status_bar(self) -> None:
        """Update the status bar with current information."""
        try:
            if (
                hasattr(self, "_status_bar")
                and self._status_bar is not None
                and hasattr(self, "_data_model")
            ):
                # Show row count in status bar
                row_count = (
                    self._data_model.row_count if hasattr(self._data_model, "row_count") else 0
                )
                self._status_bar.showMessage(f"Rows: {row_count}")
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error updating status bar: {e}")

    def _cancel_loading(self) -> None:
        """
        Cancel the current loading operation.

        This method is only connected to the progress dialog during active loading,
        not after loading is complete (when the button becomes "Confirm").
        """
        # Tell the data manager to cancel the operation
        if self._data_manager:
            self._data_manager.cancel_loading()
