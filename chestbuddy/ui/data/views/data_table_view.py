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
from ..delegates.cell_delegate import CellDelegate  # Import base delegate
from ..delegates.validation_delegate import ValidationDelegate  # Import validation delegate
from ..delegates.correction_delegate import CorrectionDelegate  # Import correction delegate
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
        self._setup_delegates()  # Call delegate setup

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
        """Set up the table view properties. This method seems incorrectly placed
        as DataTableView is a QWidget. Configuration should happen in
        _configure_table_view where self.table_view (QTableView) is available.
        Removing setup logic from here.
        """
        # Logic moved to _configure_table_view
        pass

    def _setup_layout(self):
        """Set up the main layout including the toolbar and table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create table_view before adding to layout
        self.table_view = QTableView()  # Create the table view instance
        self.table_view.setObjectName("dataTableView")
        self._configure_table_view(self.table_view)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.table_view)  # Add the configured table view

    def _configure_table_view(self, table_view: QTableView):
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

        # Set delegate on the actual table_view
        table_view.setItemDelegate(CorrectionDelegate(table_view))
        # Connect context menu on the actual table_view
        table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Connect selection changed signal from the actual table_view's selection model
        # Ensure selectionModel() exists before connecting
        selection_model = table_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(
                self._on_selection_changed
            )  # Connect to internal slot
        else:
            # Handle case where selection model is not ready yet (might need QTimer.singleShot)
            # This typically happens if setModel hasn't been called or finished.
            # For now, we assume it's available after setModel in the fixture.
            print("Warning: Selection model not available during _configure_table_view")

    def _connect_signals(self):
        """Connect signals for the container widget (if any)."""
        # Connect signals from the internal table_view or its model if needed by the container
        # Example: Forwarding selection changed if the container needs it directly
        # self.table_view.selectionModel().selectionChanged.connect(self.selection_changed)
        pass  # Keep internal connections primarily

    # --- Internal Slot for Selection --- #
    @Slot(QItemSelection, QItemSelection)
    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """Internal slot to handle selection changes from the QTableView.
        Emits the public selection_changed signal with QModelIndex list.
        """
        current_selection_indexes = self.table_view.selectionModel().selectedIndexes()
        # Emit the public signal expected by external components
        self.selection_changed.emit(current_selection_indexes)

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

    # --- Public Methods to interact with the internal table view ---
    def setModel(self, model: QAbstractItemModel | None):
        """Sets the model on the internal QTableView and updates delegates."""
        if self.table_view:
            self.table_view.setModel(model)
            self._setup_delegates()  # Re-setup delegates when model changes
        else:
            print("Error: setModel called before table_view was initialized.")

    def model(self) -> QAbstractItemModel | None:
        """Returns the model from the internal QTableView."""
        return self.table_view.model() if self.table_view else None

    def selectionModel(self) -> QItemSelectionModel | None:
        """Returns the selection model from the internal QTableView."""
        return self.table_view.selectionModel() if self.table_view else None

    def currentIndex(self) -> QModelIndex:
        """Returns the current index from the internal QTableView."""
        return self.table_view.currentIndex() if self.table_view else QModelIndex()

    def setCurrentIndex(self, index: QModelIndex):
        """Sets the current index on the internal QTableView."""
        if self.table_view:
            self.table_view.setCurrentIndex(index)

    def clearSelection(self):
        """Clears the selection on the internal QTableView."""
        if self.table_view:
            self.table_view.clearSelection()

    def setColumnVisible(self, column_index: int, visible: bool):
        """Shows or hides the specified column on the internal QTableView."""
        if self.table_view:
            self.table_view.setColumnHidden(column_index, not visible)

    def isColumnVisible(self, column_index: int) -> bool:
        """Returns True if the specified column is visible on the internal QTableView."""
        return not self.table_view.isColumnHidden(column_index) if self.table_view else False

    def _setup_delegates(self):
        """Sets up the item delegates for the internal table_view."""
        if not self.table_view:
            print("Error: Cannot setup delegates, table_view not initialized.")
            return

        # Disconnect old signals if they exist
        old_delegate = self.table_view.itemDelegate()  # Get delegate from internal view
        if isinstance(old_delegate, CellDelegate) and hasattr(old_delegate, "validationRequested"):
            try:
                old_delegate.validationRequested.disconnect(self._on_validation_requested)
            except (TypeError, RuntimeError):  # Handles disconnect errors if not connected
                pass

        # Create and set the new delegate for the internal view
        delegate = CorrectionDelegate(self.table_view)  # Parent is the internal QTableView
        self.table_view.setItemDelegate(delegate)

        # Connect the validation request signal from the new delegate
        # if hasattr(delegate, "validationRequested"):
        #    delegate.validationRequested.connect(self._on_validation_requested)

    @Slot(object, QModelIndex)
    def _on_validation_requested(self, value: object, index: QModelIndex):
        """
        Handles the validationRequested signal from the delegate.
        Currently just sets the data, validation logic will be added later.
        """
        print(
            f"DataTableView: Received validationRequested for value '{value}' at {index.row()},{index.column()}"
        )
        if self.model() and index.isValid():
            # TODO: Integrate call to ValidationService here
            # result = validation_service.validate_single_cell(index.row(), index.column(), value)
            # if result.is_valid:
            #     self.model().setData(index, value, Qt.EditRole)
            # else:
            #     # Show error feedback, maybe keep editor open?
            #     QMessageBox.warning(self, "Validation Failed", result.message)
            #     # Optionally, re-open editor: self.edit(index)

            # For now, directly set the data to maintain functionality
            success = self.model().setData(index, value, Qt.EditRole)
            if not success:
                print(f"DataTableView: setData failed for {index.row()},{index.column()}")
                QMessageBox.warning(self, "Edit Failed", "Could not set the new value.")
        else:
            print(f"DataTableView: Cannot set data - invalid model or index.")

    # Delegate other necessary QTableView methods...
    # Example:
    def resizeColumnsToContents(self):
        if self.table_view:
            self.table_view.resizeColumnsToContents()
