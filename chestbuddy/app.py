"""
ChestBuddy application main entry point.

This module provides the main ChestBuddy application class that initializes
all services and UI components.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CSVService, ValidationService, CorrectionService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class ChestBuddyApp:
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
        # Initialize config manager
        self._config = ConfigManager()

        # Initialize logging
        self._init_logging()

        # Initialize QApplication with args
        self._app = QApplication(args if args is not None else sys.argv)
        self._app.setApplicationName("Chest Buddy")
        self._app.setApplicationVersion("0.1.0")

        # Initialize models
        self._data_model = ChestDataModel()

        # Initialize services
        self._csv_service = CSVService(self._data_model)
        self._validation_service = ValidationService(self._data_model)
        self._correction_service = CorrectionService(self._data_model)

        # Initialize UI
        self._main_window = MainWindow(
            self._data_model, self._csv_service, self._validation_service, self._correction_service
        )

        # Connect signals
        self._connect_signals()

        # Set up periodic autosave
        self._setup_autosave()

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
            self._csv_service.load_csv(file_to_load)

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
