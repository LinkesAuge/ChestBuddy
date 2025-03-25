"""
Tests for the ViewStateController class.

This module contains tests for the ViewStateController class, which manages view state
and transitions between views in the ChestBuddy application.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, call
from PySide6.QtCore import Signal, QObject, QSettings, QTimer
from PySide6.QtWidgets import QWidget, QStackedWidget, QApplication

from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation


class MockView(QWidget):
    """Mock view class for testing."""

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.populated = False
        self.refreshed = False
        self.needs_population = False
        self.data_loaded = False
        self.state = {}

    def populate_table(self):
        self.populated = True
        self.needs_population = False

    def refresh(self):
        self.refreshed = True

    def needs_refresh(self):
        return True

    def set_data_loaded(self, loaded):
        self.data_loaded = loaded

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state


class MockSidebar(QObject):
    """Mock sidebar class for testing."""

    navigation_changed = Signal(str, str)
    data_dependent_view_clicked = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.active_item = None
        self.data_loaded_state = None
        self.view_availability = {}

    def set_active_item(self, item):
        self.active_item = item

    def set_data_loaded(self, has_data):
        self.data_loaded_state = has_data

    def update_view_availability(self, availability):
        self.view_availability = availability


class MockDataViewController(QObject):
    """Mock data view controller class for testing."""

    filter_applied = Signal(dict)
    sort_applied = Signal(str, bool)
    table_populated = Signal(int)
    operation_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.view = None
        self.refresh_called = False
        self.needs_refresh_result = True
        self.filter_params = {}
        self.sort_params = {"column": "", "ascending": True}

    def set_view(self, view):
        self.view = view

    def refresh_data(self):
        self.refresh_called = True
        return True

    def needs_refresh(self):
        return self.needs_refresh_result


@pytest.fixture
def mock_data_model():
    """Create a mock data model."""
    model = MagicMock(spec=ChestDataModel)
    model.data_changed = Signal()
    model.data_cleared = Signal()
    model.is_empty.return_value = True
    return model


@pytest.fixture
def mock_sidebar():
    """Create a mock sidebar."""
    return MockSidebar()


@pytest.fixture
def mock_content_stack():
    """Create a mock content stack."""
    content_stack = MagicMock(spec=QStackedWidget)
    content_stack.currentIndex.return_value = 0
    return content_stack


@pytest.fixture
def mock_views():
    """Create mock views."""
    views = {
        "Dashboard": MockView("Dashboard"),
        "Data": MockView("Data"),
        "Validation": MockView("Validation"),
        "Correction": MockView("Correction"),
        "Charts": MockView("Charts"),
    }
    return views


@pytest.fixture
def mock_data_view_controller():
    """Create a mock data view controller."""
    return MockDataViewController()


@pytest.fixture
def controller(mock_data_model, mock_sidebar, mock_content_stack, mock_views):
    """Create a ViewStateController instance."""
    controller = ViewStateController(mock_data_model)
    controller.set_ui_components(mock_views, mock_sidebar, mock_content_stack)
    return controller


class TestViewStateController:
    """Tests for the ViewStateController class."""

    def test_initialization(self, controller, mock_data_model):
        """Test controller initialization."""
        assert controller._data_model == mock_data_model
        assert controller._views != {}
        assert controller._sidebar is not None
        assert controller._content_stack is not None
        assert controller._active_view == ""
        assert controller._has_data_loaded is False

        # Check view dependencies for default views
        assert "Validation" in controller._view_dependencies
        assert "Correction" in controller._view_dependencies
        assert "Charts" in controller._view_dependencies

        # Verify initial navigation history
        assert controller._navigation_history == ["Dashboard"]
        assert controller._history_position == 0

    def test_set_active_view(self, controller, mock_views, mock_sidebar, mock_content_stack):
        """Test setting the active view."""
        # Set up mock content stack
        mock_content_stack.currentWidget.return_value = None

        # Call the method
        controller.set_active_view("Dashboard")

        # Check results
        assert controller._active_view == "Dashboard"
        assert mock_sidebar.active_item == "Dashboard"
        mock_content_stack.setCurrentWidget.assert_called_once_with(mock_views["Dashboard"])

    def test_set_active_view_data_needs_population(
        self, controller, mock_views, mock_content_stack
    ):
        """Test setting the active view to Data when it needs population."""
        # Set up mock content stack
        mock_content_stack.currentWidget.return_value = None

        # Set needs_population flag
        mock_views["Data"].needs_population = True

        # Call the method
        controller.set_active_view("Data")

        # Check results
        assert controller._active_view == "Data"
        assert mock_views["Data"].populated is True
        mock_content_stack.setCurrentWidget.assert_called_once_with(mock_views["Data"])

    def test_update_data_loaded_state(self, controller, mock_sidebar, mock_views):
        """Test updating data loaded state."""
        # Call the method
        controller.update_data_loaded_state(True)

        # Check results
        assert controller._has_data_loaded is True
        assert mock_sidebar.data_loaded_state is True

        # Check that all views received the data loaded state
        for view_name, view in mock_views.items():
            assert view.data_loaded is True

        # Check view availability was updated
        assert controller._view_availability.get("Validation", False) is True
        assert controller._view_availability.get("Correction", False) is True
        assert controller._view_availability.get("Charts", False) is True

    def test_refresh_active_view(self, controller, mock_content_stack, mock_views):
        """Test refreshing the active view."""
        # Set up mock content stack
        mock_content_stack.currentWidget.return_value = mock_views["Dashboard"]
        mock_content_stack.widget.return_value = mock_views["Dashboard"]

        # Call the method
        controller.refresh_active_view()

        # Check results
        assert mock_views["Dashboard"].refreshed is True

    def test_populate_data_view(self, controller, mock_content_stack, mock_views):
        """Test populating the data view."""
        # Set up mock content stack
        mock_content_stack.currentWidget.return_value = mock_views["Data"]

        # Call the method
        controller.populate_data_view()

        # Check results
        assert mock_views["Data"].populated is True

    def test_populate_data_view_not_current(self, controller, mock_content_stack, mock_views):
        """Test populating the data view when it's not the current view."""
        # Set up mock content stack
        mock_content_stack.currentWidget.return_value = mock_views["Dashboard"]

        # Call the method
        controller.populate_data_view()

        # Check results
        assert mock_views["Data"].populated is False
        assert mock_views["Data"].needs_population is True

    def test_on_data_changed(self, controller, mock_data_model):
        """Test handling data changed event."""
        # Set up mock
        mock_data_model.is_empty.return_value = False

        # Set up spies
        controller.update_data_loaded_state = MagicMock()
        controller.populate_data_view = MagicMock()
        controller.refresh_active_view = MagicMock()

        # Call the method
        controller._on_data_changed()

        # Check results
        controller.update_data_loaded_state.assert_called_once_with(True)
        controller.populate_data_view.assert_called_once()
        controller.refresh_active_view.assert_called_once()

    def test_on_data_cleared(self, controller):
        """Test handling data cleared event."""
        # Set up spies
        controller.update_data_loaded_state = MagicMock()
        controller.set_active_view = MagicMock()

        # Call the method
        controller._on_data_cleared()

        # Check results
        controller.update_data_loaded_state.assert_called_once_with(False)
        controller.set_active_view.assert_called_once_with("Dashboard")

    def test_register_view_dependency(self, controller):
        """Test registering a view dependency."""
        # Register a dependency
        controller.register_view_dependency("Test", {"Dashboard"})

        # Check results
        assert "Test" in controller._view_dependencies
        assert "Dashboard" in controller._view_dependencies["Test"]

    def test_register_view_prerequisite(self, controller):
        """Test registering a view prerequisite."""

        # Create a test function
        def test_prerequisite():
            return True, ""

        # Register the prerequisite
        controller.register_view_prerequisite("Test", test_prerequisite)

        # Check results
        assert "Test" in controller._view_prerequisites
        assert test_prerequisite in controller._view_prerequisites["Test"]

    def test_check_view_prerequisites_no_dependencies(self, controller):
        """Test checking view prerequisites when there are none."""
        # Call the method for Dashboard which has no dependencies
        result, reason = controller.check_view_prerequisites("Dashboard")

        # Check results
        assert result is True
        assert reason == ""

    def test_check_view_prerequisites_with_dependencies(self, controller):
        """Test checking view prerequisites with dependencies."""
        # Validation depends on Data
        result, reason = controller.check_view_prerequisites("Validation")

        # With no data loaded, prerequisites should fail
        assert result is False
        assert "Data must be loaded first" in reason

        # Now load data and try again
        controller.update_data_loaded_state(True)
        result, reason = controller.check_view_prerequisites("Validation")

        # Now prerequisites should pass
        assert result is True
        assert reason == ""

    def test_update_view_availability(self, controller, mock_sidebar):
        """Test updating view availability."""
        # Initially, data-dependent views should be unavailable
        assert controller._view_availability.get("Validation", True) is False

        # Update data loaded state to true
        controller.update_data_loaded_state(True)

        # Now data-dependent views should be available
        assert controller._view_availability.get("Validation", False) is True
        assert controller._view_availability.get("Charts", False) is True

        # Check the sidebar was updated
        assert "Validation" in mock_sidebar.view_availability
        assert mock_sidebar.view_availability["Validation"] is True

    def test_on_data_dependent_view_clicked(self, controller, monkeypatch):
        """Test handling data dependent view clicked event."""
        # Mock the QMessageBox
        mock_message_box = MagicMock()
        monkeypatch.setattr(
            "chestbuddy.core.controllers.view_state_controller.QMessageBox", mock_message_box
        )

        # Call the method
        controller._on_data_dependent_view_clicked("Validation", None)

        # Check that information dialog was shown
        mock_message_box.information.assert_called_once()

    def test_navigation_history(self, controller):
        """Test navigation history management."""
        # Initial state
        assert controller._navigation_history == ["Dashboard"]
        assert controller._history_position == 0
        assert controller.can_go_back is False
        assert controller.can_go_forward is False

        # Navigate to Data view
        controller.set_active_view("Data")
        assert controller._navigation_history == ["Dashboard", "Data"]
        assert controller._history_position == 1
        assert controller.can_go_back is True
        assert controller.can_go_forward is False

        # Navigate to Validation view
        controller.update_data_loaded_state(True)  # Need to load data for Validation
        controller.set_active_view("Validation")
        assert controller._navigation_history == ["Dashboard", "Data", "Validation"]
        assert controller._history_position == 2
        assert controller.can_go_back is True
        assert controller.can_go_forward is False

        # Navigate back to Data
        controller.navigate_back()
        assert controller._active_view == "Data"
        assert controller._history_position == 1
        assert controller.can_go_back is True
        assert controller.can_go_forward is True

        # Navigate back to Dashboard
        controller.navigate_back()
        assert controller._active_view == "Dashboard"
        assert controller._history_position == 0
        assert controller.can_go_back is False
        assert controller.can_go_forward is True

        # Navigate forward to Data
        controller.navigate_forward()
        assert controller._active_view == "Data"
        assert controller._history_position == 1
        assert controller.can_go_back is True
        assert controller.can_go_forward is True

    def test_state_persistence(self, controller, mock_views):
        """Test state persistence for views."""
        # Set initial state in a view
        data_view = mock_views["Data"]
        data_view.state = {"filter": "test", "sort": "column1"}

        # Navigate to Data view
        controller.set_active_view("Data")

        # Now navigate to another view which should save the state
        controller.set_active_view("Dashboard")

        # Check state was saved
        assert "Data" in controller._last_states
        assert controller._last_states["Data"] == {"filter": "test", "sort": "column1"}

        # Change the view's state
        data_view.state = {}

        # Navigate back to Data which should restore the state
        controller.set_active_view("Data")

        # Check state was restored
        assert data_view.state == {"filter": "test", "sort": "column1"}

    def test_save_and_load_settings(self, controller):
        """Test saving and loading settings."""
        # Setup test state
        controller.set_active_view("Data")
        controller.update_data_loaded_state(True)

        # Create settings object
        settings = QSettings("test", "test")
        settings.clear()

        # Save state
        controller.save_state(settings)

        # Reset controller
        controller._active_view = "Dashboard"
        controller._has_data_loaded = False
        controller._navigation_history = ["Dashboard"]
        controller._history_position = 0

        # Load state
        controller.load_state(settings)

        # Check state was loaded (except active view which is delayed)
        assert "Data" in controller._navigation_history

        # Test disabling persistence
        controller.state_persistence_enabled = False

        # Save in new location
        settings2 = QSettings("test2", "test2")
        settings2.clear()
        controller.save_state(settings2)

        # Reset and try to load
        controller._navigation_history = ["Dashboard"]
        controller.load_state(settings2)

        # Should not have loaded anything
        assert controller._navigation_history == ["Dashboard"]

    def test_max_history_limit(self, controller):
        """Test that history is limited to max_history entries."""
        # Set a small max history
        controller._max_history = 3

        # Navigate to several views
        controller.set_active_view("Dashboard")
        controller.set_active_view("Data")
        controller.set_active_view("Dashboard")
        controller.set_active_view("Data")
        controller.set_active_view("Dashboard")

        # History should be limited to 3 entries
        assert len(controller._navigation_history) == 3
        # And last entries should be kept
        assert controller._navigation_history[-3:] == ["Data", "Dashboard", "Data"]

    def test_data_view_controller_integration(
        self, controller, mock_data_view_controller, mock_views
    ):
        """Test integration with DataViewController."""
        # Set the data view controller
        controller.set_data_view_controller(mock_data_view_controller)

        # Navigate to Data view to trigger integration
        controller.set_active_view("Data")

        # Verify DataViewController was called
        assert mock_data_view_controller.view == mock_views["Data"]
        assert mock_data_view_controller.refresh_called

    def test_data_filter_applied(self, controller, mock_data_view_controller):
        """Test handling filter applied event from DataViewController."""
        # Set up controller with data view controller
        controller.set_data_view_controller(mock_data_view_controller)

        # Set Data view as active and initialize state
        controller.set_active_view("Data")
        controller._last_states["Data"] = {}

        # Emit filter applied signal
        filter_params = {
            "column": "PLAYER",
            "text": "test",
            "mode": "contains",
            "case_sensitive": False,
        }
        mock_data_view_controller.filter_applied.emit(filter_params)

        # Check that state was updated
        assert "Data" in controller._last_states
        assert "filter" in controller._last_states["Data"]
        assert controller._last_states["Data"]["filter"] == filter_params

    def test_data_sort_applied(self, controller, mock_data_view_controller):
        """Test handling sort applied event from DataViewController."""
        # Set up controller with data view controller
        controller.set_data_view_controller(mock_data_view_controller)

        # Set Data view as active and initialize state
        controller.set_active_view("Data")
        controller._last_states["Data"] = {}

        # Emit sort applied signal
        mock_data_view_controller.sort_applied.emit("PLAYER", True)

        # Check that state was updated
        assert "Data" in controller._last_states
        assert "sort" in controller._last_states["Data"]
        assert controller._last_states["Data"]["sort"] == {"column": "PLAYER", "ascending": True}

    def test_transition_in_progress(self, controller, monkeypatch):
        """Test handling view transitions in progress."""

        # Mock QTimer.singleShot to execute callback immediately
        def mock_single_shot(ms, callback):
            callback()

        monkeypatch.setattr(QTimer, "singleShot", mock_single_shot)

        # Spy on signals
        view_transition_started_spy = MagicMock()
        view_transition_completed_spy = MagicMock()
        controller.view_transition_started.connect(view_transition_started_spy)
        controller.view_transition_completed.connect(view_transition_completed_spy)

        # Set initial view
        controller.set_active_view("Dashboard")

        # Verify signals
        view_transition_started_spy.assert_called_once_with("", "Dashboard")
        view_transition_completed_spy.assert_called_once_with("Dashboard")

        # Verify transition flag was reset
        assert controller._view_transition_in_progress is False

    def test_throttling(self, controller, monkeypatch):
        """Test throttling of view availability updates."""
        # Mock QTimer.currentTime and QTimer.singleShot
        mock_time = MagicMock()
        mock_time.msecsSinceStartOfDay.return_value = 1000
        monkeypatch.setattr(QTimer, "currentTime", lambda: mock_time)

        def mock_single_shot(ms, callback):
            callback()

        monkeypatch.setattr(QTimer, "singleShot", mock_single_shot)

        # Update the first time
        controller._update_view_availability()

        # Update should be throttled
        assert controller._update_throttled is False

        # Try to update again immediately
        mock_time.msecsSinceStartOfDay.return_value = 1001
        controller._update_throttled = True
        controller._last_throttle_time = 1000
        controller._update_view_availability()

        # Verify that the update was skipped
        assert controller._update_throttled is False

    def test_queued_view_change(self, controller, monkeypatch):
        """Test queuing view changes during transitions."""
        # Mock QTimer.singleShot to control when callbacks execute
        callbacks = []

        def mock_single_shot(ms, callback):
            callbacks.append(callback)

        monkeypatch.setattr(QTimer, "singleShot", mock_single_shot)

        # Start a view transition
        controller._view_transition_in_progress = True

        # Request view change during transition
        controller.set_active_view("Data")

        # Verify change was queued
        assert controller._pending_view_change == "Data"

        # Mock completion of the first transition
        controller._complete_transition("Dashboard")

        # Verify pending change was processed
        assert controller._pending_view_change is None
        assert controller._active_view == "Data"

    def test_view_prerequisites_error_handling(self, controller):
        """Test error handling in view prerequisites."""

        # Register a prerequisite that raises an exception
        def failing_prerequisite():
            raise ValueError("Test error")

        controller.register_view_prerequisite("Charts", failing_prerequisite)

        # Check prerequisites
        result, reason = controller.check_view_prerequisites("Charts")

        # Verify error was handled properly
        assert result is False
        assert "Error checking prerequisites" in reason

    def test_error_handling_in_transition(self, controller, mock_views, monkeypatch):
        """Test error handling during view transition."""

        # Make populate_table raise an exception
        def raise_exception():
            raise ValueError("Test error")

        mock_views["Data"].populate_table = raise_exception

        # Mock QTimer.singleShot to execute callback immediately
        def mock_single_shot(ms, callback):
            callback()

        monkeypatch.setattr(QTimer, "singleShot", mock_single_shot)

        # Set Data view with populated needed
        mock_views["Data"].needs_population = True

        # Attempt to navigate to Data view
        controller.set_active_view("Data")

        # Verify view was still changed despite the error
        assert controller._active_view == "Data"
        assert controller._view_transition_in_progress is False
