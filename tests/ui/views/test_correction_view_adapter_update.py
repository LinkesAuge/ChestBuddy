"""
test_correction_view_adapter_update.py

Description: Tests for the CorrectionViewAdapter integration with UpdateManager.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.ui.views.correction_view_adapter import CorrectionViewAdapter
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import UpdateManager
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService
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
def correction_service(data_model):
    """Fixture providing a minimal CorrectionService instance for testing."""
    # Create a correction service with mocked methods
    service = CorrectionService(data_model)

    # Mock the correction methods we'll use in tests
    service.apply_correction = MagicMock(return_value=(5, "Success"))
    service.get_correction_history = MagicMock(return_value=[])

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
def correction_view_adapter(qtbot, data_model, correction_service):
    """Fixture providing a CorrectionViewAdapter instance."""
    view = CorrectionViewAdapter(data_model, correction_service)
    qtbot.addWidget(view)
    return view


class TestCorrectionViewAdapterUpdate:
    """Tests for CorrectionViewAdapter integration with UpdateManager."""

    def test_implements_iupdatable(self, correction_view_adapter):
        """Test that CorrectionViewAdapter implements the IUpdatable interface."""
        assert isinstance(correction_view_adapter, IUpdatable)

    def test_update_view_content_method(self, correction_view_adapter):
        """Test that _update_view_content method updates the view."""
        # Spy on the internal _correction_tab._update_view method
        correction_view_adapter._correction_tab._update_view = MagicMock()

        # Call the method
        correction_view_adapter._update_view_content()

        # Verify the correction tab was updated
        correction_view_adapter._correction_tab._update_view.assert_called_once()

    def test_refresh_method_uses_update_manager(self, correction_view_adapter, update_manager):
        """Test that refresh method calls _do_refresh."""
        # In UpdatableView, refresh() doesn't call schedule_update but calls _do_refresh directly
        # So we need to test that _do_refresh is called instead
        correction_view_adapter._do_refresh = MagicMock()

        # Call refresh
        correction_view_adapter.refresh()

        # Verify _do_refresh was called
        correction_view_adapter._do_refresh.assert_called_once()

    def test_populate_method_updates_view(self, correction_view_adapter):
        """Test that populate method updates the view and loads correction rules."""
        # Mock the correction tab's methods
        correction_view_adapter._correction_tab._update_view = MagicMock()
        correction_view_adapter._correction_tab._load_correction_rules = MagicMock()

        # Create a mock controller
        mock_controller = MagicMock()
        correction_view_adapter._controller = mock_controller

        # Call populate
        correction_view_adapter.populate()

        # Verify update_view was called
        correction_view_adapter._correction_tab._update_view.assert_called_once()

        # Verify load_correction_rules was called
        correction_view_adapter._correction_tab._load_correction_rules.assert_called_once()

    def test_reset_method_resets_form(self, correction_view_adapter):
        """Test that reset method resets the form."""
        # Spy on the internal _correction_tab._reset_form method
        correction_view_adapter._correction_tab._reset_form = MagicMock()

        # Call reset
        correction_view_adapter.reset()

        # Verify _reset_form was called
        correction_view_adapter._correction_tab._reset_form.assert_called_once()

    def test_on_apply_clicked_emits_signal(self, correction_view_adapter, qtbot):
        """Test that _on_apply_clicked method emits the correction_requested signal."""
        # Mock the _get_selected_strategy method to return a known value
        correction_view_adapter._correction_tab._get_selected_strategy = MagicMock(
            return_value="test_strategy"
        )

        # Spy on correction_tab._apply_correction
        correction_view_adapter._correction_tab._apply_correction = MagicMock()

        # Set up signal spy
        with qtbot.wait_signal(correction_view_adapter.correction_requested) as signal_spy:
            # Call _on_apply_clicked
            correction_view_adapter._on_apply_clicked()

        # Verify signal was emitted with the right arguments
        assert signal_spy.signal_triggered
        assert signal_spy.args == ["test_strategy"]

        # Verify _apply_correction was called
        correction_view_adapter._correction_tab._apply_correction.assert_called_once()

    def test_on_history_clicked_emits_signal(self, correction_view_adapter, qtbot):
        """Test that _on_history_clicked method emits the history_requested signal."""
        # Spy on correction_tab._update_history
        correction_view_adapter._correction_tab._update_history = MagicMock()

        # Set up signal spy
        with qtbot.wait_signal(correction_view_adapter.history_requested) as signal_spy:
            # Call _on_history_clicked
            correction_view_adapter._on_history_clicked()

        # Verify signal was emitted
        assert signal_spy.signal_triggered

        # Verify _update_history was called
        correction_view_adapter._correction_tab._update_history.assert_called_once()

    def test_enable_auto_update_connects_to_data_model(self, correction_view_adapter, data_model):
        """Test that enable_auto_update connects to data model signals."""
        # Spy on signal_manager.connect
        correction_view_adapter._signal_manager.connect = MagicMock()

        # Call enable_auto_update
        correction_view_adapter.enable_auto_update()

        # Verify signal_manager.connect was called with the right arguments
        correction_view_adapter._signal_manager.connect.assert_called_once_with(
            data_model, "data_changed", correction_view_adapter, "request_update"
        )

    def test_disable_auto_update_disconnects_from_data_model(
        self, correction_view_adapter, data_model
    ):
        """Test that disable_auto_update disconnects from data model signals."""
        # Spy on signal_manager.disconnect
        correction_view_adapter._signal_manager.disconnect = MagicMock()

        # Call disable_auto_update
        correction_view_adapter.disable_auto_update()

        # Verify signal_manager.disconnect was called with the right arguments
        correction_view_adapter._signal_manager.disconnect.assert_called_once_with(
            data_model, "data_changed", correction_view_adapter, "request_update"
        )

    def test_integration_with_update_manager(self, correction_view_adapter, update_manager):
        """Test integration between CorrectionViewAdapter and UpdateManager."""
        # Spy on update_manager.schedule_update
        update_manager.schedule_update = MagicMock()

        # Call schedule_update on the adapter
        correction_view_adapter.schedule_update()

        # Verify update_manager.schedule_update was called with the right arguments
        update_manager.schedule_update.assert_called_once_with(correction_view_adapter, 50)

    def test_correction_fallback_when_no_controller(self, correction_view_adapter):
        """Test that apply correction falls back to direct correction when no controller is set."""
        # Set controller to None
        correction_view_adapter._controller = None

        # Spy on the internal _correction_tab._apply_correction method
        correction_view_adapter._correction_tab._apply_correction = MagicMock()

        # Call _on_apply_clicked
        correction_view_adapter._on_apply_clicked()

        # Verify direct apply was called on the correction tab
        correction_view_adapter._correction_tab._apply_correction.assert_called_once()

    def test_on_correction_started_sets_header_status(self, correction_view_adapter):
        """Test that _on_correction_started sets the header status."""
        # Mock the _set_header_status method
        correction_view_adapter._set_header_status = MagicMock()

        # Call _on_correction_started
        correction_view_adapter._on_correction_started("test_strategy")

        # Verify _set_header_status was called with the right arguments
        correction_view_adapter._set_header_status.assert_called_once_with(
            "Applying test_strategy correction..."
        )

    def test_on_correction_completed_refreshes_view(self, correction_view_adapter):
        """Test that _on_correction_completed refreshes the view."""
        # Mock the _set_header_status and refresh methods
        correction_view_adapter._set_header_status = MagicMock()
        correction_view_adapter.refresh = MagicMock()

        # Call _on_correction_completed
        correction_view_adapter._on_correction_completed("test_strategy", 10)

        # Verify _set_header_status was called with the right arguments
        correction_view_adapter._set_header_status.assert_called_once_with(
            "Correction complete: 10 rows affected"
        )

        # Verify refresh was called
        correction_view_adapter.refresh.assert_called_once()
