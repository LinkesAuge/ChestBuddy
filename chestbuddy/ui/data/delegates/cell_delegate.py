"""
cell_delegate.py

Base delegate for rendering and editing cells in the DataTableView.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel
from PySide6.QtGui import QPainter
import typing


class CellDelegate(QStyledItemDelegate):
    """
    Base class for custom cell delegates in the DataTableView.

    Provides default rendering and editing behavior, which can be
    extended by specialized delegates (e.g., ValidationDelegate).
    """

    def __init__(self, parent=None):
        """
        Initialize the CellDelegate.

        Args:
            parent (QObject, optional): Parent object. Defaults to None.
        """
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Renders the delegate using the given painter and style option for the item specified by index.

        Args:
            painter (QPainter): The painter to use.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.
        """
        # TODO: Add custom painting logic based on cell state (validation, etc.)
        # For now, just call the base implementation
        super().paint(painter, option, index)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> typing.Optional[QWidget]:
        """
        Creates the editor to be used for editing the data item specified by index.

        Args:
            parent (QWidget): The parent widget for the editor.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.

        Returns:
            Optional[QWidget]: The editor widget, or None if no editor is needed.
        """
        # TODO: Create editors based on data type or column
        # For now, use the default editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """
        Sets the data to be displayed and edited by the editor from the data model item specified by index.

        Args:
            editor (QWidget): The editor widget.
            index (QModelIndex): The model index.
        """
        # TODO: Handle custom data types or formatting for the editor
        super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        """
        Gets data from the editor widget and stores it in the data model item specified by index.

        Args:
            editor (QWidget): The editor widget.
            model (QAbstractItemModel): The data model.
            index (QModelIndex): The model index.
        """
        # TODO: Handle custom data types or formatting from the editor
        super().setModelData(editor, model, index)

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """
        Updates the editor for the item specified by index according to the style option given.

        Args:
            editor (QWidget): The editor widget.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.
        """
        super().updateEditorGeometry(editor, option, index)

    # --- Custom methods can be added here ---
