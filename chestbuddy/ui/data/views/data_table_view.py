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
from typing import Optional

# Placeholder imports - adjust as needed when models/delegates are implemented
from ..delegates.cell_delegate import CellDelegate  # Import base delegate
from ..delegates.validation_delegate import ValidationDelegate  # Import validation delegate
from ..delegates.correction_delegate import CorrectionDelegate  # Import correction delegate

# from ..models.data_view_model import DataViewModel
from ..models.column_model import ColumnModel  # Import ColumnModel
from ..menus.context_menu_factory import (
    ContextMenuFactory,
    ActionContext,
)  # Import ContextMenuFactory and ActionContext
from ..models.filter_model import FilterModel  # Import FilterModel
from ..models.data_view_model import DataViewModel  # Import DataViewModel for type hinting


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

        self._column_model = ColumnModel(self)  # Initialize ColumnModel
        self._source_model: Optional[DataViewModel] = None  # Store source model reference
        self._filter_model = FilterModel(self)  # Initialize FilterModel

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
        self.table_view.setModel(self._filter_model)  # Set FilterModel on the view
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
        """Connect signals for the container widget and internal components."""
        # Connect signals from the internal table_view or its model if needed by the container
        # Example: Forwarding selection changed if the container needs it directly
        # self.table_view.selectionModel().selectionChanged.connect(self.selection_changed)

        # Connect to ColumnModel signal
        self._column_model.column_visibility_changed.connect(self._update_column_visibility)
        self._column_model.columns_changed.connect(
            self._initialize_column_visibility
        )  # Connect columns_changed

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
        proxy_clicked_index = self.table_view.indexAt(position)
        source_clicked_index = self._filter_model.mapToSource(proxy_clicked_index)
        proxy_selection = self.table_view.selectionModel().selectedIndexes()
        source_selection = [self._filter_model.mapToSource(idx) for idx in proxy_selection]
        source_model = self.sourceModel()  # Use the stored source model

        if not isinstance(source_model, DataViewModel):
            print("Error: Source model is not a DataViewModel instance.")
            return

        # Prepare context information
        context_info = ActionContext(
            clicked_index=source_clicked_index,  # Pass source index
            selection=source_selection,  # Pass source selection
            model=source_model,  # Pass source model
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
        model = self.sourceModel()  # Get the source model for column names/count

        if not model:
            return

        # Add actions for each column based on ColumnModel
        column_names = self._column_model.get_columns()
        for logical_index, column_name in enumerate(column_names):
            # Ensure the logical index is valid for the current model
            if logical_index >= model.columnCount():
                continue

            action = QAction(column_name, self)
            action.setCheckable(True)
            # Set checked state based on ColumnModel
            action.setChecked(self._column_model.is_column_visible(column_name))
            # Connect to a lambda that calls ColumnModel to change visibility
            action.triggered.connect(
                lambda checked, name=column_name: self._column_model.set_column_visible(
                    name, checked
                )
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

    # --- Internal Slot for Column Visibility --- #
    @Slot(str, bool)
    def _update_column_visibility(self, column_name: str, visible: bool):
        """Update the visibility of a specific column in the table view."""
        model = self.sourceModel()  # Use source model for column mapping
        if not model:
            return

        try:
            # Find the logical index for the column name
            # This assumes the underlying model (e.g., DataViewModel) can provide column names
            # or we map names to indices based on the ColumnModel's initial column list
            if hasattr(model, "column_names"):  # Example check
                column_names = model.column_names()
                if column_name in column_names:
                    logical_index = column_names.index(column_name)
                    self.table_view.setColumnHidden(logical_index, not visible)
            else:
                # Fallback: Use ColumnModel's internal list if model doesn't provide names
                # This might be less reliable if column order changes in the source model
                if column_name in self._column_model.get_columns():
                    logical_index = self._column_model.get_columns().index(column_name)
                    # Check if logical_index is valid for the current view model
                    if logical_index < model.columnCount():
                        self.table_view.setColumnHidden(logical_index, not visible)
                    else:
                        print(
                            f"Warning: Logical index {logical_index} for column '{column_name}' out of bounds for model column count {model.columnCount()}"
                        )
                else:
                    print(f"Warning: Column '{column_name}' not found for visibility update.")

        except Exception as e:
            print(f"Error updating column visibility for '{column_name}': {e}")

    @Slot(list)
    def _initialize_column_visibility(self, columns: list):
        """Initialize column visibility when columns are set in ColumnModel."""
        self._update_all_column_visibility()

    def _update_all_column_visibility(self):
        """Update visibility for all columns based on ColumnModel state."""
        model = self.sourceModel()  # Use source model for column mapping
        if not model:
            return

        column_names = self._column_model.get_columns()
        for idx, name in enumerate(column_names):
            # Ensure index is valid for the current model
            if idx < model.columnCount():
                is_visible = self._column_model.is_column_visible(name)
                self.table_view.setColumnHidden(idx, not is_visible)
            else:
                print(
                    f"Warning: Initializing visibility - index {idx} for '{name}' out of bounds ({model.columnCount()} cols)"
                )

    # --- Public Methods to interact with the internal table view ---
    def setModel(self, model: DataViewModel | None):
        """Sets the source DataViewModel and connects it to the FilterModel."""
        if self.table_view:
            # Check if the source model is the same
            if self._source_model == model:
                return  # Avoid resetting if the model is the same

            # Disconnect signals from old source model if exists
            if self._source_model and hasattr(self._source_model, "data_changed"):
                try:
                    self._source_model.data_changed.disconnect(
                        self._filter_model.invalidate
                    )  # Or a specific slot if needed
                except (TypeError, RuntimeError):
                    pass

            self._source_model = model  # Store the new source model

            # Set the source model for the filter proxy
            self._filter_model.setSourceModel(self._source_model)

            # The view keeps the filter model, we just change its source
            self._setup_delegates()  # Re-setup delegates when model changes (might depend on source)
            if self._source_model:
                # Update ColumnModel when the source model changes
                column_count = self._source_model.columnCount()
                column_names = [
                    str(self._source_model.headerData(i, Qt.Horizontal))
                    for i in range(column_count)
                ]
                self._column_model.set_columns(column_names)
                # Initial visibility update is handled by columns_changed signal connection

                # Connect new source model signals
                if hasattr(self._source_model, "data_changed"):
                    try:
                        self._source_model.data_changed.connect(self._filter_model.invalidate)
                    except (TypeError, RuntimeError):
                        print("Warning: Could not connect data_changed signal from source model")
            else:
                self._column_model.set_columns([])

    def model(self) -> FilterModel | None:
        """Returns the FilterModel used by the internal QTableView."""
        return self._filter_model if self.table_view else None

    def sourceModel(self) -> DataViewModel | None:
        """Returns the source DataViewModel."""
        return self._source_model

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
        """Sets the visibility of a column by its logical index.

        Updates the ColumnModel, which triggers the UI update via signal.
        """
        # Get column name from the source model (requires model to be set)
        model = self.sourceModel()
        if model and 0 <= column_index < model.columnCount():
            # Use the index to get the column name directly from ColumnModel's list
            column_names = self._column_model.get_columns()
            if 0 <= column_index < len(column_names):
                column_name = column_names[column_index]
                if column_name:
                    self._column_model.set_column_visible(column_name, visible)
                else:
                    print(f"Warning: Could not get name for column index {column_index}")
            else:
                print(
                    f"Warning: column index {column_index} out of bounds for ColumnModel columns list"
                )
        else:
            print(f"Warning: Invalid column index {column_index} for setColumnVisible")

    def isColumnVisible(self, column_index: int) -> bool:
        """Checks if a column is visible by its logical index, using ColumnModel."""
        source_model = self.sourceModel()
        if source_model and 0 <= column_index < source_model.columnCount():
            # Use the index to get the column name directly from ColumnModel's list
            column_names = self._column_model.get_columns()
            if 0 <= column_index < len(column_names):
                column_name = column_names[column_index]
                if column_name:
                    return self._column_model.is_column_visible(column_name)
                else:
                    print(
                        f"Warning: Could not get name for column index {column_index} in isColumnVisible"
                    )
                    return False  # Assume hidden if name not found
            else:
                print(
                    f"Warning: column index {column_index} out of bounds for ColumnModel columns list in isColumnVisible"
                )
                return False
        else:
            print(f"Warning: Invalid column index {column_index} for isColumnVisible")
            return False

    def _setup_delegates(self):
        """Set up delegates for cell rendering."""
        if not self.table_view:
            print("Error: Cannot setup delegates, table_view not initialized.")
            return

        # Disconnect old delegate signal if exists
        old_delegate = self.table_view.itemDelegate()
        if old_delegate and hasattr(old_delegate, "validationFailed"):
            try:
                old_delegate.validationFailed.disconnect(self._on_validation_failed)
            except (
                TypeError,
                RuntimeError,
            ):  # Handles signal not connected or already disconnected
                pass

        # Example: Set different delegates based on column or data type if needed
        # For now, set the CorrectionDelegate as default
        new_delegate = CorrectionDelegate(self.table_view)
        self.table_view.setItemDelegate(new_delegate)

        # Connect new delegate signal
        if hasattr(new_delegate, "validationFailed"):
            new_delegate.validationFailed.connect(self._on_validation_failed)

        # You might want to set specific delegates for columns:
        # validation_delegate = ValidationDelegate(self.table_view)
        # self.table_view.setItemDelegateForColumn(COLUMN_INDEX_FOR_VALIDATION, validation_delegate)

    @Slot(QModelIndex, str)
    def _on_validation_failed(self, index: QModelIndex, error_message: str):
        """Slot to handle validation failures from the delegate."""
        # Map index if needed (though maybe less relevant for just showing message)
        # source_index = self._filter_model.mapToSource(index)
        row = index.row()
        col = index.column()

        # Show a message box
        QMessageBox.warning(
            self,
            "Validation Failed",
            f"Invalid input for cell ({row}, {col}):\n{error_message}",
        )
        # TODO: Optionally, re-open editor or highlight the cell
        # self.table_view.edit(index)

    # Delegate other necessary QTableView methods...
    # Example:
    def resizeColumnsToContents(self):
        if self.table_view:
            self.table_view.resizeColumnsToContents()

    # --- Public Methods for Column Visibility (Convenience) ---
    def hide_column(self, column_name: str):
        """Convenience method to hide a column by name."""
        try:
            self._column_model.set_column_visible(column_name, False)
        except ValueError as e:
            print(f"Error hiding column: {e}")

    def show_column(self, column_name: str):
        """Convenience method to show a column by name."""
        try:
            self._column_model.set_column_visible(column_name, True)
        except ValueError as e:
            print(f"Error showing column: {e}")

    def get_visible_columns(self) -> typing.List[str]:
        """Get a list of names of the currently visible columns."""
        return self._column_model.get_visible_columns()

    def get_column_visibility(self) -> typing.Dict[str, bool]:
        """Get the visibility state of all columns."""
        return self._column_model.get_visibility_state()

    def set_column_visibility_state(self, state: typing.Dict[str, bool]):
        """Set the visibility state for multiple columns."""
        self._column_model.set_visibility_state(state)

    def resizeColumnsToContents(self):
        """Resizes all columns to fit their contents."""
        if self.table_view:
            self.table_view.resizeColumnsToContents()
