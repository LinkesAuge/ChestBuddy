"""
Test cases for the ErrorHandlingController.

This module contains tests for verifying the functionality of the
ErrorHandlingController including error display, logging, and signal emission.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, call

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QApplication

from chestbuddy.core.controllers import ErrorHandlingController
from chestbuddy.core.controllers.error_handling_controller import ErrorType


class TestErrorHandlingController:
    """Test cases for the ErrorHandlingController class."""

    @pytest.fixture
    def controller(self):
        """Create an ErrorHandlingController instance for testing."""
        return ErrorHandlingController()

    @pytest.fixture
    def mock_progress_controller(self):
        """Create a mock progress controller for testing."""
        mock = MagicMock()
        mock.is_progress_showing.return_value = True
        return mock

    def test_init(self, controller):
        """Test that the controller initializes correctly."""
        assert controller._progress_controller is None
        assert controller._last_error is None
        assert controller._error_handlers == {}

    def test_set_progress_controller(self, controller, mock_progress_controller):
        """Test setting the progress controller."""
        controller.set_progress_controller(mock_progress_controller)
        assert controller._progress_controller == mock_progress_controller

    def test_register_error_handler(self, controller):
        """Test registering a custom error handler."""
        handler = MagicMock()
        controller.register_error_handler(ErrorType.DATA_ERROR, handler)
        assert controller._error_handlers[ErrorType.DATA_ERROR] == handler

    @patch("chestbuddy.core.controllers.error_handling_controller.logger")
    @patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox")
    def test_show_error(self, mock_qmessagebox, mock_logger, controller):
        """Test showing an error message."""
        # Arrange
        mock_box = MagicMock()
        mock_qmessagebox.return_value = mock_box
        mock_qmessagebox.Critical = QMessageBox.Critical
        mock_qmessagebox.Ok = QMessageBox.Ok

        # Setup signal spy
        signal_spy = MagicMock()
        controller.error_occurred.connect(signal_spy)

        # Act
        controller.show_error("Test error", "Test Title", "Test details")

        # Assert
        mock_logger.error.assert_called_with("Test error\nDetails: Test details")
        mock_qmessagebox.assert_called_with(
            QMessageBox.Critical, "Test Title", "Test error", QMessageBox.Ok, None
        )
        mock_box.setDetailedText.assert_called_with("Test details")
        mock_box.exec.assert_called_once()
        signal_spy.assert_called_once()
        assert controller._last_error == {
            "message": "Test error",
            "type": ErrorType.ERROR,
            "details": "Test details",
        }

    @patch("chestbuddy.core.controllers.error_handling_controller.logger")
    @patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox")
    def test_show_warning(self, mock_qmessagebox, mock_logger, controller):
        """Test showing a warning message."""
        # Arrange
        mock_box = MagicMock()
        mock_qmessagebox.return_value = mock_box
        mock_qmessagebox.Warning = QMessageBox.Warning
        mock_qmessagebox.Ok = QMessageBox.Ok

        # Setup signal spy
        signal_spy = MagicMock()
        controller.warning_occurred.connect(signal_spy)

        # Act
        controller.show_warning("Test warning")

        # Assert
        mock_logger.warning.assert_called_with("Test warning")
        mock_qmessagebox.assert_called_with(
            QMessageBox.Warning, "Warning", "Test warning", QMessageBox.Ok, None
        )
        mock_box.exec.assert_called_once()
        signal_spy.assert_called_once()

    @patch("chestbuddy.core.controllers.error_handling_controller.logger")
    @patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox")
    def test_show_info(self, mock_qmessagebox, mock_logger, controller):
        """Test showing an info message."""
        # Arrange
        mock_box = MagicMock()
        mock_qmessagebox.return_value = mock_box
        mock_qmessagebox.Information = QMessageBox.Information
        mock_qmessagebox.Ok = QMessageBox.Ok

        # Setup signal spy
        signal_spy = MagicMock()
        controller.info_occurred.connect(signal_spy)

        # Act
        controller.show_info("Test info")

        # Assert
        mock_logger.info.assert_called_with("Test info")
        mock_qmessagebox.assert_called_with(
            QMessageBox.Information, "Information", "Test info", QMessageBox.Ok, None
        )
        mock_box.exec.assert_called_once()
        signal_spy.assert_called_once()

    @patch("chestbuddy.core.controllers.error_handling_controller.logger")
    @patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox")
    def test_handle_exception(self, mock_qmessagebox, mock_logger, controller):
        """Test handling an exception."""
        # Arrange
        mock_box = MagicMock()
        mock_qmessagebox.return_value = mock_box
        mock_qmessagebox.Critical = QMessageBox.Critical
        mock_qmessagebox.Ok = QMessageBox.Ok

        # Setup signal spy
        signal_spy = MagicMock()
        controller.exception_occurred.connect(signal_spy)

        # Act
        exception = ValueError("Test exception")
        controller.handle_exception(exception, "Test operation")

        # Assert
        mock_logger.error.assert_called_once()  # Complex string formatting, just check it's called
        mock_qmessagebox.assert_called_once()  # Complex box creation, just check it's called
        mock_box.setDetailedText.assert_called_once()
        mock_box.exec.assert_called_once()
        signal_spy.assert_called_once()

    def test_log_error_without_display(self, controller):
        """Test logging an error without displaying it."""
        # Arrange
        with patch("chestbuddy.core.controllers.error_handling_controller.logger") as mock_logger:
            # Act
            controller.log_error("Test error log", ErrorType.DATA_ERROR)

            # Assert
            mock_logger.error.assert_called_with("Test error log")

    def test_get_and_clear_last_error(self, controller):
        """Test getting and clearing the last error."""
        # Setup initial error
        controller._last_error = {"message": "Test error", "type": ErrorType.ERROR, "details": None}

        # Test get_last_error
        last_error = controller.get_last_error()
        assert last_error == {"message": "Test error", "type": ErrorType.ERROR, "details": None}

        # Test clear_last_error
        controller.clear_last_error()
        assert controller.get_last_error() is None

    def test_error_handler_is_called(self, controller):
        """Test that a registered error handler is called instead of default handling."""
        # Arrange
        handler = MagicMock()
        controller.register_error_handler(ErrorType.FILE_ERROR, handler)

        # Act
        controller.show_message("Test message", ErrorType.FILE_ERROR, "Test Title", "Test details")

        # Assert
        handler.assert_called_with(
            "Test message", ErrorType.FILE_ERROR, "Test Title", "Test details"
        )

    def test_progress_controller_integration(self, controller, mock_progress_controller):
        """Test integration with the progress controller."""
        # Arrange
        controller.set_progress_controller(mock_progress_controller)

        # Act - with error
        controller.show_error("Test error")

        # Assert
        mock_progress_controller.is_progress_showing.assert_called_once()
        mock_progress_controller.finish_progress.assert_called_with(
            "Error: Test error", is_error=True
        )

        # Reset mocks
        mock_progress_controller.reset_mock()

        # Act - with info (should not update progress)
        controller.show_info("Test info")

        # Assert
        mock_progress_controller.finish_progress.assert_not_called()

    def test_default_title_generation(self, controller):
        """Test that default titles are generated correctly for different error types."""
        assert controller._get_default_title(ErrorType.INFO) == "Information"
        assert controller._get_default_title(ErrorType.WARNING) == "Warning"
        assert controller._get_default_title(ErrorType.ERROR) == "Error"
        assert controller._get_default_title(ErrorType.CRITICAL) == "Critical Error"
        assert controller._get_default_title(ErrorType.DATA_ERROR) == "Data Error"
        assert controller._get_default_title(ErrorType.VALIDATION_ERROR) == "Validation Error"
        assert controller._get_default_title(ErrorType.FILE_ERROR) == "File Error"
        assert controller._get_default_title(ErrorType.SYSTEM_ERROR) == "System Error"
        assert controller._get_default_title(ErrorType.UI_ERROR) == "UI Error"

    @patch("chestbuddy.core.controllers.error_handling_controller.QApplication")
    @patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox")
    def test_parent_window_detection(self, mock_qmessagebox, mock_qapplication, controller):
        """Test that the parent window is detected correctly."""
        # Arrange
        mock_window = MagicMock()
        mock_qapplication.activeWindow.return_value = mock_window
        mock_qmessagebox.Critical = QMessageBox.Critical
        mock_qmessagebox.Ok = QMessageBox.Ok

        # Act
        controller.show_error("Test error")

        # Assert
        mock_qapplication.activeWindow.assert_called_once()
        mock_qmessagebox.assert_called_with(
            QMessageBox.Critical, "Error", "Test error", QMessageBox.Ok, mock_window
        )

    def test_integration_with_app(self, monkeypatch):
        """Test integration with the application."""
        # This is a more comprehensive test that simulates how the controller
        # would be used in the actual application

        # Mock necessary components
        mock_app = MagicMock()
        mock_progress_controller = MagicMock()
        mock_data_manager = MagicMock()

        # Create controller
        controller = ErrorHandlingController()
        controller.set_progress_controller(mock_progress_controller)

        # Connect signals
        mock_app._on_error = MagicMock()
        controller.error_occurred.connect(mock_app._on_error)

        # Simulate an error during file loading
        with patch("chestbuddy.core.controllers.error_handling_controller.QMessageBox"):
            controller.show_error("Failed to load file", "File Error", "File not found")

        # Verify signal was emitted and progress was updated
        mock_app._on_error.assert_called_once()
        if mock_progress_controller.is_progress_showing():
            mock_progress_controller.finish_progress.assert_called_with(
                "Error: Failed to load file", is_error=True
            )
