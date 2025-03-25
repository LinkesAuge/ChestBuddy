"""
Tests for the ViewStateController class.

This module contains tests for the ViewStateController class, which manages view state
and transitions between views in the ChestBuddy application.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Signal, QObject
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

    def populate_table(self):
        self.populated = True
        self.needs_population = False

    def refresh(self):
        self.refreshed = True

    def needs_refresh(self):
        return True

    def set_data_loaded(self, loaded):
        self.data_loaded = loaded


class MockSidebar(QObject):
    """Mock sidebar class for testing."""

    navigation_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.active_item = None
        self.data_loaded_state = None

    def set_active_item(self, item):
        self.active_item = item

    def set_data_loaded(self, has_data):
        self.data_loaded_state = has_data


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
        assert mock_views["Dashboard"].data_loaded is True

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
