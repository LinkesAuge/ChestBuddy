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

import pandas as pd

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

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.resources.style import Colors, apply_application_style
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
from chestbuddy.ui.views.dashboard_view_adapter import DashboardViewAdapter
from chestbuddy.ui.widgets import ProgressDialog, ProgressBar
from chestbuddy.ui.widgets.blockable_progress_dialog import BlockableProgressDialog
from chestbuddy.ui.views.blockable import BlockableDataView
from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.ui_state import (
    UIStateManager,
    BlockableElementMixin,
    OperationContext,
    UIOperations,
    UIElementGroups,
)
from chestbuddy.debugging import measure_time, StateSnapshot, install_debug_hooks

# Set up logger
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, BlockableElementMixin):
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
        import_complete: Signal emitted when an import operation is completed
        validation_complete: Signal emitted when a validation operation is completed
        correction_complete: Signal emitted when a correction operation is completed
        export_complete: Signal emitted when an export operation is completed

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
        - Integrates with the UI State Management system for blocking UI during operations
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
    import_complete = Signal(object)  # ChestDataModel
    validation_complete = Signal(object)  # ValidationResult
    correction_complete = Signal(object)  # CorrectionResult
    export_complete = Signal(bool)  # Success flag

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
        Initialize the main window.

        Args:
            data_model: The data model for the application.
            csv_service: Service for CSV operations.
            validation_service: Service for data validation.
            correction_service: Service for data correction.
            chart_service: Service for chart generation.
            data_manager: Optional data manager instance.
            parent: Optional parent widget.
        """
        # Initialize QMainWindow
        QMainWindow.__init__(self, parent)

        # Initialize BlockableElementMixin
        BlockableElementMixin.__init__(self)

        # Store services
        self.data_model = data_model
        self.csv_service = csv_service
        self.validation_service = validation_service
        self.correction_service = correction_service
        self.chart_service = chart_service
        self._data_manager = data_manager

        # Store views
        self._views: Dict[str, BaseView] = {}
        self._active_view = None

        # UI State Manager
        self._ui_state_manager = UIStateManager()

        # Operation context for tracking current operations
        self._import_operation_context = None

        # State flags
        self._loading_state = {}
        self._progress_dialog = None
        self._progress_dialog_finalized = False
        self._file_loading_complete = False
        self._data_loaded = False
        self._total_rows_loaded = 0
        self._total_rows_estimated = 0
        self._last_progress_current = 0

        # Set up debugging hooks if needed
        if os.environ.get("DEBUG_UI_STATE", "0") == "1":
            install_debug_hooks()

        # Recent files list
        self._recent_files = []
        self._max_recent_files = 10

        # Set up UI
        self._init_ui()
        self._create_views()
        self._init_menus()
        self._add_file_toolbar()
        self._connect_signals()
        self._load_settings()
        self._load_recent_files()
        apply_application_style(QApplication.instance())

        # Register with the UI state manager
        self.register_with_manager(self._ui_state_manager)

        # Add to appropriate groups
        self._ui_state_manager.add_element_to_group(self, UIElementGroups.MAIN_WINDOW)

        logger.debug("MainWindow initialized")

    def _apply_block(self, operation: Any = None) -> None:
        """Apply block to the main window and all its children."""
        logger.debug(f"MainWindow: Applying block for operation {operation}")
        # Original enabled state is saved by the mixin

        # We'll disable the main UI components but not the whole window
        # to allow dialog interaction
        if hasattr(self, "_sidebar") and self._sidebar:
            self._sidebar.setEnabled(False)

        if hasattr(self, "_content_stack") and self._content_stack:
            self._content_stack.setEnabled(False)

        if hasattr(self, "menuBar") and self.menuBar():
            self.menuBar().setEnabled(False)

    def _apply_unblock(self, operation: Any = None) -> None:
        """Restore original enabled state when unblocking."""
        logger.debug(f"MainWindow: Applying unblock for operation {operation}")

        # Re-enable main components
        if hasattr(self, "_sidebar") and self._sidebar:
            self._sidebar.setEnabled(True)

        if hasattr(self, "_content_stack") and self._content_stack:
            self._content_stack.setEnabled(True)

        if hasattr(self, "menuBar") and self.menuBar():
            self.menuBar().setEnabled(True)

        # Process events to ensure UI updates
        QApplication.processEvents()

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

        # Add file toolbar
        self._add_file_toolbar()

        # Set initial view to Dashboard
        self._set_active_view("Dashboard")

        # Initialize navigation based on data state
        self._update_navigation_based_on_data_state()

    def _create_views(self) -> None:
        """Create the views for the application."""
        # Dictionary to store views
        self._views: Dict[str, BaseView] = {}

        # Create Dashboard view
        dashboard_view = DashboardViewAdapter(self.data_model)
        dashboard_view.action_triggered.connect(self._on_dashboard_action)
        dashboard_view.file_selected.connect(self._on_recent_file_selected)
        dashboard_view.chart_selected.connect(self._on_chart_selected)
        dashboard_view.data_requested.connect(self._open_file)
        self._content_stack.addWidget(dashboard_view)
        self._views["Dashboard"] = dashboard_view

        # Create Data view
        data_view = DataViewAdapter(self.data_model)
        data_view.data_requested.connect(self._open_file)
        self._content_stack.addWidget(data_view)
        self._views["Data"] = data_view

        # Create Validation view
        validation_view = ValidationViewAdapter(self.data_model, self.validation_service)
        validation_view.data_requested.connect(self._open_file)
        self._content_stack.addWidget(validation_view)
        self._views["Validation"] = validation_view

        # Create Correction view
        correction_view = CorrectionViewAdapter(self.data_model, self.correction_service)
        correction_view.data_requested.connect(self._open_file)
        self._content_stack.addWidget(correction_view)
        self._views["Correction"] = correction_view

        # Create Analysis/Charts view
        chart_view = ChartViewAdapter(self.data_model, self.chart_service)
        chart_view.data_requested.connect(self._open_file)
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
        self.data_model.data_changed.connect(self._on_data_changed)
        self.data_model.validation_changed.connect(self._on_validation_changed)
        self.data_model.correction_applied.connect(self._on_correction_applied)

        # Connect data model signals
        self.data_model.data_changed.connect(self._on_data_changed)
        self.data_model.validation_changed.connect(self._on_validation_changed)
        self.data_model.correction_applied.connect(self._on_correction_applied)

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
        config = ConfigManager()

        # Load window geometry
        self.resize(
            config.get_int("UI", "window_width", 1024), config.get_int("UI", "window_height", 768)
        )

        # Load other settings as needed
        logger.debug("Application settings loaded")

    def _save_settings(self) -> None:
        """Save application settings."""
        config = ConfigManager()

        # Save window geometry
        config.set("UI", "window_width", self.width())
        config.set("UI", "window_height", self.height())

        # Save other settings as needed
        logger.debug("Application settings saved")

    def _load_recent_files(self) -> None:
        """Load recent files from settings."""
        config = ConfigManager()
        self._recent_files = [str(p) for p in config.get_recent_files()]
        self._update_recent_files_menu()
        logger.debug(f"Loaded {len(self._recent_files)} recent files")

    def _save_recent_files(self) -> None:
        """Save recent files to settings."""
        # Using ConfigManager to save recent files
        # (This is handled automatically by add_recent_file)
        logger.debug(f"Saved {len(self._recent_files)} recent files")

    def _add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the file to add.
        """
        # Convert to absolute path if not already
        file_path = os.path.abspath(file_path)

        # Remove if already in list
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)

        # Add to start of list
        self._recent_files.insert(0, file_path)

        # Keep only the most recent 10 files
        self._recent_files = self._recent_files[:10]

        # Update the menu
        self._update_recent_files_menu()

        # Save to config
        config = ConfigManager()
        config.add_recent_file(file_path)

        logger.debug(f"Added {file_path} to recent files")

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
        """Update UI state based on data availability."""
        logger.debug(f"Updating UI elements based on data state: data_loaded={self._data_loaded}")

        # Update export action
        if hasattr(self, "_export_action"):
            self._export_action.setEnabled(self._data_loaded)
            logger.debug(f"Export action enabled: {self._data_loaded}")

        # Update menu actions that depend on data availability
        if hasattr(self, "_save_action"):
            self._save_action.setEnabled(self._data_loaded)

        if hasattr(self, "_save_as_action"):
            self._save_as_action.setEnabled(self._data_loaded)

        if hasattr(self, "_validate_action"):
            self._validate_action.setEnabled(self._data_loaded)

        if hasattr(self, "_correct_action"):
            self._correct_action.setEnabled(self._data_loaded)

        if hasattr(self, "_export_validation_action"):
            self._export_validation_action.setEnabled(self._data_loaded)

        # Update status bar based on data state
        self._update_status_bar()

        # Update all views with data availability
        self._update_views_data_availability()

        # Update navigation based on data state
        self._update_navigation_based_on_data_state()

        # Process events to ensure UI updates are applied immediately
        QApplication.processEvents()

    @Slot(str)
    def _set_active_view(self, view_name: str) -> None:
        """
        Set the active view.

        Args:
            view_name: The name of the view to set active
        """
        logger.debug(f"[VIEW_TRANSITION] Setting active view to '{view_name}'")

        # Log current application state
        current_view = self._content_stack.currentWidget()
        current_view_name = "unknown"
        for name, view in self._views.items():
            if view is current_view:
                current_view_name = name
                break

        logger.debug(f"[VIEW_TRANSITION] Current view before transition: '{current_view_name}'")
        logger.debug(f"[VIEW_TRANSITION] Data loaded state: {self._data_loaded}")

        # Check if view exists
        if view_name not in self._views:
            logger.error(f"[VIEW_TRANSITION] View '{view_name}' does not exist!")
            return

        # Check if the view requires data
        view = self._views[view_name]
        requires_data = view.is_data_required()
        logger.debug(f"[VIEW_TRANSITION] View '{view_name}' requires data: {requires_data}")

        # If the view requires data but no data is loaded, switch to Dashboard view
        if requires_data and not self._data_loaded:
            logger.debug(
                f"[VIEW_TRANSITION] Cannot switch to '{view_name}', no data loaded. Redirecting to Dashboard."
            )
            self._content_stack.setCurrentWidget(self._views["Dashboard"])
            self._sidebar.set_active_item("Dashboard")
            return

        # Switch to the view and update the sidebar selection
        logger.debug(f"[VIEW_TRANSITION] Switching to view '{view_name}'")
        before_visible = view.isVisible()
        self._content_stack.setCurrentWidget(view)
        after_visible = view.isVisible()

        logger.debug(
            f"[VIEW_TRANSITION] View visibility changed: {before_visible} -> {after_visible}"
        )
        self._sidebar.set_active_item(view_name)

        # Log completion
        logger.debug(f"[VIEW_TRANSITION] Active view set to '{view_name}'")

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

        # If trying to navigate to a disabled section, return
        if not self._sidebar.is_section_enabled(section):
            logger.debug(f"Navigation to disabled section {section} prevented")
            # Restore previous selection
            if hasattr(self, "_previous_active_section"):
                self._sidebar.set_active_item(
                    self._previous_active_section.get("section", "Dashboard"),
                    self._previous_active_section.get("subsection", ""),
                )
            return

        # Store current selection for potential restoration
        self._previous_active_section = {"section": section, "subsection": subsection}

        if subsection:
            # Handle subsections
            if section == "Data":
                if subsection == "Validate":
                    self._set_active_view("Validation")
                elif subsection == "Correct":
                    self._set_active_view("Correction")
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
        """Handle data change event."""
        # Update UI elements
        self._update_ui()

        # Update table population progress
        self._update_table_population_progress()

        # Update dashboard
        dashboard_view = self._views.get("Dashboard")
        if dashboard_view and isinstance(dashboard_view, DashboardViewAdapter):
            dashboard_view.on_data_updated()

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

    @Slot(int, int, str)
    def _on_load_started(self, current: int, total: int, text: str) -> None:
        """
        Handle load started signal from data manager.

        Args:
            current: Current file index being processed
            total: Total number of files to process
            text: Status text to display
        """
        logger.info(f"Loading started - {current}/{total}: {text}")

        # Initialize loading state
        self._loading_state = {
            "current_file": "",  # Current file being processed
            "current_file_index": 0,  # Current file index (1-based)
            "total_files": total,  # Total number of files
            "processed_files": [],  # List of processed files
            "total_rows": 0,  # Total rows in current file
        }

        # Initialize file processing metrics
        self._total_rows_loaded = 0
        self._total_rows_estimated = 0
        self._last_progress_current = 0
        self._file_sizes = {}

        # Check if import operation is active
        import_active = False
        try:
            import_active = self._ui_state_manager.is_operation_active(UIOperations.IMPORT)
        except Exception as e:
            logger.error(f"Error checking if import operation is active: {e}")

        if import_active:
            # Try to reuse existing progress dialog
            try:
                if self._progress_dialog is None:
                    logger.warning("Import operation is active but progress dialog is None")
                else:
                    logger.debug("Import operation is active, reusing existing progress dialog")
                    return
            except Exception as e:
                logger.error(f"Error reusing progress dialog: {e}")

        # Close any existing progress dialog
        self._close_progress_dialog()

        # Create and show new progress dialog
        try:
            self._progress_dialog = BlockableProgressDialog(
                "Importing Data", "Cancel", 0, 100, self
            )

            # Connect cancel action
            self._progress_dialog.canceled.connect(self._cancel_loading)

            # Show the dialog with blocking operation
            try:
                # Use show_with_blocking instead of separate show() and start_operation()
                self._progress_dialog.show_with_blocking(
                    UIOperations.IMPORT, [UIElementGroups.DATA_VIEW]
                )
                logger.debug("Progress dialog shown with blocking operation")
            except Exception as e:
                logger.error(f"Error showing progress dialog with blocking: {e}")
                # Fallback to regular show if blocking fails
                self._progress_dialog.show()
        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            self._progress_dialog = None

    def _on_load_finished(self, success: bool, message: str = "") -> None:
        """
        Handle load finished signal.

        Args:
            success: Whether the loading was successful
            message: Additional message with details
        """
        logger.debug(f"Load finished, success={success}, message={message}")

        # Make sure we have a progress dialog to finalize
        if not self._progress_dialog:
            # If dialog doesn't exist, just update UI state without trying to show a dialog
            logger.warning("Missing progress dialog in _on_load_finished")
            try:
                # Update data state based on success
                self._data_loaded = success and self._check_data_available()
                self._update_navigation_based_on_data_state()
                self._update_ui()

                # End any active import operation if it exists
                if self._ui_state_manager.is_operation_active(UIOperations.IMPORT):
                    logger.warning("Import operation active but no dialog - ending operation")
                    self._ui_state_manager.end_operation(UIOperations.IMPORT)
                return
            except Exception as e:
                logger.error(f"Error handling missing dialog case: {e}")
                return

        try:
            # Disable further updates - this should be final state
            self._progress_dialog_finalized = True

            if success:
                self._finalize_loading(message, None)
            else:
                self._finalize_loading(None, message)

            # Check if there are any active operations not properly ended by the dialog
            if self._ui_state_manager.is_operation_active(UIOperations.IMPORT):
                logger.warning("Import operation still active after load finished, forcing cleanup")
                self._ui_state_manager.end_operation(UIOperations.IMPORT)

            # Ensure UI state is updated based on new data state
            self._update_navigation_based_on_data_state()
            self._update_ui()

            # Ensure the progress dialog is properly closed after we've updated UI state
            self._close_progress_dialog()

        except Exception as e:
            logger.error(f"Error in _on_load_finished: {e}")

            # Define success explicitly to avoid UnboundLocalError
            if not "success" in locals():
                success = False

            # Try to finalize with error
            try:
                self._finalize_loading(None, f"Error: {str(e)}")
            except Exception as inner_e:
                logger.error(f"Second error in finalize_loading: {inner_e}")

                # Last resort - try to update state directly
                self._data_loaded = False
                self._update_navigation_based_on_data_state()
                self._update_ui()

            # Ensure dialog is closed even if there was an error
            if self._progress_dialog:
                try:
                    self._close_progress_dialog()
                except Exception as close_e:
                    logger.error(f"Error closing dialog after exception: {close_e}")

    def _check_data_available(self) -> bool:
        """Check if data is available in the data model.

        Returns:
            bool: True if data is available, False otherwise
        """
        try:
            if hasattr(self.data_model, "data") and self.data_model.data is not None:
                return len(self.data_model.data) > 0
            return False
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return False

    def _close_progress_dialog(self) -> None:
        """
        Close the progress dialog and clean up any active operations.
        Ensures the UI state is properly restored.
        """
        logger.debug("Closing progress dialog")

        # Check if import operation is still active
        import_active = self._ui_state_manager.is_operation_active(UIOperations.IMPORT)
        if import_active:
            logger.debug("Import operation is still active during dialog close")

        # Capture dialog reference before setting to None to avoid issues with callbacks
        dialog = self._progress_dialog
        self._progress_dialog = None

        if dialog is not None:
            try:
                # End any active operation associated with the dialog
                dialog._end_operation()
                dialog.close()
                logger.debug("Progress dialog closed successfully")
            except Exception as e:
                logger.error(f"Error closing progress dialog: {e}")
        elif import_active:
            # Dialog is None but operation is active - unusual case, try to clean up
            logger.warning("No progress dialog but import operation is active - ending operation")
            try:
                self._ui_state_manager.end_operation(UIOperations.IMPORT)
            except Exception as e:
                logger.error(f"Error ending orphaned import operation: {e}")

        # Add a final safety check to ensure the operation is ended even if dialog._end_operation failed
        if self._ui_state_manager.is_operation_active(UIOperations.IMPORT):
            logger.warning("Import operation still active after cleanup - forcing operation end")
            try:
                self._ui_state_manager.end_operation(UIOperations.IMPORT)
                logger.debug("Successfully ended lingering import operation")
            except Exception as e:
                logger.error(f"Error ending lingering import operation: {e}")

    def _perform_final_ui_check(self, delay_ms: int = 500) -> None:
        """
        Perform a final check of UI elements after import.

        Note: This method is deprecated and will be removed in future versions.
        UI blocking/unblocking is now handled by the UI State Management System.

        Args:
            delay_ms: The delay in milliseconds after which this check is running
        """
        logger.debug(
            f"Final UI check at {delay_ms}ms - deprecated, using UI State Management instead"
        )
        # This method is kept for backward compatibility but is no longer needed
        # as the UI State Management System now handles blocking and unblocking UI elements

    def _capture_snapshot(self, name: str) -> None:
        """
        Capture an application state snapshot.

        Args:
            name: Name for the snapshot
        """
        try:
            snapshot = StateSnapshot(name)
            snapshot.capture_application_state()
            self._snapshots[name] = snapshot
            logger.debug(f"[SNAPSHOT] Captured application state snapshot: {name}")
        except Exception as e:
            logger.error(f"[SNAPSHOT_ERROR] Failed to capture snapshot '{name}': {e}")

    def _finalize_loading(self, success_message: str, error_message: str = None) -> None:
        """
        Finalize the loading process after completion.

        Args:
            success_message: The success message to log
            error_message: The error message to log, if any
        """
        logger.debug("[LOAD_FINALIZE] Starting load finalization process")

        # Determine success based on presence of error message
        success = error_message is None

        # Always set the progress dialog to 100%
        if self._progress_dialog:
            self._progress_dialog.setValue(100)

            # Handle errors if there are any
            if error_message:
                logger.debug("[LOAD_ERROR] Setting progress dialog to error state")
                self._progress_dialog.setState(ProgressDialog.State.ERROR)
                self._progress_dialog.setStatusText(error_message)
                self._progress_dialog.setCancelButtonText("Close")
                logger.error(f"[LOAD_FAILED] Loading failed: {error_message}")
                success = False
            else:
                # Otherwise set success state
                logger.debug("[LOAD_SUCCESS] Setting progress dialog to success state")
                self._progress_dialog.setState(ProgressDialog.State.SUCCESS)
                self._progress_dialog.setStatusText(success_message)
                self._progress_dialog.setCancelButtonText("Confirm")
                self._progress_dialog.set_confirm_button_style()
                logger.info(f"[LOAD_COMPLETED] Loading successful: {success_message}")
                success = True

        # Safely check if there are rows in the data model
        has_data_rows = self._check_data_available()
        if has_data_rows:
            logger.debug(f"[DATA_STATE] Data model has rows")
        else:
            logger.warning("[DATA_STATE] Data model has no rows or data is not accessible")

        # Update data loaded flag based on success and data availability
        previous_data_loaded = self._data_loaded  # Store previous state for comparison
        self._data_loaded = success and has_data_rows
        logger.debug(
            f"[DATA_LOADED_STATE] Previous: {previous_data_loaded}, New: {self._data_loaded}"
        )

        # Ensure UI elements are updated based on new data state
        logger.debug("[UI_UPDATE] Triggering UI update based on new data state")
        self._update_ui()  # Update all UI elements based on data availability

        # Enable navigation based on data state
        logger.debug("[NAV_UPDATE] Updating navigation based on data state")
        self._update_navigation_based_on_data_state()

        # Force process events to ensure UI updates are applied
        QApplication.processEvents()

    def _on_populate_table_requested(self, data: pd.DataFrame) -> None:
        """
        Handle request to populate table during data loading.
        This synchronizes table population with file import.

        Args:
            data: The data to populate in the table
        """
        logger.debug(f"Received request to populate table with {len(data):,} rows")

        # Set file loading complete flag
        self._file_loading_complete = True

        # The actual table population occurs in the data model and views
        # No need to show progress dialog for this step anymore
        # Table population will happen automatically after this method returns

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

        # If dialog has been finalized, don't update it anymore
        if self._progress_dialog_finalized:
            logger.debug("Progress dialog already finalized, ignoring update")
            return

        try:
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

    def _on_load_error(self, error_message: str) -> None:
        """
        Handle load error signal.

        Args:
            error_message: The error message to display
        """
        logger.error(f"Load error: {error_message}")
        self._status_bar.set_error(error_message)

        # Show error in progress dialog if it exists
        if self._progress_dialog:
            self._progress_dialog.setState(ProgressDialog.State.ERROR)
            self._progress_dialog.setStatusText(error_message)
            self._progress_dialog.setCancelButtonText("Close")

    def _cancel_loading(self) -> None:
        """Cancel the current loading operation."""
        logger.debug("Canceling loading operation from MainWindow")

        # Cancel the data loading in the data manager
        if self._data_manager:
            try:
                logger.debug("Calling data_manager.cancel_loading()")
                self._data_manager.cancel_loading()
                logger.debug("data_manager.cancel_loading() called successfully")
            except Exception as e:
                logger.error(f"Error canceling loading in data manager: {e}")
        else:
            logger.warning("No data_manager available, can't cancel loading")

        # Close the progress dialog if it exists
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            try:
                logger.debug("Closing progress dialog on cancel")
                self._progress_dialog.hide()
                self._progress_dialog.reject()
                self._progress_dialog = None

                # Process events to ensure UI updates
                QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error closing progress dialog on cancel: {e}")

        # Clear state
        self._file_loading_complete = False

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
        if self.data_model.is_empty:
            return

        file_path = self.data_model.file_path
        if not file_path:
            self._save_file_as()
            return

        try:
            self.csv_service.write_csv(file_path, self.data_model.data)
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
        if self.data_model.is_empty:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                self.csv_service.write_csv(file_path, self.data_model.data)
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
        if self.data_model.is_empty:
            return

        self.validation_requested.emit()
        self.validate_data_triggered.emit()
        self._set_active_view("Validation")

    def _correct_data(self) -> None:
        """Apply corrections to the data."""
        if self.data_model.is_empty:
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
        if self.data_model.is_empty or not self.validation_service.has_validation_results():
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
                issues = self.validation_service.get_validation_results()
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
            # Skip UI refreshes that might affect the progress dialog if it's been finalized
            # but is still visible (waiting for user to close it)
            if (
                self._progress_dialog_finalized
                and hasattr(self, "_progress_dialog")
                and self._progress_dialog
            ):
                if self._progress_dialog.isVisible():
                    logger.debug("Skipping UI refresh while finalized progress dialog is visible")
                    return

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
        """Update the status bar based on the current data state."""
        logger.debug(f"Updating status bar, data_loaded={self._data_loaded}")

        try:
            if self._data_loaded and not self.data_model.is_empty:
                # Get row count
                row_count = len(self.data_model.data)
                self._status_bar.set_record_count(row_count)

                # Get the current file path
                current_file = (
                    self.data_model.file_path if hasattr(self.data_model, "file_path") else None
                )
                if current_file:
                    self._status_bar.set_status(f"Loaded: {os.path.basename(current_file)}")
                else:
                    self._status_bar.set_status("Data loaded (unsaved)")
            else:
                # Clear status bar when no data is loaded
                self._status_bar.clear_all()
                self._status_bar.set_status("No data loaded")
        except Exception as e:
            logger.error(f"Error updating status bar: {e}")
            # Fallback status
            self._status_bar.set_status("Status unknown")

    def _update_table_population_progress(self):
        """
        Placeholder for table population progress updates.
        This method exists for backward compatibility but no longer updates the UI.
        """
        # No UI updates for table population progress
        pass

    def _update_views_data_availability(self) -> None:
        """Update all views with the data availability state."""
        logger.debug(
            f"[DATA_AVAILABILITY] Updating views data availability. Data loaded: {self._data_loaded}"
        )

        # Log state of all views before update
        for view_name, view in self._views.items():
            requires_data = view.is_data_required()
            logger.debug(
                f"[DATA_AVAILABILITY] Before update: View '{view_name}' requires data: {requires_data}"
            )

        # Update each view
        for view_name, view in self._views.items():
            logger.debug(f"[DATA_AVAILABILITY] Updating view '{view_name}'")
            view.set_data_available(self._data_loaded)

        logger.debug("[DATA_AVAILABILITY] Views data availability updated")

    def _update_navigation_based_on_data_state(self) -> None:
        """Update navigation items based on the data loaded state."""
        logger.debug(f"Updating navigation based on data state: data_loaded={self._data_loaded}")

        # Dashboard is always accessible
        self._sidebar.set_section_enabled("Dashboard", True)

        # These sections require data to be loaded
        data_dependent_sections = ["Data", "Analysis", "Reports"]
        for section in data_dependent_sections:
            self._sidebar.set_section_enabled(section, self._data_loaded)

        # Settings and Help are always accessible
        self._sidebar.set_section_enabled("Settings", True)
        self._sidebar.set_section_enabled("Help", True)

        # If no data is loaded and current view requires data, switch to Dashboard
        current_view = None
        for view_name, view in self._views.items():
            if self._content_stack.currentWidget() == view:
                current_view = view_name
                break

        if not self._data_loaded and current_view in ["Data", "Validation", "Correction", "Charts"]:
            logger.debug(f"No data loaded, switching from {current_view} to Dashboard")
            self._set_active_view("Dashboard")
            self._sidebar.set_active_item("Dashboard")

        # Update the data availability state for all views
        self._update_views_data_availability()

    def _add_file_toolbar(self) -> None:
        """Create a toolbar for file operations."""
        file_toolbar = self.addToolBar("File")
        file_toolbar.setObjectName("file_toolbar")

        # Import action
        import_action = QAction(Icons.get_icon(Icons.IMPORT), "Import Data", self)
        import_action.setStatusTip("Import data from CSV files")
        import_action.triggered.connect(self._open_file)
        file_toolbar.addAction(import_action)

        # Export action
        export_action = QAction(Icons.get_icon(Icons.EXPORT), "Export Data", self)
        export_action.setStatusTip("Export data to CSV file")
        export_action.triggered.connect(self._save_file_as)
        export_action.setEnabled(False)  # Disabled until data is loaded
        self._export_action = export_action  # Store reference for enabling/disabling
        file_toolbar.addAction(export_action)

    def _clear_data(self) -> None:
        """Clear the current dataset."""
        # Update flag
        self._data_loaded = False

        # Update views
        self._update_views_data_availability()

        # Update navigation
        self._update_navigation_based_on_data_state()

        # Update dashboard
        dashboard_view = self._views.get("Dashboard")
        if dashboard_view and isinstance(dashboard_view, DashboardViewAdapter):
            dashboard_view.on_data_cleared()

    @Slot(str)
    def _on_chart_selected(self, chart_id: str) -> None:
        """
        Handle chart selection from dashboard.

        Args:
            chart_id (str): The chart identifier
        """
        # Switch to Charts view
        self._set_active_view("Charts")

        # Activate specific chart if needed
        chart_view = self._views.get("Charts")
        if chart_view and isinstance(chart_view, ChartViewAdapter):
            # This requires ChartViewAdapter to have a method to select specific chart
            # Uncomment and implement if this functionality is needed
            # chart_view.select_chart(chart_id)
            pass

    def _import_data(self, source_type=None) -> None:
        """
        Import data from the specified source type.

        Args:
            source_type: The type of source to import from
        """
        # Capture state before import
        self._capture_snapshot("before_import")

        with measure_time("Complete Import Operation", logging.INFO):
            logger.info(f"[IMPORT] Starting import from {source_type}")

            # Create and configure progress dialog
            self._setup_progress_dialog()

            # Start the worker thread
            worker_thread = self._create_import_worker_thread(source_type)
            worker_thread.start()
