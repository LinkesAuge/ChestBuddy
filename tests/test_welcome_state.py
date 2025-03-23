import pytest
from PySide6.QtCore import Qt, Signal
from pytestqt.qtbot import QtBot

from chestbuddy.ui.widgets.welcome_state import WelcomeStateWidget


class TestWelcomeStateWidget:
    """Test suite for the WelcomeStateWidget."""

    @pytest.fixture
    def welcome_widget(self, qtbot):
        """Fixture providing a WelcomeStateWidget instance."""
        widget = WelcomeStateWidget()
        qtbot.addWidget(widget)
        return widget

    def test_initialization(self, welcome_widget):
        """Test widget initialization with default values."""
        # Check widget is properly initialized
        assert not welcome_widget.get_dont_show_again()

        # Verify there are guide steps
        assert len(welcome_widget._steps) > 0

        # Check initial step
        assert welcome_widget._current_step == 0

        # Previous button should be disabled on the first step
        assert not welcome_widget._prev_button.isEnabled()

        # Next button should be enabled
        assert welcome_widget._next_button.isEnabled()

    def test_step_navigation(self, welcome_widget, qtbot):
        """Test navigation between guide steps."""
        # Should start at step 0
        assert welcome_widget._current_step == 0

        # Click next button
        qtbot.mouseClick(welcome_widget._next_button, Qt.LeftButton)
        assert welcome_widget._current_step == 1

        # Previous button should now be enabled
        assert welcome_widget._prev_button.isEnabled()

        # Click previous button
        qtbot.mouseClick(welcome_widget._prev_button, Qt.LeftButton)
        assert welcome_widget._current_step == 0

        # Previous button should be disabled again
        assert not welcome_widget._prev_button.isEnabled()

        # Navigate to last step
        for _ in range(len(welcome_widget._steps) - 1):
            qtbot.mouseClick(welcome_widget._next_button, Qt.LeftButton)

        # Verify last step
        assert welcome_widget._current_step == len(welcome_widget._steps) - 1

        # Next button should show "Finish" on the last step
        assert welcome_widget._next_button.text() == "Finish"

    def test_welcome_action_signal(self, welcome_widget, qtbot):
        """Test welcome_action_clicked signal emission."""
        # Create signal spy
        signals_received = []

        # Connect signal
        welcome_widget.welcome_action_clicked.connect(
            lambda action: signals_received.append(action)
        )

        # Click the action button
        qtbot.mouseClick(welcome_widget._action_button, Qt.LeftButton)

        # Check signal was emitted with the correct action name
        assert len(signals_received) == 1
        assert signals_received[0] == welcome_widget._steps[0]["action_name"]

        # Navigate to the next step
        qtbot.mouseClick(welcome_widget._next_button, Qt.LeftButton)

        # Click the action button again
        qtbot.mouseClick(welcome_widget._action_button, Qt.LeftButton)

        # Check signal was emitted with the correct action name
        assert len(signals_received) == 2
        assert signals_received[1] == welcome_widget._steps[1]["action_name"]

    def test_finish_signal(self, welcome_widget, qtbot):
        """Test signal emission when finishing the guide."""
        # Create signal spy
        signals_received = []

        # Connect signal
        welcome_widget.welcome_action_clicked.connect(
            lambda action: signals_received.append(action)
        )

        # Navigate to the last step
        for _ in range(len(welcome_widget._steps) - 1):
            qtbot.mouseClick(welcome_widget._next_button, Qt.LeftButton)

        # Click the finish button
        qtbot.mouseClick(welcome_widget._next_button, Qt.LeftButton)

        # Check signal was emitted with 'welcome_complete'
        assert len(signals_received) == 1
        assert signals_received[0] == "welcome_complete"

    def test_dont_show_again(self, welcome_widget, qtbot):
        """Test "Don't show again" checkbox functionality."""
        # Create signal spy
        signals_received = []

        # Connect signal
        welcome_widget.dont_show_again_changed.connect(
            lambda checked: signals_received.append(checked)
        )

        # Initially unchecked
        assert not welcome_widget.get_dont_show_again()

        # Check the checkbox
        welcome_widget._dont_show_checkbox.setChecked(True)

        # Verify it's checked
        assert welcome_widget.get_dont_show_again()

        # Verify signal was emitted
        assert len(signals_received) == 1
        assert signals_received[0] is True

        # Uncheck the checkbox
        welcome_widget._dont_show_checkbox.setChecked(False)

        # Verify it's unchecked
        assert not welcome_widget.get_dont_show_again()

        # Verify signal was emitted
        assert len(signals_received) == 2
        assert signals_received[1] is False

    def test_set_current_step(self, welcome_widget):
        """Test manually setting the current step."""
        # Set to step 2
        welcome_widget.set_current_step(2)

        # Verify current step
        assert welcome_widget._current_step == 2

        # Previous button should be enabled
        assert welcome_widget._prev_button.isEnabled()

        # Set to invalid step (too high)
        welcome_widget.set_current_step(100)

        # Should not change
        assert welcome_widget._current_step == 2

        # Set to invalid step (negative)
        welcome_widget.set_current_step(-1)

        # Should not change
        assert welcome_widget._current_step == 2
