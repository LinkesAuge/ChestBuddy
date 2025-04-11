"""
Tests for the CellDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel
from PySide6.QtWidgets import QApplication, QWidget, QStyleOptionViewItem
from PySide6.QtGui import QPainter

from chestbuddy.ui.data.delegates.cell_delegate import CellDelegate

# Fixtures like qapp are expected from conftest.py


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
        """Test that the default createEditor method calls the superclass method."""
        mock_parent = mocker.MagicMock(spec=QWidget)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        mock_super_create = mocker.patch("PySide6.QtWidgets.QStyledItemDelegate.createEditor")

        delegate.createEditor(mock_parent, mock_option, mock_index)
        # Assert that the superclass's createEditor method was called exactly once
        # with the arguments it receives when called via super()
        mock_super_create.assert_called_once_with(mock_parent, mock_option, mock_index)

    def test_set_editor_data_calls_super(self, delegate, mocker):
        """Test that the default setEditorData method calls the superclass method."""
        mock_editor = mocker.MagicMock(spec=QWidget)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        mock_super_set_editor = mocker.patch("PySide6.QtWidgets.QStyledItemDelegate.setEditorData")

        delegate.setEditorData(mock_editor, mock_index)
        mock_super_set_editor.assert_called_once_with(mock_editor, mock_index)

    def test_set_model_data_calls_super(self, delegate, mocker):
        """Test that the default setModelData method calls the superclass method."""
        mock_editor = mocker.MagicMock(spec=QWidget)
        mock_model = mocker.MagicMock(spec=QAbstractItemModel)  # Need model import
        mock_index = mocker.MagicMock(spec=QModelIndex)

        mock_super_set_model = mocker.patch("PySide6.QtWidgets.QStyledItemDelegate.setModelData")

        delegate.setModelData(mock_editor, mock_model, mock_index)
        mock_super_set_model.assert_called_once_with(mock_editor, mock_model, mock_index)

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

    # Add similar tests for setEditorData, setModelData, updateEditorGeometry
    # to ensure they call the superclass method by default.
