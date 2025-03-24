"""
test_ui_state_error_handling.py

Description: Tests for error handling in the UI State Management System,
including exception handling and recovery.
"""

import sys
import time
from pathlib import Path
import threading
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the mock main window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow, MockBackgroundWorker

# Import UI state components
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
)


class CustomError(Exception):
    """Custom error for testing."""

    pass


class ErrorEmitter(QObject):
    """Signal emitter for testing error handling."""

    operation_error = Signal(str)
    operation_failed = Signal()
    operation_success = Signal()


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
def mock_services():
    """Create standard mock services."""
    # Create mock data model with error capability
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)
    data_model.process_data = MagicMock(side_effect=lambda *args, **kwargs: False)

    # Create a mock service that can throw errors
    error_service = MagicMock()

    def raise_error(*args, **kwargs):
        raise CustomError("Test error from error_service")

    error_service.process = MagicMock(side_effect=raise_error)

    # Create mock data manager with background worker
    data_manager = MagicMock()
    data_manager._worker = MockBackgroundWorker()

    # Add necessary signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    # Create error emitter
    error_emitter = ErrorEmitter()

    return {
        "data_model": data_model,
        "error_service": error_service,
        "data_manager": data_manager,
        "error_emitter": error_emitter,
    }


@pytest.fixture
def error_handling_main_window(qtbot, mock_services):
    """Create a main window with error handling capabilities."""
    # Create the main window
    main_window = MockMainWindow(services=mock_services)
    qtbot.addWidget(main_window)

    # Add an error label to display errors
    error_label = QLabel(main_window)
    error_label.setObjectName("errorLabel")
    error_label.setStyleSheet("color: red;")
    error_label.setText("")
    error_label.setVisible(False)
    main_window.error_label = error_label

    # Add a method to handle errors
    def handle_error(message):
        """Display an error message."""
        main_window.error_label.setText(message)
        main_window.error_label.setVisible(True)
        # Auto-hide after 3 seconds
        QTimer = pytest.importorskip("PySide6.QtCore").QTimer
        QTimer.singleShot(3000, lambda: main_window.error_label.setVisible(False))

    # Add a method that throws an exception during an operation
    def operation_with_exception():
        """Run an operation that throws an exception."""
        try:
            with OperationContext(
                main_window.ui_state_manager, UIOperations.PROCESSING, [main_window]
            ):
                # Raise an exception
                raise CustomError("Test exception during operation")
        except CustomError as e:
            # Handle the error
            handle_error(str(e))
            return False
        return True

    # Add method for operation with error from service
    def operation_with_service_error():
        """Run an operation that triggers an error in a service."""
        try:
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                # Call a service method that raises an error
                if "error_service" in mock_services:
                    mock_services["error_service"].process()
                return True
        except CustomError as e:
            # Handle the error
            handle_error(str(e))
            return False

    # Add method for operation with signal-based error
    def operation_with_signal_error():
        """Run an operation that experiences an error reported via signal."""
        with OperationContext(main_window.ui_state_manager, UIOperations.EXPORT, [main_window]):
            # Connect to error signal temporarily
            if "error_emitter" in mock_services:
                error_emitter = mock_services["error_emitter"]
                error_emitter.operation_error.connect(handle_error)

                # Emit an error
                error_emitter.operation_error.emit("Error during export operation")
                error_emitter.operation_failed.emit()

                # Disconnect to prevent memory leaks
                error_emitter.operation_error.disconnect(handle_error)
                return False
            return True

    # Add method for operation that times out
    def operation_with_timeout(timeout=0.5):
        """Run an operation that times out."""
        # Record start time
        start_time = time.time()

        try:
            with OperationContext(
                main_window.ui_state_manager, UIOperations.VALIDATION, [main_window]
            ):
                # Simulate a long-running operation that exceeds timeout
                time.sleep(timeout * 2)  # Twice the timeout duration

                # This should not be reached due to timeout
                return True
        except TimeoutError:
            # Handle timeout error
            elapsed = time.time() - start_time
            handle_error(f"Operation timed out after {elapsed:.2f} seconds")
            return False

    # Add method for nested operation with error in inner operation
    def nested_operation_with_error():
        """Run nested operations where the inner operation fails."""
        success = True

        try:
            # Outer operation
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                try:
                    # Inner operation that fails
                    with OperationContext(
                        main_window.ui_state_manager, UIOperations.PROCESSING, [main_window]
                    ):
                        # Raise an exception
                        raise CustomError("Error in inner operation")
                except CustomError as e:
                    # Handle inner error
                    handle_error(f"Inner error: {str(e)}")
                    success = False

                # Outer operation continues despite inner failure
                pass
        except Exception as e:
            # Handle any outer operation errors
            handle_error(f"Outer error: {str(e)}")
            success = False

        return success

    # Add method for operation with thread error
    def operation_with_thread_error():
        """Run an operation where an error occurs in a worker thread."""
        # Flag to track if the error was caught
        error_caught = [False]

        # Function to run in thread
        def thread_function():
            try:
                # Start an operation
                context = OperationContext(
                    main_window.ui_state_manager, UIOperations.PROCESSING, [main_window]
                )
                context.__enter__()

                try:
                    # Simulate work that fails
                    time.sleep(0.1)
                    raise CustomError("Error in worker thread")
                except CustomError as e:
                    # Set flag that we caught the error
                    error_caught[0] = True
                    # Exit the context (important)
                    context.__exit__(type(e), e, None)
                    # Signal the error through the UI
                    if "error_emitter" in mock_services:
                        mock_services["error_emitter"].operation_error.emit(str(e))
            except Exception as e:
                # Catch any other exceptions
                if "error_emitter" in mock_services:
                    mock_services["error_emitter"].operation_error.emit(
                        f"Unexpected error: {str(e)}"
                    )

        # Start thread
        thread = threading.Thread(target=thread_function)
        thread.daemon = True
        thread.start()

        # Wait for thread to complete
        thread.join(timeout=1.0)

        return error_caught[0]

    # Add all methods to the main window
    main_window.handle_error = handle_error
    main_window.operation_with_exception = operation_with_exception
    main_window.operation_with_service_error = operation_with_service_error
    main_window.operation_with_signal_error = operation_with_signal_error
    main_window.operation_with_timeout = operation_with_timeout
    main_window.nested_operation_with_error = nested_operation_with_error
    main_window.operation_with_thread_error = operation_with_thread_error

    # Connect to error emitter signals
    if "error_emitter" in mock_services:
        mock_services["error_emitter"].operation_error.connect(main_window.handle_error)

    return main_window


class TestErrorHandling:
    """Tests for error handling in the UI State Management System."""

    def test_exception_during_operation(self, qtbot, app, error_handling_main_window):
        """
        Test handling of exceptions during operations.

        This test verifies that UI state is properly restored when an
        exception occurs during an operation.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Initially, the UI should be enabled
        assert main_window.isEnabled(), "MainWindow should be enabled initially"

        # Run operation that throws an exception
        result = main_window.operation_with_exception()

        # Verify operation failed
        assert result is False, "Operation should have failed"

        # Verify error was displayed
        assert main_window.error_label.isVisible(), "Error label should be visible"
        assert "Test exception" in main_window.error_label.text(), (
            "Error message should be displayed"
        )

        # Verify UI was restored after error
        assert main_window.isEnabled(), "MainWindow should be enabled after error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_service_error_handling(self, qtbot, app, error_handling_main_window):
        """
        Test handling of errors from services.

        This test verifies that errors from service components are properly
        handled and UI state is restored.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Run operation that triggers a service error
        result = main_window.operation_with_service_error()

        # Verify operation failed
        assert result is False, "Operation should have failed"

        # Verify error was displayed
        assert main_window.error_label.isVisible(), "Error label should be visible"
        assert "Test error from error_service" in main_window.error_label.text(), (
            "Service error message should be displayed"
        )

        # Verify UI was restored after error
        assert main_window.isEnabled(), "MainWindow should be enabled after error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_signal_error_handling(self, qtbot, app, error_handling_main_window):
        """
        Test handling of errors reported via signals.

        This test verifies that errors reported through signals are properly
        handled and UI state is restored.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Run operation that reports an error via signal
        result = main_window.operation_with_signal_error()

        # Verify operation failed
        assert result is False, "Operation should have failed"

        # Verify error was displayed
        assert main_window.error_label.isVisible(), "Error label should be visible"
        assert "Error during export" in main_window.error_label.text(), (
            "Signal error message should be displayed"
        )

        # Verify UI was restored after error
        assert main_window.isEnabled(), "MainWindow should be enabled after error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_nested_operation_error_handling(self, qtbot, app, error_handling_main_window):
        """
        Test handling of errors in nested operations.

        This test verifies that when an inner operation fails with an error,
        the outer operation can continue and UI state is properly managed.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Run nested operations where inner operation fails
        result = main_window.nested_operation_with_error()

        # Verify overall operation is marked as failed due to inner failure
        assert result is False, "Nested operation should have failed"

        # Verify error was displayed
        assert main_window.error_label.isVisible(), "Error label should be visible"
        assert "Inner error" in main_window.error_label.text(), (
            "Inner error message should be displayed"
        )

        # Verify UI was restored after error
        assert main_window.isEnabled(), "MainWindow should be enabled after error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_thread_error_handling(self, qtbot, app, error_handling_main_window):
        """
        Test handling of errors in worker threads.

        This test verifies that errors occurring in worker threads are properly
        handled and UI state is restored.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Run operation with thread error
        error_caught = main_window.operation_with_thread_error()

        # Wait for the thread to complete and signals to be processed
        qtbot.wait(300)
        app.processEvents()

        # Verify error was caught
        assert error_caught, "Thread error should have been caught"

        # Verify error was displayed
        assert main_window.error_label.isVisible(), "Error label should be visible"
        assert "Error in worker thread" in main_window.error_label.text(), (
            "Thread error message should be displayed"
        )

        # Verify UI was restored after error
        assert main_window.isEnabled(), "MainWindow should be enabled after error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_ui_state_recovery_after_error(self, qtbot, app, error_handling_main_window):
        """
        Test UI state recovery after multiple errors.

        This test verifies that the UI state system can reliably recover
        from multiple errors without leaving components in a blocked state.
        """
        # Get the main window
        main_window = error_handling_main_window
        main_window.show()

        # Run multiple operations with errors
        for _ in range(5):
            # Run different error-generating operations
            main_window.operation_with_exception()
            assert main_window.isEnabled(), "MainWindow should be enabled after exception"

            main_window.operation_with_service_error()
            assert main_window.isEnabled(), "MainWindow should be enabled after service error"

            main_window.operation_with_signal_error()
            assert main_window.isEnabled(), "MainWindow should be enabled after signal error"

            main_window.nested_operation_with_error()
            assert main_window.isEnabled(), "MainWindow should be enabled after nested error"

        # Verify no operations are still active
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

        # Verify UI is fully enabled
        assert main_window.isEnabled(), "MainWindow should be enabled after all operations"

        # Try normal operation after errors
        with OperationContext(main_window.ui_state_manager, UIOperations.VALIDATION, [main_window]):
            # Temporarily disabled during normal operation
            assert not main_window.isEnabled(), "MainWindow should be disabled during operation"

        # Should be enabled again after operation
        assert main_window.isEnabled(), "MainWindow should be enabled after normal operation"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
