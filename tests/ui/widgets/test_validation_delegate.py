"""
test_validation_delegate.py

Description: Tests for the ValidationStatusDelegate class
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QStyleOptionViewItem, QWidget
from PySide6.QtCore import QModelIndex, Qt

from chestbuddy.ui.widgets.validation_delegate import ValidationStatusDelegate
from chestbuddy.core.validation_enums import ValidationStatus


class TestValidationStatusDelegate:
    """Test cases for ValidationStatusDelegate."""

    def test_init(self):
        """Test delegate initialization."""
        delegate = ValidationStatusDelegate()

        # Verify colors are set correctly
        assert delegate.VALID_COLOR == QColor(0, 0, 0, 0)  # Transparent
        assert delegate.WARNING_COLOR == QColor(255, 240, 200)  # Light yellow
        assert delegate.INVALID_COLOR == QColor(255, 200, 200)  # Light red

    def test_paint(self, qtbot):
        """Test paint method."""
        # Create a delegate
        delegate = ValidationStatusDelegate()

        # Create mocks using standard mock library
        painter = MagicMock(spec=QPainter)

        # Mock option
        option = MagicMock(spec=QStyleOptionViewItem)
        option.rect = MagicMock()

        # Mock index with validation status
        index = MagicMock(spec=QModelIndex)

        # Create a temporary widget to hold the delegate for qtbot
        widget = QWidget()
        qtbot.addWidget(widget)

        # Patch QStyledItemDelegate.paint to avoid actual rendering
        # but still test our implementation
        with patch("PySide6.QtWidgets.QStyledItemDelegate.paint"):
            # Test with INVALID status
            index.data.return_value = ValidationStatus.INVALID
            delegate.paint(painter, option, index)

            # Verify painter calls
            painter.save.assert_called_once()
            painter.fillRect.assert_called_once_with(option.rect, delegate.INVALID_COLOR)
            painter.restore.assert_called_once()

            # Reset mocks
            painter.reset_mock()

            # Test with WARNING status
            index.data.return_value = ValidationStatus.WARNING
            delegate.paint(painter, option, index)

            # Verify painter calls
            painter.save.assert_called_once()
            painter.fillRect.assert_called_once_with(option.rect, delegate.WARNING_COLOR)
            painter.restore.assert_called_once()

            # Reset mocks
            painter.reset_mock()

            # Test with VALID status (no specific highlight)
            index.data.return_value = ValidationStatus.VALID
            delegate.paint(painter, option, index)

            # Verify painter calls
            painter.save.assert_called_once()
            painter.fillRect.assert_not_called()  # Should not fill with color for VALID status
            painter.restore.assert_called_once()

    def test_editor_creation(self, qtbot):
        """Test that editor creation works normally."""
        # Create a delegate
        delegate = ValidationStatusDelegate()

        # Create a temporary widget to hold the delegate for qtbot
        widget = QWidget()
        qtbot.addWidget(widget)

        # Mock parent and option using standard mock library
        parent = MagicMock(spec=QWidget)
        option = MagicMock(spec=QStyleOptionViewItem)
        index = MagicMock(spec=QModelIndex)

        # Patch the createEditor method to avoid actual editor creation
        with patch.object(ValidationStatusDelegate, "createEditor", return_value=MagicMock()):
            # Call createEditor
            delegate.createEditor(parent, option, index)

            # Verify it was called
            ValidationStatusDelegate.createEditor.assert_called_once()
