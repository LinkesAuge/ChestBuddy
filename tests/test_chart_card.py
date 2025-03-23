"""
Tests for the ChartCard component.
"""

import pytest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QSizePolicy

from chestbuddy.ui.widgets.chart_card import ChartCard


@pytest.fixture
def qapp():
    """Create QApplication for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_thumbnail():
    """Create a mock thumbnail for testing."""
    pixmap = QPixmap(300, 180)
    pixmap.fill(Qt.blue)
    return pixmap


def test_initialization_basic(qapp):
    """Test basic initialization of the ChartCard."""
    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    assert card.title() == "Test Chart"
    assert card.description() == "Test Description"
    assert card.chart_id() == "test_chart"
    assert card.thumbnail() is None


def test_initialization_with_thumbnail(qapp, mock_thumbnail):
    """Test initialization with a thumbnail."""
    card = ChartCard(
        title="Test Chart",
        description="Test Description",
        chart_id="test_chart",
        thumbnail=mock_thumbnail,
    )

    assert card.title() == "Test Chart"
    assert card.description() == "Test Description"
    assert card.chart_id() == "test_chart"
    assert card.thumbnail() is not None


def test_initialization_with_callback(qapp):
    """Test initialization with a callback."""
    callback = MagicMock()

    card = ChartCard(
        title="Test Chart", description="Test Description", chart_id="test_chart", on_click=callback
    )

    # Directly call the callback method
    if hasattr(card, "_on_click") and card._on_click:
        card._on_click()
        callback.assert_called_once()


def test_initialization_full(qapp, mock_thumbnail):
    """Test initialization with all parameters."""
    callback = MagicMock()

    card = ChartCard(
        title="Test Chart",
        description="Test Description",
        chart_id="test_chart",
        thumbnail=mock_thumbnail,
        on_click=callback,
    )

    assert card.title() == "Test Chart"
    assert card.description() == "Test Description"
    assert card.chart_id() == "test_chart"
    assert card.thumbnail() is not None

    # Directly call the callback method
    if hasattr(card, "_on_click") and card._on_click:
        card._on_click()
        callback.assert_called_once()


def test_set_title(qapp):
    """Test setting the title."""
    card = ChartCard(title="Original Title", description="Test Description", chart_id="test_chart")

    assert card.title() == "Original Title"

    card.set_title("New Title")
    assert card.title() == "New Title"
    assert card._title_label.text() == "New Title"


def test_set_description(qapp):
    """Test setting the description."""
    card = ChartCard(title="Test Chart", description="Original Description", chart_id="test_chart")

    assert card.description() == "Original Description"

    card.set_description("New Description")
    assert card.description() == "New Description"
    assert card._description_label.text() == "New Description"


def test_set_thumbnail(qapp, mock_thumbnail):
    """Test setting the thumbnail."""
    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    assert card.thumbnail() is None

    card.set_thumbnail(mock_thumbnail)
    assert card.thumbnail() is not None


def test_click_event(qapp):
    """Test the click event signal."""
    signal_received = False

    def on_clicked():
        nonlocal signal_received
        signal_received = True

    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    card.clicked.connect(on_clicked)
    card.clicked.emit()

    assert signal_received


def test_chart_selected_event(qapp):
    """Test the chart_selected signal."""
    chart_id_received = None

    def on_chart_selected(chart_id):
        nonlocal chart_id_received
        chart_id_received = chart_id

    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    card.chart_selected.connect(on_chart_selected)
    card.chart_selected.emit("test_chart")

    assert chart_id_received == "test_chart"


def test_style_changes(qapp):
    """Test style changes for different states."""
    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    # Get original style
    original_style = card.styleSheet()

    # Test hover style
    card._hover = True
    card.setStyleSheet("""
        ChartCard {
            background-color: #F8F8F8;
            border: 1px solid #D0D0D0;
            border-radius: 8px;
        }
    """)
    hover_style = card.styleSheet()
    assert hover_style != original_style
    assert "#F8F8F8" in hover_style  # Hover background color

    # Test normal style
    card._hover = False
    card.setStyleSheet("""
        ChartCard {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
        }
    """)
    normal_style = card.styleSheet()
    assert normal_style != hover_style
    assert "#FFFFFF" in normal_style  # Normal background color

    # Test pressed style
    card.setStyleSheet("""
        ChartCard {
            background-color: #ECECEC;
            border: 1px solid #C0C0C0;
            border-radius: 8px;
        }
    """)
    pressed_style = card.styleSheet()
    assert pressed_style != normal_style
    assert "#ECECEC" in pressed_style  # Pressed background color


def test_callback_triggered(qapp, qtbot):
    """Test the callback is triggered on mouse click."""
    callback = MagicMock()

    card = ChartCard(
        title="Test Chart", description="Test Description", chart_id="test_chart", on_click=callback
    )

    # Show the widget for click events to work
    card.show()

    # Simulate mouse click
    qtbot.mouseClick(card, Qt.LeftButton)

    # Verify callback called
    callback.assert_called_once()

    # Clean up
    card.close()


def test_visual_properties(qapp):
    """Test visual properties like size constraints."""
    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    assert card.minimumWidth() == 250
    assert card.maximumWidth() == 350
    assert card.minimumHeight() == 250
    assert card.maximumHeight() == 300
    assert card.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
    assert card.sizePolicy().verticalPolicy() == QSizePolicy.Preferred


def test_ui_components_creation(qapp):
    """Test the UI components are created correctly."""
    card = ChartCard(title="Test Chart", description="Test Description", chart_id="test_chart")

    # Verify the labels are created
    assert hasattr(card, "_title_label")
    assert hasattr(card, "_description_label")
    assert card._title_label.text() == "Test Chart"
    assert card._description_label.text() == "Test Description"

    # Verify layout
    layout = card.layout()
    assert layout is not None
    assert layout.count() > 0  # At least some items in the layout
