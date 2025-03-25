"""
test_data_view_adapter_update.py

Description: Tests for the DataViewAdapter integration with UpdateManager.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import UpdateManager
from chestbuddy.core.models import ChestDataModel
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
def data_view_adapter(qtbot, data_model):
    """Fixture providing a DataViewAdapter instance."""
    view = DataViewAdapter(data_model)
    qtbot.addWidget(view)
    return view


class TestDataViewAdapterUpdate:
    """Tests for DataViewAdapter integration with UpdateManager."""

    def test_implements_iupdatable(self, data_view_adapter):
        """Test that DataViewAdapter implements the IUpdatable interface."""
        assert isinstance(data_view_adapter, IUpdatable)

    def test_update_view_content_method(self, data_view_adapter):
        """Test that _update_view_content method updates the view."""
        # Spy on the internal _data_view._update_view method
        data_view_adapter._data_view._update_view = MagicMock()

        # Call the method
        data_view_adapter._update_view_content()

        # Verify the data view was updated
        data_view_adapter._data_view._update_view.assert_called_once()

    def test_refresh_method_uses_update_manager(self, data_view_adapter, update_manager):
        """Test that refresh method uses UpdateManager to schedule an update."""
        # Spy on schedule_update
        data_view_adapter.schedule_update = MagicMock()

        # Call refresh
        data_view_adapter.refresh()

        # Verify schedule_update was called
        data_view_adapter.schedule_update.assert_called_once()

    def test_needs_update_method(self, data_view_adapter, data_model):
        """Test that needs_update correctly detects data changes."""
        # Initially, the view should not need update (just set up)
        data_view_adapter._update_data_state()

        # Modify the data model
        new_data = pd.DataFrame(
            {
                "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "PLAYER": ["Player1", "Player2", "Player3"],
                "CHEST": ["Gold", "Silver", "Bronze"],
                "SCORE": [100, 200, 300],
            }
        )
        data_model.update_data(new_data)

        # Now the view should need update
        assert data_view_adapter.needs_update()

    def test_on_data_changed_requests_update(self, data_view_adapter):
        """Test that _on_data_changed method requests an update."""
        # Spy on request_update
        data_view_adapter.request_update = MagicMock()

        # Call _on_data_changed
        data_view_adapter._on_data_changed()

        # Verify request_update was called
        data_view_adapter.request_update.assert_called_once()

    def test_request_update_sets_needs_update_flag(self, data_view_adapter, update_manager):
        """Test that request_update sets the needs_update flag and schedules an update."""
        # Spy on schedule_update
        data_view_adapter.schedule_update = MagicMock()

        # Reset the needs_update flag
        data_view_adapter._update_state["needs_update"] = False

        # Call request_update
        data_view_adapter.request_update()

        # Verify needs_update flag was set and schedule_update was called
        assert data_view_adapter._update_state["needs_update"] is True
        data_view_adapter.schedule_update.assert_called_once()

    def test_enable_auto_update_connects_to_data_model(self, data_view_adapter, data_model):
        """Test that enable_auto_update connects to data model signals."""
        # Spy on signal_manager.connect
        data_view_adapter._signal_manager.connect = MagicMock()

        # Call enable_auto_update
        data_view_adapter.enable_auto_update()

        # Verify signal_manager.connect was called with the right arguments
        data_view_adapter._signal_manager.connect.assert_called_once_with(
            data_model, "data_changed", data_view_adapter, "request_update"
        )

    def test_disable_auto_update_disconnects_from_data_model(self, data_view_adapter, data_model):
        """Test that disable_auto_update disconnects from data model signals."""
        # Spy on signal_manager.disconnect
        data_view_adapter._signal_manager.disconnect = MagicMock()

        # Call disable_auto_update
        data_view_adapter.disable_auto_update()

        # Verify signal_manager.disconnect was called with the right arguments
        data_view_adapter._signal_manager.disconnect.assert_called_once_with(
            data_model, "data_changed", data_view_adapter, "request_update"
        )

    def test_integration_with_update_manager(self, data_view_adapter, update_manager):
        """Test integration between DataViewAdapter and UpdateManager."""
        # Spy on update_manager.schedule_update
        update_manager.schedule_update = MagicMock()

        # Call schedule_update on the adapter
        data_view_adapter.schedule_update()

        # Verify update_manager.schedule_update was called with the right arguments
        update_manager.schedule_update.assert_called_once_with(data_view_adapter, 50)

    def test_refresh_fallback_on_update_manager_error(self, data_view_adapter):
        """Test that refresh falls back to direct update if UpdateManager raises an error."""
        # Spy on _update_view_content
        data_view_adapter._update_view_content = MagicMock()

        # Make schedule_update raise an exception
        with patch("chestbuddy.ui.views.data_view_adapter.get_update_manager") as mock_get_update:
            mock_get_update.side_effect = KeyError("update_manager not registered")

            # Make needs_update return True
            data_view_adapter.needs_update = MagicMock(return_value=True)

            # Call refresh
            data_view_adapter.refresh()

            # Verify _update_view_content was called directly as fallback
            data_view_adapter._update_view_content.assert_called_once()

    def test_populate_table_updates_data_state(self, data_view_adapter):
        """Test that populate_table updates the data state tracking."""
        # Create a mock controller
        mock_controller = MagicMock()
        data_view_adapter._controller = mock_controller

        # Spy on _update_data_state
        data_view_adapter._update_data_state = MagicMock()

        # Call populate_table
        data_view_adapter.populate_table()

        # Verify controller.populate_table and _update_data_state were called
        mock_controller.populate_table.assert_called_once()
        data_view_adapter._update_data_state.assert_called_once()

        # Verify _needs_population was reset
        assert data_view_adapter._needs_population is False
