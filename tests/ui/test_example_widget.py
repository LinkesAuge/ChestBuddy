"""
Example UI test.

This is a sample UI test to demonstrate testing PySide6 components.
"""

import pytest
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, Slot, Qt
from tests.utils.helpers import SignalSpy


class ExampleWidget(QWidget):
    """Example widget for demonstration purposes."""

    textChanged = Signal(str)

    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        self.label = QLabel("Click the button")
        self.button = QPushButton("Change Text")

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.button.clicked.connect(self.on_button_clicked)

    @Slot()
    def on_button_clicked(self):
        """Handle button click."""
        self.label.setText("Button was clicked!")
        self.textChanged.emit("Button was clicked!")


@pytest.mark.ui
class TestExampleWidget:
    """Test case for the example widget."""

    def test_initial_state(self, enhanced_qtbot):
        """Test the initial state of the widget."""
        # Create and add widget to qtbot
        widget = enhanced_qtbot.add_widget(ExampleWidget())

        # Check initial state
        assert widget.label.text() == "Click the button"
        assert widget.button.text() == "Change Text"

    def test_button_click(self, enhanced_qtbot):
        """Test button click changes label text."""
        # Create and add widget to qtbot
        widget = enhanced_qtbot.add_widget(ExampleWidget())

        # Create a signal spy with automatic tracking
        spy = enhanced_qtbot.add_spy(widget.textChanged)

        # Click the button
        enhanced_qtbot.click_button(widget.button)

        # Check that the label text was updated
        assert widget.label.text() == "Button was clicked!"

        # Check that the signal was emitted
        assert spy.count == 1
        assert spy.emitted[0][0] == "Button was clicked!"

    def test_with_enhanced_qtbot(self, enhanced_qtbot):
        """Test using the enhanced qtbot fixture."""
        # Create widget with tracking
        widget = enhanced_qtbot.add_widget(ExampleWidget())

        # Click the button with enhanced method
        enhanced_qtbot.click_button(widget.button)

        # Check that the label text was updated
        assert widget.label.text() == "Button was clicked!"
