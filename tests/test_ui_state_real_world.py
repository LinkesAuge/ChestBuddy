"""
test_ui_state_real_world.py

Description: End-to-end tests for the UI State Management System
focusing on real-world scenarios, especially the first import workflow.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
from PySide6.QtCore import Qt, QTimer, QObject
from PySide6.QtWidgets import QApplication

# Import the MockMainWindow for testing
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow


class MockBackgroundWorker(QObject):
    """Mock BackgroundWorker for testing with necessary signals."""

    def __init__(self):
        super().__init__()
        self.started = MagicMock()
        self.progress = MagicMock()
        self.finished = MagicMock()
        self.success = MagicMock()
        self.error = MagicMock()
        self.cancelled = MagicMock()


@pytest.fixture
def app():
    """Create a QApplication for UI testing."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def test_csv_file():
    """Create a test CSV file with sample data."""
    with tempfile.NamedTemporaryFile(prefix="test_ui_state0", suffix=".csv", delete=False) as f:
        # Write sample data
        f.write(b"id,name,value\n")
        f.write(b"1,Item 1,100\n")
        f.write(b"2,Item 2,200\n")
        f.write(b"3,Item 3,300\n")
        f.write(b"4,Item 4,400\n")
        f.write(b"5,Item 5,500\n")

    yield f.name
    # Clean up the temporary file
    os.unlink(f.name)


@pytest.fixture
def mock_services():
    """Create mock services for the MainWindow."""
    # Create a simple mock data model
    data_model = MagicMock()
    # Manually add required methods
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)

    # Create mock CSV service
    csv_service = MagicMock()

    # Create mock data manager
    data_manager = MagicMock()

    # Add background worker
    data_manager._worker = MockBackgroundWorker()

    # Add MagicMock signals instead of real signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    # Add load_file method to data_manager for our tests
    def load_file(file_path):
        data_manager.load_started.emit()
        data_manager.load_progress.emit("", 50, 100)

        # Get data from csv_service (which will be mocked)
        data = csv_service.read_csv(file_path)

        # Update the model
        data_model.set_data(data)

        # Emit signals for completion
        data_manager.load_finished.emit(True, "File loaded successfully")
        data_manager.load_success.emit(file_path)

    data_manager.load_file = load_file

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "data_manager": data_manager,
    }


class TestFirstImportWorkflow:
    """Tests for the first import workflow with the UI State Management System."""

    def test_first_import_ui_state(self, qtbot, app, mock_services, test_csv_file):
        """
        Test the UI state during and after the first import operation.

        This test simulates the critical first import scenario that previously
        caused UI blocking issues. It verifies that all UI elements are properly
        unblocked after the import completes.
        """
        # Patch the csv_service to return our test data
        mock_services["csv_service"].read_csv.return_value = pd.read_csv(test_csv_file)

        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Capture the initial UI state
        assert main_window.isEnabled(), "MainWindow should be enabled initially"

        # Get references to key UI elements we want to monitor
        data_view = main_window.get_view("data")
        assert data_view is not None, "DataView should exist"

        # Verify data view is initially enabled
        assert data_view.isEnabled(), "DataView should be enabled initially"

        # Keep track of UI state changes
        ui_states = {
            "main_window": [True],  # Initially enabled
            "data_view": [True],  # Initially enabled
        }

        # Create a slot to track UI state during import
        def track_ui_state():
            ui_states["main_window"].append(main_window.isEnabled())
            ui_states["data_view"].append(data_view.isEnabled())

        # Setup tracking timer to check UI state during import
        timer = QTimer()
        timer.timeout.connect(track_ui_state)
        timer.start(100)  # Check every 100ms

        # Flag to track completion
        import_completed = False

        def on_import_complete(*args, **kwargs):
            nonlocal import_completed
            import_completed = True

        # Connect to our mock signal
        mock_services["data_manager"].load_success.emit = on_import_complete

        try:
            # Start the import
            main_window.import_file(test_csv_file)

            # Wait for import to complete
            for _ in range(50):  # Wait up to 5 seconds (50 * 100ms)
                if import_completed:
                    break
                qtbot.wait(100)
                app.processEvents()

            # Verify import completed
            assert import_completed, "Import should have completed"

            # Wait for UI to update
            qtbot.wait(500)
            app.processEvents()
        finally:
            # Stop the timer to prevent accessing deleted Qt objects
            timer.stop()

        # There should be multiple UI state checks
        assert len(ui_states["main_window"]) > 1, "UI state should have been tracked multiple times"

        # Check if UI was blocked during import
        assert False in ui_states["main_window"] or False in ui_states["data_view"], (
            "UI should have been blocked at some point during import"
        )

        # Check final UI state - UI should be unblocked after import
        assert main_window.isEnabled(), "MainWindow should be enabled after import"
        assert data_view.isEnabled(), "DataView should be enabled after import"

        # Verify UI state manager registered operations
        assert main_window.ui_state_manager is not None, "UIStateManager should exist"
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after import"
        )

    def test_import_cancellation(self, qtbot, app, mock_services, test_csv_file):
        """
        Test UI state after cancelling an import operation.

        This test verifies that UI elements are properly unblocked when
        an import operation is cancelled.
        """

        # Make the CSV import take long enough to allow cancellation
        def slow_read_csv(*args, **kwargs):
            # Simulate slow read
            qtbot.wait(500)
            if "progress_callback" in kwargs and kwargs["progress_callback"]:
                kwargs["progress_callback"](50)  # Report 50% progress

            # Return test data
            return pd.read_csv(test_csv_file)

        mock_services["csv_service"].read_csv = MagicMock(side_effect=slow_read_csv)

        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Get references to UI elements
        data_view = main_window.get_view("data")

        # Start the import process
        import_started = False
        import_cancelled = False

        # Simulate import cancellation
        def cancel_import():
            nonlocal import_started, import_cancelled
            import_started = True
            import_cancelled = True
            # Emit cancelled signal from worker
            mock_services["data_manager"]._worker.cancelled.emit()

        # Setup timer to cancel import
        cancel_timer = QTimer()
        cancel_timer.timeout.connect(cancel_import)
        cancel_timer.setSingleShot(True)
        cancel_timer.start(200)  # Cancel after 200ms

        try:
            # Start import
            main_window.import_file(test_csv_file)

            # Wait for cancellation to complete
            for _ in range(20):  # Wait up to 2 seconds
                if import_cancelled:
                    break
                qtbot.wait(100)
                app.processEvents()

            # Wait for processing to complete
            qtbot.wait(1000)
            app.processEvents()
        finally:
            # Make sure timer is stopped
            if cancel_timer.isActive():
                cancel_timer.stop()

        # Verify UI elements are unblocked after cancellation or completion
        assert main_window.isEnabled(), "MainWindow should be enabled after operation"
        assert data_view.isEnabled(), "DataView should be enabled after operation"

        # Verify no active operations
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after operation"
        )

    def test_multiple_imports(self, qtbot, app, mock_services, test_csv_file):
        """
        Test UI state after multiple sequential imports.

        This test verifies that UI elements are properly blocked and unblocked
        during multiple sequential import operations.
        """
        # Patch the csv_service to return our test data
        mock_services["csv_service"].read_csv.return_value = pd.read_csv(test_csv_file)

        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Get references to UI elements
        data_view = main_window.get_view("data")

        # Track operation counts
        operation_counts = []

        # Flag to track completion
        import_completed = False

        def on_import_complete(*args, **kwargs):
            nonlocal import_completed
            import_completed = True

        # Connect to our mock signal
        mock_services["data_manager"].load_success.emit = on_import_complete

        try:
            # Perform multiple imports and check UI state after each
            for i in range(3):
                # Reset import completion flag
                import_completed = False

                # Import file
                main_window.import_file(test_csv_file)

                # Wait for import to complete
                for _ in range(50):  # Wait up to 5 seconds (50 * 100ms)
                    if import_completed:
                        break
                    qtbot.wait(100)
                    app.processEvents()

                # Verify import completed
                assert import_completed, f"Import {i + 1} should have completed"

                # Wait for UI to update
                qtbot.wait(300)
                app.processEvents()

                # Record operation count
                operation_counts.append(len(main_window.ui_state_manager._operations))

                # Verify UI is unblocked after each import
                assert main_window.isEnabled(), f"MainWindow should be enabled after import {i + 1}"
                assert data_view.isEnabled(), f"DataView should be enabled after import {i + 1}"

                # Verify no active operations
                assert len(main_window.ui_state_manager._operations) == 0, (
                    f"No operations should be active after import {i + 1}"
                )

            # Verify operations were cleaned up properly
            assert all(count == 0 for count in operation_counts), (
                "Operation count should be 0 after each import"
            )
        except Exception:
            # Ensure we process events before exiting to avoid Qt warnings
            app.processEvents()
            raise


class TestProgressDialogIntegration:
    """Tests for the progress dialog integration with UI State Management."""

    def test_progress_dialog_cleanup(self, qtbot, app, mock_services, test_csv_file):
        """
        Test that the progress dialog is properly cleaned up after import.

        This test verifies that the progress dialog is properly disposed of
        after the import completes, to prevent memory leaks and UI issues.
        """
        # Patch the csv_service to return our test data
        mock_services["csv_service"].read_csv.return_value = pd.read_csv(test_csv_file)

        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Count progress dialogs before import
        dialog_count_before = 0
        for widget in app.topLevelWidgets():
            if hasattr(widget, "windowTitle") and "Progress" in widget.windowTitle():
                dialog_count_before += 1

        # Flag to track completion
        import_completed = False

        def on_import_complete(*args, **kwargs):
            nonlocal import_completed
            import_completed = True

        # Connect to our mock signal
        mock_services["data_manager"].load_success.emit = on_import_complete

        try:
            # Import file
            main_window.import_file(test_csv_file)

            # Wait for import to complete
            for _ in range(50):  # Wait up to 5 seconds (50 * 100ms)
                if import_completed:
                    break
                qtbot.wait(100)
                app.processEvents()

            # Verify import completed
            assert import_completed, "Import should have completed"

            # Wait for import to complete and UI to update
            qtbot.wait(300)
            app.processEvents()

            # Count progress dialogs after import
            qtbot.wait(500)  # Give some time for dialogs to be cleaned up
            app.processEvents()

            dialog_count_after = 0
            for widget in app.topLevelWidgets():
                if hasattr(widget, "windowTitle") and "Progress" in widget.windowTitle():
                    dialog_count_after += 1

            # Verify no new progress dialogs are left visible
            assert dialog_count_after <= dialog_count_before, (
                "No new progress dialogs should remain after import"
            )

            # Verify UI is unblocked
            assert main_window.isEnabled(), "MainWindow should be enabled after import"
            assert main_window.get_view("data").isEnabled(), (
                "DataView should be enabled after import"
            )
        except Exception:
            # Ensure we process events before exiting to avoid Qt warnings
            app.processEvents()
            raise


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
