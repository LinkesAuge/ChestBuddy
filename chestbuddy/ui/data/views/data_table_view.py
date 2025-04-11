"""
data_table_view.py

A specialized table view for displaying chest data with validation
and correction visualizations.
"""

from PySide6.QtWidgets import QTableView, QHeaderView, QMenu, QToolBar, QVBoxLayout, QWidget
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QItemSelection,
    QItemSelectionModel,
    QAbstractItemModel,
)
from PySide6.QtGui import QAction
import typing

# Placeholder imports - adjust as needed when models/delegates are implemented
# from ..delegates.cell_delegate import CellDelegate
from ..delegates.correction_delegate import CorrectionDelegate  # Import CorrectionDelegate
# from ..models.data_view_model import DataViewModel


class DataTableView(QWidget):
    """
    DataTableView displays chest data with potential validation and correction
    visualizations (to be implemented).

    It inherits from QWidget and contains a QToolBar and a QTableView.
    """

    # --- Signals ---
    # Emits a list of currently selected QModelIndex objects
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        """
        Initialize the DataTableView.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_toolbar()
        self._setup_table()
        self._setup_layout()
        self._connect_signals()

        # INTERNAL STATE (if needed)
        # self._some_internal_state = None

    # --- Setup Methods ---

    def _setup_toolbar(self):
        """Set up the toolbar with placeholder actions."""
        self.toolbar = QToolBar("Data Actions")
        self.toolbar.setMovable(False)

        # Placeholder actions - connect later
        self.import_action = QAction("Import", self)
        self.export_action = QAction("Export", self)
        self.copy_action = QAction("Copy", self)
        self.paste_action = QAction("Paste", self)
        self.delete_action = QAction("Delete", self)
        self.validate_action = QAction("Validate", self)
        self.correct_action = QAction("Correct", self)

        self.toolbar.addAction(self.import_action)
        self.toolbar.addAction(self.export_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.copy_action)
        self.toolbar.addAction(self.paste_action)
        self.toolbar.addAction(self.delete_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.validate_action)
        self.toolbar.addAction(self.correct_action)

    def _setup_table(self):
        """Set up the table view properties."""
        # Set selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        # Custom context menus (to be implemented later)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_layout(self):
        """Set up the main layout including the toolbar and table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.table_view)  # Add the actual table view

        # Need to manage the table view separately now
        # self refers to the container widget, self.table_view is the QTableView
        self.table_view = QTableView()  # Create the table view instance
        self.table_view.setObjectName("dataTableView")
        self._configure_table_view(self.table_view)
        layout.addWidget(self.table_view)

    def _configure_table_view(self, table_view):
        """Configure the QTableView instance."""
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table_view.setAlternatingRowColors(True)
        table_view.setShowGrid(True)
        table_view.setSortingEnabled(True)
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        table_view.verticalHeader().setVisible(False)
        table_view.setItemDelegate(CorrectionDelegate(table_view))
        table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Need to forward signals from the actual table_view if the container needs them
        table_view.selectionModel().selectionChanged.connect(self.selection_changed)

    def _connect_signals(self):
        """Connect signals for the container widget (if any)."""
        # Connect toolbar actions to slots (implement later)
        # self.copy_action.triggered.connect(self._on_copy)
        pass

    @Slot(QPoint)
    def _show_context_menu(self, position):
        """Show the context menu at the given position relative to the table view."""
        # Get the index at the clicked position
        index = self.table_view.indexAt(position)
        # TODO: Get selection information to enable/disable actions
        selection = self.table_view.selectionModel().selectedIndexes()

        menu = QMenu(self)

        # Standard Edit Actions
        copy_action = QAction("Copy", self)
        paste_action = QAction("Paste", self)
        cut_action = QAction("Cut", self)
        delete_action = QAction("Delete", self)

        # TODO: Set icons for actions (e.g., using QIcon.fromTheme)

        # TODO: Enable/Disable actions based on selection and cell state
        # Example: Enable paste only if clipboard has data
        # Example: Enable cut/delete only if selection is not empty
        copy_action.setEnabled(len(selection) > 0)
        cut_action.setEnabled(len(selection) > 0)  # and editable
        delete_action.setEnabled(len(selection) > 0)  # and editable
        # paste_action.setEnabled(clipboard.hasText()) # Placeholder

        # TODO: Connect actions to actual slots
        # copy_action.triggered.connect(self._on_copy)
        # paste_action.triggered.connect(self._on_paste)
        # cut_action.triggered.connect(self._on_cut)
        # delete_action.triggered.connect(self._on_delete)

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addAction(cut_action)
        menu.addAction(delete_action)
        menu.addSeparator()

        # Placeholder for future actions (validation, correction)
        menu.addAction(QAction("Validate Selected (TODO)", self))
        menu.addAction(QAction("Correct Selected (TODO)", self))

        # Execute the menu at the global position mapped from the table view
        global_pos = self.table_view.viewport().mapToGlobal(position)
        menu.exec(global_pos)

    # Placeholder for context_menu method if separate generation is needed
    # def context_menu(self, index: QModelIndex) -> QMenu:
    #    ...

    # --- Public Methods to interact with the internal table view ---
    def setModel(self, model):
        self.table_view.setModel(model)

    def model(self):
        return self.table_view.model()

    def selectionModel(self):
        return self.table_view.selectionModel()

    def currentIndex(self):
        return self.table_view.currentIndex()

    def setCurrentIndex(self, index):
        self.table_view.setCurrentIndex(index)

    def clearSelection(self):
        self.table_view.clearSelection()

    # Delegate other necessary QTableView methods...
