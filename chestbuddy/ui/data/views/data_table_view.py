"""
data_table_view.py

A specialized table view for displaying chest data with validation
and correction visualizations.
"""

from PySide6.QtWidgets import QTableView, QHeaderView, QMenu
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QItemSelection,
    QItemSelectionModel,
    QAbstractItemModel,
)
import typing

# Placeholder imports - adjust as needed when models/delegates are implemented
from ..delegates.cell_delegate import CellDelegate
# from ..models.data_view_model import DataViewModel


class DataTableView(QTableView):
    """
    DataTableView displays chest data with potential validation and correction
    visualizations (to be implemented).

    It inherits from QTableView and will be customized with specific
    delegates, context menus, and interaction logic.
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

        # SETUP
        self._setup_ui()
        self._connect_signals()

        # INTERNAL STATE (if needed)
        # self._some_internal_state = None

    # --- Setup Methods ---

    def _setup_ui(self) -> None:
        """Set up basic UI components and style for the table view."""
        # Basic QTableView setup
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setSortingEnabled(True)  # Basic sorting via header click

        # Selection behavior
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.ExtendedSelection)

        # Header setup
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)  # Hide vertical row numbers for now

        # Set a default delegate (placeholder until custom delegates are ready)
        # from PySide6.QtWidgets import QStyledItemDelegate
        # self.setItemDelegate(QStyledItemDelegate(self))
        self.setItemDelegate(CellDelegate(self))

        # Enable custom context menus (to be implemented later)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def _connect_signals(self) -> None:
        """Connect internal signals and slots."""
        # Connect base QTableView signals if needed for internal logic
        # Connect selection model's signal to our custom handler
        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(self._on_internal_selection_changed)

        self.customContextMenuRequested.connect(self._show_context_menu)  # Connect placeholder

    # --- Placeholder Slots / Event Handlers ---

    @Slot(QItemSelection, QItemSelection)
    def _on_internal_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles the internal selectionChanged signal and emits the custom signal."""
        selected_indices = self.selectionModel().selectedIndexes()
        self.selection_changed.emit(selected_indices)

    @Slot(QPoint)
    def _show_context_menu(self, position) -> typing.Optional[QMenu]:
        """Shows a context menu at the given position and returns the menu.

        Note: Returning the menu is primarily for testing purposes.
        """
        # Get the index under the cursor
        index = self.indexAt(position)

        # Create the menu
        menu = QMenu(self)

        # Add basic actions (will be expanded later)
        copy_action = menu.addAction("Copy")
        # paste_action = menu.addAction("Paste")
        # delete_action = menu.addAction("Delete")

        # TODO: Connect actions to actual slots
        # copy_action.triggered.connect(self._copy_selection)

        # TODO: Add context-specific actions based on index and selection

        # Show the menu at the global position
        global_pos = self.viewport().mapToGlobal(position)
        menu.exec_(global_pos)

        return menu  # Return the created menu for testing

    # --- Public API (Example) ---

    # def get_selected_data(self):
    #    pass

    # --- Overrides (Example) ---

    # def keyPressEvent(self, event: QKeyEvent) -> None:
    #     super().keyPressEvent(event)

    def setModel(self, model: QAbstractItemModel) -> None:
        """Overrides setModel to connect to the new selection model."""
        # Disconnect from old selection model if it exists
        old_selection_model = self.selectionModel()
        if old_selection_model:
            try:
                old_selection_model.selectionChanged.disconnect(self._on_internal_selection_changed)
            except RuntimeError:  # Raised if not connected
                pass

        super().setModel(model)

        # Connect to the new selection model
        new_selection_model = self.selectionModel()
        if new_selection_model:
            new_selection_model.selectionChanged.connect(self._on_internal_selection_changed)
