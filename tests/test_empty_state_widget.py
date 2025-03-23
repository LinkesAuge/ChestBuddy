"""
test_empty_state_widget.py

Contains tests for the EmptyStateWidget UI component.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget


class SignalCatcher:
    """Helper class to catch Qt signals."""

    def __init__(self):
        self.signal_received = False
        self.signal_args = None
        self.signal_count = 0

    def handler(self, *args):
        self.signal_received = True
        self.signal_args = args
        self.signal_count += 1


@pytest.fixture
def app():
    """Create a QApplication instance."""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


class TestEmptyStateWidget:
    def test_initialization_basic(self, qtbot, app):
        """Test basic initialization with title and message."""
        widget = EmptyStateWidget(title="No Data Available", message="Import data to get started.")
        qtbot.addWidget(widget)

        assert widget.title() == "No Data Available"
        assert widget.message() == "Import data to get started."
        assert widget.action_button() is None  # No action button by default
        assert widget.icon().isNull()  # No icon by default

    def test_initialization_with_action(self, qtbot, app):
        """Test initialization with action button."""
        widget = EmptyStateWidget(
            title="No Data Available",
            message="Import data to get started.",
            action_text="Import Data",
        )
        qtbot.addWidget(widget)

        assert widget.title() == "No Data Available"
        assert widget.message() == "Import data to get started."
        assert widget.action_button() is not None
        assert widget.action_button().text() == "Import Data"

    def test_initialization_with_icon(self, qtbot, app):
        """Test initialization with custom icon."""
        # Create an actual icon with a small pixmap
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.red)
        icon = QIcon(pixmap)

        widget = EmptyStateWidget(
            title="No Data Available", message="Import data to get started.", icon=icon
        )
        qtbot.addWidget(widget)

        assert not widget.icon().isNull()

    def test_initialization_full(self, qtbot, app):
        """Test initialization with all properties."""
        # Create an actual icon with a small pixmap
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.blue)
        icon = QIcon(pixmap)

        action_called = False

        def on_action():
            nonlocal action_called
            action_called = True

        widget = EmptyStateWidget(
            title="No Data Available",
            message="Import data to get started.",
            action_text="Import Data",
            action_callback=on_action,
            icon=icon,
        )
        qtbot.addWidget(widget)

        assert widget.title() == "No Data Available"
        assert widget.message() == "Import data to get started."
        assert widget.action_button() is not None
        assert widget.action_button().text() == "Import Data"
        assert not widget.icon().isNull()

        # Test the callback
        qtbot.mouseClick(widget.action_button(), Qt.LeftButton)
        assert action_called

    def test_set_title(self, qtbot, app):
        """Test setting the title."""
        widget = EmptyStateWidget(title="Initial Title", message="Some message")
        qtbot.addWidget(widget)

        widget.set_title("New Title")

        assert widget.title() == "New Title"

    def test_set_message(self, qtbot, app):
        """Test setting the message."""
        widget = EmptyStateWidget(title="Some Title", message="Initial Message")
        qtbot.addWidget(widget)

        widget.set_message("New Message")

        assert widget.message() == "New Message"

    def test_set_action(self, qtbot, app):
        """Test setting the action button."""
        widget = EmptyStateWidget(title="No Data Available", message="Import data to get started.")
        qtbot.addWidget(widget)

        # Initially no action button
        assert widget.action_button() is None

        # Add an action button
        widget.set_action("Import Data")

        assert widget.action_button() is not None
        assert widget.action_button().text() == "Import Data"

        # Change the action text
        widget.set_action("Load Data")

        assert widget.action_button().text() == "Load Data"

    def test_action_clicked_signal(self, qtbot, app):
        """Test that action button emits signal when clicked."""
        widget = EmptyStateWidget(
            title="No Data Available",
            message="Import data to get started.",
            action_text="Import Data",
        )
        qtbot.addWidget(widget)

        signal_catcher = SignalCatcher()
        widget.action_clicked.connect(signal_catcher.handler)

        # Click the action button
        qtbot.mouseClick(widget.action_button(), Qt.LeftButton)

        assert signal_catcher.signal_received
        assert signal_catcher.signal_count == 1

    def test_custom_action_callback(self, qtbot, app):
        """Test custom action callback."""
        callback_called = False

        def action_callback():
            nonlocal callback_called
            callback_called = True

        widget = EmptyStateWidget(
            title="No Data Available",
            message="Import data to get started.",
            action_text="Import Data",
            action_callback=action_callback,
        )
        qtbot.addWidget(widget)

        # Click the action button
        qtbot.mouseClick(widget.action_button(), Qt.LeftButton)

        assert callback_called

    def test_set_icon(self, qtbot, app):
        """Test setting the icon."""
        widget = EmptyStateWidget(title="No Data Available", message="Import data to get started.")

        qtbot.addWidget(widget)

        # Initially no custom icon
        assert widget.icon().isNull()

        # Set an icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.green)
        icon = QIcon(pixmap)
        widget.set_icon(icon)

        assert not widget.icon().isNull()

    def test_refresh_ui(self, qtbot, app):
        """Test that UI refreshes correctly after property changes."""
        widget = EmptyStateWidget(title="Initial Title", message="Initial Message")
        qtbot.addWidget(widget)

        # Change multiple properties
        widget.set_title("New Title")
        widget.set_message("New Message")
        widget.set_action("Do Action")

        # Check that UI reflects the changes
        assert widget.title() == "New Title"
        assert widget.message() == "New Message"
        assert widget.action_button() is not None
        assert widget.action_button().text() == "Do Action"
