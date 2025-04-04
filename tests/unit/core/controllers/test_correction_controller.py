"""
Test suite for CorrectionController.

This module contains test cases for the CorrectionController class that is responsible
for coordinating correction operations, including rule management and applying corrections.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
from typing import Dict, List, Any, Tuple
from PySide6.QtCore import QObject, Signal

from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.utils.signal_manager import SignalManager


class MockSignalReceiver(QObject):
    """Mock class for capturing signals emitted by the controller."""

    def __init__(self):
        """Initialize with empty capture lists for each signal."""
        super().__init__()
        self.started_signals = []
        self.progress_signals = []
        self.completed_signals = []
        self.error_signals = []

    def on_correction_started(self, description: str) -> None:
        """Capture correction_started signal."""
        self.started_signals.append(description)

    def on_correction_progress(self, current: int, total: int) -> None:
        """Capture correction_progress signal."""
        self.progress_signals.append((current, total))

    def on_correction_completed(self, stats: Dict[str, Any]) -> None:
        """Capture correction_completed signal."""
        self.completed_signals.append(stats)

    def on_correction_error(self, error_message: str) -> None:
        """Capture correction_error signal."""
        self.error_signals.append(error_message)


@pytest.fixture
def signal_manager():
    """Fixture providing a SignalManager instance."""
    return SignalManager(debug_mode=True)


@pytest.fixture
def mock_correction_service():
    """Create a mock correction service for testing."""
    service = MagicMock()
    service.apply_corrections.return_value = {
        "total_corrections": 5,
        "corrected_rows": 3,
        "corrected_cells": 5,
    }
    service._data_model = MagicMock()
    service._data_model.data = pd.DataFrame(
        {"PLAYER": ["player1", "player2", "player3"], "CHEST": ["Gold", "Silver", "Bronze"]}
    )
    return service


@pytest.fixture
def mock_rule_manager():
    """Create a mock rule manager for testing."""
    rule_manager = MagicMock()
    rule_manager.get_rules.return_value = [
        CorrectionRule(
            from_value="player1", to_value="Player 1", category="player", status="enabled"
        ),
        CorrectionRule(
            from_value="Gold", to_value="Golden Chest", category="chest", status="enabled"
        ),
    ]
    return rule_manager


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager for testing."""
    config_manager = MagicMock()
    config_manager.get_auto_correct_on_validation.return_value = False
    config_manager.get_auto_correct_on_import.return_value = False
    return config_manager


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service for testing."""
    validation_service = MagicMock()
    return validation_service


@pytest.fixture
def mock_view():
    """Fixture providing a mock view."""
    view = MagicMock()
    view.refresh = MagicMock()
    view.update_rule_list = MagicMock()
    return view


@pytest.fixture
def controller(
    mock_correction_service, mock_rule_manager, mock_config_manager, mock_validation_service
):
    """Create a correction controller for testing."""
    controller = CorrectionController(
        mock_correction_service, mock_rule_manager, mock_config_manager, mock_validation_service
    )
    return controller


@pytest.fixture
def signal_receiver():
    """Fixture providing a signal receiver to capture controller signals."""
    return MockSignalReceiver()


@pytest.fixture
def connected_controller(controller, signal_receiver):
    """Fixture providing a controller with connected signals."""
    controller.correction_started.connect(signal_receiver.on_correction_started)
    controller.correction_progress.connect(signal_receiver.on_correction_progress)
    controller.correction_completed.connect(signal_receiver.on_correction_completed)
    controller.correction_error.connect(signal_receiver.on_correction_error)
    return controller


class TestCorrectionController:
    """Test cases for the CorrectionController class."""

    def test_initialization(
        self, controller, mock_correction_service, mock_rule_manager, mock_config_manager
    ):
        """Test that controller initializes correctly with dependencies."""
        assert controller._correction_service == mock_correction_service
        assert controller._rule_manager == mock_rule_manager
        assert controller._config_manager == mock_config_manager
        assert controller._view is None
        assert controller._worker is None
        assert controller._worker_thread is None

    def test_set_view(self, controller, mock_view):
        """Test setting the view."""
        # Initially no view
        assert controller._view is None

        # Set the view
        controller.set_view(mock_view)

        # View should be set
        assert controller._view == mock_view

    def test_add_rule(self, controller, mock_rule_manager, mock_view):
        """Test adding a rule."""
        # Set up the view
        controller.set_view(mock_view)

        # Create a rule to add
        rule = CorrectionRule(
            to_value="player", from_value="Player", category="player", status="enabled"
        )

        # Add the rule
        result = controller.add_rule(rule)

        # Verify the rule manager was called
        mock_rule_manager.add_rule.assert_called_once_with(rule)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_update_rule(self, controller, mock_rule_manager, mock_view):
        """Test updating a rule."""
        # Set up the view
        controller.set_view(mock_view)

        # Create a rule to update
        rule = CorrectionRule(
            to_value="player", from_value="Player", category="player", status="enabled"
        )

        # Update the rule
        result = controller.update_rule(1, rule)

        # Verify the rule manager was called
        mock_rule_manager.update_rule.assert_called_once_with(1, rule)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_delete_rule(self, controller, mock_rule_manager, mock_view):
        """Test deleting a rule."""
        # Set up the view
        controller.set_view(mock_view)

        # Delete the rule
        result = controller.delete_rule(1)

        # Verify the rule manager was called
        mock_rule_manager.delete_rule.assert_called_once_with(1)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_reorder_rule(self, controller, mock_rule_manager, mock_view):
        """Test reordering a rule."""
        # Set up the view
        controller.set_view(mock_view)

        # Reorder the rule
        result = controller.reorder_rule(1, 2)

        # Verify the rule manager was called
        mock_rule_manager.move_rule.assert_called_once_with(1, 2)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_move_rule_to_top(self, controller, mock_rule_manager, mock_view):
        """Test moving a rule to the top."""
        # Set up the view
        controller.set_view(mock_view)

        # Move the rule to the top
        result = controller.move_rule_to_top(1)

        # Verify the rule manager was called
        mock_rule_manager.move_rule_to_top.assert_called_once_with(1)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_move_rule_to_bottom(self, controller, mock_rule_manager, mock_view):
        """Test moving a rule to the bottom."""
        # Set up the view
        controller.set_view(mock_view)

        # Move the rule to the bottom
        result = controller.move_rule_to_bottom(1)

        # Verify the rule manager was called
        mock_rule_manager.move_rule_to_bottom.assert_called_once_with(1)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_toggle_rule_status(self, controller, mock_rule_manager, mock_view):
        """Test toggling a rule's status."""
        # Set up the view
        controller.set_view(mock_view)

        # Toggle the rule's status
        result = controller.toggle_rule_status(1)

        # Verify the rule manager was called
        mock_rule_manager.toggle_rule_status.assert_called_once_with(1)

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

        # Verify the result
        assert result is True

    def test_get_rules(self, controller, mock_rule_manager):
        """Test getting rules."""
        # Test with category and status parameters
        rules = controller.get_rules(category="player", status="enabled")

        # Verify the rule manager was called with the correct parameters
        mock_rule_manager.get_rules.assert_called_once_with(
            category="player", status="enabled", search_term=None
        )

        # Verify the result
        assert rules == mock_rule_manager.get_rules.return_value

        # Reset the mock
        mock_rule_manager.reset_mock()

        # Test with category, status, and search_term parameters
        rules = controller.get_rules(category="player", status="enabled", search_term="test")

        # Verify the rule manager was called with all parameters including search_term
        mock_rule_manager.get_rules.assert_called_once_with(
            category="player", status="enabled", search_term="test"
        )

        # Verify the result
        assert rules == mock_rule_manager.get_rules.return_value

    def test_get_prioritized_rules(self, controller, mock_rule_manager):
        """Test getting prioritized rules."""
        # Get the prioritized rules
        rules = controller.get_prioritized_rules()

        # Verify the rule manager was called
        mock_rule_manager.get_prioritized_rules.assert_called_once()

        # Verify the result
        assert rules == mock_rule_manager.get_prioritized_rules.return_value

    def test_apply_corrections(
        self, controller, mock_correction_service, connected_controller, signal_receiver
    ):
        """Test applying corrections."""
        with patch(
            "chestbuddy.core.controllers.correction_controller.BackgroundWorker"
        ) as mock_worker_class:
            # Mock the worker
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            # Apply corrections
            controller.apply_corrections(only_invalid=True)

            # Verify the worker was created correctly
            mock_worker_class.assert_called_once()

            # Verify task was started
            mock_worker.start.assert_called_once()

            # Verify the correction_started signal was emitted
            assert len(signal_receiver.started_signals) == 1
            assert signal_receiver.started_signals[0] == "Applying correction rules"

    def test_apply_corrections_task(self, controller, mock_correction_service, mock_view):
        """Test applying corrections in a background task."""
        # Set up
        controller.set_view(mock_view)

        # Run the task
        result = controller._apply_corrections_task(only_invalid=True)

        # Verify service was called
        mock_correction_service.apply_corrections.assert_called_once_with(only_invalid=True)

        # Verify result matches service output
        assert result == mock_correction_service.apply_corrections.return_value

    def test_recursive_correction(self, mocker, controller, mock_correction_service):
        """Test that corrections are applied recursively until no more changes occur."""
        # Configure mock service to return different results for each call
        # First call: 5 corrections, second call: 3 corrections, third call: 0 corrections
        mock_correction_service.apply_corrections.side_effect = [
            {"total_corrections": 5, "corrected_rows": 3, "corrected_cells": 5},
            {"total_corrections": 3, "corrected_rows": 2, "corrected_cells": 3},
            {"total_corrections": 0, "corrected_rows": 0, "corrected_cells": 0},
        ]

        # Mock data hash method to simulate data changes
        controller._get_data_hash = mocker.Mock()
        controller._get_data_hash.side_effect = ["hash1", "hash2", "hash3", "hash3"]

        # Call the method with recursive=True
        result = controller._apply_corrections_task(recursive=True)

        # Verify service was called three times
        assert mock_correction_service.apply_corrections.call_count == 3

        # Verify accumulated statistics
        assert result["total_corrections"] == 8  # 5 + 3
        assert result["corrected_rows"] == 3  # Max value
        assert result["corrected_cells"] == 5  # Max value
        assert result["iterations"] == 3

    def test_selection_based_correction(
        self, mocker, controller, mock_correction_service, mock_view
    ):
        """Test that corrections are applied only to selected cells when selected_only=True."""
        # Setup view
        controller.set_view(mock_view)

        # Configure mocks
        mock_correction_service.apply_corrections.return_value = {
            "total_corrections": 5,
            "corrected_rows": 3,
            "corrected_cells": 5,
        }

        # Setup selected cells
        mock_view.get_selected_indexes = mocker.Mock(return_value=[(0, 1), (1, 2), (2, 3)])

        # Mock data model
        mock_data_model = mocker.Mock()
        mock_data_model.apply_selection_filter = mocker.Mock()
        mock_data_model.restore_from_filtered_changes = mocker.Mock()

        # Attach data model to controller
        controller._data_model = mock_data_model

        # Call the method with selected_only=True
        result = controller._apply_corrections_task(selected_only=True)

        # Verify selection filter was applied
        mock_data_model.apply_selection_filter.assert_called_once()

        # Verify data was restored after correction
        mock_data_model.restore_from_filtered_changes.assert_called_once()

        # Verify service was called with the filtered data
        assert mock_correction_service.apply_corrections.call_count == 1

    def test_apply_corrections_task_with_progress(self, controller, mock_correction_service):
        """Test the apply_corrections_task method with progress reporting."""
        # Create a progress callback
        progress_callback = MagicMock()

        # Directly call the task method
        controller._apply_corrections_task(only_invalid=False, progress_callback=progress_callback)

        # Verify progress was reported
        assert progress_callback.called

    def test_on_corrections_completed(
        self, controller, mock_view, connected_controller, signal_receiver
    ):
        """Test the on_corrections_completed method."""
        # Set up the view
        controller.set_view(mock_view)

        # Create correction stats
        stats = {"total_corrections": 10, "corrected_rows": 5, "corrected_cells": 10}

        # Call the completion handler
        controller._on_corrections_completed(stats)

        # Verify the view was refreshed
        mock_view.refresh.assert_called_once()

        # Verify the correction_completed signal was emitted
        assert len(signal_receiver.completed_signals) == 1
        assert signal_receiver.completed_signals[0] == stats

    def test_on_corrections_error(self, connected_controller, signal_receiver):
        """Test the on_corrections_error method."""
        # Create an error message
        error_message = "Test error message"

        # Call the error handler
        connected_controller._on_corrections_error(error_message)

        # Verify the correction_error signal was emitted
        assert len(signal_receiver.error_signals) == 1
        assert signal_receiver.error_signals[0] == error_message

    def test_apply_single_rule(
        self, controller, mock_correction_service, mock_view, connected_controller, signal_receiver
    ):
        """Test applying a single rule."""
        # Set up the view
        controller.set_view(mock_view)

        # Create a rule to apply
        rule = CorrectionRule("Player", "player", "player", "enabled", 0)

        # Apply the single rule
        controller.apply_single_rule(rule, only_invalid=True)

        # Verify the correction service was called
        mock_correction_service.apply_single_rule.assert_called_once_with(rule, only_invalid=True)

        # Verify the view was refreshed
        mock_view.refresh.assert_called_once()

        # Verify the correction_completed signal was emitted
        assert len(signal_receiver.completed_signals) == 1

    def test_get_cells_with_available_corrections(self, controller, mock_correction_service):
        """Test getting cells with available corrections."""
        # Get cells with available corrections
        cells = controller.get_cells_with_available_corrections()

        # Verify the correction service was called
        mock_correction_service.get_cells_with_available_corrections.assert_called_once()

        # Verify the result
        assert cells == mock_correction_service.get_cells_with_available_corrections.return_value

    def test_get_correction_preview(self, controller, mock_correction_service):
        """Test getting a correction preview."""
        # Create a rule to preview
        rule = CorrectionRule("Player", "player", "player", "enabled", 0)

        # Get correction preview
        preview = controller.get_correction_preview(rule)

        # Verify the correction service was called
        mock_correction_service.get_correction_preview.assert_called_once_with(rule)

        # Verify the result
        assert preview == mock_correction_service.get_correction_preview.return_value

    def test_import_rules(self, controller, mock_rule_manager, mock_view):
        """Test importing rules."""
        # Set up the view
        controller.set_view(mock_view)

        # Import rules
        file_path = "path/to/rules.csv"
        replace_existing = True

        controller.import_rules(file_path, replace_existing)

        # Verify the rule manager was called
        mock_rule_manager.load_rules.assert_called_once_with(
            file_path=file_path, replace_existing=replace_existing
        )

        # Verify the view was updated
        mock_view.update_rule_list.assert_called_once()

    def test_export_rules(self, controller, mock_rule_manager):
        """Test exporting rules."""
        # Export rules
        file_path = "path/to/export.csv"
        only_enabled = True

        controller.export_rules(file_path, only_enabled)

        # Verify the rule manager was called
        mock_rule_manager.save_rules.assert_called_once_with(
            file_path=file_path, only_enabled=only_enabled
        )

    def test_worker_cleanup(self, controller):
        """Test worker cleanup."""
        # Create mock worker and thread
        mock_worker = MagicMock()
        controller._worker = mock_worker
        controller._worker_thread = MagicMock()

        # Call cleanup
        controller._cleanup_worker()

        # Verify the worker was stopped
        mock_worker.stop.assert_called_once()

        # Verify the worker and thread are None
        assert controller._worker is None
        assert controller._worker_thread is None

    def test_worker_cleanup_on_del(self, controller):
        """Test worker cleanup on deletion."""
        # Create mock worker and thread
        controller._worker = MagicMock()
        controller._worker_thread = MagicMock()

        # Patch the cleanup method to check it's called
        with patch.object(controller, "_cleanup_worker") as mock_cleanup:
            # Call __del__
            controller.__del__()

            # Verify cleanup was called
            mock_cleanup.assert_called_once()

    def test_apply_corrections(controller, mock_correction_service):
        """Test applying corrections."""
        # Call the apply_corrections method
        controller.apply_corrections(only_invalid=True, recursive=True)

        # Check that the correction service was called with the right parameters
        mock_correction_service.apply_corrections.assert_called_once_with(only_invalid=True)

    def test_auto_correct_after_validation(
        controller, mock_correction_service, mock_config_manager
    ):
        """Test auto-correction after validation."""
        # Test when auto-correction is disabled
        mock_config_manager.get_auto_correct_on_validation.return_value = False
        result = controller.auto_correct_after_validation()
        assert result is False
        mock_correction_service.apply_corrections.assert_not_called()

        # Test when auto-correction is enabled
        mock_config_manager.get_auto_correct_on_validation.return_value = True
        result = controller.auto_correct_after_validation()
        assert result is True
        mock_correction_service.apply_corrections.assert_called_once_with(
            only_invalid=True, recursive=True
        )

    def test_auto_correct_on_import(controller, mock_correction_service, mock_config_manager):
        """Test auto-correction on import."""
        # Test when auto-correction is disabled
        mock_config_manager.get_auto_correct_on_import.return_value = False
        result = controller.auto_correct_on_import()
        assert result is False
        mock_correction_service.apply_corrections.assert_not_called()

        # Test when auto-correction is enabled
        mock_config_manager.get_auto_correct_on_import.return_value = True
        result = controller.auto_correct_on_import()
        assert result is True
        mock_correction_service.apply_corrections.assert_called_once_with(
            only_invalid=False, recursive=True
        )
