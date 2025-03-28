import logging
import sys
from typing import List, Optional
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt, QMetaObject

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.controllers.error_handling_controller import ErrorHandlingController
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.resources.style import apply_application_style
from chestbuddy.ui.resources.resource_manager import ResourceManager
from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


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

            # Create controllers - create error controller early
            self._error_controller = ErrorHandlingController()

            # Create services
            try:
                self._csv_service = CSVService()
                self._validation_service = ValidationService(self._data_model)
                self._correction_service = CorrectionService(self._data_model)
                self._chart_service = ChartService(self._data_model)
                self._data_manager = DataManager(self._data_model, self._csv_service)

                # Initialize DataManager with config_manager
                self._data_manager._config = self._config_manager
            except Exception as e:
                logger.error(f"Error initializing services: {e}")
                self._error_controller.handle_exception(e, "Error initializing services")
                raise

            # Create remaining controllers
            try:
                self._file_controller = FileOperationsController(
                    self._data_manager, self._config_manager
                )
                self._progress_controller = ProgressController()
                self._view_state_controller = ViewStateController(self._data_model)
                self._data_view_controller = DataViewController(self._data_model)
                self._ui_state_controller = UIStateController()
            except Exception as e:
                logger.error(f"Error initializing controllers: {e}")
                self._error_controller.handle_exception(e, "Error initializing controllers")
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
            # Create logs directory if it doesn't exist
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # Set up file handler
            log_file = log_dir / "chestbuddy.log"
            file_handler = logging.FileHandler(log_file)
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

            logger.info("Logging initialized")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            # Continue without logging

    def _create_ui(self) -> None:
        """Create the user interface."""
        try:
            # Create main window
            self._main_window = MainWindow(
                self._data_model,
                self._csv_service,
                self._validation_service,
                self._correction_service,
                self._chart_service,
                self._data_manager,
                self._file_controller,
                self._progress_controller,
                self._view_state_controller,
                self._data_view_controller,
                self._ui_state_controller,
            )

            # Show the main window
            self._main_window.show()

            logger.info("UI created and shown")
        except Exception as e:
            logger.critical(f"Failed to create UI: {e}")
            self._error_controller.handle_exception(e, "Failed to create UI")
            sys.exit(1)

    def _connect_signals(self) -> None:
        """Connect signals between components using SignalManager."""
        try:
            logger.info("Connecting application signals...")
            
            # Connect DataManager signals to app-level handlers
            logger.debug("Connecting DataManager signals...")
            self._signal_manager.connect(
                self._data_manager, "load_started",
                self, "_on_load_started"
            )
            self._signal_manager.connect(
                self._data_manager, "load_progress",
                self, "_on_load_progress"
            )
            self._signal_manager.connect(
                self._data_manager, "load_finished",
                self, "_on_load_finished"
            )
            self._signal_manager.connect(
                self._data_manager, "load_error",
                self, "_on_load_error"
            )
            self._signal_manager.connect(
                self._data_manager, "save_success",
                self, "_on_save_success"
            )
            self._signal_manager.connect(
                self._data_manager, "save_error",
                self, "_on_save_error"
            )
            
            # Add connections for data loading state changes
            logger.debug("Connecting data state signals...")
            self._signal_manager.connect(
                self._data_manager, "data_loaded",
                lambda: logger.info("App: Data loaded signal received")
            )
            
            # Connect directly to data model to track changes
            if hasattr(self._data_model, "data_changed"):
                logger.debug("Connecting data model signals...")
                self._signal_manager.connect(
                    self._data_model, "data_changed",
                    lambda: logger.info("App: Data model changed signal received")
                )
                self._signal_manager.connect(
                    self._data_model, "data_cleared",
                    lambda: logger.info("App: Data model cleared signal received")
                )
            
            # Connect FileOperationsController signals
            logger.debug("Connecting FileOperationsController signals...")
            self._signal_manager.connect(
                self._file_controller, "load_csv_triggered",
                self._data_manager, "load_csv"
            )
            self._signal_manager.connect(
                self._file_controller, "save_csv_triggered",
                self._data_manager, "save_csv"
            )
            self._signal_manager.connect(
                self._file_controller, "recent_files_changed",
                self, "_on_recent_files_changed"
            )
            
            # Connect MainWindow signals for file operations
            if hasattr(self._main_window, "file_opened"):
                logger.debug("Connecting MainWindow file operation signals...")
                self._signal_manager.connect(
                    self._main_window, "file_opened",
                    lambda path: logger.info(f"App: File opened signal received: {path}")
                )
            
            # Connect ProgressController signals
            logger.debug("Connecting ProgressController signals...")
            self._signal_manager.connect(
                self._progress_controller, "progress_canceled",
                self._data_manager, "cancel_loading"
            )
            
            # Connect cancellation signals bidirectionally
            self._signal_manager.connect(
                self._progress_controller, "progress_canceled",
                lambda: logger.info("App: Progress canceled signal received")
            )
            
            # Connect DataViewController signals
            logger.debug("Connecting DataViewController signals...")
            self._signal_manager.connect(
                self._data_view_controller, "operation_error",
                self, "_on_data_view_error"
            )
            self._signal_manager.connect(
                self._data_view_controller, "table_populated",
                lambda rows: logger.info(f"App: Table populated with {rows} rows")
            )
            
            logger.info("All signals connected successfully")
            
            # In debug mode, print all connections
            if __debug__:
                logger.debug("Signal connections summary:")
                self._signal_manager.print_connections()
                
        except Exception as e:
            logger.critical(f"Failed to connect signals: {e}", exc_info=True)
            self._error_controller.handle_exception(e, "Failed to connect signals")
            sys.exit(1)
    
    def cleanup(self) -> None:
        """
        Clean up resources before application exit.
        
        This method disconnects all signal connections to prevent
        signals firing during shutdown.
        """
        try:
            # Disconnect all signals
            logger.info("Disconnecting all signals...")
            count = self._signal_manager.disconnect_all()
            logger.info(f"Disconnected {count} signal connections")
            
            # Add other cleanup as needed
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

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

        # If it was successful, schedule the data table to be populated
        if not is_error and self._main_window:
            QTimer.singleShot(2000, self._main_window.populate_data_table)

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
        return app.exec()
    except Exception as e:
        print(f"Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())