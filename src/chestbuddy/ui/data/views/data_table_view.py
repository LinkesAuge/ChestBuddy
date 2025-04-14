from PySide6.QtWidgets import QTableView, QMenu, QWidget
from PySide6.QtCore import Signal, QPoint, QModelIndex, QItemSelection
from PySide6.QtGui import (
    QAction,
    QContextMenuEvent,
    QKeyEvent,
    QMouseEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
)
import typing
import logging

from chestbuddy.ui.data.delegates import (
    # ... other delegates ...
    TextEditDelegate,
)
from chestbuddy.ui.data.menus.context_menu_factory import ContextMenuFactory
from chestbuddy.ui.data.menus.base_action import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import TableStateManager

logger = logging.getLogger(__name__)


class DataTableView(QTableView):
    """Custom QTableView for displaying and interacting with chest data."""

    selection_changed_signal = Signal(list)  # Emits list of selected rows indices
    context_menu_requested_signal = Signal(QPoint)
    correction_action_triggered = Signal(QModelIndex, object)  # Emitted by CorrectionDelegate
    cell_edit_validation_requested = Signal(QModelIndex, str)  # New signal

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._context_menu: QMenu | None = None
        self._created_actions: typing.Dict[str, QAction] = {}
        self._state_manager: TableStateManager | None = None
        # Initialize delegates - Assuming this happens elsewhere or is passed in

    def set_state_manager(self, state_manager: TableStateManager):
        self._state_manager = state_manager

    def _show_context_menu(self, position: QPoint):
        """Creates and shows the context menu at the given position."""
        index = self.indexAt(position)
        if not index.isValid() or not self.model():
            return

        model = self.model()
        # Ensure we get the source model if using a proxy
        source_model = model
        while hasattr(source_model, "sourceModel"):
            source_model = source_model.sourceModel()

        if not isinstance(source_model, DataViewModel):
            logger.warning("ContextMenu: Source model is not a DataViewModel.")
            return

        selection_indices = self.selectionModel().selectedIndexes()
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text() if clipboard.mimeData().hasText() else None
        column_name = source_model.headerData(
            index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )

        context = ActionContext(
            clicked_index=index,
            selection=selection_indices,
            model=source_model,
            parent_widget=self,
            state_manager=self._state_manager,  # Make sure this is set
            clipboard_text=clipboard_text,
            column_name=column_name,
        )

        self._context_menu, self._created_actions = ContextMenuFactory.create_context_menu(context)
        self._context_menu.popup(self.viewport().mapToGlobal(position))

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """Emit signal when selection changes."""
        super().selectionChanged(selected, deselected)
        # Example: emit list of selected source model rows
        if self.selectionModel():
            selected_rows = sorted(
                list(set(idx.row() for idx in self.selectionModel().selectedRows()))
            )
            self.selection_changed_signal.emit(selected_rows)
        else:
            self.selection_changed_signal.emit([])

    # --- Placeholder for connecting delegate signals ---
    def connect_delegate_signals(self):
        # This method should be called after delegates are set for columns
        logger.debug("Connecting delegate signals...")
        model = self.model()
        if not model:
            logger.error("Cannot connect delegate signals: No model set.")
            return

        # Get the actual source model if a proxy is used
        source_model = model
        while hasattr(source_model, "sourceModel"):
            source_model = source_model.sourceModel()

        if not isinstance(source_model, DataViewModel):
            logger.error("Cannot connect delegate signals: Source model is not DataViewModel.")
            return

        column_count = source_model.columnCount()
        logger.debug(f"Iterating through {column_count} columns to connect delegate signals.")

        for col_idx in range(column_count):
            delegate = self.itemDelegateForColumn(col_idx)
            if delegate:
                # Connect TextEditDelegate signal
                if isinstance(delegate, TextEditDelegate):
                    try:
                        # Disconnect first to prevent duplicates if called multiple times
                        delegate.validation_requested.disconnect(
                            self._handle_cell_validation_request
                        )
                    except (TypeError, RuntimeError):
                        pass  # Ignore if not connected or already deleted
                    delegate.validation_requested.connect(self._handle_cell_validation_request)
                    logger.info(
                        f"Connected TextEditDelegate.validation_requested for column {col_idx}"
                    )

                # Connect CorrectionDelegate signal
                # Need to import CorrectionDelegate first
                # from chestbuddy.ui.data.delegates import CorrectionDelegate
                # if isinstance(delegate, CorrectionDelegate):
                #     try:
                #         delegate.correction_selected.disconnect(self._handle_correction_selected)
                #     except (TypeError, RuntimeError):
                #         pass
                #     delegate.correction_selected.connect(self._handle_correction_selected)
                #     logger.info(f"Connected CorrectionDelegate.correction_selected for column {col_idx}")

                # Add connections for other delegates here if needed
            # else:
            #     logger.debug(f"No specific delegate set for column {col_idx}, using default.")

        logger.debug("Finished connecting delegate signals.")

    @Slot(QModelIndex, str)
    def _handle_cell_validation_request(self, index: QModelIndex, new_value: str):
        """Handle validation request from delegate and emit view signal."""
        logger.debug(
            f"View received validation_requested for index {index.row()},{index.column()} with value '{new_value}'"
        )
        # We need to map the view index (potentially from a proxy model)
        # back to the source model index if necessary before emitting.
        # Assuming self.model() might be a proxy:
        source_model = self.model()
        source_index = index
        if hasattr(source_model, "mapToSource"):
            source_index = source_model.mapToSource(index)
            if not source_index.isValid():
                logger.warning("Could not map view index to source index for validation request.")
                return

        self.cell_edit_validation_requested.emit(source_index, new_value)

    # Slot for CorrectionDelegate signal (if needed)
    # @Slot(QModelIndex, object)
    # def _handle_correction_selected(self, index: QModelIndex, correction_data: object):
    #     logger.debug(f"View received correction_selected for index {index.row()},{index.column()} with data '{correction_data}'")
    #     # Map index if necessary
    #     source_model = self.model()
    #     source_index = index
    #     if hasattr(source_model, 'mapToSource'):
    #         source_index = source_model.mapToSource(index)
    #         if not source_index.isValid(): return
    #     self.correction_action_triggered.emit(source_index, correction_data)

    # Override other event handlers like keyPressEvent if needed
    # def keyPressEvent(self, event: QKeyEvent):
    #     super().keyPressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_rows()
        else:
            super().keyPressEvent(event)

    def delete_selected_rows(self):
        selected_indexes = self.selectedIndexes()
        if selected_indexes:
            self.model().removeRows(
                selected_indexes[0].row(), len(selected_indexes), selected_indexes[0].parent()
            )
        else:
            logger.warning("No rows selected for deletion")

    def contextMenuEvent(self, event: QContextMenuEvent):
        super().contextMenuEvent(event)
        index = self.indexAt(event.pos())
        if index.isValid():
            self.context_menu_requested_signal.emit(event.globalPos())

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.RightButton:
            self.setFocus()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                self.correction_action_triggered.emit(index, None)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
        else:
            self.setDragEnabled(False)
            self.setAcceptDrops(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("text/plain"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("text/plain"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat("text/plain"):
            event.accept()
            indexes = self.selectedIndexes()
            if indexes:
                self.model().dropMimeData(
                    event.mimeData(),
                    event.dropAction(),
                    indexes[0].row(),
                    indexes[0].column(),
                    indexes[0].parent(),
                )
        else:
            event.ignore()

    def show_correction_menu(self, index: QModelIndex):
        menu = QMenu()
        correction_action = QAction("Correct", self)
        correction_action.triggered.connect(
            lambda: self.correction_action_triggered.emit(index, None)
        )
        menu.addAction(correction_action)
        menu.exec(self.viewport().mapToGlobal(index.siblingAtColumn(0)))

    def show_cell_edit_validation_menu(self, index: QModelIndex, text: str):
        menu = QMenu()
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.cell_edit_validation_requested.emit(index, text))
        menu.addAction(edit_action)
        menu.exec(self.viewport().mapToGlobal(index.siblingAtColumn(0)))
