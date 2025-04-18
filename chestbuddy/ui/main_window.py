"""
main_window.py

Description: Main window of the ChestBuddy application
Usage:
    window = MainWindow(data_model, services)
    window.show()
"""

import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Set, Tuple

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QSettings,
    QSize,
    QTimer,
    QObject,
    QDateTime,
    QModelIndex,
)
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
    QToolBar,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QCloseEvent

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CSVService, ValidationService, CorrectionService, ChartService
from chestbuddy.core.controllers import (
    FileOperationsController,
    ProgressController,
    ViewStateController,
    DataViewController,
    ErrorHandlingController,
    UIStateController,
)
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.resources.resource_manager import ResourceManager
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation, NavigationSection
from chestbuddy.ui.widgets.status_bar import StatusBar
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.views.dashboard_view import DashboardView
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.views.chart_view import ChartView
from chestbuddy.ui.widgets import ProgressDialog, ProgressBar
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.delegates.correction_delegate import CorrectionDelegate
from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.utils.config import ConfigManager

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
        data_manager,
        file_operations_controller: FileOperationsController,
        progress_controller: ProgressController,
        view_state_controller: ViewStateController,
        data_view_controller: DataViewController,
        ui_state_controller: UIStateController,
        config_manager=None,
        table_state_manager=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the MainWindow.

        Args:
            data_model (ChestDataModel): The data model.
            csv_service (CSVService): The CSV service.
            validation_service (ValidationService): The validation service.
            correction_service (CorrectionService): The correction service.
            chart_service (ChartService): The chart service.
            data_manager: The data manager.
            file_operations_controller (FileOperationsController): The file operations controller.
            progress_controller (ProgressController): The progress controller.
            view_state_controller (ViewStateController): The view state controller.
            data_view_controller (DataViewController): The data view controller.
            ui_state_controller (UIStateController): The UI state controller.
            config_manager: The configuration manager.
            table_state_manager: The table state manager.
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        self._data_model = data_model
        self._csv_service = csv_service
        self._validation_service = validation_service
        self._correction_service = correction_service
        self._chart_service = chart_service
        self._data_manager = data_manager
        self._file_controller = file_operations_controller
        self._progress_controller = progress_controller
        self._view_state_controller = view_state_controller
        self._data_view_controller = data_view_controller
        self._ui_state_controller = ui_state_controller
        self._config_manager = config_manager
        self._table_state_manager = table_state_manager

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

        # State tracking for file loading progress
        self._loading_state = {
            "current_file": "",
            "current_file_index": 0,
            "processed_files": [],
            "total_files": 0,  # Will be set by the caller via total_files property
            "total_rows": 0,
        }

        # Data state tracking
        self._has_data_loaded = False

        # UI state flags to prevent duplicate dialogs
        self._is_opening_file = False
        self._is_saving_file = False
        self._is_handling_import = False
        self._is_loading_files = False  # New flag to track if files are currently loading

        # Update UI
        self._update_ui()

        # Transition to using controllers
        self._register_with_controllers()

    def _register_with_controllers(self):
        """Register with controllers and connect signals."""
        # Connect file controller signals to local handlers
        self._file_controller.file_opened.connect(self._on_file_opened)
        self._file_controller.file_saved.connect(self._on_file_saved)
        self._file_controller.recent_files_changed.connect(self._on_recent_files_changed)

        # Connect to dialog canceled signal to reset import flags
        if hasattr(self._file_controller, "file_dialog_canceled"):
            self._file_controller.file_dialog_canceled.connect(self._on_file_dialog_canceled)

        # Connect data view controller signals
        self._data_view_controller.filter_applied.connect(self._on_filter_applied)
        self._data_view_controller.sort_applied.connect(self._on_sort_applied)
        self._data_view_controller.table_populated.connect(self._on_table_populated)

        # Connect ui state controller signals
        self._ui_state_controller.status_message_changed.connect(self._on_status_message_changed)
        self._ui_state_controller.actions_state_changed.connect(self._on_actions_state_changed)
        self._ui_state_controller.ui_refresh_needed.connect(self.refresh_ui)

        # Connect view import signals to the handler method directly
        # This uses direct Qt connections instead of SignalManager to fix the startup error
        for view_name, view in self._views.items():
            if hasattr(view, "import_requested"):
                logger.debug(
                    f"Connecting {view_name}.import_requested to _on_import_requested handler"
                )
                # Use direct Qt connection to the handler method that prevents duplicate dialogs
                view.import_requested.connect(self._on_import_requested)

    @Slot()
    def _on_import_requested(self):
        """
        Handle import requests from views.

        This slot is connected to view import_requested signals via SignalManager.
        It delegates to the FileOperationsController but adds guard logic
        to prevent duplicate dialogs.
        """
        logger.debug(
            f"_on_import_requested called with flags: _is_handling_import={getattr(self, '_is_handling_import', False)}, _is_loading_files={getattr(self, '_is_loading_files', False)}"
        )

        # Get current time to implement debounce
        current_time = QDateTime.currentMSecsSinceEpoch()
        last_cancel_time = getattr(self, "_last_dialog_cancel_time", 0)

        # Add a debounce period to prevent rapid successive dialog requests (e.g., after cancellation)
        DEBOUNCE_MS = 500  # 500ms debounce
        if (current_time - last_cancel_time) < DEBOUNCE_MS:
            logger.debug(
                f"Import request too soon after cancellation ({current_time - last_cancel_time}ms), debouncing"
            )
            return

        # Check if we're already handling an import to prevent duplicate dialogs
        if hasattr(self, "_is_handling_import") and self._is_handling_import:
            logger.debug("Already handling an import request, ignoring duplicate")
            return

        # Check if we're already loading files to prevent duplicate dialogs
        if hasattr(self, "_is_loading_files") and self._is_loading_files:
            logger.debug("Already loading files, ignoring duplicate import request")
            return

        # Check if we're already showing a progress dialog
        if (
            hasattr(self, "_progress_controller")
            and self._progress_controller.is_progress_showing()
        ):
            logger.debug("Progress dialog is showing, ignoring import request")
            return

        # Set flag to prevent duplicate dialogs
        self._is_handling_import = True
        logger.debug(
            "Handling import request via FileOperationsController - set flag: _is_handling_import=True"
        )

        # Delegate to file controller - let _on_file_dialog_canceled handle cancellation
        self._file_controller.open_file(self)

    @Slot(dict)
    def _on_filter_applied(self, filter_params: Dict) -> None:
        """
        Handle when a filter is applied via the controller.

        Args:
            filter_params (Dict): Filter parameters
        """
        if filter_params:
            logger.info(f"Filter applied: {filter_params}")
            # Update status bar with filter information
            column = filter_params.get("column", "")
            text = filter_params.get("text", "")
            if column and text:
                self._status_bar.set_status(f"Filter applied: {column}={text}")
        else:
            # Filter was cleared
            logger.info("Filter cleared")
            self._status_bar.set_status("Filter cleared")

    @Slot(str, bool)
    def _on_sort_applied(self, column: str, ascending: bool) -> None:
        """
        Handle when sorting is applied via the controller.

        Args:
            column (str): Column name
            ascending (bool): Sort direction
        """
        direction = "ascending" if ascending else "descending"
        logger.info(f"Sort applied: {column} ({direction})")
        self._status_bar.set_status(f"Sorted by {column} ({direction})")

    @Slot(int)
    def _on_table_populated(self, row_count: int) -> None:
        """
        Handle when the table is populated via the controller.

        Args:
            row_count (int): Number of rows populated
        """
        logger.info(f"Table populated with {row_count} rows")
        self._status_bar.set_status(f"Loaded {row_count} rows")

    @Slot(str)
    def _on_file_opened(self, file_path: str) -> None:
        """
        Handle when a file is opened via the controller.

        Args:
            file_path (str): Path to the opened file
        """
        logger.info(f"File opened: {file_path}")

        # Update status bar
        self._status_bar.set_status(f"Loaded: {os.path.basename(file_path)}")

        # Update last modified timestamp
        try:
            modified_time = os.path.getmtime(file_path)
            self._status_bar.set_last_modified(modified_time)
        except Exception as e:
            logger.error(f"Error getting file modified time: {e}")

    @Slot(str)
    def _on_file_saved(self, file_path: str) -> None:
        """
        Handle when a file is saved via the controller.

        Args:
            file_path (str): Path to the saved file
        """
        logger.info(f"File saved: {file_path}")

        # Update status bar
        self._status_bar.set_status(f"Saved: {os.path.basename(file_path)}")

        # Update last modified timestamp
        try:
            modified_time = os.path.getmtime(file_path)
            self._status_bar.set_last_modified(modified_time)
        except Exception as e:
            logger.error(f"Error getting file modified time: {e}")

    @Slot(list)
    def _on_recent_files_changed(self, recent_files: List[str]) -> None:
        """
        Handle when the recent files list changes via the controller.

        Args:
            recent_files (List[str]): Updated list of recent files
        """
        logger.debug(f"Recent files updated: {len(recent_files)} files")

        # Update local recent files list
        self._recent_files = recent_files

        # Update the recent files menu
        self._update_recent_files_menu()

        # Update dashboard
        dashboard_view = self._views.get("Dashboard")
        if dashboard_view and isinstance(dashboard_view, DashboardView):
            dashboard_view.set_recent_files(recent_files)

    @Slot(str)
    def _on_status_message_changed(self, message: str) -> None:
        """
        Handle changes to the status message.

        Args:
            message: The new status message
        """
        if hasattr(self, "_status_bar") and self._status_bar is not None:
            self._status_bar.set_status(message)

    @Slot(dict)
    def _on_actions_state_changed(self, action_states: Dict[str, bool]) -> None:
        """
        Handle changes to action states.

        Args:
            action_states: Dictionary mapping action names to boolean states
        """
        # Update actions based on their names
        for action_name, enabled in action_states.items():
            action = None

            # Map action names to actual action objects
            if action_name == "save":
                action = self._save_action
            elif action_name == "save_as":
                action = self._save_as_action
            elif action_name == "export":
                action = self._export_validation_action
            elif action_name == "validate":
                action = self._validate_action
            elif action_name == "correct":
                action = self._correct_action

            # Enable/disable the action if found
            if action is not None:
                action.setEnabled(enabled)

    @Slot()
    def _on_file_dialog_canceled(self):
        """
        Handle cancellation of file dialog.

        This resets the import handling flag to ensure future import requests work correctly.
        Also blocks signals temporarily to prevent duplicate dialog requests.
        """
        logger.debug(
            f"_on_file_dialog_canceled called with flags before reset: _is_handling_import={getattr(self, '_is_handling_import', False)}"
        )

        # Record cancellation time to support debouncing in _on_import_requested
        self._last_dialog_cancel_time = QDateTime.currentMSecsSinceEpoch()

        # Get all views that might emit import_requested signals
        dashboard_view = self._views.get("Dashboard")
        data_view = self._views.get("Data")
        sidebar = self._sidebar if hasattr(self, "_sidebar") else None

        # Block signals from all possible sources of import requests
        blocked_widgets = []

        try:
            # Block signals to prevent new import requests during cleanup
            for widget in [dashboard_view, data_view, sidebar]:
                if widget and hasattr(widget, "blockSignals"):
                    widget.blockSignals(True)
                    blocked_widgets.append(widget)

            # Also block empty state widgets if they exist
            if dashboard_view and hasattr(dashboard_view, "_empty_state_widget"):
                if hasattr(dashboard_view._empty_state_widget, "blockSignals"):
                    dashboard_view._empty_state_widget.blockSignals(True)
                    blocked_widgets.append(dashboard_view._empty_state_widget)

            # Reset the import handling flag to ensure future import requests work correctly
            self._is_handling_import = False

            # Also check if we need to reset any other states
            if hasattr(self, "_is_loading_files") and self._is_loading_files:
                logger.debug("Also resetting _is_loading_files flag that was still set")
                self._is_loading_files = False

            logger.debug("File dialog canceled, reset import handling flag to False")
        finally:
            # Process events before re-enabling signals, to avoid queued events triggering another dialog
            QApplication.processEvents()

            # Re-enable signals
            for widget in blocked_widgets:
                if widget and hasattr(widget, "blockSignals"):
                    widget.blockSignals(False)

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
        self._sidebar.data_dependent_view_clicked.connect(self._on_data_dependent_view_clicked)
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

        # Initialize view state controller with UI components
        self._view_state_controller.set_ui_components(
            self._views, self._sidebar, self._content_stack
        )

        # Connect view state controller signals
        self._view_state_controller.view_changed.connect(self._on_view_changed)
        self._view_state_controller.data_state_changed.connect(self._on_data_state_changed)

        # Set initial view to Dashboard
        self._view_state_controller.set_active_view("Dashboard")

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
        logger.debug("=== Creating DataViewAdapter in MainWindow ===")
        data_view_adapter = DataViewAdapter(data_model=self._data_model)
        data_view_id = id(data_view_adapter)
        logger.debug(f"Created DataViewAdapter with ID: {data_view_id}")

        if hasattr(data_view_adapter, "_data_view") and data_view_adapter._data_view:
            data_view_internal_id = id(data_view_adapter._data_view)
            logger.debug(f"Internal DataView has ID: {data_view_internal_id}")
        else:
            logger.warning("DataViewAdapter does not have a _data_view attribute or it is None")

        data_view_adapter.export_requested.connect(self._save_file_as)

        # Set the table state manager on the data view
        if hasattr(data_view_adapter, "set_table_state_manager") and self._table_state_manager:
            logger.debug("Setting TableStateManager on DataViewAdapter via adapter method")
            data_view_adapter.set_table_state_manager(self._table_state_manager)
            logger.info("TableStateManager set on DataViewAdapter")
        elif (
            hasattr(data_view_adapter, "_data_view")
            and hasattr(data_view_adapter._data_view, "set_table_state_manager")
            and self._table_state_manager
        ):
            logger.debug("Setting TableStateManager directly on internal DataView")
            data_view_adapter._data_view.set_table_state_manager(self._table_state_manager)
            logger.info("TableStateManager set on DataView within DataViewAdapter")
        elif self._table_state_manager:
            logger.warning(
                "Unable to set TableStateManager on data view - set_table_state_manager method not found"
            )

        # Set up the data view controller with the view
        logger.debug("Setting DataViewAdapter in DataViewController")
        self._data_view_controller.set_view(data_view_adapter)

        self._content_stack.addWidget(data_view_adapter)
        self._views["Data"] = data_view_adapter
        logger.debug(f"Added DataViewAdapter to content stack and views dictionary with key 'Data'")

        # Get CorrectionController (should be available via ServiceLocator or passed in)
        correction_controller = ServiceLocator.get("correction_controller")

        # Get the actual DataTableView and its delegate
        actual_table_view = None
        if isinstance(data_view_adapter, DataViewAdapter) and hasattr(
            data_view_adapter, "get_table_view"
        ):
            actual_table_view = data_view_adapter.get_table_view()
        elif isinstance(data_view_adapter, DataTableView):
            actual_table_view = data_view_adapter  # If it's the table view directly

        if (
            actual_table_view
            and isinstance(actual_table_view.itemDelegate(), CorrectionDelegate)
            and correction_controller
        ):
            delegate = actual_table_view.itemDelegate()
            logger.info(
                "Connecting CorrectionDelegate.correction_selected to CorrectionController.apply_correction_from_ui"
            )
            delegate.correction_selected.connect(correction_controller.apply_correction_from_ui)
        else:
            logger.warning(
                "Could not connect CorrectionDelegate signal: TableView, Delegate, or Controller not found/valid."
            )

        # Create Validation view
        validation_view = ValidationViewAdapter(
            data_model=self._data_model, validation_service=self._validation_service
        )
        # Set up the validation view to use the data view controller
        validation_view.set_controller(self._data_view_controller)
        self._content_stack.addWidget(validation_view)
        self._views["Validation"] = validation_view

        # Create Correction view - use our new implementation
        from chestbuddy.ui.views.correction_view import CorrectionView

        correction_view = CorrectionView(
            data_model=self._data_model, correction_service=self._correction_service
        )
        # Set up the view to use both controllers
        correction_view.set_controller(self._data_view_controller)
        if correction_controller:
            correction_view.set_correction_controller(correction_controller)
        else:
            logger.warning("Correction controller not available from app")

        self._content_stack.addWidget(correction_view)
        self._views["Correction"] = correction_view

        # Create Analysis/Charts view
        chart_view = ChartView(data_model=self._data_model, chart_service=self._chart_service)
        # Set up the chart view to use the data view controller
        chart_view.set_controller(self._data_view_controller)
        self._content_stack.addWidget(chart_view)
        self._views["Charts"] = chart_view

        # Create Settings view
        from chestbuddy.ui.views import SettingsViewAdapter

        settings_view = SettingsViewAdapter(config_manager=self._config_manager)
        settings_view.settings_changed.connect(self._on_settings_changed)
        settings_view.config_reset.connect(self._on_config_reset)
        settings_view.config_imported.connect(self._on_config_imported)
        settings_view.config_exported.connect(self._on_config_exported)
        self._content_stack.addWidget(settings_view)
        self._views["Settings"] = settings_view

        # Set services in the data view controller
        self._data_view_controller.set_services(
            validation_service=self._validation_service, correction_service=self._correction_service
        )
        logger.info("Services set in data view controller")

        # TODO: Add placeholder views for other sections
        # For Reports, Help if needed

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

        # Export Validation Issues action
        self._export_validation_action = QAction("Export &Validation Issues...", self)
        self._export_validation_action.setStatusTip("Export validation issues to a file")
        self._export_validation_action.triggered.connect(self._export_validation_issues)
        data_menu.addAction(self._export_validation_action)

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")

        # About action
        self._about_action = QAction("&About", self)
        self._about_action.setStatusTip("Show the application's About box")
        self._about_action.triggered.connect(self._show_about)
        help_menu.addAction(self._about_action)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect signals from sidebar navigation
        self._sidebar.navigation_changed.connect(self._on_navigation_changed)
        self._sidebar.data_dependent_view_clicked.connect(self._on_data_dependent_view_clicked)

        # Connect signals from data model
        self._data_model.data_changed.connect(self._on_data_model_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect file menu signals
        self._open_action.triggered.connect(self._open_file)
        self._save_action.triggered.connect(self._save_file)
        self._save_as_action.triggered.connect(self._save_file_as)

        # Connect tools menu signals
        self._validate_action.triggered.connect(self._validate_data)
        self._correct_action.triggered.connect(self._correct_data)
        self._export_validation_action.triggered.connect(self._export_validation_issues)

        # Connect help menu signals
        self._about_action.triggered.connect(self._show_about)

        # Connect DataManager signals
        self._data_manager.load_started.connect(self._on_load_started)
        self._data_manager.load_finished.connect(self._on_load_finished)
        self._data_manager.load_progress.connect(self._on_load_progress)
        self._data_manager.load_error.connect(self._on_load_error)
        self._data_manager.load_success.connect(self.refresh_ui)

        # Connect data_loaded signal to populate_data_table method
        # This ensures the table is populated even for subsequent file loads
        self._data_manager.data_loaded.connect(self._ensure_data_table_populated)

        # Connect DataTableView signal
        data_view_instance = self._views.get("data")
        # Check if it's DataTableView or DataViewAdapter containing it
        actual_table_view = None
        if isinstance(data_view_instance, DataTableView):
            actual_table_view = data_view_instance
        elif hasattr(data_view_instance, "get_table_view"):  # Check if adapter has a getter
            actual_table_view = data_view_instance.get_table_view()
        elif hasattr(data_view_instance, "table_view"):  # Or direct access
            actual_table_view = data_view_instance.table_view

        if actual_table_view and hasattr(actual_table_view, "correction_apply_requested"):
            print("Connecting DataTableView.correction_apply_requested")  # Debug
            actual_table_view.correction_apply_requested.connect(
                self._on_correction_apply_requested
            )
        elif data_view_instance:
            print(
                f"Warning: Could not find correction_apply_requested signal on view 'data' or its table_view (Type: {type(data_view_instance)}). Cannot connect correction signal."
            )
        else:
            print(
                "Warning: Data view instance not found in self._views. Cannot connect correction signal."
            )

        # Connect UI State Controller
        if self._ui_state_controller:
            self._ui_state_controller.status_message_changed.connect(self.statusBar().showMessage)
            self._ui_state_controller.actions_state_changed.connect(self._on_actions_state_changed)
            self._ui_state_controller.ui_refresh_needed.connect(self.refresh_ui)

        # Connect File Controller
        if self._file_controller:
            self._file_controller.file_opened.connect(self._on_file_opened)
            self._file_controller.file_saved.connect(self._on_file_saved)
            self._file_controller.recent_files_changed.connect(self._on_recent_files_changed)
            if hasattr(self._file_controller, "file_dialog_canceled"):
                self._file_controller.file_dialog_canceled.connect(self._on_file_dialog_canceled)

        # Connect Progress Controller (for manual progress dialog if needed elsewhere)
        # if self._progress_controller:
        #     pass # Connect signals if MainWindow needs to directly show progress

        # Connect signals for validation view
        validation_view = self._views.get("validation")
        if validation_view and hasattr(validation_view, "import_requested"):
            validation_view.import_requested.connect(self._on_import_requested)

        # Connect DataTableView correction request to DataViewController slot
        data_view = self._views.get("data")
        if data_view and hasattr(data_view, "_data_view"):
            data_table_view = data_view._data_view  # Get the DataTableView instance
            if data_table_view and hasattr(data_table_view, "correction_action_triggered"):
                data_table_view.correction_action_triggered.connect(
                    self._data_view_controller._handle_apply_correction
                )
                logger.debug(
                    "Connected DataTableView correction_action_triggered to DataViewController._handle_apply_correction"
                )

        # Connect application quit signal
        app = QApplication.instance()

    def _load_settings(self) -> None:
        """Load application settings."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Recent files are now handled by the file controller
        # No need to load them here

    def _save_settings(self) -> None:
        """Save application settings."""
        settings = QSettings("ChestBuddy", "ChestBuddy")
        settings.setValue("geometry", self.saveGeometry())
        settings.sync()

        # Recent files are now handled by the file controller
        # No need to save them here

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
        """Update UI based on current state."""
        # Get data model state
        has_data = self._data_model is not None and not self._data_model.is_empty

        # Update data loaded state through UI state controller
        self._ui_state_controller.update_data_dependent_ui(has_data)

        # Update dashboard information
        if "Dashboard" in self._views:
            dashboard_view = self._views["Dashboard"]
            dashboard_view.set_recent_files(self._recent_files)

            if has_data:
                # Update dashboard stats
                dashboard_view.update_stats(
                    dataset_rows=len(self._data_model.data),
                    validation_status="Not Validated"
                    if self._data_model.get_validation_status().empty
                    else f"{len(self._data_model.get_validation_status())} issues",
                    corrections=self._data_model.get_correction_row_count(),
                    last_import=datetime.now().strftime("%Y-%m-%d %H:%M") if has_data else "Never",
                )

        # Update status bar
        self._update_status_bar()

    def _update_data_loaded_state(self, has_data: bool) -> None:
        """
        Update UI components based on whether data is loaded.

        Args:
            has_data: Whether data is loaded.
        """
        # Delegate to the view state controller
        self._view_state_controller.update_data_loaded_state(has_data)

        # Delegate to the UI state controller for action states
        self._ui_state_controller.update_data_dependent_ui(has_data)

        # Store the data loaded state
        self._has_data_loaded = has_data

    @Slot(str)
    def _set_active_view(self, view_name: str) -> None:
        """
        Set the active view in the content stack.

        Args:
            view_name (str): The name of the view to activate
        """
        # Delegate to the view state controller
        try:
            self._view_state_controller.set_active_view(view_name)
        except Exception as e:
            logger.error(f"Error setting active view to '{view_name}': {e}")
            QMessageBox.critical(self, "Error", f"Error switching to {view_name} view: {str(e)}")

    # ===== Slots =====

    @Slot(str)
    def _on_view_changed(self, view_name: str) -> None:
        """
        Handle view changed signal from the ViewStateController.

        Args:
            view_name (str): The name of the active view
        """
        # Update UI components based on the new view
        self._update_ui()

    @Slot(bool)
    def _on_data_state_changed(self, has_data: bool) -> None:
        """
        Handle data state changed signal from the ViewStateController.

        Args:
            has_data (bool): Whether data is loaded
        """
        # Update actions
        self._save_action.setEnabled(has_data)
        self._save_as_action.setEnabled(has_data)
        self._validate_action.setEnabled(has_data)
        self._correct_action.setEnabled(has_data)

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
                    # Check if we're already handling an import to prevent duplicate dialogs
                    if hasattr(self, "_is_handling_import") and self._is_handling_import:
                        logger.debug(
                            "Already handling an import request, ignoring navigation request"
                        )
                        return
                    self._on_import_requested()
                elif subsection == "Validate":
                    self._view_state_controller.set_active_view("Validation")
                elif subsection == "Correct":
                    self._view_state_controller.set_active_view("Correction")
                elif subsection == "Export":
                    self._save_file_as()
            elif section == "Analysis":
                if subsection == "Charts":
                    self._view_state_controller.set_active_view("Charts")
                elif subsection == "Tables":
                    # TODO: Handle tables view
                    pass
            elif section == "Settings":
                # TODO: Handle settings subsections
                pass
        else:
            # Handle main sections
            if section == "Dashboard":
                self._view_state_controller.set_active_view("Dashboard")
            elif section == "Data":
                self._view_state_controller.set_active_view("Data")
            elif section == "Analysis":
                self._view_state_controller.set_active_view("Charts")
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
            # Use the same method that handles import requests to prevent duplicate dialogs
            self._on_import_requested()
        elif action == "validate":
            self._validate_data()
            self._view_state_controller.set_active_view("Validation")
        elif action == "analyze":
            self._view_state_controller.set_active_view("Charts")
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
    def _on_data_model_changed(self) -> None:
        """Handle data model changes."""
        # Prevent recursive actions during data changes
        if hasattr(self, "_is_data_changing") and self._is_data_changing:
            return

        self._is_data_changing = True
        try:
            self._update_ui()

            # Update data loaded state
            has_data = self._data_model is not None and not self._data_model.is_empty
            self._update_data_loaded_state(has_data)
        finally:
            self._is_data_changing = False

    @Slot(object)
    def _on_validation_changed(self, validation_status: Optional[pd.DataFrame] = None) -> None:
        """
        Handle changes in validation status from the DataManager or other sources.

        Args:
            validation_status (Optional[pd.DataFrame]): DataFrame with validation status, if provided.
        """
        # Update UI elements that depend on validation status
        # e.g., update status bar, enable/disable actions
        try:
            if validation_status is not None and not validation_status.empty:
                issue_count = sum(
                    1 for idx, row in validation_status.iterrows() if not row.get("STATUS", True)
                )
                message = (
                    f"Validation complete: {issue_count} issues found"
                    if issue_count > 0
                    else "Validation complete: No issues found"
                )
                # Use UIStateController to update status
                if self._ui_state_controller:
                    self._ui_state_controller.handle_validation_results(
                        validation_status.to_dict("index")
                    )  # Pass results
            else:
                message = "Validation status cleared or unavailable"
                # Reset validation state in UI controller
                if self._ui_state_controller:
                    self._ui_state_controller.update_validation_state(reset=True)

            # Log the update
            logger.debug(f"MainWindow handling validation change: {message}")

        except Exception as e:
            logger.error(f"Error in MainWindow._on_validation_changed: {e}")

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
        """Handle load started signal."""
        logger.debug("MainWindow._on_load_started called")

        # Set the loading flag to prevent duplicate import dialogs
        self._is_loading_files = True

        if self._progress_controller:
            self._progress_controller.start_progress("Loading Data", "Loading data...", True)
        self._update_ui()

    @Slot(str)
    def _on_load_finished(self, status_message: str) -> None:
        """
        Handle load finished signal.

        Args:
            status_message: Status message to display
        """
        logger.debug(f"Load finished signal received: {status_message}")

        # Reset the loading flag when file loading completes
        self._is_loading_files = False

        # Reset the handling import flag as well
        self._is_handling_import = False

        if self._progress_controller:
            if "Processing" in status_message:
                # If we're processing data, update the progress dialog
                # but don't close it yet
                self._progress_controller.update_progress(
                    100,
                    100,
                    f"{status_message}...",
                    None,  # No file path needed for processing stage
                )
            else:
                # Loading is completely finished, close the progress dialog
                self._progress_controller.close_progress()

        # Set is_finishing_load flag to prevent duplicate dialogs during finalization
        try:
            self._is_finishing_load = True

            # Update views
            self._view_state_controller.update_data_loaded_state(not self._data_model.is_empty)
        finally:
            self._is_finishing_load = False

        # Update UI
        self._update_ui()

    def _on_load_progress(self, file_path: str, current: int, total: int) -> None:
        """
        Handle progress updates during loading.

        Args:
            file_path: Path of the file being processed (empty for overall progress)
            current: Current progress value
            total: Total progress value
        """
        # Progress controller now handles all progress tracking and updates
        # This method is kept for backward compatibility but delegates to the controller
        self._progress_controller.update_file_progress(file_path, current, total)

    def _on_load_error(self, message: str) -> None:
        """
        Handle errors during the loading process.

        Args:
            message: Error message
        """
        logger.error(f"Load error: {message}")

        # Progress controller handles updating the progress dialog
        # We just need to handle UI-specific error handling here

        # Update the UI to reflect the error state
        self._status_bar.set_status(f"Error: {message}", is_error=True)

        # Reset any file loading state in the UI

    def _cancel_loading(self) -> None:
        """Cancel the current loading operation."""
        logger.info("Canceling loading operation")

        # Tell data manager to cancel the current operation
        if self._data_manager:
            self._data_manager.cancel_loading()

    # ===== Actions =====

    def _open_file(self) -> None:
        """Open one or more CSV files."""
        # Check if we're already handling an import to prevent duplicate dialogs
        if hasattr(self, "_is_handling_import") and self._is_handling_import:
            logger.debug("Already handling an import request, ignoring open file")
            return

        # Prevent opening a file dialog if we're already finishing a load operation
        if hasattr(self, "_is_finishing_load") and self._is_finishing_load:
            logger.debug("Preventing file dialog during load completion")
            return

        # Also check if we already have a progress dialog showing
        if (
            hasattr(self, "_progress_controller")
            and self._progress_controller.is_progress_showing()
        ):
            logger.debug("Preventing file dialog while progress dialog is visible")
            return

        # Set flag to prevent duplicate dialogs
        self._is_handling_import = True

        # Note: This method is directly connected to UI actions like menu items
        # Import requests from views are now handled by _on_import_requested
        # which uses the SignalManager to avoid duplicate connections
        self._file_controller.open_file(self)

    def _open_recent_file(self, file_path: str) -> None:
        """
        Open a recent file.

        Args:
            file_path: The path of the file to open.
        """
        # Delegate to the controller
        self._file_controller.open_recent_file(file_path)

    def _save_file(self) -> None:
        """Save the current file."""
        if self._data_model.is_empty:
            return

        # Delegate to the controller
        self._file_controller.save_file(self)

    def _save_file_as(self) -> None:
        """Save the file with a new name."""
        if self._data_model.is_empty:
            return

        # Prevent duplicate file dialogs
        if hasattr(self, "_is_saving_file") and self._is_saving_file:
            logger.debug("Preventing duplicate file save dialog")
            return

        # Set flag to prevent duplicate dialogs
        self._is_saving_file = True

        # Delegate to the controller
        self._file_controller.save_file_as(self)

    def _validate_data(self) -> None:
        """Validate the data."""
        if self._data_model.is_empty:
            return

        self.validation_requested.emit()
        self.validate_data_triggered.emit()
        self._view_state_controller.set_active_view("Validation")

    def _correct_data(self) -> None:
        """Apply corrections to the data."""
        if self._data_model.is_empty:
            return

        self.correction_requested.emit()
        self.apply_corrections_triggered.emit()
        self._view_state_controller.set_active_view("Correction")

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
        if hasattr(self, "_progress_controller") and self._progress_controller:
            try:
                self._progress_controller.close_progress()
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
            # Delegate to the view state controller for active view refreshing
            self._view_state_controller.refresh_active_view()

            # Use data view controller to refresh data if needed
            if self._content_stack.currentWidget() == self._views.get("Data"):
                self._data_view_controller.refresh_data()

            # Update status bar (keeping this here as it's UI-specific)
            if hasattr(self, "_status_bar") and self._status_bar is not None:
                self._update_status_bar()
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error refreshing UI: {e}")

    def _update_status_bar(self) -> None:
        """Update the status bar with current information."""
        if hasattr(self, "_data_model") and self._data_model:
            if not self._data_model.is_empty:
                # Get row count
                row_count = len(self._data_model.data)

                # Delegate to UI state controller
                self._ui_state_controller.update_status_message(f"Data loaded: {row_count:,} rows")
            else:
                # Delegate to UI state controller
                self._ui_state_controller.update_status_message("No data loaded")
        else:
            # Delegate to UI state controller
            self._ui_state_controller.update_status_message("No data model available")

    @Slot(str, str)
    def _on_data_dependent_view_clicked(self, section: str, item: str) -> None:
        """
        Handle when a data-dependent view is clicked while data is not loaded.

        Args:
            section (str): The section that was clicked
            item (str): The item that was clicked (empty for main section)
        """
        # Show message to user
        QMessageBox.information(
            self,
            "No Data Loaded",
            "Please import data first to access this feature.",
            QMessageBox.Ok,
        )

        # Optionally, we could automatically navigate to the dashboard or show the import dialog
        # self._set_active_view("Dashboard")

    def populate_data_table(self) -> None:
        """Populate the data table with current data."""
        # Delegate to the data view controller
        self._data_view_controller.populate_table()

    def _ensure_data_table_populated(self):
        """
        Ensure the data table is populated after data is loaded.
        This is especially important for subsequent file loads.
        """
        logger.info("Data loaded signal received, ensuring data table is populated")

        # Delegate to the data view controller
        if self._data_view_controller.needs_refresh():
            logger.info("Data view needs refresh, populating table")
            self._data_view_controller.populate_table()
        else:
            logger.info("Data view doesn't need refresh, skipping table population")

        # As a fallback, try to force population on any data view adapters
        try:
            data_view_adapter = self._view_state_controller.get_view("Data")
            if data_view_adapter and hasattr(data_view_adapter, "populate_table"):
                logger.info("Forcing population on DataViewAdapter as fallback")
                data_view_adapter.populate_table()
        except Exception as e:
            logger.error(f"Error in fallback table population: {e}")

    # Add handler methods for settings view signals
    def _on_settings_changed(self, section: str, option: str, value: str) -> None:
        """
        Handle settings changed event.

        Args:
            section (str): Configuration section
            option (str): Configuration option
            value (str): New value
        """
        logger.info(f"Setting changed: [{section}] {option} = {value}")

        # Update status bar
        self._status_bar.showMessage(f"Setting updated: [{section}] {option}", 3000)

        # Apply certain settings immediately if needed
        if section == "UI":
            # UI settings might require immediate application
            pass
        elif section == "General":
            # General settings like theme might need application restart
            if option == "theme":
                # Show hint that restart is needed for full effect
                self._show_info_message(
                    "Theme Change",
                    "The theme has been changed. Some changes may require an application restart to take full effect.",
                )

    def _on_config_reset(self, section: str) -> None:
        """
        Handle configuration reset event.

        Args:
            section (str): The section that was reset, or "all"
        """
        logger.info(f"Configuration reset: {section}")

        # Update status bar
        self._status_bar.showMessage(f"Settings reset: {section}", 3000)

        # Show notification
        self._show_info_message(
            "Settings Reset",
            f"The {'settings' if section == 'all' else section + ' settings'} have been reset to defaults.",
        )

    def _on_config_imported(self, file_path: str) -> None:
        """
        Handle configuration import event.

        Args:
            file_path (str): Path to the imported file
        """
        logger.info(f"Configuration imported from: {file_path}")

        # Update status bar
        self._status_bar.showMessage(f"Settings imported from: {file_path}", 3000)

        # Show notification
        self._show_info_message(
            "Settings Imported",
            f"Settings have been imported from:\n{file_path}\n\nSome changes may require an application restart to take full effect.",
        )

    def _on_config_exported(self, file_path: str) -> None:
        """
        Handle configuration export event.

        Args:
            file_path (str): Path to the exported file
        """
        logger.info(f"Configuration exported to: {file_path}")

        # Update status bar
        self._status_bar.showMessage(f"Settings exported to: {file_path}", 3000)

    def _init_services(self) -> None:
        """Initialize the application services."""
        # Load configuration manager
        self._config_manager = ConfigManager()

        # Initialize data model
        self._data_model = ChestDataModel()

        # Create services with the data model
        self._validation_service = ValidationService(self._data_model, self._config_manager)
        self._correction_service = CorrectionService(self._data_model, self._config_manager)

        # Set up service cross-references
        self._validation_service.set_correction_service(self._correction_service)

        # Initialize controllers with services and data model
        self._init_controllers()

    @Slot(QModelIndex, object)
    def _on_correction_apply_requested(self, source_index: QModelIndex, suggestion: object) -> None:
        """Handles the request from the DataTableView to apply a correction."""
        if not source_index.isValid():
            print("MainWindow received invalid index for correction request.")
            return

        print(
            f"MainWindow received correction request for {source_index.row()},{source_index.column()}."
            f" Suggestion: {suggestion}"
        )

        # Retrieve the CorrectionService
        correction_service = ServiceLocator.get("correction_service")
        if not correction_service:
            QMessageBox.critical(
                self,
                "Correction Error",
                "Correction service is not available. Cannot apply correction.",
            )
            print("CorrectionService not found in ServiceLocator.")
            return

        # Get the corrected value from the suggestion object
        # (Assuming suggestion has a 'corrected_value' attribute)
        corrected_value = getattr(suggestion, "corrected_value", None)
        if corrected_value is None:
            QMessageBox.warning(
                self, "Correction Error", "Could not determine corrected value from suggestion."
            )
            print("Could not get corrected_value from suggestion object.")
            return

        # Call the service to apply the correction
        # Option 1: Service takes index + value
        # Option 2: Service takes index + suggestion object
        # Let's assume Option 1 for now, modify if service API differs
        try:
            # Assuming the service has a method like apply_correction(row, col, value)
            if hasattr(correction_service, "apply_correction") and callable(
                getattr(correction_service, "apply_correction")
            ):
                success = correction_service.apply_correction(
                    source_index.row(), source_index.column(), corrected_value
                )
                if success:
                    print(
                        f"Correction applied successfully via service for {source_index.row()},{source_index.column()}"
                    )
                    # Optionally show a brief status message or rely on data model refresh
                    self.statusBar().showMessage("Correction applied.", 2000)
                else:
                    QMessageBox.warning(
                        self,
                        "Correction Error",
                        f"Correction service failed to apply change for cell ({source_index.row()},{source_index.column()}).",
                    )
                    print(
                        f"CorrectionService returned False for {source_index.row()},{source_index.column()}"
                    )
            else:
                # Fallback: Try setting data directly on the source model
                print("CorrectionService.apply_correction not found, attempting model.setData")
                source_model = self._source_model  # Ensure we have access to the source model
                if source_model:
                    success = source_model.setData(source_index, corrected_value, Qt.EditRole)
                    if success:
                        print(
                            f"Correction applied successfully via model.setData for {source_index.row()},{source_index.column()}"
                        )
                        self.statusBar().showMessage("Correction applied.", 2000)
                    else:
                        QMessageBox.warning(
                            self,
                            "Correction Error",
                            f"Failed to apply change via model.setData for cell ({source_index.row()},{source_index.column()}).",
                        )
                        print(
                            f"model.setData returned False for {source_index.row()},{source_index.column()}"
                        )
                else:
                    raise AttributeError(
                        "CorrectionService missing apply_correction and source_model not available"
                    )

        except Exception as e:
            logger.error(
                f"Error calling CorrectionService.apply_correction or model.setData: {e}",
                exc_info=True,
            )
            QMessageBox.critical(
                self,
                "Correction Error",
                f"An unexpected error occurred while applying the correction: {e}",
            )
