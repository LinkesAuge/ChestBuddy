"""
main_window.py

Description: Main window of the ChestBuddy application
Usage:
    window = MainWindow(data_model, services)
    window.show()
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple

from PySide6.QtCore import Qt, Signal, Slot, QSettings, QSize, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QToolBar,
    QMenuBar,
    QStatusBar,
    QMenu,
    QFileDialog,
    QMessageBox,
    QApplication,
    QStackedWidget,
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
        load_csv_triggered (str): Signal emitted when a CSV file load is triggered.
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
    load_csv_triggered = Signal(str)
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
            parent: The parent widget.
        """
        super().__init__(parent)

        # Store references to services
        self._data_model = data_model
        self._csv_service = csv_service
        self._validation_service = validation_service
        self._correction_service = correction_service
        self._chart_service = chart_service

        # Set window title and icon
        self.setWindowTitle("ChestBuddy - Chest Data Analysis Tool")
        self.setWindowIcon(Icons.get_icon(Icons.APP_ICON))

        # Set window size
        self.resize(1200, 800)

        # Initialize UI
        self._init_ui()

        # Create menus and toolbars
        self._init_menus()
        self._init_toolbar()

        # Connect signals
        self._connect_signals()

        # Load settings
        self._load_settings()

        # Initialize recent files
        self._recent_files: List[str] = []
        self._load_recent_files()

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

    def _init_toolbar(self) -> None:
        """Initialize the application toolbar."""
        # Create main toolbar
        self._toolbar = QToolBar("Main Toolbar")
        self._toolbar.setMovable(False)
        self._toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self._toolbar)

        # Add actions to toolbar
        self._toolbar.addAction(self._open_action)
        self._toolbar.addAction(self._save_action)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._validate_action)
        self._toolbar.addAction(self._correct_action)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect data model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

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

    def _set_active_view(self, view_name: str) -> None:
        """
        Set the active view.

        Args:
            view_name: The name of the view to activate.
        """
        view = self._views.get(view_name)
        if view:
            self._content_stack.setCurrentWidget(view)
            self._sidebar.set_active_item(view_name)

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

    # ===== Actions =====

    def _open_file(self) -> None:
        """Open a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                self._csv_service.read_csv(file_path)
                self._add_recent_file(file_path)
                self.file_opened.emit(file_path)
                self.load_csv_triggered.emit(file_path)
                self._status_bar.set_status(f"Loaded: {os.path.basename(file_path)}")

                # Update last modified timestamp
                modified_time = os.path.getmtime(file_path)
                self._status_bar.set_last_modified(modified_time)
            except Exception as e:
                logger.error(f"Error opening file: {e}")
                QMessageBox.critical(self, "Error", f"Error opening file: {str(e)}")

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
            self._csv_service.read_csv(file_path)
            self._add_recent_file(file_path)  # This will move it to the top
            self.file_opened.emit(file_path)
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
            if hasattr(self, "_tab_widget") and self._tab_widget is not None:
                current_index = self._tab_widget.currentIndex()
                current_widget = self._tab_widget.widget(current_index)

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
