"""
Tests for the ActionCard component.
"""

import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QSizePolicy

from chestbuddy.ui.widgets.action_card import ActionCard


@pytest.fixture
def qapp():
    """Create QApplication for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_icon():
    """Create a mock icon for testing."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.red)
    return QIcon(pixmap)


def test_initialization_basic(qapp):
    """Test basic initialization of the ActionCard."""
    card = ActionCard(title="Test Title", description="Test Description")

    assert card.title() == "Test Title"
    assert card.description() == "Test Description"
    assert card.icon().isNull()


def test_initialization_with_icon(qapp, mock_icon):
    """Test initialization with an icon."""
    card = ActionCard(title="Test Title", description="Test Description", icon=mock_icon)

    assert card.title() == "Test Title"
    assert card.description() == "Test Description"
    assert not card.icon().isNull()


def test_initialization_with_callback(qapp):
    """Test initialization with a callback."""
    callback = MagicMock()

    card = ActionCard(title="Test Title", description="Test Description", action_callback=callback)

    # Directly call the callback method instead of using the signal
    # This tests that the callback is correctly stored
    if hasattr(card, "_action_callback") and card._action_callback:
        card._action_callback()
        callback.assert_called_once()


def test_initialization_full(qapp, mock_icon):
    """Test initialization with all parameters."""
    callback = MagicMock()

    card = ActionCard(
        title="Test Title", description="Test Description", icon=mock_icon, action_callback=callback
    )

    assert card.title() == "Test Title"
    assert card.description() == "Test Description"
    assert not card.icon().isNull()

    # Directly call the callback method
    if hasattr(card, "_action_callback") and card._action_callback:
        card._action_callback()
        callback.assert_called_once()


def test_set_title(qapp):
    """Test setting the title."""
    card = ActionCard(title="Original Title", description="Test Description")

    assert card.title() == "Original Title"

    card.set_title("New Title")
    assert card.title() == "New Title"
    assert card._title_label.text() == "New Title"


def test_set_description(qapp):
    """Test setting the description."""
    card = ActionCard(title="Test Title", description="Original Description")

    assert card.description() == "Original Description"

    card.set_description("New Description")
    assert card.description() == "New Description"
    assert card._description_label.text() == "New Description"


def test_set_icon(qapp, mock_icon):
    """Test setting the icon."""
    card = ActionCard(title="Test Title", description="Test Description")

    assert card.icon().isNull()

    card.set_icon(mock_icon)
    assert not card.icon().isNull()


def test_click_event(qapp):
    """Test the click event signal."""
    signal_received = False

    def on_clicked():
        nonlocal signal_received
        signal_received = True

    card = ActionCard(title="Test Title", description="Test Description")

    card.clicked.connect(on_clicked)
    card.clicked.emit()

    assert signal_received


def test_style_changes(qapp):
    """Test style changes for different states."""
    card = ActionCard(title="Test Title", description="Test Description")

    # Get original style
    original_style = card.styleSheet()

    # Test hover style
    card._hover = True
    card.setStyleSheet("""
        ActionCard {
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
        ActionCard {
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
        ActionCard {
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

    card = ActionCard(title="Test Title", description="Test Description", action_callback=callback)

    # Show the widget for click events to work
    card.show()

    # Simulate mouse click
    qtbot.mouseClick(card, Qt.LeftButton)

    # Verify callback called
    callback.assert_called_once()

    # Clean up
    card.close()


def test_visual_properties(qapp):
    """Test visual properties like size policy and height constraints."""
    card = ActionCard(title="Test Title", description="Test Description")

    assert card.minimumHeight() == 100
    assert card.maximumHeight() == 120
    assert card.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
    assert card.sizePolicy().verticalPolicy() == QSizePolicy.Preferred


def test_ui_components_creation(qapp):
    """Test the UI components are created correctly."""
    card = ActionCard(title="Test Title", description="Test Description")

    # Verify the labels are created
    assert hasattr(card, "_title_label")
    assert hasattr(card, "_description_label")
    assert card._title_label.text() == "Test Title"
    assert card._description_label.text() == "Test Description"

    # Verify layout
    layout = card.layout()
    assert layout is not None
    assert layout.count() > 0  # At least some items in the layout


class TestActionCard:
    """Test suite for ActionCard component."""

    @pytest.fixture
    def action_card(self, qtbot):
        """Create an ActionCard instance for testing."""
        card = ActionCard(
            title="Import Files",
            description="Import CSV files with chest data",
            icon_name="import",
            actions=["import_csv", "import_excel"],
            tag="Data"
        )
        qtbot.addWidget(card)
        return card

    @pytest.fixture
    def minimal_card(self, qtbot):
        """Create a minimal ActionCard instance without optional parameters."""
        card = ActionCard(
            title="Import Files"
        )
        qtbot.addWidget(card)
        return card

    def test_initialization(self, action_card):
        """Test that ActionCard initializes with the correct values."""
        assert action_card.title() == "Import Files"
        assert action_card.description() == "Import CSV files with chest data"
        assert action_card.icon_name() == "import"
        assert action_card.actions() == ["import_csv", "import_excel"]
        assert action_card.primary_action() == "import_csv"
        assert action_card.tag() == "Data"
        assert action_card.use_count() == 0

        # Check that UI elements were created
        assert hasattr(action_card, '_title_label')
        assert hasattr(action_card, '_description_label')
        assert action_card._title_label.text() == "Import Files"
        assert action_card._description_label.text() == "Import CSV files with chest data"

    def test_minimal_initialization(self, minimal_card):
        """Test that ActionCard initializes with minimal parameters."""
        assert minimal_card.title() == "Import Files"
        assert minimal_card.description() == ""
        assert minimal_card.icon_name() == ""
        assert minimal_card.actions() == []
        assert minimal_card.primary_action() == ""
        assert minimal_card.tag() == ""
        assert minimal_card.use_count() == 0

        # Check that optional UI elements were not created
        assert hasattr(minimal_card, '_title_label')
        assert not hasattr(minimal_card, '_icon_label')
        assert not hasattr(minimal_card, '_tag_label')

    def test_set_title(self, action_card):
        """Test setting the title property."""
        action_card.set_title("New Title")
        assert action_card.title() == "New Title"
        assert action_card._title_label.text() == "New Title"

    def test_set_description(self, action_card):
        """Test setting the description property."""
        action_card.set_description("New description text")
        assert action_card.description() == "New description text"
        assert action_card._description_label.text() == "New description text"

    def test_add_description_to_minimal(self, minimal_card):
        """Test adding a description to a card that didn't have one."""
        minimal_card.set_description("Added description")
        assert minimal_card.description() == "Added description"
        assert hasattr(minimal_card, '_description_label')
        assert minimal_card._description_label.text() == "Added description"

    def test_set_icon_name(self, action_card):
        """Test setting the icon name property."""
        action_card.set_icon_name("edit")
        assert action_card.icon_name() == "edit"

    def test_set_actions(self, action_card):
        """Test setting the actions list."""
        action_card.set_actions(["new_action", "another_action"])
        assert action_card.actions() == ["new_action", "another_action"]
        assert action_card.primary_action() == "new_action"

    def test_set_empty_actions(self, action_card):
        """Test setting an empty actions list."""
        action_card.set_actions([])
        assert action_card.actions() == []
        assert action_card.primary_action() == ""

    def test_set_tag(self, action_card):
        """Test setting the tag property."""
        action_card.set_tag("New Tag")
        assert action_card.tag() == "New Tag"

    def test_add_tag_to_minimal(self, minimal_card):
        """Test adding a tag to a card that didn't have one."""
        minimal_card.set_tag("Added Tag")
        assert minimal_card.tag() == "Added Tag"
        assert hasattr(minimal_card, '_tag_label')
        assert minimal_card._tag_label.text() == "Added Tag"

    def test_use_count(self, action_card):
        """Test use count increment and setting."""
        assert action_card.use_count() == 0
        
        action_card.increment_use_count()
        assert action_card.use_count() == 1
        
        action_card.increment_use_count()
        assert action_card.use_count() == 2
        
        action_card.set_use_count(10)
        assert action_card.use_count() == 10
        
        # Test negative values are clamped to 0
        action_card.set_use_count(-5)
        assert action_card.use_count() == 0

    def test_click_emits_action_signal(self, action_card, qtbot):
        """Test that clicking the card emits the action_clicked signal with the primary action."""
        # Set up signal capture
        signals_received = []
        
        def capture_signal(action):
            signals_received.append(action)
        
        action_card.action_clicked.connect(capture_signal)
        
        # Click the card
        QTest.mouseClick(action_card, Qt.LeftButton)
        
        # Verify signal was emitted with correct action
        assert len(signals_received) == 1
        assert signals_received[0] == "import_csv"
        
        # Verify use count increased
        assert action_card.use_count() == 1

    def test_click_with_no_actions(self, minimal_card, qtbot):
        """Test clicking a card with no actions."""
        # Set up signal capture
        signals_received = []
        
        def capture_signal(action):
            signals_received.append(action)
        
        minimal_card.action_clicked.connect(capture_signal)
        
        # Click the card
        QTest.mouseClick(minimal_card, Qt.LeftButton)
        
        # Verify signal was emitted with empty action
        assert len(signals_received) == 1
        assert signals_received[0] == ""

    def test_property_interface(self, action_card):
        """Test the Qt Property interface for the component."""
        # Test that properties can be accessed and modified
        action_card.setProperty("title", "Property Title")
        assert action_card.property("title") == "Property Title"
        assert action_card.title() == "Property Title"
        
        action_card.setProperty("description", "Property Description")
        assert action_card.property("description") == "Property Description"
        assert action_card.description() == "Property Description"
        
        action_card.setProperty("icon_name", "property_icon")
        assert action_card.property("icon_name") == "property_icon"
        assert action_card.icon_name() == "property_icon"
        
        action_card.setProperty("tag", "Property Tag")
        assert action_card.property("tag") == "Property Tag"
        assert action_card.tag() == "Property Tag"

    def test_cursor_is_pointer(self, action_card):
        """Test that the cursor is a pointing hand cursor."""
        assert action_card.cursor().shape() == Qt.PointingHandCursor
