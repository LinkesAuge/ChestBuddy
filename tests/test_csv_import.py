"""
test_csv_import.py

Description: Test script for CSV import functionality
Usage:
    python -m tests.test_csv_import
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add project root to path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "tests" / "csv_import_test.log"),
    ],
)

logger = logging.getLogger("csv_import_test")

# Import required modules
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager


def test_csv_import():
    """Test CSV import functionality directly."""
    logger.info("Starting CSV import test")

    # Create Qt application (needed for signals)
    app = QApplication([])

    # Create services and model
    logger.info("Creating services and model")
    csv_service = CSVService()
    data_model = ChestDataModel()
    data_manager = DataManager(data_model, csv_service)

    # Add progress monitoring
    data_manager.load_started.connect(lambda: logger.info("Load started"))
    data_manager.load_progress.connect(
        lambda file_path, current, total: logger.info(
            f"Progress: {file_path or 'Overall'} - {current}/{total} ({int(current / total * 100) if total else 0}%)"
        )
    )
    data_manager.load_success.connect(lambda msg: logger.info(f"Load success: {msg}"))
    data_manager.load_error.connect(lambda msg: logger.error(f"Load error: {msg}"))
    data_manager.load_finished.connect(lambda msg: logger.info(f"Load finished: {msg}"))

    # Find CSV files
    input_dir = project_root / "chestbuddy" / "data" / "input"
    csv_files = list(input_dir.glob("*.csv"))

    if not csv_files:
        logger.error(f"No CSV files found in {input_dir}")
        return

    logger.info(f"Found {len(csv_files)} CSV files: {[f.name for f in csv_files]}")

    # Start import
    try:
        logger.info("Starting CSV import")
        data_manager.load_csv([str(f) for f in csv_files])

        # Process events to allow signals to be delivered
        for _ in range(600):  # Run for up to 60 seconds (100ms checks)
            app.processEvents()
            if not data_manager._worker.is_running:
                logger.info("CSV import completed")
                break
            time.sleep(0.1)

            # Debug output every 10 iterations
            if _ % 100 == 0:
                logger.debug(f"Still waiting for import to complete... ({_ // 10} seconds)")

        # Check result
        if data_manager._worker.is_running:
            logger.warning("CSV import still running after timeout")
            data_manager.cancel_loading()

            # Give it time to cancel properly
            for _ in range(20):  # Wait another 2 seconds
                app.processEvents()
                time.sleep(0.1)

        # Wait a bit to make sure callbacks have completed
        logger.info("Waiting for all callbacks to complete...")
        for _ in range(20):  # Additional 2 second delay
            app.processEvents()
            time.sleep(0.1)

        if data_model.data is not None and not data_model.data.empty:
            row_count = len(data_model.data)
            col_count = len(data_model.data.columns)
            logger.info(f"Data loaded successfully: {row_count} rows, {col_count} columns")
            logger.info(f"Columns: {list(data_model.data.columns)}")
            logger.info(f"First 5 rows: {data_model.data.head(5)}")
        else:
            logger.error("No data loaded")

    except Exception as e:
        logger.exception(f"Error during CSV import: {e}")

    finally:
        # Clean up
        logger.info("Clean-up and shutdown")

        # Ensure worker is properly stopped
        if hasattr(data_manager, "_worker") and data_manager._worker:
            if data_manager._worker.is_running:
                logger.info("Cancelling any running tasks")
                try:
                    data_manager.cancel_loading()

                    # Process events to allow cancellation to complete
                    for _ in range(20):  # 2 seconds
                        app.processEvents()
                        time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error during worker cancellation: {e}")

        # Ensure signals are disconnected
        try:
            logger.info("Disconnecting signals")
            data_manager.load_started.disconnect()
            data_manager.load_progress.disconnect()
            data_manager.load_success.disconnect()
            data_manager.load_error.disconnect()
            data_manager.load_finished.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting signals: {e}")

        # Process events one final time
        app.processEvents()

        # Exit the app
        logger.info("Shutting down application")
        app.quit()

        # Allow time for application to clean up
        time.sleep(1)


if __name__ == "__main__":
    logger.info("CSV Import Test Script")
    test_csv_import()
    logger.info("Test completed")
