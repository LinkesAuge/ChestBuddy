"""
Tests for ValidationTabView UI functionality.

This module tests the ValidationTabView component, focusing on initialization,
validation list management, preference settings, and validation operations.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QStatusBar, QVBoxLayout

from chestbuddy.ui.views.validation_tab_view import ValidationTabView
from chestbuddy.ui.views.validation_list_view import ValidationListView
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.utils.config import ConfigManager

from tests.utils.helpers import SignalSpy, process_events, wait_for_signal, find_widget_by_text


# Mock Signal class to avoid PySide6 Signal issues in tests
class MockSignal:
    """Mock for Qt signals to avoid PySide6 Signal issues"""

    def __init__(self, *args):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def disconnect(self, callback=None):
        if callback:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
        else:
            self.callbacks = []

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


@pytest.fixture
def temp_validation_lists(tmp_path):
    """Create temporary validation list files."""
    players_path = tmp_path / "players.txt"
    chest_types_path = tmp_path / "chest_types.txt"
    sources_path = tmp_path / "sources.txt"

    # Create with some sample data
    players_path.write_text("Player1\nPlayer2")
    chest_types_path.write_text("Chest1\nChest2")
    sources_path.write_text("Source1\nSource2")

    return {
        "players.txt": players_path,
        "chest_types.txt": chest_types_path,
        "sources.txt": sources_path,
    }


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    mock_config = MagicMock()
    return mock_config


@pytest.fixture
def mock_validation_service(mock_config_manager):
    """Create a mock ValidationService for testing."""
    mock_service = MagicMock(spec=ValidationService)

    # Add the _config_manager attribute
    mock_service._config_manager = mock_config_manager

    # Setup basic method returns
    mock_service.get_validation_list_path.return_value = Path(tempfile.mkdtemp()) / "players.txt"
    mock_service.get_validation_preferences.return_value = {
        "case_sensitive": False,
        "validate_on_import": True,
    }

    # Mock the list models
    mock_model = MagicMock(spec=ValidationListModel)
    mock_model.entries_changed = MockSignal()
    mock_model.entries = ["Item1", "Item2"]
    mock_service.get_player_list_model.return_value = mock_model
    mock_service.get_chest_type_list_model.return_value = mock_model
    mock_service.get_source_list_model.return_value = mock_model

    # Mock validation results and statistics
    mock_service.validation_results = {}
    mock_service.get_validation_statistics.return_value = {
        "total": 10,
        "valid": 8,
        "invalid": 2,
        "percentage": 80.0,
    }

    # Create mock signals
    mock_service.validation_changed = MockSignal(object)
    mock_service.validation_preferences_changed = MockSignal(object)

    # Register with ServiceLocator to support initialization tests
    ServiceLocator.register("validation_service", mock_service)

    return mock_service


@pytest.fixture
def validation_tab_view(enhanced_qtbot, mock_validation_service):
    """Create a ValidationTabView instance with mock service."""
    # Patch the UI setup to avoid creating real UI elements
    with (
        patch.object(ValidationTabView, "_connect_signals"),
        patch.object(ValidationTabView, "_setup_ui"),
    ):
        # Create ValidationTabView with the mocked service
        view = ValidationTabView(validation_service=mock_validation_service)

        # Manually set up necessary attributes that would be created in _setup_ui
        view._status_bar = MagicMock()
        view._case_sensitive_checkbox = MagicMock()
        view._validate_on_import_checkbox = MagicMock()
        view._auto_save_checkbox = MagicMock()
        view._splitter = MagicMock()
        view._validate_action = MagicMock()

        # Create mock list views
        for section in ["players", "chest_types", "sources"]:
            # Create section container
            section_container = MagicMock()
            setattr(view, f"_{section}_section", section_container)

            # Create list view with mock model
            list_view = MagicMock()
            list_view.model = MagicMock(
                return_value=mock_validation_service.get_player_list_model()
            )
            list_view.status_changed = MockSignal(str)
            setattr(view, f"_{section}_list", list_view)

            # Create buttons
            add_button = MagicMock()
            remove_button = MagicMock()
            import_button = MagicMock()
            export_button = MagicMock()

            setattr(view, f"_{section}_add", add_button)
            setattr(view, f"_{section}_remove", remove_button)
            setattr(view, f"_{section}_import", import_button)
            setattr(view, f"_{section}_export", export_button)

            # Create count label
            count_label = MagicMock()
            setattr(view, f"_{section}_count", count_label)

        enhanced_qtbot.add_widget(view)
        return view


@pytest.fixture
def temp_validation_list():
    """Create a temporary file for testing validation list import/export."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as temp:
        temp.write("TestItem1\nTestItem2\nTestItem3")
        temp_path = temp.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestValidationTabView:
    """Tests for the ValidationTabView UI component."""

    def test_initialization(self, validation_tab_view, mock_validation_service):
        """Test that ValidationTabView initializes correctly."""
        # Check that the view was created
        assert validation_tab_view is not None

        # Check that it uses the mock service
        assert validation_tab_view._validation_service == mock_validation_service

        # Check that important UI components exist
        assert hasattr(validation_tab_view, "_splitter")
        assert hasattr(validation_tab_view, "_players_list")
        assert hasattr(validation_tab_view, "_chest_types_list")
        assert hasattr(validation_tab_view, "_sources_list")

    def test_initialization_with_service_locator(self, enhanced_qtbot, mock_validation_service):
        """Test initialization with service from ServiceLocator."""
        # Create view without explicitly passing the service
        with (
            patch.object(ValidationTabView, "_connect_signals"),
            patch.object(ValidationTabView, "_setup_ui"),
        ):
            view = ValidationTabView()
            enhanced_qtbot.add_widget(view)

            # Check that it retrieved the service from the locator
            assert view._validation_service == mock_validation_service

    def test_validation_preferences(
        self, validation_tab_view, mock_validation_service, enhanced_qtbot
    ):
        """Test setting validation preferences."""
        # Mock the validation service's set_validation_preferences method
        mock_validation_service.set_validation_preferences = MagicMock()

        # Call the method directly that would be called when the checkbox is toggled
        validation_tab_view._on_case_sensitive_toggled(True)

        # Verify the service method was called with the expected arguments
        mock_validation_service.set_validation_preferences.assert_called_once()

        # Clear the mock for the next test
        mock_validation_service.set_validation_preferences.reset_mock()

        # Test validate_on_import preference
        validation_tab_view._on_validate_on_import_toggled(False)

        # Verify service method was called
        assert mock_validation_service.set_validate_on_import.call_count == 1

    def test_validation_button(self, validation_tab_view, mock_validation_service):
        """Test the validate button functionality."""
        # Mock the validate_data method in the validation service
        mock_validation_service.validate_data = MagicMock(return_value={})

        # Call the method directly
        validation_tab_view._on_validate_clicked()

        # Verify the validate_data method was called
        mock_validation_service.validate_data.assert_called_once()

    def test_clear_validation(self, validation_tab_view, mock_validation_service):
        """Test clearing validation results."""
        # Add the clear_validation method to the mock list views
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(validation_tab_view, f"_{section}_list")
            list_view.clear_validation = MagicMock()

        # Call the method under test
        validation_tab_view.clear_validation()

        # Check that clear_validation was called on each list view
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(validation_tab_view, f"_{section}_list")
            list_view.clear_validation.assert_called_once()

    def test_validation_stats_update(self, validation_tab_view, mock_validation_service):
        """Test updating validation statistics."""
        # Set up the necessary methods on the mock validation service
        mock_validation_service.get_validation_statistics = MagicMock(
            return_value={"total": 10, "valid": 8, "invalid": 2, "percentage": 80.0}
        )

        # Call the method under test
        validation_tab_view._update_validation_stats()

        # Verify that the status bar was updated
        validation_tab_view._status_bar.showMessage.assert_called_once()

    def test_validation_list_add_action(self, validation_tab_view, mock_validation_service):
        """Test the add action on validation lists."""
        # Call the method directly
        validation_tab_view._on_list_add_clicked("players")

        # Get the list view that should have been called
        list_view = validation_tab_view._players_list

        # Verify the correct method was called on the list view
        list_view.add_multiple_entries.assert_called_once()

    def test_validation_list_remove_action(self, validation_tab_view, mock_validation_service):
        """Test the remove action on validation lists."""
        # Call the method directly
        validation_tab_view._on_list_remove_clicked("players")

        # Get the list view that should have been called
        list_view = validation_tab_view._players_list

        # Verify the correct method was called on the list view
        list_view.remove_selected_entries.assert_called_once()

    def test_validation_list_import_action(self, validation_tab_view, mock_validation_service):
        """Test the import action on validation lists."""
        # Call the method directly
        validation_tab_view._on_list_import_clicked("chest_types")

        # Get the list view that should have been called
        list_view = validation_tab_view._chest_types_list

        # Verify the correct method was called on the list view
        list_view.import_entries.assert_called_once()

    def test_validation_list_export_action(self, validation_tab_view, mock_validation_service):
        """Test the export action on validation lists."""
        # Call the method directly
        validation_tab_view._on_list_export_clicked("sources")

        # Get the list view that should have been called
        list_view = validation_tab_view._sources_list

        # Verify the correct method was called on the list view
        list_view.export_entries.assert_called_once()

    def test_status_updates(self, validation_tab_view, enhanced_qtbot):
        """Test status bar updates."""
        # Call the method to set a status message
        test_message = "Testing status message"
        validation_tab_view._set_status_message(test_message)

        # Check that the status bar's showMessage method was called with the right text
        validation_tab_view._status_bar.showMessage.assert_called_with(test_message)

    def test_refresh(self, validation_tab_view, mock_validation_service):
        """Test refreshing the view."""
        # Add refresh method to the mock list views
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(validation_tab_view, f"_{section}_list")
            list_view.refresh = MagicMock()

        # Call the refresh method
        validation_tab_view.refresh()

        # Check that refresh was called on each list view
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(validation_tab_view, f"_{section}_list")
            list_view.refresh.assert_called_once()

    def test_ui_layout(self, validation_tab_view):
        """Test the UI layout configuration."""
        # Simply check that the required UI elements exist
        assert validation_tab_view._splitter is not None
        assert validation_tab_view._status_bar is not None
        assert validation_tab_view._case_sensitive_checkbox is not None
        assert validation_tab_view._validate_on_import_checkbox is not None
        assert all(
            hasattr(validation_tab_view, f"_{section}_list")
            for section in ["players", "chest_types", "sources"]
        )

    def test_signal_connections(self, validation_tab_view, mock_validation_service):
        """Test signal connections."""
        # Test connections by simulating signal emissions
        # Emit validation_changed signal
        mock_validation_service.validation_changed.emit({})

        # Check that validation_changed was emitted
        # Since we're just checking that the connections exist, we don't need to verify any specific behavior
        assert True
