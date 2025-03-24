"""
test_ui_state_thread_safety.py

Description: Tests for thread safety in the UI State Management System,
focusing on concurrent operations and background worker integration.
"""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the mock main window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow, MockBackgroundWorker

# Import the UI state management components
from chestbuddy.utils.ui_state import (
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
)


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
def test_csv_file(tmp_path):
    """Create a test CSV file with sample data."""
    file_path = tmp_path / "test_data.csv"
    with open(file_path, "w") as f:
        # Write header
        f.write("id,name,value\n")
        # Write some data
        f.write("1,Item 1,100\n")
        f.write("2,Item 2,200\n")
        f.write("3,Item 3,300\n")
    return file_path


@pytest.fixture
def mock_services():
    """Create standard mock services."""
    # Create a simple mock data model
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)

    # Create mock CSV service
    csv_service = MagicMock()

    # Create mock data manager with background worker
    data_manager = MagicMock()
    data_manager._worker = MockBackgroundWorker()

    # Add the necessary signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "data_manager": data_manager,
    }


@pytest.fixture
def concurrent_workers():
    """Create workers for running concurrent operations."""
    workers = []
    for i in range(5):  # Create 5 workers
        worker = MockBackgroundWorker()
        workers.append(worker)
    return workers


@pytest.fixture
def threaded_mock_main_window(qtbot, mock_services, concurrent_workers):
    """Set up a main window with threading capabilities."""
    # Create the main window
    main_window = MockMainWindow(services=mock_services)
    qtbot.addWidget(main_window)

    # Add workers to the main window
    main_window.workers = concurrent_workers

    # Add method to run concurrent operations
    def run_concurrent_operations(operation_count=5):
        """Run multiple operations concurrently."""
        results = []

        # Create a signal to notify when all operations complete
        all_done = [False]
        completed_count = [0]

        def on_operation_complete(success):
            results.append(success)
            completed_count[0] += 1
            if completed_count[0] >= operation_count:
                all_done[0] = True

        # Start concurrent operations
        for i in range(operation_count):
            # Create a unique operation type
            operation_type = getattr(UIOperations, f"OPERATION_{i + 1}", UIOperations.IMPORT)

            # Start the operation in a new thread
            def worker_thread(idx):
                # Thread function that manages the operation context
                try:
                    # Create and enter the context
                    # We can't use 'with' statement here because it needs to be in the thread
                    ctx = OperationContext(
                        main_window.ui_state_manager, operation_type, [main_window]
                    )

                    # Enter the context
                    ctx.__enter__()
                    try:
                        # Simulate work
                        time.sleep(0.1 + (idx * 0.05))  # Slightly different times
                        # Signal success
                        on_operation_complete(True)
                    finally:
                        # Exit the context (important for cleanup)
                        ctx.__exit__(None, None, None)
                except Exception as e:
                    print(f"Thread error: {e}")
                    on_operation_complete(False)

            # Create and start the thread
            thread = threading.Thread(target=worker_thread, args=(i,))
            thread.daemon = True
            thread.start()

        # Wait for all operations to complete or timeout
        wait_start = time.time()
        max_wait = 10.0  # Maximum wait time in seconds

        while not all_done[0] and time.time() - wait_start < max_wait:
            # Process events while waiting
            QApplication.processEvents()
            time.sleep(0.1)

        # Check if we timed out
        if not all_done[0]:
            print(
                f"Timed out waiting for operations to complete. Completed: {completed_count[0]}/{operation_count}"
            )

        return all_done[0], results

    main_window.run_concurrent_operations = run_concurrent_operations

    # Add method for background worker operation
    def import_with_background_worker(file_path):
        """Import a file using a background worker."""
        # Create an operation context
        with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
            # Start the import
            main_window.import_started.emit()

            # Use a separate thread for the import
            def import_thread():
                try:
                    # Simulate work
                    time.sleep(0.5)

                    # Emit progress updates
                    mock_services["data_manager"].load_progress.emit(50, "Loading data...")

                    # Simulate more work
                    time.sleep(0.5)

                    # Complete import
                    mock_services["data_manager"].load_finished.emit(True, "Import completed")
                    mock_services["data_manager"].load_success.emit(file_path)
                except Exception as e:
                    # Handle error
                    mock_services["data_manager"].load_error.emit(str(e))
                    mock_services["data_manager"].load_finished.emit(False, str(e))

            # Create and start thread
            thread = threading.Thread(target=import_thread)
            thread.daemon = True
            thread.start()

            # Return reference to the thread for test control
            return thread

    main_window.import_with_background_worker = import_with_background_worker

    return main_window


class TestThreadSafety:
    """Tests for thread safety in the UI State Management System."""

    def test_concurrent_operations(self, qtbot, app, threaded_mock_main_window):
        """
        Test UI state with concurrent operations.

        This test verifies that multiple operations running concurrently
        properly manage UI state without race conditions.
        """
        # Get the main window
        main_window = threaded_mock_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Run concurrent operations
        all_completed, results = main_window.run_concurrent_operations(operation_count=5)

        # Verify all operations completed
        assert all_completed, "All operations should have completed"
        assert len(results) == 5, "Should have 5 operation results"
        assert all(results), "All operations should have succeeded"

        # Verify UI state after concurrent operations
        assert main_window.isEnabled(), "MainWindow should be enabled after all operations"
        assert data_view.isEnabled(), "DataView should be enabled after all operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_background_worker_integration(
        self, qtbot, app, threaded_mock_main_window, test_csv_file
    ):
        """
        Test integration between background workers and UI state.

        This test verifies that background workers properly interact with
        the UI State Management System.
        """
        # Get the main window
        main_window = threaded_mock_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # UI should be enabled initially
        assert main_window.isEnabled(), "MainWindow should be enabled initially"
        assert data_view.isEnabled(), "DataView should be enabled initially"

        # Start import with background worker
        import_thread = main_window.import_with_background_worker(test_csv_file)

        # Wait briefly for the operation to start
        qtbot.wait(100)
        app.processEvents()

        # UI should be blocked during import
        assert not main_window.isEnabled(), "MainWindow should be blocked during import"

        # Wait for import to complete
        import_thread.join(timeout=5.0)  # Wait up to 5 seconds

        # Process events to ensure signals are handled
        qtbot.wait(500)
        app.processEvents()

        # UI should be unblocked after import completes
        assert main_window.isEnabled(), "MainWindow should be enabled after import"
        assert data_view.isEnabled(), "DataView should be enabled after import"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_mutex_locking(self, qtbot, app, threaded_mock_main_window):
        """
        Test mutex locking in the UI State Management System.

        This test verifies that the mutex properly protects the UI state manager
        from race conditions.
        """
        # Get the main window
        main_window = threaded_mock_main_window
        main_window.show()

        # Track start and end calls to test for race conditions
        operation_starts = []
        operation_ends = []
        original_start = main_window.ui_state_manager.start_operation
        original_end = main_window.ui_state_manager.end_operation

        # Patch the methods to track calls
        def track_start_operation(*args, **kwargs):
            operation_starts.append(time.time())
            return original_start(*args, **kwargs)

        def track_end_operation(*args, **kwargs):
            operation_ends.append(time.time())
            return original_end(*args, **kwargs)

        main_window.ui_state_manager.start_operation = track_start_operation
        main_window.ui_state_manager.end_operation = track_end_operation

        try:
            # Run operations with high concurrency to increase chance of race conditions
            all_completed, results = main_window.run_concurrent_operations(operation_count=10)

            # Verify operations completed
            assert all_completed, "All operations should have completed"

            # Verify we recorded the expected number of operations
            assert len(operation_starts) == 10, "Should have recorded 10 operation starts"
            assert len(operation_ends) == 10, "Should have recorded 10 operation ends"

            # Verify UI state after operations
            assert main_window.isEnabled(), "MainWindow should be enabled after operations"

            # No operations should be active
            assert len(main_window.ui_state_manager._operations) == 0, (
                "No operations should be active"
            )
        finally:
            # Restore original methods
            main_window.ui_state_manager.start_operation = original_start
            main_window.ui_state_manager.end_operation = original_end

    def test_operation_cancel_from_thread(
        self, qtbot, app, threaded_mock_main_window, test_csv_file
    ):
        """
        Test canceling operations from a separate thread.

        This test verifies that operations can be properly canceled from
        a separate thread without causing deadlocks or race conditions.
        """
        # Get the main window
        main_window = threaded_mock_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Create a long-running operation with cancellation
        def import_with_cancellation():
            # Operation context
            context = OperationContext(
                main_window.ui_state_manager, UIOperations.IMPORT, [main_window, data_view]
            )

            # Enter the context
            context.__enter__()

            # Start a separate thread to cancel the operation
            def cancel_thread():
                # Wait a bit before canceling
                time.sleep(0.3)

                # End the operation
                main_window.ui_state_manager.end_operation(UIOperations.IMPORT)

                # Emit cancellation signal
                if "data_manager" in main_window.services:
                    if hasattr(main_window.services["data_manager"], "_worker"):
                        worker = main_window.services["data_manager"]._worker
                        if hasattr(worker, "cancelled"):
                            worker.cancelled.emit()

            # Start the cancellation thread
            cancel_thread = threading.Thread(target=cancel_thread)
            cancel_thread.daemon = True
            cancel_thread.start()

            # Wait longer than the cancel thread, but the operation should
            # be canceled before this completes
            time.sleep(1.0)

            # Exit the context (should be a no-op since the operation was already ended)
            context.__exit__(None, None, None)

        # Run the operation in a separate thread
        import_thread = threading.Thread(target=import_with_cancellation)
        import_thread.daemon = True
        import_thread.start()

        # UI should be blocked during operation
        qtbot.wait(100)
        app.processEvents()
        assert not main_window.isEnabled(), "MainWindow should be blocked during operation"

        # Wait for cancellation to take effect
        import_thread.join(timeout=2.0)
        qtbot.wait(500)
        app.processEvents()

        # UI should be unblocked after cancellation
        assert main_window.isEnabled(), "MainWindow should be enabled after cancellation"
        assert data_view.isEnabled(), "DataView should be enabled after cancellation"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_thread_safe_reference_counting(self, qtbot, app, threaded_mock_main_window):
        """
        Test thread-safe reference counting in nested operations.

        This test verifies that reference counting works correctly when operations
        are started and ended from different threads.
        """
        # Get the main window
        main_window = threaded_mock_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Track contexts to ensure proper cleanup
        contexts = []

        # Create nested operations across threads
        def outer_operation():
            # Start outer operation
            outer_ctx = OperationContext(
                main_window.ui_state_manager, UIOperations.IMPORT, [main_window]
            )
            contexts.append(outer_ctx)
            outer_ctx.__enter__()

            # Start a thread for inner operation
            def inner_operation_thread():
                # Start inner operation
                inner_ctx = OperationContext(
                    main_window.ui_state_manager, UIOperations.VALIDATION, [data_view]
                )
                contexts.append(inner_ctx)
                inner_ctx.__enter__()

                # Simulate work
                time.sleep(0.5)

                # End inner operation
                inner_ctx.__exit__(None, None, None)

            # Start the inner operation thread
            inner_thread = threading.Thread(target=inner_operation_thread)
            inner_thread.daemon = True
            inner_thread.start()

            # Simulate work in outer operation
            time.sleep(0.2)

            # Wait for inner operation to complete
            inner_thread.join(timeout=2.0)

            # End outer operation
            outer_ctx.__exit__(None, None, None)

        # Run the nested operations
        outer_thread = threading.Thread(target=outer_operation)
        outer_thread.daemon = True
        outer_thread.start()

        # Wait for operations to complete
        outer_thread.join(timeout=5.0)
        qtbot.wait(500)
        app.processEvents()

        # Verify UI state after operations
        assert main_window.isEnabled(), "MainWindow should be enabled after operations"
        assert data_view.isEnabled(), "DataView should be enabled after operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

        # All contexts should be properly exited
        for ctx in contexts:
            assert not ctx.is_active(), "All contexts should be inactive"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
