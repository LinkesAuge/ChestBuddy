"""
test_main_window_view_interaction.py

Description: Tests for MainWindow view interaction with ViewStateController
Usage:
    pytest tests/ui/test_main_window_view_interaction.py
"""

import pytest
from unittest.mock import MagicMock, patch, call
import logging

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QApplication, QWidget, QStackedWidget, QMessageBox

from chestbuddy.ui.main_window import MainWindow
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation
from chestbuddy.core.models import ChestDataModel


class MockSignal:
    """
    Mock PySide6 Signal for testing.

    This class mimics the behavior of PySide6 signals for testing purposes,
    allowing tests to connect to signals and emit them.
    """

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


class MockViewWithSignals(QWidget):
    """Mock view with signals for testing."""

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.needs_population = False
        self.populate_called = False
        self.controller = None
        self.state = {}

    def populate_table(self):
        self.populate_called = True

    def set_controller(self, controller):
        self.controller = controller

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state


@pytest.fixture
def mock_sidebar():
    """Create a mock sidebar navigation."""
    sidebar = MagicMock(spec=SidebarNavigation)
    # Replace signals with mock signals
    sidebar.navigation_changed = MockSignal(str)
    sidebar.data_dependent_view_clicked = MockSignal(str)
    return sidebar


@pytest.fixture
def mock_views():
    """Create mock views for testing."""
    views = {
        "Dashboard": MockViewWithSignals("Dashboard"),
        "Data": MockViewWithSignals("Data"),
        "Validation": MockViewWithSignals("Validation"),
        "Correction": MockViewWithSignals("Correction"),
        "Charts": MockViewWithSignals("Charts"),
        "Settings": MockViewWithSignals("Settings"),
    }
    return views


@pytest.fixture
def mock_data_model():
    """Create a mock data model."""
    model = MagicMock(spec=ChestDataModel)
    model.has_data.return_value = False
    return model


@pytest.fixture
def mock_view_state_controller(mock_data_model):
    """Create a mock ViewStateController."""
    controller = MagicMock(spec=ViewStateController)

    # Replace signals with mock signals
    controller.view_changed = MockSignal(str)
    controller.data_state_changed = MockSignal(bool)
    controller.view_prerequisites_failed = MockSignal(str, str)
    controller.view_availability_changed = MockSignal(dict)
    controller.navigation_history_changed = MockSignal(bool, bool)
    controller.view_transition_started = MockSignal(str, str)
    controller.view_transition_completed = MockSignal(str)

    controller.can_go_back = False
    controller.can_go_forward = False

    return controller


@pytest.fixture
def mock_file_operations_controller():
    """Create a mock FileOperationsController."""
    return MagicMock(spec=FileOperationsController)


@pytest.fixture
def mock_data_view_controller():
    """Create a mock DataViewController."""
    return MagicMock(spec=DataViewController)


@pytest.fixture
def mock_progress_controller():
    """Create a mock ProgressController."""
    return MagicMock(spec=ProgressController)


@pytest.fixture
def mock_ui_state_controller():
    """Create a mock UIStateController."""
    return MagicMock(spec=UIStateController)


@pytest.fixture
def main_window(
    qtbot,
    mock_data_model,
    mock_file_operations_controller,
    mock_progress_controller,
    mock_view_state_controller,
    mock_data_view_controller,
    mock_ui_state_controller,
):
    """Create a MainWindow instance with mocked controllers."""
    # Mock other services needed by MainWindow
    csv_service = MagicMock()
    validation_service = MagicMock()
    correction_service = MagicMock()
    chart_service = MagicMock()
    data_manager = MagicMock()
    config_manager = MagicMock()

    # Patch QMessageBox to avoid actual dialog display
    with patch("PySide6.QtWidgets.QMessageBox", autospec=True):
        # Create MainWindow instance
        window = MainWindow(
            data_model=mock_data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=mock_file_operations_controller,
            progress_controller=mock_progress_controller,
            view_state_controller=mock_view_state_controller,
            data_view_controller=mock_data_view_controller,
            ui_state_controller=mock_ui_state_controller,
            config_manager=config_manager,
        )

        qtbot.addWidget(window)
        window.show()

        # Reset the mocks to clear any calls during initialization
        mock_view_state_controller.reset_mock()
        mock_file_operations_controller.reset_mock()
        mock_data_view_controller.reset_mock()

        yield window

        # Clean up
        window.close()


class TestMainWindowViewInteraction:
    """Tests for MainWindow view interaction with ViewStateController."""

    def test_init_registers_views_with_controller(self, main_window, mock_view_state_controller):
        """Test that MainWindow correctly initializes the ViewStateController with UI components."""
        # Verify that set_ui_components was called during initialization
        assert mock_view_state_controller.set_ui_components.called

        # Verify set_active_view was called with "Dashboard" during initialization
        mock_view_state_controller.set_active_view.assert_called_with("Dashboard")

    def test_navigation_via_sidebar_triggers_view_change(
        self, main_window, mock_view_state_controller, monkeypatch
    ):
        """Test that sidebar navigation triggers view changes in ViewStateController."""
        # Get the sidebar instance
        sidebar = main_window._sidebar

        # Mock the sidebar's navigation_changed signal
        monkeypatch.setattr(sidebar, "navigation_changed", MockSignal(str))

        # Connect MainWindow to the signal
        sidebar.navigation_changed.connect(main_window._set_active_view)

        # Emit navigation_changed signal
        sidebar.navigation_changed.emit("Charts")

        # Verify that ViewStateController's set_active_view was called
        mock_view_state_controller.set_active_view.assert_called_with("Charts")

    def test_menu_view_actions_trigger_view_change(
        self, main_window, mock_view_state_controller, qtbot
    ):
        """Test that view menu actions trigger view changes."""
        # Get view menu actions
        view_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        assert view_menu is not None, "View menu not found"

        # Find Dashboard action
        dashboard_action = None
        for action in view_menu.actions():
            if "Dashboard" in action.text():
                dashboard_action = action
                break

        assert dashboard_action is not None, "Dashboard action not found"

        # Reset the mock to clear initialization calls
        mock_view_state_controller.reset_mock()

        # Trigger the action
        dashboard_action.trigger()

        # Verify ViewStateController was called
        mock_view_state_controller.set_active_view.assert_called_with("Dashboard")

    def test_response_to_view_changed_signal(
        self, main_window, mock_view_state_controller, monkeypatch
    ):
        """Test that MainWindow responds correctly to view_changed signal."""
        # Mock _update_ui to verify it gets called
        update_ui_mock = MagicMock()
        monkeypatch.setattr(main_window, "_update_ui", update_ui_mock)

        # Emit view_changed signal
        mock_view_state_controller.view_changed.emit("Charts")

        # Verify _update_ui was called
        update_ui_mock.assert_called_once()

    def test_response_to_data_state_changed_signal(self, main_window, mock_view_state_controller):
        """Test that MainWindow responds correctly to data_state_changed signal."""
        # Get references to data-dependent actions
        save_action = main_window._save_action
        validate_action = main_window._validate_action

        # Reset action enabled states
        save_action.setEnabled(False)
        validate_action.setEnabled(False)

        # Emit data_state_changed signal with True
        mock_view_state_controller.data_state_changed.emit(True)

        # Verify actions are enabled
        assert save_action.isEnabled()
        assert validate_action.isEnabled()

        # Emit data_state_changed signal with False
        mock_view_state_controller.data_state_changed.emit(False)

        # Verify actions are disabled
        assert not save_action.isEnabled()
        assert not validate_action.isEnabled()

    def test_view_history_navigation(self, main_window, mock_view_state_controller, qtbot):
        """Test view history navigation (back/forward)."""
        # Get back/forward actions
        back_action = main_window._back_action
        forward_action = main_window._forward_action

        # Set can_go_back and can_go_forward
        mock_view_state_controller.can_go_back = True
        mock_view_state_controller.can_go_forward = False

        # Emit navigation_history_changed
        mock_view_state_controller.navigation_history_changed.emit(True, False)

        # Verify actions are enabled/disabled appropriately
        assert back_action.isEnabled()
        assert not forward_action.isEnabled()

        # Trigger back action
        back_action.trigger()

        # Verify ViewStateController.go_back was called
        mock_view_state_controller.go_back.assert_called_once()

        # Reset and test forward
        mock_view_state_controller.reset_mock()
        mock_view_state_controller.can_go_back = False
        mock_view_state_controller.can_go_forward = True

        # Emit navigation_history_changed
        mock_view_state_controller.navigation_history_changed.emit(False, True)

        # Verify actions are enabled/disabled appropriately
        assert not back_action.isEnabled()
        assert forward_action.isEnabled()

        # Trigger forward action
        forward_action.trigger()

        # Verify ViewStateController.go_forward was called
        mock_view_state_controller.go_forward.assert_called_once()

    def test_data_dependent_view_protection(
        self, main_window, mock_view_state_controller, monkeypatch
    ):
        """Test protection for data-dependent views when no data is loaded."""
        # Mock QMessageBox to verify it's called
        mock_message_box = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", mock_message_box)

        # Emit view_prerequisites_failed signal
        mock_view_state_controller.view_prerequisites_failed.emit("Data", "No data loaded")

        # Verify QMessageBox.warning was called
        mock_message_box.assert_called_once()

    def test_view_availability_changed_updates_sidebar(
        self, main_window, mock_view_state_controller
    ):
        """Test that view_availability_changed signal updates the sidebar."""
        # Get sidebar
        sidebar = main_window._sidebar

        # Reset the sidebar mock
        sidebar.update_item_availability.reset_mock()

        # Create availability dict
        availability = {"Dashboard": True, "Data": False, "Validation": False}

        # Emit view_availability_changed signal
        mock_view_state_controller.view_availability_changed.emit(availability)

        # Verify sidebar.update_item_availability was called
        sidebar.update_item_availability.assert_called_with(availability)
