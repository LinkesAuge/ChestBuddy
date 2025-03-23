"""
test_action_toolbar.py

Contains tests for the ActionToolbar UI component.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.widgets.action_button import ActionButton
from chestbuddy.ui.widgets.action_toolbar import ActionToolbar


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


class TestActionToolbar:
    def test_initialization_empty(self, qtbot, app):
        """Test initialization with no buttons."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        assert toolbar.count() == 0
        assert toolbar.group_count() == 0

    def test_add_button(self, qtbot, app):
        """Test adding a button to the toolbar."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button = ActionButton("Test Button")
        toolbar.add_button(button)

        assert toolbar.count() == 1
        assert toolbar.get_button(0) == button

    def test_add_multiple_buttons(self, qtbot, app):
        """Test adding multiple buttons to the toolbar."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button1 = ActionButton("Button 1")
        button2 = ActionButton("Button 2")
        button3 = ActionButton("Button 3")

        toolbar.add_button(button1)
        toolbar.add_button(button2)
        toolbar.add_button(button3)

        assert toolbar.count() == 3
        assert toolbar.get_button(0) == button1
        assert toolbar.get_button(1) == button2
        assert toolbar.get_button(2) == button3

    def test_button_group(self, qtbot, app):
        """Test adding buttons in groups with separators."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        # Add first group
        toolbar.start_group("Group 1")
        group1_button1 = ActionButton("Group 1 Button 1")
        group1_button2 = ActionButton("Group 1 Button 2")
        toolbar.add_button(group1_button1)
        toolbar.add_button(group1_button2)
        toolbar.end_group()

        # Add second group
        toolbar.start_group("Group 2")
        group2_button1 = ActionButton("Group 2 Button 1")
        group2_button2 = ActionButton("Group 2 Button 2")
        toolbar.add_button(group2_button1)
        toolbar.add_button(group2_button2)
        toolbar.end_group()

        assert toolbar.count() == 4  # 4 buttons
        assert toolbar.group_count() == 2  # 2 groups

        # Check that there's a separator between groups
        assert toolbar.has_separator_after(1)  # After Group 1 Button 2

        # Check group contents
        group1_buttons = toolbar.get_buttons_in_group("Group 1")
        assert len(group1_buttons) == 2
        assert group1_buttons[0] == group1_button1
        assert group1_buttons[1] == group1_button2

        group2_buttons = toolbar.get_buttons_in_group("Group 2")
        assert len(group2_buttons) == 2
        assert group2_buttons[0] == group2_button1
        assert group2_buttons[1] == group2_button2

    def test_remove_button(self, qtbot, app):
        """Test removing a button from the toolbar."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button1 = ActionButton("Button 1")
        button2 = ActionButton("Button 2")

        toolbar.add_button(button1)
        toolbar.add_button(button2)

        assert toolbar.count() == 2

        # Remove the first button
        result = toolbar.remove_button(button1)

        assert result is True
        assert toolbar.count() == 1
        assert toolbar.get_button(0) == button2

    def test_button_click(self, qtbot, app):
        """Test that buttons in toolbar emit correct signals."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button = ActionButton("Test Button")
        toolbar.add_button(button)

        signal_catcher = SignalCatcher()
        button.clicked.connect(signal_catcher.handler)

        # Click the button in the toolbar
        qtbot.mouseClick(button, Qt.LeftButton)

        assert signal_catcher.signal_received
        assert signal_catcher.signal_count == 1

    def test_layout_spacing(self, qtbot, app):
        """Test that spacing is applied correctly."""
        toolbar = ActionToolbar(spacing=10)
        qtbot.addWidget(toolbar)

        # Default layout is horizontal, check horizontal spacing
        assert toolbar._layout.spacing() == 10

        # Change spacing
        toolbar.set_spacing(20)

        assert toolbar._layout.spacing() == 20

    def test_get_button_by_name(self, qtbot, app):
        """Test retrieving a button by name."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button = ActionButton("Test Button", name="test_button")
        toolbar.add_button(button)

        retrieved_button = toolbar.get_button_by_name("test_button")

        assert retrieved_button == button
        assert retrieved_button.text() == "Test Button"

    def test_vertical_toolbar(self, qtbot, app):
        """Test toolbar in vertical orientation."""
        toolbar = ActionToolbar(vertical=True)
        qtbot.addWidget(toolbar)

        # Add a few buttons
        button1 = ActionButton("Button 1")
        button2 = ActionButton("Button 2")
        toolbar.add_button(button1)
        toolbar.add_button(button2)

        # Make sure we have the correct layout type
        assert toolbar._vertical is True

        # We'd need a way to verify the layout is vertical
        # This is a bit simplistic but checks that our class property is set
        assert toolbar.count() == 2

    def test_add_spacer(self, qtbot, app):
        """Test adding a spacer to the toolbar."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        button1 = ActionButton("Button 1")
        button2 = ActionButton("Button 2")
        toolbar.add_button(button1)

        # Add a spacer
        toolbar.add_spacer()

        # Add another button
        toolbar.add_button(button2)

        # Verify buttons are still accessible
        assert toolbar.count() == 2
        assert toolbar.get_button(0) == button1
        assert toolbar.get_button(1) == button2

    def test_clear(self, qtbot, app):
        """Test clearing all buttons from the toolbar."""
        toolbar = ActionToolbar()
        qtbot.addWidget(toolbar)

        # Add some buttons in groups
        toolbar.start_group("Group 1")
        toolbar.add_button(ActionButton("Button 1"))
        toolbar.add_button(ActionButton("Button 2"))
        toolbar.end_group()

        assert toolbar.count() == 2
        assert toolbar.group_count() == 1

        # Clear the toolbar
        toolbar.clear()

        assert toolbar.count() == 0
        assert toolbar.group_count() == 0
