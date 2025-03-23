"""
test_stat_card.py

Contains tests for the StatCard UI component.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from pytestqt.qtbot import QtBot

from chestbuddy.ui.widgets.stat_card import StatCard
from chestbuddy.ui.resources.style import Colors


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


@pytest.fixture
def sample_icon():
    """Create a sample icon for testing."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.blue)
    return QIcon(pixmap)


class TestStatCard:
    """Test suite for the StatCard component."""

    @pytest.fixture
    def stat_card(self, qtbot):
        """Fixture providing a basic StatCard instance."""
        card = StatCard(title="Test Stat", value="100", subtitle="Test Subtitle", trend="+10%")
        qtbot.addWidget(card)
        return card

    def test_initialization(self, stat_card):
        """Test card initialization with default values."""
        # Check that properties are set correctly
        assert stat_card.title() == "Test Stat"
        assert stat_card.value() == "100"
        assert stat_card.subtitle() == "Test Subtitle"
        assert stat_card.trend() == "+10%"
        assert stat_card.size_hint() == "medium"

        # Check that UI elements exist
        assert stat_card._title_label.text() == "Test Stat"
        assert stat_card._value_label.text() == "100"
        assert stat_card._subtitle_label.text() == "Test Subtitle"
        assert stat_card._trend_label.text() == "+10%"

    def test_initialization_without_optional(self, qtbot):
        """Test card initialization without optional parameters."""
        card = StatCard(title="Basic Stat", value="50")
        qtbot.addWidget(card)

        # Check that properties are set correctly
        assert card.title() == "Basic Stat"
        assert card.value() == "50"
        assert card.subtitle() == ""
        assert card.trend() == ""

        # Check that optional UI elements don't exist
        assert card._subtitle_label is None
        assert card._trend_label is None

    def test_set_title(self, stat_card):
        """Test setting the title."""
        stat_card.set_title("New Title")
        assert stat_card.title() == "New Title"
        assert stat_card._title_label.text() == "New Title"

    def test_set_value(self, stat_card, qtbot):
        """Test setting the value and signal emission."""
        # Create signal spy
        signals_received = []
        stat_card.value_changed.connect(lambda value: signals_received.append(value))

        # Set new value
        stat_card.set_value("200")

        # Check value was updated
        assert stat_card.value() == "200"
        assert stat_card._value_label.text() == "200"

        # Check signal was emitted
        assert len(signals_received) == 1
        assert signals_received[0] == "200"

        # Set same value - signal should not be emitted again
        stat_card.set_value("200")
        assert len(signals_received) == 1

    def test_set_subtitle(self, stat_card):
        """Test setting the subtitle."""
        stat_card.set_subtitle("New Subtitle")
        assert stat_card.subtitle() == "New Subtitle"
        assert stat_card._subtitle_label.text() == "New Subtitle"

    def test_add_subtitle_later(self, qtbot):
        """Test adding a subtitle to a card that didn't have one initially."""
        # Create card without subtitle
        card = StatCard(title="Test", value="75")
        qtbot.addWidget(card)

        # Verify no subtitle label initially
        assert card._subtitle_label is None

        # Add subtitle
        card.set_subtitle("Added Later")

        # Verify subtitle was added
        assert card.subtitle() == "Added Later"
        assert card._subtitle_label is not None
        assert card._subtitle_label.text() == "Added Later"

    def test_set_trend(self, stat_card):
        """Test setting the trend."""
        # Test positive trend
        stat_card.set_trend("+20%")
        assert stat_card.trend() == "+20%"
        assert stat_card._trend_label.text() == "+20%"
        assert "color: #4caf50" in stat_card._trend_label.styleSheet()

        # Test negative trend
        stat_card.set_trend("-5%")
        assert stat_card.trend() == "-5%"
        assert stat_card._trend_label.text() == "-5%"
        assert "color: #f44336" in stat_card._trend_label.styleSheet()

        # Test neutral trend
        stat_card.set_trend("0%")
        assert stat_card.trend() == "0%"
        assert stat_card._trend_label.text() == "0%"
        assert "color: #7c7c7c" in stat_card._trend_label.styleSheet()

    def test_add_trend_later(self, qtbot):
        """Test adding a trend to a card that didn't have one initially."""
        # Create card without trend
        card = StatCard(title="Test", value="75")
        qtbot.addWidget(card)

        # Verify no trend label initially
        assert card._trend_label is None

        # Add trend
        card.set_trend("+15%")

        # Verify trend was added
        assert card.trend() == "+15%"
        assert card._trend_label is not None
        assert card._trend_label.text() == "+15%"
        assert "color: #4caf50" in card._trend_label.styleSheet()

    def test_size_hint(self, stat_card):
        """Test changing the size hint."""
        # Test small size
        stat_card.set_size_hint("small")
        assert stat_card.size_hint() == "small"
        assert stat_card.minimumHeight() == 80
        assert "font-size: 22px" in stat_card._value_label.styleSheet()

        # Test medium size
        stat_card.set_size_hint("medium")
        assert stat_card.size_hint() == "medium"
        assert stat_card.minimumHeight() == 100
        assert "font-size: 28px" in stat_card._value_label.styleSheet()

        # Test large size
        stat_card.set_size_hint("large")
        assert stat_card.size_hint() == "large"
        assert stat_card.minimumHeight() == 120
        assert "font-size: 36px" in stat_card._value_label.styleSheet()

        # Test invalid size (should not change)
        stat_card.set_size_hint("invalid")
        assert stat_card.size_hint() == "large"  # Remains unchanged

    def test_property_interface(self, stat_card):
        """Test Qt Property interface for the component."""
        # Test title property
        stat_card.setProperty("title", "Property Title")
        assert stat_card.property("title") == "Property Title"
        assert stat_card._title_label.text() == "Property Title"

        # Test value property
        stat_card.setProperty("value", "500")
        assert stat_card.property("value") == "500"
        assert stat_card._value_label.text() == "500"

        # Test subtitle property
        stat_card.setProperty("subtitle", "Property Subtitle")
        assert stat_card.property("subtitle") == "Property Subtitle"
        assert stat_card._subtitle_label.text() == "Property Subtitle"

        # Test trend property
        stat_card.setProperty("trend", "-10%")
        assert stat_card.property("trend") == "-10%"
        assert stat_card._trend_label.text() == "-10%"

        # Test size_hint property
        stat_card.setProperty("size_hint", "small")
        assert stat_card.property("size_hint") == "small"
        assert stat_card.minimumHeight() == 80

    def test_init_with_title_only(self, qtbot, app):
        """Test initializing a stat card with title only."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)

        assert card.title() == "Total Files"
        assert card.value() == ""
        assert card.subtitle() == ""
        assert card.icon().isNull()
        assert card.is_compact() is False
        assert card.is_clickable() is True
        assert card.trend() == StatCard.Trend.NONE
        assert card.trend_text() == ""

    def test_init_with_title_and_value(self, qtbot, app):
        """Test initializing a stat card with title and value."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        assert card.title() == "Total Files"
        assert card.value() == "156"
        assert card.subtitle() == ""
        assert card.icon().isNull()

    def test_init_with_all_props(self, qtbot, app, sample_icon):
        """Test initializing a stat card with all properties."""
        card = StatCard(
            title="Total Files",
            value="156",
            subtitle="CSV files loaded",
            icon=sample_icon,
            compact=True,
        )
        qtbot.addWidget(card)

        assert card.title() == "Total Files"
        assert card.value() == "156"
        assert card.subtitle() == "CSV files loaded"
        assert not card.icon().isNull()
        assert card.is_compact() is True

    def test_click_signal(self, qtbot, app):
        """Test that clicking the card emits the clicked signal."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        signal_catcher = SignalCatcher()
        card.clicked.connect(signal_catcher.handler)

        # Click the card
        qtbot.mouseClick(card, Qt.LeftButton)

        assert signal_catcher.signal_received
        assert signal_catcher.signal_count == 1

    def test_set_value_color(self, qtbot, app):
        """Test setting the value color."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        initial_color = card.value_color()
        assert initial_color.name() != QColor(Colors.SUCCESS).name()

        card.set_value_color(QColor(Colors.SUCCESS))
        assert card.value_color().name() == QColor(Colors.SUCCESS).name()
