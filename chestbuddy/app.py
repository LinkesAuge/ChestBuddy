"""
ChestBuddy application main entry point.

This module provides the main ChestBuddy application class that initializes
all services and UI components.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt, QMetaObject

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import (
    CSVService,
    ValidationService,
    CorrectionService,
    ChartService,
    DataManager,
)
from chestbuddy.core.controllers import (
    FileOperationsController,
    ProgressController,
    ViewStateController,
    DataViewController,
    ErrorHandlingController,
    UIStateController,
)
from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.background_processing import BackgroundWorker
from chestbuddy.ui.resources.style import apply_application_style
from chestbuddy.ui.resources.resource_manager import ResourceManager
from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.ui.utils.update_manager import UpdateManager
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.table_state_manager import TableStateManager
from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.ui.data.adapters.correction_adapter import CorrectionAdapter

# Set up logger
logger = logging.getLogger(__name__)


# Define a custom exception for critical errors
class CriticalError(Exception):
    pass


class ChestBuddyApp(QObject):
    """
    Main application class for the ChestBuddy application.

    This class initializes all the necessary services and UI components,
    connects their signals and slots, and provides application-level methods.

    Implementation Notes:
        - Manages the lifecycle of the application
        - Initializes services and UI components
        - Connects signals between services and UI components using SignalManager
        - Handles application-level events
    """

    def __init__(self, args: List[str] = None) -> None:
        """
        Initialize the ChestBuddy application.

        Args:
            args: Command-line arguments
        """
        super().__init__()
        self._data_model = None
        self._main_window = None
        self._args = args or []

        # Create signal manager
        self._signal_manager = SignalManager(debug_mode=False)

        # Initialize application
        self._initialize_application()

    def _initialize_application(self) -> None:
        """Initialize the application and its components."""
        try:
            # Set up logging
            self._setup_logging()

            # Create configuration manager
            self._config_manager = ConfigManager("chestbuddy")

            # Initialize data model
            self._data_model = ChestDataModel()

            # Initialize table state manager
            self._table_state_manager = TableStateManager(self._data_model)
            ServiceLocator.register("table_state_manager", self._table_state_manager)
            logger.info("TableStateManager initialized and registered")

            # Create controllers - create error controller early
            self._error_controller = ErrorHandlingController(self._signal_manager)

            # Create services
            try:
                # Create services
                self._csv_service = CSVService()

                # Create DataManager with the correct arguments
                self._data_manager = DataManager(self._data_model, self._csv_service)

                self._validation_service = ValidationService(self._data_model, self._config_manager)
                ServiceLocator.register("validation_service", self._validation_service)
                logger.info("ValidationService initialized and registered")

                # Initialize CorrectionRuleManager and CorrectionService with all required parameters
                self._correction_rule_manager = CorrectionRuleManager(self._config_manager)
                self._correction_service = CorrectionService(self._data_model, self._config_manager)
                self._correction_service._validation_service = self._validation_service
                ServiceLocator.register("correction_service", self._correction_service)
                logger.info("CorrectionService initialized and registered")

                # Load correction rules
                try:
                    self._correction_rule_manager.load_rules()
                    logger.info("Correction rules loaded during startup")
                except Exception as e:
                    logger.warning(f"Error loading correction rules during startup: {e}")

                self._chart_service = ChartService(self._data_model)

                # Create and Connect Adapters
                self._validation_adapter = ValidationAdapter(
                    validation_service=self._validation_service,
                    table_state_manager=self._table_state_manager,
                )
                logger.info("ValidationAdapter initialized and connected")

                self._correction_adapter = CorrectionAdapter(
                    correction_service=self._correction_service,
                    table_state_manager=self._table_state_manager,
                )
                logger.info("CorrectionAdapter initialized and connected")

                # Initialize DataManager with config_manager
                self._data_manager._config = self._config_manager
            except Exception as e:
                logger.error(f"Error initializing services: {e}")
                self._error_controller.handle_exception(e, "Error initializing services")
                raise

            # Create remaining controllers
            try:
                self._file_controller = FileOperationsController(
                    self._data_manager, self._config_manager, self._signal_manager
                )
                self._progress_controller = ProgressController(self._signal_manager)
                self._view_state_controller = ViewStateController(
                    self._data_model, self._signal_manager
                )
                self._ui_state_controller = UIStateController(self._signal_manager)
                self._data_view_controller = DataViewController(
                    self._data_model,
                    self._signal_manager,
                    ui_state_controller=self._ui_state_controller,
                )

                # Initialize CorrectionController
                self._correction_controller = CorrectionController(
                    self._correction_service,
                    self._correction_rule_manager,
                    self._config_manager,
                    self._validation_service,
                    self._signal_manager,
                )
                ServiceLocator.register("correction_controller", self._correction_controller)
                logger.info("CorrectionController initialized and registered")

            except Exception as e:
                logger.error(f"Error initializing controllers: {e}")
                self._error_controller.handle_exception(e, "Error initializing controllers")
                raise

            # Initialize UpdateManager and register with ServiceLocator
            try:
                self._update_manager = UpdateManager()
                # Register with class name and string name for compatibility
                ServiceLocator.register(UpdateManager, self._update_manager)
                ServiceLocator.register("update_manager", self._update_manager)
                logger.info("UpdateManager initialized and registered with ServiceLocator")
            except Exception as e:
                logger.error(f"Error initializing UpdateManager: {e}")
                self._error_controller.handle_exception(e, "Error initializing UpdateManager")
                raise

            # Set up controller relationships
            self._error_controller.set_progress_controller(self._progress_controller)

            # Connect ViewStateController and DataViewController
            self._view_state_controller.set_data_view_controller(self._data_view_controller)

            # Create resource manager
            self._resource_manager = ResourceManager()

            # Create UI
            self._create_ui()

            # Connect signals
            self._connect_signals()

            # Apply application-wide styling
            app = QApplication.instance()
            apply_application_style(app)

            logger.info("Application initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize application: {e}")
            self._error_controller.handle_exception(e, "Failed to initialize application")
            sys.exit(1)

    def _setup_logging(self) -> None:
        """Set up logging for the application."""
        try:
            # Get application base directory (directory containing app.py)
            base_dir = Path(__file__).parent
            # Create logs directory in chestbuddy/logs
            log_dir = base_dir / "logs"
            log_dir.mkdir(exist_ok=True, parents=True)

            # Set up file handler with UTF-8 encoding
            log_file = log_dir / "chestbuddy.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)

            # Set up console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Set up formatters
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")

            # Apply formatters
            file_handler.setFormatter(file_formatter)
            console_handler.setFormatter(console_formatter)

            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

            logger.info(f"Logging initialized with UTF-8 support in {log_file}")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            # Continue without logging

    def _create_ui(self) -> None:
        """
        Create and setup the UI components.
        """
        try:
            logging.info("Creating UI...")
            self._main_window = MainWindow(
                data_model=self._data_model,
                csv_service=self._csv_service,
                validation_service=self._validation_service,
                correction_service=self._correction_service,
                chart_service=self._chart_service,
                data_manager=self._data_manager,
                file_operations_controller=self._file_controller,
                progress_controller=self._progress_controller,
                view_state_controller=self._view_state_controller,
                data_view_controller=self._data_view_controller,
                ui_state_controller=self._ui_state_controller,
                config_manager=self._config_manager,
                table_state_manager=self._table_state_manager,
            )
            self._main_window.show()
            logging.info("UI created successfully")
        except Exception as e:
            logger.critical(f"Failed to create UI: {e}")
            self._error_controller.handle_exception(e, "Failed to create UI")
            sys.exit(1)

    def _connect_signals(self) -> None:
        """Connect application-level signals."""
        try:
            logger.debug("Connecting ChestBuddyApp signals")

            # Connect data model signals to appropriate handlers
            self._data_model.data_changed.connect(self._on_data_changed)

            # Connect MainWindow signals (e.g., file open, save)
            if hasattr(self._main_window, "_open_action"):
                # Connect to the controller method that shows the dialog
                self._main_window._open_action.triggered.connect(self._file_controller.open_file)
            else:
                logger.warning("MainWindow does not have _open_action.")

            if hasattr(self._main_window, "_save_action"):
                # Connect to the controller method that handles save logic
                self._main_window._save_action.triggered.connect(self._file_controller.save_file)
            else:
                logger.warning("MainWindow does not have _save_action.")

            if hasattr(self._main_window, "_save_as_action"):
                # Connect to the controller method that shows the 'Save As' dialog
                self._main_window._save_as_action.triggered.connect(
                    self._file_controller.save_file_as
                )
            else:
                logger.warning("MainWindow does not have _save_as_action.")

            if hasattr(self._main_window, "_validate_action"):
                self._main_window._validate_action.triggered.connect(
                    self._validation_service.validate_data
                )
            else:
                logger.warning("MainWindow does not have _validate_action.")

            if hasattr(self._main_window, "_correct_action"):
                self._main_window._correct_action.triggered.connect(
                    self._correction_controller.apply_corrections
                )
            else:
                logger.warning("MainWindow does not have _correct_action.")

            # MainWindow does not emit preferences_requested directly
            # Preferences are handled by the Settings view/controller
            # self._main_window.preferences_requested.connect(self._show_preferences_dialog)

            # Connect signal emitted by FileOperationsController when a dialog is cancelled
            self._file_controller.file_dialog_canceled.connect(self._on_file_dialog_canceled)

            # Connect DataViewController signals
            self._data_view_controller.status_message_changed.connect(
                self._main_window._on_status_message_changed
            )
            self._data_view_controller.actions_state_changed.connect(
                self._main_window._on_actions_state_changed
            )
            self._data_view_controller.recent_files_updated.connect(
                self._main_window._on_recent_files_changed
            )

            # Connect signals from DataView (via adapter) to controllers
            # Access the adapter from the MainWindow's view dictionary
            data_view_adapter = self._main_window._views.get("Data")
            if data_view_adapter and hasattr(data_view_adapter, "correction_selected"):
                # Connect correction signal from the view/delegate to the CorrectionAdapter's slot
                try:
                    self._signal_manager.safe_connect(
                        data_view_adapter,  # Source: The DataView adapter/wrapper
                        "correction_selected",  # Signal: Emitted by delegate/view when a correction is chosen
                        self._correction_adapter,  # Target: The CorrectionAdapter instance
                        "apply_correction_from_ui",  # Slot: Handles applying the correction via CorrectionService
                    )
                    logger.info(
                        "Connected correction_selected signal from DataView to CorrectionAdapter."
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to connect correction_selected signal to CorrectionAdapter: {e}"
                    )
            else:
                logger.warning(
                    f"Data view adapter not found or missing correction_selected signal. Cannot connect correction signal. Found type: {type(data_view_adapter).__name__ if data_view_adapter else 'None'}"
                )

            # Connect ValidationController signals
            self._validation_service.validation_changed.connect(self._on_validation_changed)
            self._validation_service.status_message_changed.connect(
                self._main_window._on_status_message_changed
            )
            # Comment out the problematic line causing the startup error
            # There's no _settings_controller yet, and we're migrating to the new DataView
            # self._validation_service.validation_preferences_changed.connect(
            #     self._settings_controller.update_validation_preferences
            # )

            # Connect CorrectionController signals
            self._correction_controller.correction_completed.connect(self._on_correction_complete)
            self._correction_controller.status_message_changed.connect(
                self._main_window._on_status_message_changed
            )

            logger.debug("ChestBuddyApp signals connected successfully")

        except AttributeError as e:
            logger.error(f"Error connecting signals: {e}")
            logger.exception(f"Exception: {e}")
            raise CriticalError(f"Error connecting signals: {e}")

    def cleanup(self) -> None:
        """Clean up application resources before exit."""
        try:
            logger.info("Cleaning up application resources")

            # Process pending signals - only invoke if method exists
            try:
                QMetaObject.invokeMethod(
                    self, "_process_pending", Qt.ConnectionType.DirectConnection
                )
            except Exception as e:
                logger.debug(f"Skipping _process_pending: {e}")

            # Disconnect all signals
            self._signal_manager.disconnect_all()

            # Clear the ServiceLocator
            ServiceLocator.clear()

            # If main window exists, close it
            if self._main_window is not None:
                self._main_window.close()

            # Save configuration
            if hasattr(self, "_config_manager"):
                self._config_manager.save()

            # Clean up BackgroundWorker threads
            BackgroundWorker.shutdown()

            logger.info("Application cleanup completed")
        except Exception as e:
            logger.error(f"Error during application cleanup: {e}")

    @Slot()
    def _process_pending(self) -> None:
        """
        Process any pending events before shutdown.
        This method is called during cleanup to ensure all pending events are processed.
        """
        logger.debug("Processing pending events before shutdown")
        # Process any pending events in the event queue
        QApplication.processEvents()

    # ===== Slots =====

    @Slot(str)
    def _on_data_view_error(self, error_message: str) -> None:
        """
        Handle data view error.

        Args:
            error_message (str): Error message
        """
        logger.error(f"Data view error: {error_message}")
        self._error_controller.show_error(error_message, "Data View Error")

    @Slot()
    def _on_load_started(self) -> None:
        """Handle load started signal."""
        logger.info("Load started")

        # Start progress with cancellation callback
        self._progress_controller.start_progress(
            "Loading Data", "Preparing to load data...", True, self._data_manager.cancel_loading
        )

        # Set total files if available
        if hasattr(self._data_manager, "total_files"):
            self._progress_controller.set_total_files(self._data_manager.total_files)

    @Slot(str, int, int)
    def _on_load_progress(self, file_path: str, current: int, total: int) -> None:
        """
        Handle load progress signal.

        Args:
            file_path: Path of the file being processed
            current: Current progress value
            total: Total progress value
        """
        # Use enhanced file progress tracking in the controller
        self._progress_controller.update_file_progress(file_path, current, total)

    @Slot(str)
    def _on_load_finished(self, message: str) -> None:
        """
        Handle load finished signal.

        Args:
            message: Completion message
        """
        logger.info(f"Load finished: {message}")
        is_error = "error" in message.lower() or "failed" in message.lower()

        # First finish the progress with the final message
        self._progress_controller.finish_progress(message, is_error)

        # Wait a brief moment for UI to update before closing
        QTimer.singleShot(1500, self._progress_controller.close_progress)

        # If it was successful, schedule the data table to be populated with minimal delay
        if not is_error and self._main_window:
            QTimer.singleShot(100, self._main_window.populate_data_table)

    @Slot(str)
    def _on_load_error(self, error_message: str) -> None:
        """
        Handle load error signal.

        Args:
            error_message: Error message
        """
        logger.error(f"Load error: {error_message}")
        self._error_controller.show_error(error_message, "Load Error")

    @Slot(str)
    def _on_save_success(self, file_path: str) -> None:
        """
        Handle save success signal.

        Args:
            file_path: Path where the file was saved
        """
        logger.info(f"Save success: {file_path}")
        if self._main_window:
            self._main_window.statusBar().showMessage(f"Saved to {file_path}", 5000)

    @Slot(str)
    def _on_save_error(self, error_message: str) -> None:
        """
        Handle save error signal.

        Args:
            error_message: Error message
        """
        logger.error(f"Save error: {error_message}")
        self._error_controller.show_error(error_message, "Save Error")

    @Slot(list)
    def _on_recent_files_changed(self, recent_files: List[str]) -> None:
        """
        Handle recent files changed signal.

        Args:
            recent_files: List of recent files
        """
        # Update the recent files in the main window
        if self._main_window and hasattr(self._main_window, "set_recent_files"):
            self._main_window.set_recent_files(recent_files)

    @Slot()
    def _on_data_loaded(self) -> None:
        """Handler for data loaded signal."""
        logger.info("App: Data loaded signal received")

    @Slot(object)
    def _on_data_changed(self, data_state=None) -> None:
        """
        Handle data model changes.

        Args:
            data_state: The current DataState object (optional)
        """
        try:
            if data_state:
                has_data = data_state.has_data
            else:
                has_data = not self._data_model.is_empty

            logger.info(f"Data changed event: has_data={has_data}")
        except Exception as e:
            logger.error(f"Error in _on_data_changed: {e}")

    @Slot(object)
    def _update_table_state_from_validation(self, validation_results):
        """
        Update the TableStateManager with validation results.

        Args:
            validation_results: The validation results from the validation service
        """
        if not self._table_state_manager:
            logger.warning("Cannot update table state: TableStateManager not initialized")
            return

        try:
            # First reset all cell states to ensure clean state
            self._table_state_manager.reset_cell_states()
            logger.debug("Reset cell states in TableStateManager")

            # Process validation results if available
            if validation_results is not None:
                # Update the table state based on validation results
                self._table_state_manager.update_cell_states_from_validation(validation_results)
                logger.info(f"Updated TableStateManager with validation results")
            else:
                logger.warning("Validation results are None, skipping table state update")
        except Exception as e:
            logger.error(f"Error updating table state from validation: {e}")

    @Slot()
    def _on_data_cleared(self) -> None:
        """Handler for data cleared signal."""
        logger.info("App: Data model cleared signal received")

    @Slot(str)
    def _on_file_opened(self, path: str) -> None:
        """Handler for file opened signal."""
        logger.info(f"App: File opened signal received: {path}")

    @Slot()
    def _on_progress_canceled(self) -> None:
        """Handler for progress canceled signal."""
        logger.info("App: Progress canceled signal received")

    @Slot(int)
    def _on_table_populated(self, rows: int) -> None:
        """Handler for table populated signal."""
        logger.info(f"App: Table populated with {rows} rows")

    @Slot()
    def _on_file_dialog_canceled(self) -> None:
        """Handle the cancellation of a file dialog shown by FileOperationsController."""
        logger.info("App: File dialog was canceled by the user.")
        # Add any necessary state reset logic here if needed
        # e.g., self._ui_state_controller.set_app_state(AppState.IDLE)

    def get_correction_controller(self):
        """
        Get the correction controller instance.

        Returns:
            CorrectionController: The correction controller or None if not initialized
        """
        return getattr(self, "_correction_controller", None)

    @Slot(object)
    def _on_validation_changed(self, validation_status_df) -> None:
        """Handle validation changed signal from ValidationService."""
        logger.info(
            f"App: Received validation_changed signal. Status DF shape: {validation_status_df.shape if validation_status_df is not None else 'None'}"
        )

    @Slot(object)
    def _on_correction_complete(self, correction_stats):
        """
        Handle correction completion.

        Args:
            correction_stats: Dictionary with correction statistics
        """
        logger.info(f"Corrections completed: {correction_stats}")
        affected_rows = correction_stats.get("corrected_rows", 0)

        # Update status if needed
        status_message = f"Applied corrections to {affected_rows} rows"
        logger.debug(status_message)

        # Trigger validation after correction if auto-validation is enabled
        if (
            hasattr(self._validation_service, "get_auto_validation")
            and self._validation_service.get_auto_validation()
        ):
            logger.info("Auto-validation after correction is enabled, validating data...")
            QTimer.singleShot(100, self._validation_service.validate_data)

    def run(self) -> int:
        """
        Run the application.

        Returns:
            int: Exit code
        """
        # Run the Qt event loop
        app = QApplication.instance()
        return app.exec() if app else 1


def main():
    """Main entry point for the application."""
    try:
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("ChestBuddy")
        app.setOrganizationName("ChestBuddy")
        app.setOrganizationDomain("chestbuddy.org")

        # Create and initialize ChestBuddyApp
        chest_buddy_app = ChestBuddyApp(sys.argv)

        # Connect aboutToQuit signal to cleanup
        app.aboutToQuit.connect(chest_buddy_app.cleanup)

        # Start the event loop
        return chest_buddy_app.run()
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
