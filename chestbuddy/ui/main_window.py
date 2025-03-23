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
            "phase": "loading",  # Track current phase (loading or processing)
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
        # Connect navigation signals
        self._sidebar.navigation_changed.connect(self._on_navigation_changed)

        # Connect dashboard signals
        self._dashboard_view.action_triggered.connect(self._on_dashboard_action)

        # Connect data manager signals if available
        if self._data_manager:
            self._data_manager.load_started.connect(self._on_load_started)
            self._data_manager.load_finished.connect(self._on_load_finished)
            self._data_manager.load_error.connect(self._on_load_error)
            self._data_manager.load_success.connect(self._on_data_load_success)
            # Connect to new chunk processing signals
            self._data_manager.chunk_processing_started.connect(self._on_chunk_processing_started)
            self._data_manager.chunk_processed.connect(self._on_chunk_processed)

        # Connect model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        if hasattr(self._data_model, "validation_changed"):
            self._data_model.validation_changed.connect(self._on_validation_changed)
        if hasattr(self._data_model, "correction_applied"):
            self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect other signals as needed

    def _on_load_started(self) -> None:
        """Handle the start of a loading operation."""
        logger.debug("Load operation started")

        # Initialize loading state
        self._loading_state = {
            "current_file": "",
            "current_file_index": 0,
            "processed_files": [],
            "total_files": 0,
            "total_rows": 0,
            "phase": "loading",  # Track current phase (loading or processing)
        }

        # Reset row counter
        self._total_rows_loaded = 0
        self._last_progress_current = 0

        # Show progress dialog if not already visible
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            # Use existing dialog
            self._progress_dialog.setLabelText("Preparing to load data...")
            self._progress_dialog.setValue(0)
            self._progress_dialog.setStatusText("")
            self._progress_dialog.setCancelButtonText("Cancel")
            self._progress_dialog.reset()

        else:
            # Create a new progress dialog with our custom implementation
            self._progress_dialog = ProgressDialog(
                "Preparing to load data...", "Cancel", 0, 100, self
            )
            self._progress_dialog.setWindowTitle("CSV Import - ChestBuddy")

            # Connect cancel button
            self._progress_dialog.canceled.connect(self._cancel_loading)

        # Make sure dialog is visible and activated
        self._progress_dialog.show()
        self._progress_dialog.raise_()
        self._progress_dialog.activateWindow()

        # Process events to ensure UI updates
        QApplication.processEvents()

    def _on_chunk_processing_started(self) -> None:
        """Handle the start of the chunk processing phase."""
        logger.debug("Chunk processing phase started")

        # Update loading state
        self._loading_state["phase"] = "processing"

        # Update progress dialog
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.setLabelText("Processing data chunks...")
            self._progress_dialog.setValue(50)  # Loading phase is 50% complete
            self._progress_dialog.setStatusText("Populating table...")

            # Process events to ensure UI updates
            QApplication.processEvents()

    def _on_chunk_processed(self, current_chunk: int, total_chunks: int) -> None:
        """
        Handle progress updates during chunk processing.

        Args:
            current_chunk: Current chunk being processed
            total_chunks: Total number of chunks to process
        """
        # Ensure progress dialog exists
        if not hasattr(self, "_progress_dialog") or not self._progress_dialog:
            return

        try:
            # Calculate progress percentage for processing phase (50-100%)
            percentage = 50 + min(50, int((current_chunk * 50) / total_chunks))

            # Update the dialog
            self._progress_dialog.setLabelText(
                f"Processing data ({current_chunk}/{total_chunks} chunks)..."
            )
            self._progress_dialog.setValue(percentage)
            self._progress_dialog.setStatusText(
                f"Populating table with {self._total_rows_loaded:,} rows..."
            )

            # Only make visibility adjustments if the dialog is not already visible
            if not self._progress_dialog.isVisible():
                self._progress_dialog.show()
                self._progress_dialog.raise_()
                self._progress_dialog.activateWindow()

            # Process events to ensure UI updates, but limit this to avoid excessive refreshing
            QApplication.processEvents()

        except Exception as e:
            # Add error handling to prevent crashes
            logger.error(f"Error updating progress dialog during chunk processing: {e}")

    def _on_load_progress(self, file_path: str, current: int, total: int) -> None:
        """
        Handle progress updates during loading phase.

        Args:
            file_path: Path of the file being processed (empty for overall progress)
            current: Current progress value
            total: Total progress value
        """
        # Ensure progress dialog exists
        if not hasattr(self, "_progress_dialog") or not self._progress_dialog:
            return

        try:
            # Only process file loading updates during the loading phase
            if self._loading_state["phase"] != "loading":
                return

            # Update loading state based on signal type
            if file_path:
                # This is a file-specific progress update
                # If this is a new file, update the file index
                if file_path != self._loading_state["current_file"]:
                    # If we're moving to a new file, record the size of the completed file
                    if self._loading_state["current_file"]:
                        # Keep track of completed files
                        processed_files = self._loading_state["processed_files"]
                        if self._loading_state["current_file"] not in processed_files:
                            processed_files.append(self._loading_state["current_file"])

                    # Add new file to processed files if needed
                    if file_path not in self._loading_state["processed_files"]:
                        self._loading_state["current_file_index"] += 1
                        if file_path not in self._loading_state["processed_files"]:
                            self._loading_state["processed_files"].append(file_path)
                        self._loading_state["total_files"] = max(
                            self._loading_state["current_file_index"],
                            self._loading_state["total_files"],
                            len(self._loading_state["processed_files"]),
                        )
                    self._loading_state["current_file"] = file_path

                # Update total rows for current file
                self._loading_state["total_rows"] = max(total, self._loading_state["total_rows"])

                # Track rows across all files
                if not hasattr(self, "_total_rows_loaded"):
                    self._total_rows_loaded = 0
                    self._last_progress_current = 0

                # Increment total rows loaded by the increase since last update
                if hasattr(self, "_last_progress_current"):
                    # Only increment if current is greater than last value (to avoid counting backwards)
                    if current > self._last_progress_current:
                        self._total_rows_loaded += current - self._last_progress_current
                    self._last_progress_current = current
                else:
                    self._last_progress_current = current

            # Calculate progress percentage for loading phase (0-50%)
            file_percentage = min(100, int((current * 100 / total) if total > 0 else 0))
            loading_percentage = min(50, int(file_percentage / 2))  # Scale to 0-50% range

            # Create a simple progress message with actual counts, no estimates
            filename = (
                os.path.basename(self._loading_state["current_file"])
                if self._loading_state["current_file"]
                else ""
            )

            # Build a descriptive progress message
            if self._loading_state["total_files"] > 0:
                # Simple file count information
                file_info = f"{self._loading_state['current_file_index']} / {self._loading_state['total_files']} files"

                # Include row count information, showing only actual processed rows
                if hasattr(self, "_total_rows_loaded") and self._total_rows_loaded > 0:
                    # Format with commas for readability
                    message = f"Loading file: {filename}"
                    self._progress_dialog.setStatusText(
                        f"{file_info} - {self._total_rows_loaded:,} rows processed"
                    )
                else:
                    message = f"Loading file: {filename}"
                    self._progress_dialog.setStatusText(file_info)
            else:
                # Fallback if we don't have file count yet
                message = f"Loading {filename}..."
                self._progress_dialog.setStatusText("")

            # Update the dialog
            self._progress_dialog.setLabelText(message)
            self._progress_dialog.setValue(loading_percentage)

            # Only make visibility adjustments if the dialog is not already visible
            if not self._progress_dialog.isVisible():
                self._progress_dialog.show()
                self._progress_dialog.raise_()
                self._progress_dialog.activateWindow()

            # Process events to ensure UI updates, but limit this to avoid excessive refreshing
            # Only process events if the percentage changes significantly
            if loading_percentage % 5 == 0 or loading_percentage >= 50:
                QApplication.processEvents()

        except Exception as e:
            # Add error handling to prevent crashes
            logger.error(f"Error updating progress dialog: {e}")
            # Don't crash the application if there's an error updating the progress

    def _on_load_finished(self, message: str = None) -> None:
        """
        Handle the completion of a loading operation.

        Args:
            message: Optional message to display
        """
        logger.debug("MainWindow._on_load_finished called")

        # If the progress dialog exists
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                # Check if this is a processing message (intermediate step)
                if message and "Processing" in message:
                    self._progress_dialog.setLabelText(message)
                    self._progress_dialog.setValue(100)
                    self._progress_dialog.setCancelButtonText("Please wait...")
                    self._progress_dialog.setStatusText("Processing data...")

                    # Process events to update the UI
                    QApplication.processEvents()
                    return  # Don't complete the dialog yet

                # Set the label to indicate completion
                completion_message = "Loading complete"

                # Extract actual row count from the message if present
                actual_row_count = None
                if message and "loaded" in message:
                    try:
                        # Try to extract the row count from messages like "Successfully loaded 12345 rows of data"
                        parts = message.split("loaded")[1].split("rows")[0].strip()
                        actual_row_count = int(parts.replace(",", ""))
                    except (IndexError, ValueError):
                        # Fall back to the tracked count if parsing fails
                        actual_row_count = None

                if actual_row_count is None and hasattr(self, "_total_rows_loaded"):
                    actual_row_count = self._total_rows_loaded
                elif actual_row_count is None:
                    actual_row_count = self._loading_state["total_rows"]

                # Display final message with total files and rows
                total_files = self._loading_state["total_files"]
                final_status = f"{total_files} file{'s' if total_files != 1 else ''} - {actual_row_count:,} rows processed"

                # Ensure progress dialog is updated with completion status
                self._progress_dialog.setLabelText(completion_message)
                self._progress_dialog.setValue(100)  # Ensure 100% progress is shown

                # Set success state for the progress bar
                self._progress_dialog.setState(ProgressBar.State.SUCCESS)

                # Set status with final message
                self._progress_dialog.setStatusText(final_status)

                # Update the cancel button to "Close" or "Confirm"
                self._progress_dialog.setCancelButtonText("Confirm")

                # Disconnect previous cancel signal connections
                try:
                    self._progress_dialog.canceled.disconnect()
                except:
                    pass  # It's OK if it wasn't connected

                # Connect cancel button to close the dialog
                self._progress_dialog.canceled.connect(self._progress_dialog.close)

                # Make sure dialog is visible without excessive UI updates
                if not self._progress_dialog.isVisible():
                    self._progress_dialog.show()
                    self._progress_dialog.raise_()
                    self._progress_dialog.activateWindow()

                # Process events to update the UI
                QApplication.processEvents()

                logger.debug("Progress dialog updated for completion")
            except Exception as e:
                logger.error(f"Error updating progress dialog on completion: {e}")

            # Reset loading state
            self._loading_state = {
                "total_files": 0,
                "current_file_index": 0,
                "current_file": "",
                "processed_files": [],
                "total_rows": 0,
            }
        else:
            logger.warning("No progress dialog found in _on_load_finished")

    def _cancel_loading(self) -> None:
        """
        Cancel the current loading operation.

        This method is only connected to the progress dialog during active loading,
        not after loading is complete (when the button becomes "Confirm").
        """
        # Tell the data manager to cancel the operation
        if self._data_manager:
            self._data_manager.cancel_loading()

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
