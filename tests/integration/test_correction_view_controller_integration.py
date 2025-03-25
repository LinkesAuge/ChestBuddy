"""
Integration tests for CorrectionViewAdapter and DataViewController interactions.

These tests verify that CorrectionViewAdapter properly integrates with DataViewController,
ensuring correction operations work correctly and signals are properly handled.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.views.correction_view_adapter import CorrectionViewAdapter
from chestbuddy.ui.correction_tab import CorrectionTab


def process_events():
    """Helper function to process Qt events."""
    loop = QEventLoop()
    QTimer.singleShot(10, loop.quit)
    loop.exec()


class SignalCatcher(QObject):
    """Utility class for catching and monitoring Qt signals."""

    def __init__(self):
        """Initialize signal catcher."""
        super().__init__()
        self.signal_emitted = {}
        self.signal_arguments = {}

    def catch_signal(self, signal):
        """
        Connect to a signal to monitor its emissions.

        Args:
            signal: The Qt signal to monitor
        """
        self.signal_emitted[signal] = False
        self.signal_arguments[signal] = []

        def slot(*args):
            self.signal_emitted[signal] = True
            self.signal_arguments[signal].append(args)

        signal.connect(slot)

    def was_signal_emitted(self, signal):
        """
        Check if a signal was emitted.

        Args:
            signal: The Qt signal to check

        Returns:
            bool: Whether the signal was emitted
        """
        return self.signal_emitted.get(signal, False)

    def get_signal_arguments(self, signal):
        """
        Get the arguments from the last emission of a signal.

        Args:
            signal: The Qt signal to get arguments for

        Returns:
            list: The arguments from the last emission
        """
        args_list = self.signal_arguments.get(signal, [])
        return args_list[-1] if args_list else None

    def reset(self):
        """Reset the signal tracking state."""
        self.signal_emitted = {}
        self.signal_arguments = {}


@pytest.fixture
def app():
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def signal_catcher():
    """Create a SignalCatcher for testing."""
    return SignalCatcher()


@pytest.fixture
def mock_data_model():
    """Create a mock data model for testing."""
    data_model = MagicMock(spec=ChestDataModel)
    data_model.is_empty = MagicMock(return_value=False)
    data_model.data_changed = Signal()
    data_model.row_count = 10
    data_model.column_count = 5
    data_model.column_names = ["player_name", "chest_type", "loot_1", "loot_2", "timestamp"]
    data_model.get_data = MagicMock(
        return_value=pd.DataFrame(
            {
                "player_name": ["Player1", "Player2", "Player3"],
                "chest_type": ["Gold", "Silver", "Gold"],
                "loot_1": ["Sword", "Potion", "Armor"],
                "loot_2": ["Shield", "Coin", "Ring"],
                "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
            }
        )
    )
    return data_model


@pytest.fixture
def mock_correction_tab():
    """Create a mock CorrectionTab for testing."""
    correction_tab = MagicMock(spec=CorrectionTab)
    correction_tab._update_view = MagicMock()
    correction_tab._apply_correction = MagicMock()
    correction_tab._update_history = MagicMock()
    return correction_tab


@pytest.fixture
def mock_correction_service():
    """Create a mock correction service for testing."""
    correction_service = MagicMock(spec=CorrectionService)
    correction_service.correction_completed = Signal(str, int)

    # Mock correction results
    correction_service.apply_correction.return_value = (True, None)
    correction_service.get_correction_history.return_value = [
        {"strategy": "PlayerNameFix", "affected_rows": 2, "timestamp": "2023-01-01 12:00:00"}
    ]

    return correction_service


@pytest.fixture
def controller(mock_data_model, mock_correction_service):
    """Create a DataViewController for testing."""
    controller = DataViewController(mock_data_model, correction_service=mock_correction_service)
    return controller


@pytest.fixture
def correction_view(app, mock_data_model, mock_correction_service, mock_correction_tab):
    """Create a CorrectionViewAdapter for testing."""
    with patch(
        "chestbuddy.ui.views.correction_view_adapter.CorrectionTab",
        return_value=mock_correction_tab,
    ):
        view = CorrectionViewAdapter(mock_data_model, mock_correction_service)
        view._set_header_status = MagicMock()
        return view


class TestCorrectionViewControllerIntegration:
    """Integration tests for CorrectionViewAdapter and DataViewController."""

    def test_controller_connection(self, correction_view, controller):
        """Test setting the controller and establishing signal connections."""
        # Set controller
        correction_view.set_controller(controller)

        # Check controller reference
        assert correction_view._controller == controller

        # Process events to allow signal connections to be established
        process_events()

        # Verify correct setup
        assert correction_view._controller is not None

    def test_apply_button_with_controller(
        self, correction_view, controller, mock_correction_service
    ):
        """Test that apply button uses the controller to apply correction."""
        # Set controller
        correction_view.set_controller(controller)

        # Mock the apply_correction method
        controller.apply_correction = MagicMock(return_value=True)

        # Trigger the correction action
        correction_view._on_action_clicked("apply")

        # Since we still need to call the tab's method to get parameters
        # we should verify the tab's method was called
        correction_view._correction_tab._apply_correction.assert_called_once()

    def test_correction_started_signal(self, correction_view, controller, signal_catcher):
        """Test that correction_started signal is properly handled."""
        # Set controller
        correction_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.correction_started)

        # Emit the signal
        strategy_name = "PlayerNameFix"
        controller.correction_started.emit(strategy_name)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.correction_started)
        correction_view._set_header_status.assert_called_with(
            f"Applying {strategy_name} correction..."
        )

    def test_correction_completed_signal(
        self, correction_view, controller, signal_catcher, mock_correction_tab
    ):
        """Test that correction_completed signal is properly handled."""
        # Set controller
        correction_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.correction_completed)

        # Setup parameters
        strategy_name = "PlayerNameFix"
        affected_rows = 2

        # Emit the signal
        controller.correction_completed.emit(strategy_name, affected_rows)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.correction_completed)
        correction_view._set_header_status.assert_called_with(
            f"Correction complete: {affected_rows} rows affected"
        )
        mock_correction_tab._update_view.assert_called_once()

    def test_correction_error_signal(self, correction_view, controller, signal_catcher):
        """Test that correction_error signal is properly handled."""
        # Set controller
        correction_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.correction_error)

        # Emit the signal
        error_msg = "Correction failed"
        controller.correction_error.emit(error_msg)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.correction_error)
        correction_view._set_header_status.assert_called_with(f"Correction error: {error_msg}")

    def test_operation_error_signal(self, correction_view, controller, signal_catcher):
        """Test that operation_error signal is properly handled."""
        # Set controller
        correction_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.operation_error)

        # Emit the signal
        error_msg = "Operation failed"
        controller.operation_error.emit(error_msg)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.operation_error)
        correction_view._set_header_status.assert_called_with(f"Error: {error_msg}")

    def test_history_button_functionality(self, correction_view, controller, mock_correction_tab):
        """Test that history button functions properly."""
        # Set controller
        correction_view.set_controller(controller)

        # Mock the get_correction_history method
        controller.get_correction_history = MagicMock(
            return_value=[
                {
                    "strategy": "PlayerNameFix",
                    "affected_rows": 2,
                    "timestamp": "2023-01-01 12:00:00",
                }
            ]
        )

        # Trigger the history action
        correction_view._on_action_clicked("history")

        # Verify get_correction_history was called on the controller
        controller.get_correction_history.assert_called_once()

        # Verify update_history was called on the correction tab
        mock_correction_tab._update_history.assert_called_once()

    def test_refresh_button_functionality(self, correction_view, controller, mock_correction_tab):
        """Test that refresh button functions properly."""
        # Set controller
        correction_view.set_controller(controller)

        # Trigger the refresh action
        correction_view._on_action_clicked("refresh")

        # Verify refresh was called on the correction tab
        mock_correction_tab._update_view.assert_called_once()

    def test_fallback_to_direct_apply(self, correction_view, mock_correction_tab):
        """Test fallback to direct apply when controller not set."""
        # Do not set controller
        assert correction_view._controller is None

        # Trigger the apply action
        correction_view._on_action_clicked("apply")

        # Verify correction tab's apply method was called directly
        mock_correction_tab._apply_correction.assert_called_once()

    def test_fallback_to_direct_history(self, correction_view, mock_correction_tab):
        """Test fallback to direct history update when controller not set."""
        # Do not set controller
        assert correction_view._controller is None

        # Trigger the history action
        correction_view._on_action_clicked("history")

        # Verify correction tab's update_history method was called directly
        mock_correction_tab._update_history.assert_called_once()
