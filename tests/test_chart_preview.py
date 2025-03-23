"""
test_chart_preview.py

Contains tests for the ChartPreview UI component.
"""

import pytest
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from chestbuddy.ui.widgets.chart_preview import ChartPreview
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
def sample_chart():
    """Create a sample chart for testing."""
    chart = QChart()
    chart.setTitle("Sample Chart")

    # Create a simple bar series
    series = QBarSeries()
    bar_set = QBarSet("Values")
    bar_set.append([3, 5, 8, 13, 5])
    series.append(bar_set)

    chart.addSeries(series)

    # Set up axes
    axis_x = QBarCategoryAxis()
    axis_x.append(["A", "B", "C", "D", "E"])
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setRange(0, 15)
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)

    return chart


@pytest.fixture
def sample_icon():
    """Create a sample icon for testing."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.blue)
    return QIcon(pixmap)


class TestChartPreview:
    def test_init_with_title_only(self, qtbot, app):
        """Test initializing a chart preview with title only."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        assert preview.title() == "Sample Chart"
        assert preview.subtitle() == ""
        assert preview.icon().isNull()

    def test_init_with_all_props(self, qtbot, app, sample_chart, sample_icon):
        """Test initializing a chart preview with all properties."""
        preview = ChartPreview(
            title="Sample Chart",
            subtitle="Data from last month",
            chart=sample_chart,
            icon=sample_icon,
        )
        qtbot.addWidget(preview)

        assert preview.title() == "Sample Chart"
        assert preview.subtitle() == "Data from last month"
        assert not preview.icon().isNull()
        assert preview.chart() is not None

    def test_click_signal(self, qtbot, app):
        """Test that clicking the preview emits the clicked signal."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        signal_catcher = SignalCatcher()
        preview.clicked.connect(signal_catcher.handler)

        # Click the preview
        qtbot.mouseClick(preview, Qt.LeftButton)

        assert signal_catcher.signal_received
        assert signal_catcher.signal_count == 1

    def test_set_title(self, qtbot, app):
        """Test setting the title after initialization."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        preview.set_title("Updated Chart")
        assert preview.title() == "Updated Chart"

    def test_set_subtitle(self, qtbot, app):
        """Test setting the subtitle after initialization."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        preview.set_subtitle("New data analysis")
        assert preview.subtitle() == "New data analysis"

    def test_set_chart(self, qtbot, app, sample_chart):
        """Test setting the chart after initialization."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        preview.set_chart(sample_chart)
        assert preview.chart() is not None

    def test_set_icon(self, qtbot, app, sample_icon):
        """Test setting the icon after initialization."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        preview.set_icon(sample_icon)
        assert not preview.icon().isNull()

    def test_set_clickable(self, qtbot, app):
        """Test setting the clickable property."""
        preview = ChartPreview(title="Sample Chart")
        qtbot.addWidget(preview)

        assert preview.is_clickable() is True

        preview.set_clickable(False)
        assert preview.is_clickable() is False

        # Test that clicking doesn't emit signal when not clickable
        signal_catcher = SignalCatcher()
        preview.clicked.connect(signal_catcher.handler)
        qtbot.mouseClick(preview, Qt.LeftButton)
        assert not signal_catcher.signal_received

    def test_set_compact(self, qtbot, app, sample_chart):
        """Test setting the compact mode."""
        preview = ChartPreview(title="Sample Chart", chart=sample_chart)
        qtbot.addWidget(preview)

        assert preview.is_compact() is False

        preview.set_compact(True)
        assert preview.is_compact() is True

    def test_clear_chart(self, qtbot, app, sample_chart):
        """Test clearing the chart."""
        preview = ChartPreview(title="Sample Chart", chart=sample_chart)
        qtbot.addWidget(preview)

        assert preview.chart() is not None

        preview.clear_chart()
        assert preview.chart() is None
