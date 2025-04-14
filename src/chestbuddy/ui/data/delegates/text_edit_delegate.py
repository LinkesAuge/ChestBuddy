from PySide6.QtCore import QAbstractItemModel, QEvent, QModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLineEdit, QStyleOptionViewItem, QStyledItemDelegate, QWidget


class TextEditDelegate(QStyledItemDelegate):
    """A delegate that allows text editing."""

    # Signal to request validation for an edited value
    # Emits: index (QModelIndex), new_value (str)
    validation_requested = Signal(QModelIndex, str)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        """Create a QLineEdit editor."""
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex):
        """Set the editor's text to the model's data."""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
        """Set the model's data from the editor's text and request validation."""
        new_value = editor.text()

        # Emit signal to request validation *before* setting data
        # This allows the controller layer to potentially intercept or react
        self.validation_requested.emit(index, new_value)

        # Still set the underlying model data to what the user typed
        model.setData(index, new_value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Set the editor's geometry."""
        editor.setGeometry(option.rect)

    # Optional: Implement paint if custom painting is needed
    # def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
    #     super().paint(painter, option, index)

    # Optional: Implement sizeHint if custom sizing is needed
    # def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
    #     return super().sizeHint(option, index)
