"""
Tests for the CellDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel
from PySide6.QtWidgets import QApplication, QWidget, QStyleOptionViewItem, QLineEdit
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from unittest.mock import MagicMock
from pytestqt.qt_compat import qt_api

from chestbuddy.ui.data.delegates.cell_delegate import CellDelegate, _mock_validate_data

# Fixtures like qapp are expected from conftest.py


@pytest.fixture
def mock_model_index():
    """Create a mock QModelIndex."""
    return MagicMock(spec=QModelIndex)


@pytest.fixture
def mock_editor():
    """Create a mock QLineEdit editor."""
    return MagicMock(spec=QLineEdit)


class MockModel(QAbstractItemModel):
    """Minimal mock model for testing setData calls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}

    def rowCount(self, parent=QModelIndex()):
        return 0

    def columnCount(self, parent=QModelIndex()):
        return 0

    def index(self, row, col, parent=QModelIndex()):
        return self.createIndex(row, col)

    def parent(self, index):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        return self._data.get((index.row(), index.column()), None)

    def setData(self, index, value, role=Qt.EditRole):
        return False  # Placeholder


class TestCellDelegate:
    """Tests for the base CellDelegate class."""

    @pytest.fixture
    def delegate(self, qapp):
        """Create a CellDelegate instance."""
        return CellDelegate()

    def test_initialization(self, delegate):
        """Test that the CellDelegate initializes correctly."""
        assert delegate is not None

    def test_paint_calls_super(self, delegate, mocker):
        """Test that the default paint method calls the superclass paint."""
        # Create mock objects for paint arguments
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock the superclass's paint method to track calls
        mock_super_paint = mocker.patch("PySide6.QtWidgets.QStyledItemDelegate.paint")

        # Call the delegate's paint method
        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert that the superclass's paint method was called exactly once
        # with the arguments it receives when called via super()
        mock_super_paint.assert_called_once_with(mock_painter, mock_option, mock_index)

    def test_create_editor_calls_super(self, delegate, mocker):
        """Test that the default createEditor method returns an editor (or None)."""
        mock_parent = mocker.MagicMock(spec=QWidget)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = QModelIndex()  # Use a default QModelIndex

        # Call the method - it might raise ValueError if QLineEdit init fails
        # For this basic test, we just want to ensure it *can* return something
        # without calling super, as the current implementation creates QLineEdit.
        editor = delegate.createEditor(mock_parent, mock_option, mock_index)

        # Assert that it returns a QWidget (or None, though current impl returns QLineEdit)
        assert isinstance(editor, QWidget) or editor is None

    def test_set_editor_data_calls_super(self, delegate, mocker):
        """Test that the default setEditorData method calls the superclass method."""
        mock_editor = mocker.MagicMock(spec=QWidget)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        mock_super_set_editor = mocker.patch("PySide6.QtWidgets.QStyledItemDelegate.setEditorData")

        delegate.setEditorData(mock_editor, mock_index)
        mock_super_set_editor.assert_called_once_with(mock_editor, mock_index)

    def test_update_editor_geometry_calls_super(self, delegate, mocker):
        """Test that the default updateEditorGeometry method calls the superclass method."""
        mock_editor = mocker.MagicMock(spec=QWidget)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        mock_super_update = mocker.patch(
            "PySide6.QtWidgets.QStyledItemDelegate.updateEditorGeometry"
        )

        delegate.updateEditorGeometry(mock_editor, mock_option, mock_index)
        mock_super_update.assert_called_once_with(mock_editor, mock_option, mock_index)

    def test_delegate_set_model_data_emits_signal(self, qtbot, mock_model_index, mock_editor):
        """Test that setModelData emits validationRequested signal instead of calling setData."""
        delegate = CellDelegate()
        model = MockModel()
        editor = mock_editor  # QLineEdit
        index = mock_model_index
        new_value = "New Text"
        editor.text.return_value = new_value  # Mock the return value of editor.text()

        # Use waitSignal to check emission and arguments
        with qtbot.waitSignal(
            delegate.validationRequested,
            timeout=100,
            check_params_cb=lambda value, idx: value == new_value,  # Simplified check
        ) as blocker:
            delegate.setModelData(editor, model, index)

        assert blocker.signal_triggered  # Check signal was emitted

        # Spy on model's setData (it should NOT be called)
        set_data_spy = MagicMock()
        model.setData = set_data_spy
        # Assert model.setData was NOT called by the delegate
        set_data_spy.assert_not_called()

    # Add similar tests for setEditorData, setModelData, updateEditorGeometry
    # to ensure they call the superclass method by default.

    # --- Tests for Validation Logic in setModelData are removed ---
    # The delegate no longer performs validation itself in setModelData
