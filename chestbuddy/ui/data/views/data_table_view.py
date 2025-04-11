"""
data_table_view.py

A specialized table view for displaying chest data with validation
and correction visualizations.
"""

from PySide6.QtWidgets import (
    QTableView,
    QHeaderView,
    QMenu,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QAbstractItemView,
)
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QItemSelection,
    QItemSelectionModel,
    QAbstractItemModel,
    QModelIndex,
)
from PySide6.QtGui import QAction, QGuiApplication, QIcon
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

        # Enable column reordering
        header = table_view.horizontalHeader()
        header.setSectionsMovable(True)

        # Enable header context menu
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_context_menu)

        table_view.setItemDelegate(CorrectionDelegate(table_view))
        table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Need to forward signals from the actual table_view if the container needs them
        table_view.selectionModel().selectionChanged.connect(self.selection_changed)

    def _connect_signals(self):
        """Connect signals for the container widget (if any)."""
        # Connections for actions are now handled dynamically by the factory
        # when the menu is created.
        # self.copy_action.triggered.connect(self._on_copy)
        # self.paste_action.triggered.connect(self._on_paste)
        # self.cut_action.triggered.connect(self._on_cut)
        # self.delete_action.triggered.connect(self._on_delete)

        # Toolbar actions still need connections if they exist separately
        # self.toolbar_copy_action.triggered.connect(...) # Example

    @Slot(QPoint)
    def _show_context_menu(self, position):
        """Gather context and show the context menu created by the factory."""
        clicked_index = self.table_view.indexAt(position)
        selection = self.table_view.selectionModel().selectedIndexes()
        model = self.table_view.model()  # Should be DataViewModel

        if not isinstance(model, DataViewModel):
            print("Error: Model is not a DataViewModel instance.")
            return

        # Prepare context information
        context_info = ActionContext(
            clicked_index=clicked_index,
            selection=selection,
            model=model,
            parent_widget=self,  # Pass the DataTableView widget as parent
        )

        # Create menu using the factory
        menu, _ = ContextMenuFactory.create_context_menu(context_info)
        # We don't need the actions dict here as connections are made in the factory

        # Execute the menu at the global position
        global_pos = self.table_view.viewport().mapToGlobal(position)
        menu.exec(global_pos)

    @Slot(QPoint)
    def _show_header_context_menu(self, position):
        """Show context menu for the horizontal header."""
        header = self.table_view.horizontalHeader()
        menu = QMenu(self)

        # Add actions for each column
        for logical_index in range(self.table_view.model().columnCount()):
            visual_index = header.visualIndex(logical_index)
            if visual_index < 0:  # Column might be hidden by moveSection
                continue

            column_name = self.table_view.model().headerData(logical_index, Qt.Horizontal)
            action = QAction(column_name, self)
            action.setCheckable(True)
            action.setChecked(not self.table_view.isColumnHidden(logical_index))
            action.triggered.connect(
                lambda checked, col=logical_index: self.setColumnVisible(col, checked)
            )
            menu.addAction(action)

        # Add separator and other header actions if needed
        menu.addSeparator()
        # Example: Action to resize columns to fit content
        resize_action = QAction("Resize Columns to Contents", self)
        resize_action.triggered.connect(self.table_view.resizeColumnsToContents)
        menu.addAction(resize_action)

        global_pos = header.mapToGlobal(position)
        menu.exec(global_pos)

    # --- Action Slots ---
    # Remove old slots as execute logic is now in Action classes
    # @Slot()
    # def _on_copy(self):
    #    ...
    # @Slot()
    # def _on_paste(self):
    #    ...
    # @Slot()
    # def _on_cut(self):
    #    ...
    # @Slot()
    # def _on_delete(self):
    #    ...
    # @Slot(QModelIndex)
    # def _on_view_error(self, index: QModelIndex):
    #    ...
    # @Slot(QModelIndex)
    # def _on_apply_correction(self, index: QModelIndex):
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

    def setColumnVisible(self, column_index: int, visible: bool):
        """Shows or hides the specified column."""
        self.table_view.setColumnHidden(column_index, not visible)

    def isColumnVisible(self, column_index: int) -> bool:
        """Returns True if the specified column is visible."""
        return not self.table_view.isColumnHidden(column_index)

    # Delegate other necessary QTableView methods...
