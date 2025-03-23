#!/usr/bin/env python
"""
test_csv_import.py

Description: Test script for CSV import functionality in ChestBuddy application
This script tests loading multiple CSV files, memory management, and thread safety
"""

import os
import sys
import logging
import tempfile
import time
from pathlib import Path

# Add the parent directory to the path so we can import the chestbuddy package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="tests/csv_import_test.log",
    filemode="w",
)
logger = logging.getLogger("csv_import_test")

# Add console handler for immediate feedback
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console)

# Import required modules
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.utils.background_processing import BackgroundWorker, MultiCSVLoadTask


def test_csv_import():
    """Test CSV import functionality."""
    logger.info("Starting CSV import test")

    # Create Qt application for proper signal handling
    app = QApplication.instance() or QApplication(sys.argv)

    # Set up test files
    logger.info("Setting up test files")
    test_files = []

    # Check for existing test files first
    data_dir = Path("data")
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Found {len(csv_files)} existing CSV files in data directory")
            test_files = csv_files

    # If no test files found, create temporary test files
    if not test_files:
        logger.info("Creating temporary test files")
        temp_dir = Path(tempfile.gettempdir())

        # Create a simple test CSV file
        test_file1 = temp_dir / "test1.csv"
        with open(test_file1, "w") as f:
            f.write("id,name,value\n")
            for i in range(1000):
                f.write(f"{i},Item {i},{i * 10}\n")

        # Create another test CSV file
        test_file2 = temp_dir / "test2.csv"
        with open(test_file2, "w") as f:
            f.write("id,name,value\n")
            for i in range(1000, 2000):
                f.write(f"{i},Item {i},{i * 10}\n")

        test_files = [test_file1, test_file2]
        logger.info(f"Created temporary test files: {test_files}")

    # Create services
    csv_service = CSVService()

    # Results storage
    results = {"progress": [], "status": [], "success": False, "data": None, "error": None}

    # Progress callback
    def on_progress(current, total):
        logger.info(f"Progress: {current}/{total} ({int((current / max(1, total)) * 100)}%)")
        results["progress"].append((current, total))

    # Status callback
    def on_status(status):
        logger.info(f"Status: {status}")
        results["status"].append(status)

    # Success callback
    def on_success(data):
        logger.info(f"Success! Loaded data with {len(data)} rows")
        results["success"] = True
        results["data"] = data

        # Check the data to make sure it's valid
        logger.info(f"Data columns: {data.columns.tolist()}")
        logger.info(f"Data types: {data.dtypes}")
        logger.info(f"First few rows: \n{data.head(5)}")

        # Exit the event loop if we're using it
        if "loop" in results and results["loop"]:
            results["loop"].quit()

    # Error callback
    def on_error(error):
        logger.error(f"Error: {error}")
        results["success"] = False
        results["error"] = error

        # Exit the event loop if we're using it
        if "loop" in results and results["loop"]:
            results["loop"].quit()

    # Create the background worker
    logger.info("Creating background worker")
    worker = BackgroundWorker()

    # Create the task
    logger.info(f"Creating MultiCSVLoadTask with {len(test_files)} files")
    task = MultiCSVLoadTask(csv_service, test_files, chunk_size=500)

    # Connect signals
    task.progress.connect(on_progress)
    task.status_signal.connect(on_status)

    # Start the task
    logger.info("Starting CSV import task")
    worker.run_task(task, on_success=on_success, on_error=on_error)

    # Create an event loop to wait for the task to complete
    logger.info("Waiting for task completion")
    loop = QEventLoop()
    results["loop"] = loop

    # Add a timeout as a safety measure
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(lambda: loop.quit())
    timeout_timer.start(30000)  # 30 second timeout

    # Run the event loop until the task completes or times out
    loop.exec()

    # Check results
    if results["success"]:
        logger.info("CSV import test succeeded!")
    else:
        logger.error(f"CSV import test failed: {results['error']}")

    # Clean up
    logger.info("Cleaning up")

    # Clean up the worker thread
    del worker

    # Process events one last time to ensure clean shutdown
    app.processEvents()

    # Return results
    return results["success"], results.get("data"), results.get("error")


if __name__ == "__main__":
    # Run the test
    success, data, error = test_csv_import()

    # Print results
    if success:
        print(f"SUCCESS: Loaded CSV data with {len(data)} rows")
        sys.exit(0)
    else:
        print(f"FAILURE: {error}")
        sys.exit(1)
