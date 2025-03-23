#!/usr/bin/env python3
"""
test_import_flow.py

Description: Automated test script for testing the import flow in ChestBuddy
Usage:
    python test_import_flow.py [--iterations=10] [--sample-data=path/to/data]
"""

import sys
import os
import time
import argparse
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QDialog
from PySide6.QtCore import (
    Qt,
    QTimer,
    QObject,
    QEvent,
    Signal,
    QThread,
    QMetaObject,
    Qt,
    QCoreApplication,
    QEventLoop,
)
from PySide6.QtTest import QTest

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("import_flow_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ImportFlowTest:
    """
    Automated test for the import flow in ChestBuddy.
    Tests multiple imports to identify UI blocking issues.
    """

    def __init__(self, iterations: int = 10, sample_data_path: Optional[str] = None):
        """
        Initialize the import flow test.

        Args:
            iterations: Number of import iterations to run
            sample_data_path: Path to sample data for testing
        """
        self.iterations = iterations
        self.sample_data_path = sample_data_path or self._find_sample_data()

        # Data paths prepared for testing
        self.data_paths = []

        # Test results
        self.results = []

        # Import flow metrics tracking
        self.import_metrics = []

    def _find_sample_data(self) -> str:
        """
        Find sample data files for testing.

        Returns:
            Path to sample data directory
        """
        # Look in various locations
        possible_paths = [
            Path("./sample_data"),
            Path("../sample_data"),
            Path("./tests/sample_data"),
            Path("./data/samples"),
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                return str(path)

        logger.warning("No sample data directory found. Using current directory.")
        return "."

    def _prepare_test_data(self) -> List[str]:
        """
        Prepare test data files for import tests.

        Returns:
            List of data file paths to use for testing
        """
        data_dir = Path(self.sample_data_path)

        # Find all CSV files
        csv_files = list(data_dir.glob("**/*.csv"))

        if not csv_files:
            # If no CSV files, create a simple one for testing
            logger.warning(f"No CSV files found in {data_dir}. Creating a sample file.")
            sample_file = data_dir / "sample_test_data.csv"
            with open(sample_file, "w") as f:
                f.write("Name,Value\n")
                f.write("Test1,100\n")
                f.write("Test2,200\n")
                f.write("Test3,300\n")

            csv_files = [sample_file]

        # Use all found files
        data_paths = [str(f) for f in csv_files]
        logger.info(f"Found {len(data_paths)} data files for testing")

        self.data_paths = data_paths
        return data_paths

    def run_test(self) -> Dict[str, Any]:
        """
        Run the automated import flow test.

        Returns:
            Dictionary of test results
        """
        logger.info(f"Starting import flow test with {self.iterations} iterations")

        # Prepare test data
        self._prepare_test_data()

        # Create and set up application
        app = QApplication(sys.argv)

        # Import the main window directly - you may need to adjust this
        # based on your project structure
        try:
            from chestbuddy.ui.main_window import MainWindow

            # Create the main window
            main_window = MainWindow()
            main_window.show()
        except ImportError:
            logger.error(
                "Failed to import MainWindow. Ensure the script is run from the project root."
            )
            return {"success": False, "error": "Failed to import MainWindow class"}

        # Wait for main window to fully initialize
        QCoreApplication.processEvents()
        time.sleep(1)
        QCoreApplication.processEvents()

        # Run import iterations
        total_success = 0
        import_metrics = []

        for i in range(self.iterations):
            logger.info(f"Starting import iteration {i + 1}/{self.iterations}")

            # Simulate user clicking "Import from file" (you'll need to adjust these for your UI)
            metrics = self._run_single_import(main_window, i)
            import_metrics.append(metrics)

            if metrics.get("success", False):
                total_success += 1

            # Wait between iterations for stability
            time.sleep(2)
            QCoreApplication.processEvents()

        # Calculate results
        success_rate = (total_success / self.iterations) * 100
        logger.info(f"Test complete. Success rate: {success_rate:.1f}%")

        # Store results
        results = {
            "success": True,
            "iterations": self.iterations,
            "success_rate": success_rate,
            "successful_imports": total_success,
            "metrics": import_metrics,
        }

        self.results = results
        return results

    def _run_single_import(self, main_window: QMainWindow, iteration: int) -> Dict[str, Any]:
        """
        Run a single import test cycle.

        Args:
            main_window: The application's main window
            iteration: Current iteration number

        Returns:
            Dictionary with timing metrics and success status
        """
        metrics = {
            "iteration": iteration + 1,
            "success": False,
            "ui_responsive_after": False,
            "data_file": "",
            "timing": {},
        }

        try:
            # Record start time
            start_time = time.time()
            metrics["timing"]["start"] = start_time

            # Choose a data file
            data_file = random.choice(self.data_paths) if self.data_paths else None
            if not data_file:
                raise ValueError("No data files available for testing")

            metrics["data_file"] = data_file

            # Find the "Import" button in Dashboard view
            dashboard_import_button = None

            # Try to find the import button by object name or text
            import_buttons = main_window.findChildren(QPushButton, "import_button")
            if import_buttons:
                dashboard_import_button = import_buttons[0]
            else:
                # Try by text if not found by name
                for button in main_window.findChildren(QPushButton):
                    if button.text() == "Import" or "Import" in button.text():
                        dashboard_import_button = button
                        break

            if not dashboard_import_button:
                raise ValueError("Import button not found in main window")

            # Click the import button
            logger.info(f"Clicking import button")
            QTest.mouseClick(dashboard_import_button, Qt.LeftButton)
            QCoreApplication.processEvents()
            metrics["timing"]["import_button_clicked"] = time.time()

            # Wait for import dialog to appear
            time.sleep(0.5)
            QCoreApplication.processEvents()

            # Find and handle the file import dialog
            # Note: This part would depend on your specific UI flow
            # You might need to adjust this section to match your application's structure

            # Assuming your app will now show a progress dialog
            # Find it by class or name
            progress_dialog = None
            max_attempts = 10
            attempts = 0

            while not progress_dialog and attempts < max_attempts:
                # Look for progress dialog
                for dialog in QApplication.topLevelWidgets():
                    if isinstance(dialog, QDialog) and dialog.isVisible():
                        # This might be our progress dialog
                        if (
                            "Progress" in dialog.objectName()
                            or "progress" in dialog.objectName().lower()
                        ):
                            progress_dialog = dialog
                            break

                if not progress_dialog:
                    QCoreApplication.processEvents()
                    time.sleep(0.2)
                    attempts += 1

            if not progress_dialog:
                raise ValueError("Progress dialog not found after import button click")

            metrics["timing"]["progress_dialog_appeared"] = time.time()

            # Wait for progress dialog to complete
            # Finding the appropriate button to click might require adjustments
            confirm_button = None

            # Wait for the operation to complete
            max_wait_time = 30  # seconds
            wait_start = time.time()

            while time.time() - wait_start < max_wait_time:
                # Process events to keep UI responsive
                QCoreApplication.processEvents()

                # Look for the confirm button (it might appear when operation completes)
                for button in progress_dialog.findChildren(QPushButton):
                    if button.text() in ["Confirm", "Close", "OK", "Done"]:
                        confirm_button = button
                        break

                if confirm_button and confirm_button.isEnabled():
                    break

                time.sleep(0.2)

            metrics["timing"]["import_complete"] = time.time()

            if not confirm_button:
                raise ValueError("Confirm button not found in progress dialog")

            # Click the confirm button
            logger.info(f"Clicking confirm button")
            QTest.mouseClick(confirm_button, Qt.LeftButton)
            QCoreApplication.processEvents()
            metrics["timing"]["confirm_clicked"] = time.time()

            # Wait for dialog to close
            time.sleep(0.5)
            QCoreApplication.processEvents()

            # Check if dialog is still visible
            dialog_closed = not (progress_dialog.isVisible() if progress_dialog else False)
            metrics["dialog_closed"] = dialog_closed

            # Test UI responsiveness
            # Try clicking in the main window and check if it responds
            ui_responsive = self._test_ui_responsiveness(main_window)
            metrics["ui_responsive_after"] = ui_responsive

            # Record end time
            end_time = time.time()
            metrics["timing"]["end"] = end_time
            metrics["total_duration"] = end_time - start_time

            # Mark as successful if everything went as expected
            metrics["success"] = dialog_closed and ui_responsive

            # Log success or failure
            if metrics["success"]:
                logger.info(
                    f"Import test {iteration + 1} successful. Total time: {metrics['total_duration']:.2f}s"
                )
            else:
                logger.warning(
                    f"Import test {iteration + 1} failed. Dialog closed: {dialog_closed}, UI responsive: {ui_responsive}"
                )

        except Exception as e:
            logger.error(f"Error during import test {iteration + 1}: {e}")
            metrics["error"] = str(e)

        return metrics

    def _test_ui_responsiveness(self, main_window: QMainWindow) -> bool:
        """
        Test if the UI is responsive after import.

        Args:
            main_window: The application's main window

        Returns:
            True if UI is responsive, False otherwise
        """
        # Create a test flag to check UI responsiveness
        responsive = False

        # Try clicking in different parts of the window
        try:
            # Process any pending events
            QCoreApplication.processEvents()

            # Try to find interactive elements to test
            # Start with the sidebar or navigation elements
            sidebar_buttons = []

            # Look for buttons or tabs that might be in the sidebar
            for widget in main_window.findChildren(QPushButton):
                # Sidebar buttons are typically visible and enabled
                if widget.isVisible() and widget.isEnabled():
                    sidebar_buttons.append(widget)

            if sidebar_buttons:
                # Try clicking a button
                test_button = sidebar_buttons[0]
                logger.debug(
                    f"Testing UI responsiveness by clicking: {test_button.objectName() or test_button.text()}"
                )
                QTest.mouseClick(test_button, Qt.LeftButton)
                QCoreApplication.processEvents()

                # If we got here without freezing, UI is responsive
                responsive = True
            else:
                # If no buttons found, try clicking in the center of the window
                logger.debug("No suitable buttons found, clicking in center of main window")
                center_x = main_window.width() // 2
                center_y = main_window.height() // 2
                QTest.mouseClick(main_window, Qt.LeftButton, pos=Qt.QPoint(center_x, center_y))
                QCoreApplication.processEvents()

                # If we got here without freezing, UI is responsive
                responsive = True

        except Exception as e:
            logger.error(f"Error testing UI responsiveness: {e}")
            responsive = False

        logger.info(f"UI responsiveness test {'passed' if responsive else 'failed'}")
        return responsive

    def generate_report(self) -> None:
        """Generate a report of the test results."""
        if not self.results:
            logger.warning("No test results to report")
            return

        report = []
        report.append("=" * 50)
        report.append("IMPORT FLOW TEST REPORT")
        report.append("=" * 50)
        report.append(f"Iterations: {self.results['iterations']}")
        report.append(f"Success Rate: {self.results['success_rate']:.1f}%")
        report.append(
            f"Successful Imports: {self.results['successful_imports']}/{self.results['iterations']}"
        )
        report.append("-" * 50)
        report.append("TIMING METRICS (averages in seconds)")

        # Calculate averages for timing metrics
        timing_keys = set()
        for metric in self.results["metrics"]:
            timing_keys.update(metric.get("timing", {}).keys())

        # For each timing key, calculate average
        timing_sums = {key: 0 for key in timing_keys}
        timing_counts = {key: 0 for key in timing_keys}

        for metric in self.results["metrics"]:
            timing = metric.get("timing", {})
            for key, value in timing.items():
                if key in timing_keys:
                    timing_sums[key] += value
                    timing_counts[key] += 1

        # Calculate averages and add to report
        timing_avgs = {}
        for key in timing_keys:
            if timing_counts[key] > 0:
                timing_avgs[key] = timing_sums[key] / timing_counts[key]

        # Create timing report
        first_import = self.results["metrics"][0] if self.results["metrics"] else {}
        subsequent_imports = self.results["metrics"][1:] if len(self.results["metrics"]) > 1 else []

        report.append("First Import vs Subsequent Imports:")
        if first_import and subsequent_imports:
            # Calculate average timing for first import
            first_import_timing = first_import.get("timing", {})

            # Calculate average timing for subsequent imports
            subsequent_timing_sums = {key: 0 for key in timing_keys}
            subsequent_timing_counts = {key: 0 for key in timing_keys}

            for metric in subsequent_imports:
                timing = metric.get("timing", {})
                for key, value in timing.items():
                    if key in timing_keys:
                        subsequent_timing_sums[key] += value
                        subsequent_timing_counts[key] += 1

            subsequent_timing_avgs = {}
            for key in timing_keys:
                if subsequent_timing_counts[key] > 0:
                    subsequent_timing_avgs[key] = (
                        subsequent_timing_sums[key] / subsequent_timing_counts[key]
                    )

            # Calculate and report time differences for each metric
            sorted_keys = sorted([k for k in timing_keys if k != "start" and k != "end"])
            prev_key = "start"

            report.append(f"{'Phase':30} {'First (s)':10} {'Later (s)':10} {'Diff (s)':10}")
            report.append("-" * 65)

            for key in sorted_keys:
                if key in first_import_timing and key in subsequent_timing_avgs:
                    first_time = first_import_timing[key]
                    later_time = subsequent_timing_avgs[key]

                    # Calculate phase duration
                    phase_name = key.replace("_", " ").title()

                    # If we have the previous timing point, calculate phase duration
                    if prev_key in first_import_timing and prev_key in subsequent_timing_avgs:
                        first_phase = first_time - first_import_timing[prev_key]
                        later_phase = later_time - subsequent_timing_avgs[prev_key]
                        diff = first_phase - later_phase

                        report.append(
                            f"{phase_name:30} {first_phase:10.3f} {later_phase:10.3f} {diff:10.3f}"
                        )

                    prev_key = key

            # Total duration comparison
            if "total_duration" in first_import and subsequent_imports:
                first_total = first_import["total_duration"]
                later_total_avg = sum(m["total_duration"] for m in subsequent_imports) / len(
                    subsequent_imports
                )
                diff = first_total - later_total_avg

                report.append("-" * 65)
                report.append(
                    f"{'Total Duration':30} {first_total:10.3f} {later_total_avg:10.3f} {diff:10.3f}"
                )
        else:
            report.append("Insufficient data to compare first and subsequent imports")

        report.append("-" * 50)
        report.append("UI RESPONSIVENESS")

        # Report UI responsiveness
        first_responsive = first_import.get("ui_responsive_after", False) if first_import else False
        subsequent_responsive_count = sum(
            1 for m in subsequent_imports if m.get("ui_responsive_after", False)
        )
        subsequent_responsive_rate = (
            (subsequent_responsive_count / len(subsequent_imports)) * 100
            if subsequent_imports
            else 0
        )

        report.append(f"First Import UI Responsive: {'Yes' if first_responsive else 'No'}")
        report.append(f"Subsequent Imports UI Responsive Rate: {subsequent_responsive_rate:.1f}%")

        report.append("-" * 50)
        report.append("DETAILED RESULTS BY ITERATION")

        for i, metric in enumerate(self.results["metrics"]):
            report.append(f"Iteration {i + 1}:")
            report.append(f"  Success: {'Yes' if metric.get('success', False) else 'No'}")
            report.append(
                f"  UI Responsive: {'Yes' if metric.get('ui_responsive_after', False) else 'No'}"
            )
            report.append(f"  Duration: {metric.get('total_duration', 0):.2f}s")
            if "error" in metric:
                report.append(f"  Error: {metric['error']}")
            report.append("")

        # Write report to file
        with open("import_flow_test_report.txt", "w") as f:
            f.write("\n".join(report))

        logger.info(f"Test report written to import_flow_test_report.txt")

        # Print summary to console
        print("\n".join(report[:10]))
        print("...")
        print("\n".join(report[-5:]))


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test the import flow in ChestBuddy")
    parser.add_argument(
        "--iterations", type=int, default=5, help="Number of import iterations to run"
    )
    parser.add_argument(
        "--sample-data", type=str, default=None, help="Path to sample data for testing"
    )

    args = parser.parse_args()

    test = ImportFlowTest(iterations=args.iterations, sample_data_path=args.sample_data)

    try:
        results = test.run_test()
        test.generate_report()

        if results["success"]:
            print(f"Test completed with {results['success_rate']:.1f}% success rate")
            return 0
        else:
            print(f"Test failed: {results.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
