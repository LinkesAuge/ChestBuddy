"""
test_validation_preferences_view.py

Description: Tests for the ValidationPreferencesView class
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.ui.views.validation_preferences_view import ValidationPreferencesView


@pytest.fixture
def app():
    """Fixture to create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def validation_service():
    """Create a ValidationService instance for testing."""
    data_model = MagicMock(spec=ChestDataModel)
    config_manager = MagicMock()

    # Mock the get_bool method to return predefined values
    config_manager.get_bool.side_effect = lambda section, key, default: {
        ("Validation", "case_sensitive"): False,
        ("Validation", "validate_on_import"): True,
    }.get((section, key), default)

    # Create a partially mocked ValidationService
    service = ValidationService(data_model, config_manager)

    # Mock validation methods to avoid file access
    service.set_case_sensitive = MagicMock()
    service.set_validate_on_import = MagicMock()
    service.get_validation_preferences = MagicMock(
        return_value={"case_sensitive": False, "validate_on_import": True}
    )

    return service


@pytest.fixture
def preferences_view(app, validation_service):
    """Create a ValidationPreferencesView for testing."""
    view = ValidationPreferencesView(validation_service)
    view.resize(400, 200)
    view.show()
    QTest.qWaitForWindowExposed(view)
    yield view
    view.close()


class TestValidationPreferencesView:
    """Tests for the ValidationPreferencesView class."""

    def test_initialization(self, preferences_view, validation_service):
        """Test that the view initializes correctly."""
        assert preferences_view is not None
        assert preferences_view.validation_service == validation_service

        # Check that checkboxes are initialized with correct values
        assert preferences_view.case_sensitive_checkbox.isChecked() is False
        assert preferences_view.validate_on_import_checkbox.isChecked() is True

    def test_case_sensitive_checkbox(self, preferences_view, validation_service):
        """Test that changing the case sensitive checkbox calls the service."""
        # Determine initial state
        initial_state = preferences_view.case_sensitive_checkbox.isChecked()

        # Mock the service method
        mock_set_case = MagicMock()
        validation_service.set_case_sensitive = mock_set_case

        # Reset mock before action
        mock_set_case.reset_mock()

        # Set checkbox state directly and call the handler
        new_state = not initial_state
        preferences_view.case_sensitive_checkbox.setChecked(new_state)
        preferences_view._on_case_sensitive_changed(new_state)

        # Check that the service method was called with correct parameter
        mock_set_case.assert_called_once_with(new_state)

    def test_validate_on_import_checkbox(self, preferences_view, validation_service):
        """Test that changing the validate on import checkbox calls the service."""
        # Determine initial state
        initial_state = preferences_view.validate_on_import_checkbox.isChecked()

        # Mock the service method
        mock_set_validate = MagicMock()
        validation_service.set_validate_on_import = mock_set_validate

        # Reset mock before action
        mock_set_validate.reset_mock()

        # Set checkbox state directly and call the handler
        new_state = not initial_state
        preferences_view.validate_on_import_checkbox.setChecked(new_state)
        preferences_view._on_validate_on_import_changed(new_state)

        # Check that the service method was called with correct parameter
        mock_set_validate.assert_called_once_with(new_state)

    def test_preferences_changed_signal(self, preferences_view, validation_service):
        """Test that preferences_changed signal is emitted correctly."""
        # Setup mock for get_validation_preferences to return a test dict
        validation_service.get_validation_preferences.return_value = {
            "case_sensitive": True,
            "validate_on_import": False,
        }

        # Create signal spy
        signal_spy = MagicMock()
        preferences_view.preferences_changed.connect(signal_spy)

        # Reset spy before action
        signal_spy.reset_mock()

        # Directly call the method that emits the signal
        preferences_view._emit_preferences_changed()

        # Allow time for signal processing
        QTest.qWait(50)

        # Check that signal was emitted
        signal_spy.assert_called_once()

        # Verify the emitted preferences are correct
        args = signal_spy.call_args[0]
        assert isinstance(args[0], dict)
        assert args[0]["case_sensitive"] == True
        assert args[0]["validate_on_import"] == False

    def test_refresh(self, preferences_view, validation_service):
        """Test that refresh method reloads preferences from service."""
        # Change the preferences in the service mock
        validation_service.get_validation_preferences.return_value = {
            "case_sensitive": True,
            "validate_on_import": False,
        }

        # Call refresh
        preferences_view.refresh()

        # Check that checkboxes were updated to match the service values
        assert preferences_view.case_sensitive_checkbox.isChecked() is True
        assert preferences_view.validate_on_import_checkbox.isChecked() is False
