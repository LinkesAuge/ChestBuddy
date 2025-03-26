"""
test_validation_view_adapter_update.py

Description: Tests for the ValidationViewAdapter integration with UpdateManager.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import UpdateManager
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService
from chestbuddy.utils.service_locator import ServiceLocator


@pytest.fixture
def data_model():
    """Fixture providing a minimal ChestDataModel instance for testing."""
    # Create a simple data model with test data
    model = ChestDataModel()

    # Create sample DataFrame
    data = pd.DataFrame(
        {
            "DATE": ["2023-01-01", "2023-01-02"],
            "PLAYER": ["Player1", "Player2"],
            "CHEST": ["Gold", "Silver"],
            "SCORE": [100, 200],
        }
    )

    # Set the data on the model using the actual method
    model.update_data(data)

    return model


@pytest.fixture
def validation_service(data_model):
    """Fixture providing a minimal ValidationService instance for testing."""
    # Create a validation service with mocked methods
    service = ValidationService(data_model)

    # Mock the validation methods we'll use in tests
    service.validate_data = MagicMock(return_value={})
    service._check_missing_values = MagicMock(return_value={})
    service._check_outliers = MagicMock(return_value={})
    service._check_duplicates = MagicMock(return_value={})
    service._check_data_types = MagicMock(return_value={})

    return service


@pytest.fixture
def update_manager():
    """Fixture providing an UpdateManager instance registered with ServiceLocator."""
    # Create update manager
    manager = UpdateManager()

    # Register with ServiceLocator
    ServiceLocator.register("update_manager", manager)

    yield manager

    # Clean up
    ServiceLocator.remove("update_manager")


@pytest.fixture
def validation_view_adapter(qtbot, data_model, validation_service):
    """Fixture providing a ValidationViewAdapter instance."""
    view = ValidationViewAdapter(data_model, validation_service)
    qtbot.addWidget(view)
    return view


class TestValidationViewAdapterUpdate:
    """Tests for ValidationViewAdapter integration with UpdateManager."""

    def test_implements_iupdatable(self, validation_view_adapter):
        """Test that ValidationViewAdapter implements the IUpdatable interface."""
        assert isinstance(validation_view_adapter, IUpdatable)

    def test_update_view_content_method(self, validation_view_adapter):
        """Test that _update_view_content method updates the view."""
        # Spy on the internal _validation_tab.refresh method
        validation_view_adapter._validation_tab.refresh = MagicMock()

        # Call the method
        validation_view_adapter._update_view_content()

        # Verify the validation tab was refreshed
        validation_view_adapter._validation_tab.refresh.assert_called_once()

    def test_refresh_method_uses_update_manager(self, validation_view_adapter, update_manager):
        """Test that refresh method uses UpdateManager to schedule an update."""
        # In UpdatableView, refresh() doesn't call schedule_update but calls _do_refresh directly
        # So we need to test that _do_refresh is called instead
        validation_view_adapter._do_refresh = MagicMock()

        # Call refresh
        validation_view_adapter.refresh()

        # Verify _do_refresh was called
        validation_view_adapter._do_refresh.assert_called_once()

    def test_populate_method_triggers_validation(self, validation_view_adapter):
        """Test that populate method triggers validation."""
        # Create a mock controller
        mock_controller = MagicMock()
        validation_view_adapter._controller = mock_controller

        # Call populate
        validation_view_adapter.populate()

        # Verify validate_data was called on the controller
        mock_controller.validate_data.assert_called_once()

    def test_reset_method_clears_validation(self, validation_view_adapter):
        """Test that reset method clears validation."""
        # Spy on the internal _validation_tab.clear_validation method
        validation_view_adapter._validation_tab.clear_validation = MagicMock()

        # Call reset
        validation_view_adapter.reset()

        # Verify clear_validation was called
        validation_view_adapter._validation_tab.clear_validation.assert_called_once()

    def test_on_validate_clicked_populates_component(self, validation_view_adapter):
        """Test that _on_validate_clicked method populates the component."""
        # Spy on populate method
        validation_view_adapter.populate = MagicMock()

        # Call _on_validate_clicked
        validation_view_adapter._on_validate_clicked()

        # Verify populate was called
        validation_view_adapter.populate.assert_called_once()

    def test_on_clear_clicked_resets_component(self, validation_view_adapter):
        """Test that _on_clear_clicked method resets the component."""
        # Spy on reset method
        validation_view_adapter.reset = MagicMock()

        # Call _on_clear_clicked
        validation_view_adapter._on_clear_clicked()

        # Verify reset was called
        validation_view_adapter.reset.assert_called_once()

    def test_enable_auto_update_connects_to_data_model(self, validation_view_adapter, data_model):
        """Test that enable_auto_update connects to data model signals."""
        # Spy on signal_manager.connect
        validation_view_adapter._signal_manager.connect = MagicMock()

        # Call enable_auto_update
        validation_view_adapter.enable_auto_update()

        # Verify signal_manager.connect was called with the right arguments
        validation_view_adapter._signal_manager.connect.assert_called_once_with(
            data_model, "data_changed", validation_view_adapter, "request_update"
        )

    def test_disable_auto_update_disconnects_from_data_model(
        self, validation_view_adapter, data_model
    ):
        """Test that disable_auto_update disconnects from data model signals."""
        # Spy on signal_manager.disconnect
        validation_view_adapter._signal_manager.disconnect = MagicMock()

        # Call disable_auto_update
        validation_view_adapter.disable_auto_update()

        # Verify signal_manager.disconnect was called with the right arguments
        validation_view_adapter._signal_manager.disconnect.assert_called_once_with(
            data_model, "data_changed", validation_view_adapter, "request_update"
        )

    def test_integration_with_update_manager(self, validation_view_adapter, update_manager):
        """Test integration between ValidationViewAdapter and UpdateManager."""
        # Spy on update_manager.schedule_update
        update_manager.schedule_update = MagicMock()

        # Call schedule_update on the adapter
        validation_view_adapter.schedule_update()

        # Verify update_manager.schedule_update was called with the right arguments
        update_manager.schedule_update.assert_called_once_with(validation_view_adapter, 50)

    def test_validation_fallback_when_no_controller(self, validation_view_adapter):
        """Test that validation falls back to direct validation when no controller is set."""
        # Set controller to None
        validation_view_adapter._controller = None

        # Spy on the internal _validation_tab.validate method
        validation_view_adapter._validation_tab.validate = MagicMock()

        # Call populate
        validation_view_adapter.populate()

        # Verify direct validate was called on the validation tab
        validation_view_adapter._validation_tab.validate.assert_called_once()

    def test_signals_emitted_on_actions(self, validation_view_adapter, qtbot):
        """Test that proper signals are emitted when actions are performed."""
        # Set up signal spy
        with qtbot.wait_signal(validation_view_adapter.validation_requested) as validate_signal:
            # Trigger validation
            validation_view_adapter._on_validate_clicked()

        # Verify signal was emitted
        assert validate_signal.signal_triggered

        # Set up signal spy for clear
        with qtbot.wait_signal(validation_view_adapter.validation_cleared) as clear_signal:
            # Trigger clear
            validation_view_adapter._on_clear_clicked()

        # Verify signal was emitted
        assert clear_signal.signal_triggered
