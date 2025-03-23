"""
test_stat_card.py

Contains tests for the StatCard UI component.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

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

    def test_set_title(self, qtbot, app):
        """Test setting the title after initialization."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)

        card.set_title("Available Files")
        assert card.title() == "Available Files"

    def test_set_value(self, qtbot, app):
        """Test setting the value after initialization."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        card.set_value("210")
        assert card.value() == "210"

    def test_set_subtitle(self, qtbot, app):
        """Test setting the subtitle after initialization."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)

        card.set_subtitle("CSV files loaded")
        assert card.subtitle() == "CSV files loaded"

    def test_set_icon(self, qtbot, app, sample_icon):
        """Test setting the icon after initialization."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)
        assert card.icon().isNull()

        card.set_icon(sample_icon)
        assert not card.icon().isNull()

    def test_set_trend(self, qtbot, app):
        """Test setting the trend indicator."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        assert card.trend() == StatCard.Trend.NONE
        assert card.trend_text() == ""

        card.set_trend(StatCard.Trend.UP, "12% increase")
        assert card.trend() == StatCard.Trend.UP
        assert card.trend_text() == "12% increase"

        card.set_trend(StatCard.Trend.DOWN, "5% decrease")
        assert card.trend() == StatCard.Trend.DOWN
        assert card.trend_text() == "5% decrease"

    def test_set_compact(self, qtbot, app):
        """Test setting the compact mode after initialization."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)
        assert card.is_compact() is False

        card.set_compact(True)
        assert card.is_compact() is True

    def test_set_clickable(self, qtbot, app):
        """Test setting the clickable property."""
        card = StatCard(title="Total Files")
        qtbot.addWidget(card)
        assert card.is_clickable() is True

        card.set_clickable(False)
        assert card.is_clickable() is False

        # Test that clicking doesn't emit signal when not clickable
        signal_catcher = SignalCatcher()
        card.clicked.connect(signal_catcher.handler)
        qtbot.mouseClick(card, Qt.LeftButton)
        assert not signal_catcher.signal_received

    def test_set_value_color(self, qtbot, app):
        """Test setting the value color."""
        card = StatCard(title="Total Files", value="156")
        qtbot.addWidget(card)

        initial_color = card.value_color()
        assert initial_color.name() != QColor(Colors.SUCCESS).name()

        card.set_value_color(QColor(Colors.SUCCESS))
        assert card.value_color().name() == QColor(Colors.SUCCESS).name()
