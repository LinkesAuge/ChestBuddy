"""
ChestBuddy application main entry point.

This module provides the main ChestBuddy application class that initializes
all services and UI components.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Qt

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CSVService, ValidationService, CorrectionService, ChartService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.background_processing import BackgroundWorker
from chestbuddy.ui.resources.style import apply_application_style
from chestbuddy.ui.resources.resource_manager import ResourceManager

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
        - Connects signals between services and UI components
        - Handles application-level events
    """

    def __init__(self, args: List[str] = None) -> None:
        """
        Initialize the ChestBuddy application.

        Args:
            args: Command-line arguments passed to the application.
        """
        super().__init__()

        # Initialize config manager
        self._config = ConfigManager()

        # Initialize logging
        self._init_logging()

        # Initialize QApplication with args
        self._app = QApplication(args if args is not None else sys.argv)
        self._app.setApplicationName("Chest Buddy")
        self._app.setApplicationVersion("0.1.0")
        self._app.setOrganizationName("ChestBuddy")
        self._app.setOrganizationDomain("chestbuddy.org")

        # Initialize models
        self._data_model = ChestDataModel()

        # Initialize services
        self._csv_service = CSVService()
        self._validation_service = ValidationService(self._data_model)
        self._correction_service = CorrectionService(self._data_model)
        self._chart_service = ChartService(self._data_model)

        # Initialize background worker
        self._worker = BackgroundWorker()

        # Initialize UI
        self._main_window = MainWindow(
            self._data_model,
            self._csv_service,
            self._validation_service,
            self._correction_service,
            self._chart_service,
        )

        # Connect signals
        self._connect_signals()

        # Set up periodic autosave
        self._setup_autosave()

        # Initialize resources
        ResourceManager.initialize()

        # Apply application style
        apply_application_style(self._app)

        logger.info("ChestBuddy application initialized")

    def _init_logging(self) -> None:
        """Initialize the logging system."""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Set up logging configuration
        log_level = self._config.get("Logging", "level", "INFO")
        log_file = logs_dir / "chestbuddy.log"

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        logger.info(f"Logging initialized at level {log_level}")

    def _connect_signals(self) -> None:
        """Connect signals between services and UI components."""
        # Connect application shutdown signal
        self._app.aboutToQuit.connect(self._on_shutdown)

        # Connect main window signals
        self._main_window.load_csv_triggered.connect(self._load_csv)
        self._main_window.save_csv_triggered.connect(self._save_csv)
        self._main_window.validate_data_triggered.connect(self._validate_data)
        self._main_window.apply_corrections_triggered.connect(self._apply_corrections)
        self._main_window.export_validation_issues_triggered.connect(self._export_validation_issues)

        # Connect data model signals
        self._data_model.data_changed.connect(self._on_data_changed)

        # Connect background worker signals
        self._worker.task_completed.connect(self._on_background_task_completed)
        self._worker.task_failed.connect(self._on_background_task_failed)

    def _setup_autosave(self) -> None:
        """Set up periodic autosave functionality."""
        # Check if autosave is enabled
        if self._config.get_bool("Autosave", "enabled", True):
            interval = self._config.get_int("Autosave", "interval_minutes", 5)

            # Convert minutes to milliseconds
            interval_ms = interval * 60 * 1000

            # Create autosave timer
            self._autosave_timer = QTimer(self._app)
            self._autosave_timer.timeout.connect(self._on_autosave)
            self._autosave_timer.start(interval_ms)

            logger.info(f"Autosave enabled with interval of {interval} minutes")

    def _on_autosave(self) -> None:
        """Handle autosave timer timeout."""
        if self._data_model.is_empty:
            logger.debug("Autosave skipped: No data in model")
            return

        # Get the last autosave path or use a default
        autosave_path = self._config.get_path("Autosave", "path", Path("data") / "autosave.csv")

        # Create parent directory if it doesn't exist
        autosave_path.parent.mkdir(exist_ok=True)

        # Save the data
        self._csv_service.save_csv(autosave_path)
        logger.info(f"Autosave completed to {autosave_path}")

    def _on_shutdown(self) -> None:
        """Handle application shutdown."""
        # Save any unsaved work
        if not self._data_model.is_empty:
            self._on_autosave()

        # Save configuration
        self._config.save()

        logger.info("Application shutdown")

    def _load_csv(self, file_path):
        """
        Load a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        logger.info(f"Loading CSV file: {file_path}")

        # Add the file to the list of recent files
        recent_files = self._config.get_list("Files", "recent_files", [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        # Keep only the 5 most recent files
        recent_files = recent_files[:5]
        self._config.set_list("Files", "recent_files", recent_files)
        self._config.set("Files", "last_file", file_path)
        self._config.set_path("Files", "last_directory", os.path.dirname(file_path))

        # Temporarily disconnect data_changed signals during import to prevent cascading updates
        self._data_model.blockSignals(True)
        try:
            # Use the background worker to load the file
            self._worker.run_task(
                self._csv_service.read_csv,
                file_path,
                task_id="load_csv",
                on_success=self._on_csv_load_success,
            )
        except Exception as e:
            # Ensure signals are unblocked even if an error occurs
            self._data_model.blockSignals(False)
            logger.error(f"Error during CSV import: {e}")
            self._show_error(f"Error loading file: {str(e)}")

    def _on_csv_load_success(self, result):
        """Handle successful CSV load."""
        try:
            df, error = result
            if df is not None:
                # Update the data model with signals blocked
                self._data_model.update_data(df)
                logger.info(f"CSV file loaded successfully with {len(df)} rows")
            else:
                self._show_error(f"Error loading file: {error}")
        finally:
            # Always unblock signals when done
            self._data_model.blockSignals(False)
            # Emit one controlled data_changed signal
            self._data_model.data_changed.emit()

    def _save_csv(self, file_path):
        """
        Save a CSV file.

        Args:
            file_path (str): Path to save the CSV file.
        """
        logger.info(f"Saving CSV file: {file_path}")

        # Get the dataframe from the model
        df = self._data_model.data

        # Use the background worker to save the file
        self._worker.run_task(self._csv_service.save_csv, df, file_path, task_id="save_csv")

    def _validate_data(self):
        """Validate the data in the model."""
        logger.info("Validating data")

        # Get the dataframe from the model
        df = self._data_model.data

        # Use the background worker to validate the data
        self._worker.run_task(
            self._validation_service.validate_data,
            df,
            task_id="validate_data",
            on_success=lambda issues: self._data_model.set_validation_status(issues),
        )

    def _apply_corrections(self):
        """Apply corrections to the data."""
        logger.info("Applying corrections")

        # Get the dataframe from the model
        df = self._data_model.data

        # Use the background worker to apply corrections
        self._worker.run_task(
            self._correction_service.apply_corrections,
            df,
            task_id="apply_corrections",
            on_success=lambda df: self._data_model.update_data(df),
        )

    def _export_validation_issues(self, file_path):
        """
        Export validation issues to a file.

        Args:
            file_path (str): Path to save the validation issues.
        """
        logger.info(f"Exporting validation issues: {file_path}")

        # Get the validation issues from the model
        issues = self._data_model.get_validation_status()

        # Use the background worker to export the issues
        self._worker.run_task(
            self._validation_service.export_issues,
            issues,
            file_path,
            task_id="export_issues",
        )

    def _on_data_changed(self):
        """Handle data changed events from the model."""
        try:
            # Use simple string without formatting to avoid potential recursion
            logging.getLogger("chestbuddy.app").info("Data model changed")
        except RecursionError:
            # If we encounter a recursion error in logging, silently ignore it
            pass
        except Exception:
            # For any other exception, also silently continue
            pass

    def _on_background_task_completed(self, task_id, result):
        """Handle background task completion."""
        logger.info(f"Background task completed: {task_id}")

    def _on_background_task_failed(self, task_id, error):
        """Handle background task failure."""
        logger.error(f"Background task failed: {task_id}, error: {error}")

    def _show_error(self, message: str) -> None:
        """
        Show an error message to the user.

        Args:
            message: The error message to display.
        """
        logger.error(message)
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, "Error", message)

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code.
        """
        # Show the main window
        self._main_window.show()

        # Check for initial file to load from command-line args
        file_to_load = self._parse_args()
        if file_to_load:
            self._load_csv(file_to_load)

        # Enter main event loop
        logger.info("Starting application main event loop")
        return self._app.exec()

    def _parse_args(self) -> Optional[Path]:
        """
        Parse command-line arguments.

        Returns:
            Path to file to load, if specified, otherwise None.
        """
        args = self._app.arguments()
        if len(args) > 1:
            file_path = Path(args[1])
            if file_path.exists() and file_path.suffix.lower() == ".csv":
                return file_path
        return None


def main():
    """Main entry point for the ChestBuddy application."""
    # Initialize and run the application
    app = ChestBuddyApp()
    exit_code = app.run()

    # Return exit code to OS
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
