"""
test_dashboard_view_update.py

Description: Tests for the DashboardView integration with UpdateManager.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.ui.views.dashboard_view import DashboardView
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
def mock_controller():
    """Fixture providing a mock controller for testing integration."""
    controller = MagicMock()
    controller.update_dashboard_view = MagicMock()
    return controller


@pytest.fixture
def dashboard_view(qtbot, data_model):
    """Fixture providing a DashboardView instance."""
    view = DashboardView(data_model)
    qtbot.addWidget(view)
    # Make the view visible
    view.show()
    return view


class TestDashboardViewUpdate:
    """Tests for DashboardView integration with UpdateManager."""

    def test_implements_iupdatable(self, dashboard_view):
        """Test that DashboardView implements the IUpdatable interface."""
        assert isinstance(dashboard_view, IUpdatable)

    def test_do_update_method(self, dashboard_view):
        """Test that _do_update method updates the dashboard."""
        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()

        # Ensure the view is visible
        dashboard_view.setVisible(True)

        # Call the method
        dashboard_view._do_update()

        # Verify the dashboard was updated
        dashboard_view._update_recent_file_list.assert_called_once()
        dashboard_view._update_dashboard_stats.assert_called_once()

    def test_do_update_skips_when_not_visible(self, dashboard_view):
        """Test that _do_update skips updates when the view is not visible."""
        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()

        # Make the view not visible
        dashboard_view.setVisible(False)

        # Call the method
        dashboard_view._do_update()

        # Verify the update methods were not called
        dashboard_view._update_recent_file_list.assert_not_called()
        dashboard_view._update_dashboard_stats.assert_not_called()

    def test_do_refresh_method(self, dashboard_view):
        """Test that _do_refresh method refreshes the dashboard."""
        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()

        # Call the method
        dashboard_view._do_refresh()

        # Verify the dashboard was refreshed
        dashboard_view._update_recent_file_list.assert_called_once()
        dashboard_view._update_dashboard_stats.assert_called_once()

    def test_do_populate_method_with_new_model(self, dashboard_view):
        """Test that _do_populate method populates the dashboard with a new model."""
        # Create a new model for testing
        new_model = MagicMock()
        # Use PropertyMock for is_empty property
        type(new_model).is_empty = PropertyMock(return_value=False)

        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()
        dashboard_view.set_data_loaded = MagicMock()

        # Call the method with a new model
        dashboard_view._do_populate(new_model)

        # Verify the dashboard was updated properly
        # We don't check if the model was replaced because the condition in
        # _do_populate is "if data is not None and self._data_model is None"
        # and we're providing a non-None data model but _data_model is also non-None
        dashboard_view._update_recent_file_list.assert_called_once()
        dashboard_view._update_dashboard_stats.assert_called_once()
        dashboard_view.set_data_loaded.assert_called_once_with(True)

    def test_do_populate_method_with_empty_initial_model(self, dashboard_view):
        """Test that _do_populate method with a new model when initial model is None."""
        # Set the data_model to None first
        dashboard_view._data_model = None

        # Create a new model for testing
        new_model = MagicMock()
        # Use PropertyMock for is_empty property
        type(new_model).is_empty = PropertyMock(return_value=False)

        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()
        dashboard_view.set_data_loaded = MagicMock()

        # Call the method with a new model
        dashboard_view._do_populate(new_model)

        # Now we should verify the model was replaced
        assert dashboard_view._data_model == new_model
        dashboard_view._update_recent_file_list.assert_called_once()
        dashboard_view._update_dashboard_stats.assert_called_once()
        dashboard_view.set_data_loaded.assert_called_once_with(True)

    def test_do_populate_method_with_existing_model(self, dashboard_view):
        """Test that _do_populate method populates the dashboard with existing model."""
        # Spy on internal update methods
        dashboard_view._update_recent_file_list = MagicMock()
        dashboard_view._update_dashboard_stats = MagicMock()
        dashboard_view.set_data_loaded = MagicMock()

        # Instead of directly patching the property, just patch the specific method call
        with patch.object(
            DashboardView, "_do_populate", wraps=dashboard_view._do_populate
        ) as mock_populate:
            # Mock the is_empty check inside the method
            with patch.object(dashboard_view, "_data_model") as mock_model:
                type(mock_model).is_empty = PropertyMock(return_value=False)

                # Call _do_populate directly since we're patching it
                dashboard_view._do_populate()

                # Verify the method was called and used the existing model
                mock_populate.assert_called_once()
                dashboard_view._update_recent_file_list.assert_called_once()
                dashboard_view._update_dashboard_stats.assert_called_once()
                dashboard_view.set_data_loaded.assert_called_once_with(True)

    def test_do_reset_method(self, dashboard_view):
        """Test that _do_reset method resets the dashboard."""
        # Spy on methods
        dashboard_view.update_stats = MagicMock()
        dashboard_view.set_recent_files = MagicMock()
        dashboard_view.set_data_loaded = MagicMock()

        # Call the method
        dashboard_view._do_reset()

        # Verify the dashboard was reset
        dashboard_view.update_stats.assert_called_once_with(0, "N/A", 0, "Never")
        dashboard_view.set_recent_files.assert_called_once_with([])
        dashboard_view.set_data_loaded.assert_called_once_with(False)

    def test_schedule_dashboard_update(self, dashboard_view, update_manager):
        """Test that schedule_dashboard_update method schedules an update."""
        # Spy on schedule_update
        dashboard_view.schedule_update = MagicMock()

        # Call the method
        dashboard_view.schedule_dashboard_update(200)

        # Verify schedule_update was called with correct debounce time
        dashboard_view.schedule_update.assert_called_once_with(200)

    def test_refresh_uses_updatable_view_implementation(self, dashboard_view):
        """Test that refresh method uses UpdatableView's implementation."""
        # Spy on super().refresh
        with patch("chestbuddy.ui.views.updatable_view.UpdatableView.refresh") as mock_refresh:
            # Call refresh
            dashboard_view.refresh()

            # Verify super().refresh was called
            mock_refresh.assert_called_once()

    def test_update_stats_method(self, dashboard_view):
        """Test that update_stats method updates the stats cards."""
        # Spy on the stats cards' set_value methods
        dashboard_view._dataset_card.set_value = MagicMock()
        dashboard_view._validation_card.set_value = MagicMock()
        dashboard_view._correction_card.set_value = MagicMock()
        dashboard_view._import_card.set_value = MagicMock()

        # Spy on set_data_loaded
        dashboard_view.set_data_loaded = MagicMock()

        # Call update_stats
        dashboard_view.update_stats(
            dataset_rows=1000,
            validation_status="5 issues",
            corrections=500,
            last_import="2023-01-01",
        )

        # Verify stats cards were updated
        dashboard_view._dataset_card.set_value.assert_called_once_with("1,000 rows")
        dashboard_view._validation_card.set_value.assert_called_once_with("5 issues")
        dashboard_view._correction_card.set_value.assert_called_once_with("500 corrected")
        dashboard_view._import_card.set_value.assert_called_once_with("2023-01-01")

        # Verify set_data_loaded was called with True
        dashboard_view.set_data_loaded.assert_called_once_with(True)

    def test_set_recent_files_method(self, dashboard_view):
        """Test that set_recent_files method updates the recent files list."""
        # Spy on _recent_files.set_files
        dashboard_view._recent_files.set_files = MagicMock()

        # Call set_recent_files
        files = ["file1.csv", "file2.csv"]
        dashboard_view.set_recent_files(files)

        # Verify _recent_files.set_files was called with the correct files
        dashboard_view._recent_files.set_files.assert_called_once_with(files)

    def test_set_data_loaded_method(self, dashboard_view):
        """Test that set_data_loaded method switches between empty state and content views."""
        # Call set_data_loaded with True
        dashboard_view.set_data_loaded(True)

        # Verify the stacked widget index was changed
        assert dashboard_view._stacked_widget.currentIndex() == 1
        assert dashboard_view._data_loaded is True

        # Call set_data_loaded with False
        dashboard_view.set_data_loaded(False)

        # Verify the stacked widget index was changed
        assert dashboard_view._stacked_widget.currentIndex() == 0
        assert dashboard_view._data_loaded is False

    def test_integration_with_update_manager(self, dashboard_view, update_manager):
        """Test integration between DashboardView and UpdateManager."""
        # Spy on update_manager.schedule_update
        update_manager.schedule_update = MagicMock()

        # Call schedule_update on the dashboard view
        dashboard_view.schedule_update()

        # Verify update_manager.schedule_update was called with the right arguments
        update_manager.schedule_update.assert_called_once_with(dashboard_view, 50)

    def test_update_dashboard_stats_with_data_model(self, dashboard_view):
        """Test that _update_dashboard_stats method works with the data model."""
        # Create a mock model with appropriate attributes and methods
        mock_model = MagicMock()
        mock_model.is_empty = False
        mock_model.data = pd.DataFrame({"test": range(5)})  # 5 rows
        mock_model.get_validation_status.return_value = pd.DataFrame(
            {"issue": range(3)}
        )  # 3 issues
        mock_model.get_correction_row_count.return_value = 10

        # Replace the data model
        dashboard_view._data_model = mock_model

        # Spy on update_stats
        dashboard_view.update_stats = MagicMock()

        # Call the method
        dashboard_view._update_dashboard_stats()

        # Verify update_stats was called with the right arguments
        # The exact format of arguments might need adjustment based on actual implementation
        dashboard_view.update_stats.assert_called_once()
        args = dashboard_view.update_stats.call_args[1]
        assert args["dataset_rows"] == 5
        assert args["validation_status"] == "3 issues"
        assert args["corrections"] == 10
        # We can't easily verify last_import as it uses datetime.now()

    def test_controller_integration(self, dashboard_view, mock_controller):
        """Test integration with a controller."""
        # Connect the controller to the view signals
        dashboard_view.action_triggered.connect(mock_controller.handle_dashboard_action)
        dashboard_view.file_selected.connect(mock_controller.open_selected_file)
        dashboard_view.import_requested.connect(mock_controller.handle_import_request)

        # Test action_triggered signal
        dashboard_view.action_triggered.emit("validate")
        mock_controller.handle_dashboard_action.assert_called_with("validate")

        # Test file_selected signal
        dashboard_view.file_selected.emit("test_file.csv")
        mock_controller.open_selected_file.assert_called_with("test_file.csv")

        # Test import_requested signal
        dashboard_view.import_requested.emit()
        mock_controller.handle_import_request.assert_called_once()

    def test_initialization_with_data(self, qtbot):
        """Test that DashboardView is properly initialized with data."""
        # Create a model with data
        model = MagicMock()
        model.is_empty = False

        # Create a view with this model
        view = DashboardView(model)
        qtbot.addWidget(view)

        # The view should be initialized with data loaded state
        assert view._data_model == model

        # Initial population should have been triggered
        # We can't easily test this directly, but we can verify the view is ready
        assert view.is_populated() is True
