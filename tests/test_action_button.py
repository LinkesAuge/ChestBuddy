"""
test_action_button.py

Contains tests for the ActionButton UI component.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.widgets.action_button import ActionButton


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


class TestActionButton:
    def test_init_with_text_only(self, qtbot, app):
        """Test initializing a button with text only."""
        button = ActionButton("Test Button")
        qtbot.addWidget(button)

        assert button.text() == "Test Button"
        assert button.icon().isNull()
        assert button.is_compact() is False
        assert button.is_primary() is False
        assert button.name() == ""

    def test_init_with_icon_only(self, qtbot, app):
        """Test initializing a button with icon only."""
        # Create an actual icon with a small pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.red)
        icon = QIcon(pixmap)

        button = ActionButton(icon=icon)
        qtbot.addWidget(button)

        assert button.text() == ""
        assert not button.icon().isNull()

    def test_init_with_text_and_icon(self, qtbot, app):
        """Test initializing a button with both text and icon."""
        # Create an actual icon with a small pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.blue)
        icon = QIcon(pixmap)

        button = ActionButton("Test Button", icon=icon)
        qtbot.addWidget(button)

        assert button.text() == "Test Button"
        assert not button.icon().isNull()

    def test_init_with_tooltip(self, qtbot, app):
        """Test initializing a button with a tooltip."""
        button = ActionButton("Test Button", tooltip="This is a tooltip")
        qtbot.addWidget(button)

        assert button.toolTip() == "This is a tooltip"

    def test_init_compact(self, qtbot, app):
        """Test initializing a button in compact mode."""
        button = ActionButton("Test Button", compact=True)
        qtbot.addWidget(button)

        assert button.is_compact() is True

    def test_init_primary(self, qtbot, app):
        """Test initializing a button with primary styling."""
        button = ActionButton("Test Button", primary=True)
        qtbot.addWidget(button)

        assert button.is_primary() is True

    def test_init_disabled(self, qtbot, app):
        """Test initializing a disabled button."""
        button = ActionButton("Test Button")
        button.setEnabled(False)
        qtbot.addWidget(button)

        assert not button.isEnabled()

    def test_init_with_name(self, qtbot, app):
        """Test initializing a button with a name identifier."""
        button = ActionButton("Test Button", name="test_button")
        qtbot.addWidget(button)

        assert button.name() == "test_button"

    def test_click_signal(self, qtbot, app):
        """Test that clicking the button emits the clicked signal."""
        button = ActionButton("Test Button")
        qtbot.addWidget(button)

        signal_catcher = SignalCatcher()
        button.clicked.connect(signal_catcher.handler)

        # Click the button
        qtbot.mouseClick(button, Qt.LeftButton)

        assert signal_catcher.signal_received
        assert signal_catcher.signal_count == 1

    def test_set_compact(self, qtbot, app):
        """Test setting the compact mode after initialization."""
        button = ActionButton("Test Button")
        qtbot.addWidget(button)

        assert button.is_compact() is False

        button.set_compact(True)

        assert button.is_compact() is True

    def test_set_primary(self, qtbot, app):
        """Test setting the primary styling after initialization."""
        button = ActionButton("Test Button")
        qtbot.addWidget(button)

        assert button.is_primary() is False

        button.set_primary(True)

        assert button.is_primary() is True
