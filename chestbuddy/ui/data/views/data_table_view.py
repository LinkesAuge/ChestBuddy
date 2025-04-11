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
        table_view.setItemDelegate(CorrectionDelegate(table_view))
        table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Need to forward signals from the actual table_view if the container needs them
        table_view.selectionModel().selectionChanged.connect(self.selection_changed)

    def _connect_signals(self):
        """Connect signals for the container widget (if any)."""
        # Connect toolbar actions to slots (implement later)
        self.paste_action.triggered.connect(self._on_paste)
        self.cut_action.triggered.connect(self._on_cut)
        self.delete_action.triggered.connect(self._on_delete)
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
        copy_action = QAction(
            QIcon.fromTheme("edit-copy", QIcon(":/icons/edit-copy.png")), "Copy", self
        )
        paste_action = QAction(
            QIcon.fromTheme("edit-paste", QIcon(":/icons/edit-paste.png")), "Paste", self
        )
        cut_action = QAction(
            QIcon.fromTheme("edit-cut", QIcon(":/icons/edit-cut.png")), "Cut", self
        )
        delete_action = QAction(
            QIcon.fromTheme("edit-delete", QIcon(":/icons/edit-delete.png")), "Delete", self
        )

        # TODO: Set icons for actions (e.g., using QIcon.fromTheme)
        # Icons added above using fromTheme with fallbacks (assuming resource paths exist)

        # TODO: Enable/Disable actions based on selection and cell state
        model = self.table_view.model()
        clipboard = QGuiApplication.clipboard()
        has_selection = len(selection) > 0
        target_index = self.table_view.currentIndex()  # Default target for paste
        if selection:
            target_index = min(selection)

        # Check editability of the target cell for paste
        paste_target_editable = False
        if target_index.isValid():
            paste_target_editable = bool(model.flags(target_index) & Qt.ItemIsEditable)

        # Check editability for selection (cut/delete)
        # For simplicity, enable if *any* selected cell is editable. Refine if needed.
        selection_editable = False
        if has_selection:
            selection_editable = any(
                bool(model.flags(idx) & Qt.ItemIsEditable) for idx in selection
            )

        copy_action.setEnabled(has_selection)
        paste_action.setEnabled(clipboard and bool(clipboard.text()) and paste_target_editable)
        cut_action.setEnabled(has_selection and selection_editable)
        delete_action.setEnabled(has_selection and selection_editable)

        # TODO: Connect actions to actual slots
        copy_action.triggered.connect(self._on_copy)
        paste_action.triggered.connect(self._on_paste)
        cut_action.triggered.connect(self._on_cut)
        delete_action.triggered.connect(self._on_delete)

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addAction(cut_action)
        menu.addAction(delete_action)
        menu.addSeparator()

        # Get cell state for context-specific actions
        validation_state = None
        correction_state = None  # Placeholder for correction state role
        if index.isValid():
            validation_state = model.data(index, DataViewModel.ValidationStateRole)
            # correction_state = model.data(index, DataViewModel.CorrectionStateRole)

        # --- Validation/Correction Actions ---
        if validation_state == "INVALID":  # Replace with CellState enum comparison later
            view_error_action = QAction(
                QIcon.fromTheme("dialog-error"), "View Validation Error", self
            )
            view_error_action.triggered.connect(lambda: self._on_view_error(index))
            menu.addAction(view_error_action)

        if validation_state == "CORRECTABLE":  # Replace with CellState enum comparison later
            apply_correction_action = QAction(QIcon.fromTheme("edit-fix"), "Apply Correction", self)
            apply_correction_action.triggered.connect(lambda: self._on_apply_correction(index))
            menu.addAction(apply_correction_action)
            # Add submenu for multiple suggestions if needed

        # Add actions to add to validation/correction lists (implement later)
        menu.addSeparator()
        add_to_correction_action = QAction("Add to Correction List (TODO)", self)
        add_to_validation_action = QAction("Add to Validation List (TODO)", self)
        menu.addAction(add_to_correction_action)
        menu.addAction(add_to_validation_action)

        # Placeholder for future actions (validation, correction)
        # menu.addAction(QAction("Validate Selected (TODO)", self))
        # menu.addAction(QAction("Correct Selected (TODO)", self))

        # Execute the menu at the global position mapped from the table view
        global_pos = self.table_view.viewport().mapToGlobal(position)
        menu.exec(global_pos)

    @Slot()
    def _on_paste(self):
        """Handles the Paste action."""
        clipboard = QGuiApplication.clipboard()
        if not clipboard or not clipboard.text():
            print("Clipboard is empty or unavailable.")
            return

        pasted_text = clipboard.text()
        pasted_lines = pasted_text.strip("\n").split("\n")
        pasted_data = [line.split("\t") for line in pasted_lines]

        if not pasted_data:
            print("No data parsed from clipboard text.")
            return

        # Determine target start cell (top-left of current selection or current index)
        selection = self.table_view.selectionModel().selectedIndexes()
        if selection:
            start_index = min(selection)  # Top-left index of the selection block
        else:
            start_index = self.table_view.currentIndex()

        if not start_index.isValid():
            print("No valid target cell selected for paste.")
            return

        start_row = start_index.row()
        start_col = start_index.column()

        model = self.table_view.model()
        num_rows_to_paste = len(pasted_data)
        num_cols_to_paste = max(len(row) for row in pasted_data)  # Max columns in pasted data

        # Check if paste exceeds table bounds (optional: could expand table)
        if (
            start_row + num_rows_to_paste > model.rowCount()
            or start_col + num_cols_to_paste > model.columnCount()
        ):
            print("Paste operation exceeds table bounds. Ignoring excess data.")
            # Adjust paste dimensions or handle error as needed
            num_rows_to_paste = min(num_rows_to_paste, model.rowCount() - start_row)
            num_cols_to_paste = min(num_cols_to_paste, model.columnCount() - start_col)

        # Prepare for potential model updates (optional but good practice)
        # model.beginResetModel() # Or use more granular beginInsertRows/beginRemoveRows

        # Paste data cell by cell
        for r_offset, row_data in enumerate(pasted_data[:num_rows_to_paste]):
            target_row = start_row + r_offset
            for c_offset, cell_value in enumerate(row_data[:num_cols_to_paste]):
                target_col = start_col + c_offset
                target_index = model.index(target_row, target_col)

                # Check if cell is editable before setting data
                flags = model.flags(target_index)
                if flags & Qt.ItemIsEditable:
                    if not model.setData(target_index, cell_value, Qt.EditRole):
                        print(f"Warning: Failed to set data at ({target_row}, {target_col})")
                else:
                    print(f"Warning: Cell ({target_row}, {target_col}) is not editable. Skipping.")

        # Finalize model updates
        # model.endResetModel()
        print(f"Pasted data into range starting at ({start_row}, {start_col})")

    @Slot()
    def _on_cut(self):
        """Handles the Cut action (Copy + Delete)."""
        # First, copy the selection to the clipboard
        self._on_copy()
        # Then, delete the content of the selection
        self._on_delete()
        print("Cut operation performed (Copy + Delete).")

    @Slot()
    def _on_delete(self):
        """Handles the Delete action."""
        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            print("Nothing selected to delete.")
            return

        model = self.table_view.model()
        deleted_count = 0

        # Group changes by row to potentially optimize model updates if needed
        # For now, update cell by cell

        # Use a set for efficient lookup
        selected_indices_set = set(selection)

        # Determine bounds if needed for batch signals, but iterate through selection
        min_row = min(idx.row() for idx in selection)
        max_row = max(idx.row() for idx in selection)
        min_col = min(idx.column() for idx in selection)
        max_col = max(idx.column() for idx in selection)

        # Prepare for model updates (optional)
        # top_left = model.index(min_row, min_col)
        # bottom_right = model.index(max_row, max_col)
        # self.dataChanged.emit(top_left, bottom_right, [Qt.EditRole]) # Needs model support

        for index in selected_indices_set:
            # Check if cell is editable (deletable)
            flags = model.flags(index)
            if flags & Qt.ItemIsEditable:
                # Set data to empty string (or None, depending on model handling)
                if model.setData(index, "", Qt.EditRole):
                    deleted_count += 1
                else:
                    print(f"Warning: Failed to delete data at ({index.row()}, {index.column()})")
            else:
                print(
                    f"Warning: Cell ({index.row()}, {index.column()}) is not editable/deletable. Skipping."
                )

        print(f"Deleted content from {deleted_count} selected cells.")
        # If using begin/end methods, call endResetModel() here.

    @Slot(QModelIndex)
    def _on_view_error(self, index: QModelIndex):
        """Shows the validation error details for the given cell."""
        if not index.isValid():
            return

        model = self.table_view.model()
        if not isinstance(model, DataViewModel):
            print("Error: Cannot view error, model is not DataViewModel")
            return

        # TODO: Get detailed error message from TableStateManager via Model
        # Assuming TableStateManager has a method like get_cell_details
        # And DataViewModel exposes it or provides the detail via a specific role
        error_details = "Placeholder: Detailed validation error message not yet implemented."
        if (
            hasattr(model, "_table_state_manager") and model._table_state_manager
        ):  # Check if manager is set
            if hasattr(model._table_state_manager, "get_cell_details"):
                details = model._table_state_manager.get_cell_details(index.row(), index.column())
                if details:
                    error_details = details
            else:
                print("Warning: TableStateManager has no get_cell_details method.")
        else:
            print("Warning: TableStateManager not set on DataViewModel.")

        QMessageBox.warning(
            self,
            "Validation Error",
            f"Error in cell ({index.row()}, {index.column()}):\n\n{error_details}",
        )

    @Slot(QModelIndex)
    def _on_apply_correction(self, index: QModelIndex):
        """Applies the suggested correction for the given cell."""
        if not index.isValid():
            return

        print(f"TODO: Apply correction for cell ({index.row()}, {index.column()})")
        # 1. Get suggestions from StateManager/Model
        # 2. If multiple, show selection dialog/submenu
        # 3. Call CorrectionService/Model to apply selected correction

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
