"""
data_view_model.py

This module contains the DataViewModel class, which serves as an adapter between
the ChestDataModel and the DataTableView, providing data access, sorting, and filtering.
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, Slot
from PySide6.QtGui import QColor
import typing
import pandas as pd

from chestbuddy.core.models import ChestDataModel  # Assuming this is the source model
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState

# Placeholder for ChestDataModel and TableStateManager if needed
# from chestbuddy.core.models import ChestDataModel
# from chestbuddy.core.managers import TableStateManager
ChestDataModel = typing.NewType("ChestDataModel", object)  # Placeholder type
TableStateManager = typing.NewType("TableStateManager", object)  # Placeholder type

# Placeholder for CorrectionSuggestion structure
CorrectionSuggestion = typing.NewType("CorrectionSuggestion", object)


class DataViewModel(QAbstractTableModel):
    """
    Implementation of the DataViewModel, which adapts the ChestDataModel
    for display in a QTableView.

    Provides data access, basic role handling, and placeholders for
    validation state integration.
    """

    # Define custom roles
    ValidationStateRole = Qt.UserRole + 1
    CorrectionStateRole = Qt.UserRole + 2
    ErrorDetailsRole = Qt.UserRole + 3
    CorrectionSuggestionsRole = Qt.UserRole + 4  # Role for suggestions
    ValidationErrorRole = Qt.UserRole + 5  # Add role for error details

    # Signals
    # validation_updated = Signal() # Might not be needed if using dataChanged

    def __init__(self, source_model: ChestDataModel, state_manager: TableStateManager, parent=None):
        """
        Initializes the DataViewModel.

        Args:
            source_model (ChestDataModel): The underlying data model.
            state_manager (TableStateManager): The table state manager instance.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self._source_model = source_model
        self._state_manager = state_manager

        self._connect_source_model_signals()
        self._connect_state_manager_signals()  # Connect to state manager

        # Sort state
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

    def _connect_source_model_signals(self):
        """Connect signals from the source ChestDataModel."""
        if self._source_model and hasattr(self._source_model, "data_changed"):
            try:
                # Disconnect first to prevent duplicate connections if called again
                try:
                    self._source_model.data_changed.disconnect(self._on_source_data_changed)
                except RuntimeError:
                    pass  # Signal was not connected
                self._source_model.data_changed.connect(self._on_source_data_changed)
                print("Successfully connected source model data_changed signal.")  # Debug
            except Exception as e:
                print(f"Error connecting source model data_changed signal: {e}")  # Debug
        else:
            print("Source model does not have data_changed signal or is None.")  # Debug

    def _connect_state_manager_signals(self):
        """Connect signals from the TableStateManager."""
        if self._state_manager and hasattr(self._state_manager, "state_changed"):
            try:
                # Disconnect first
                try:
                    self._state_manager.state_changed.disconnect(
                        self._on_state_manager_state_changed
                    )
                except RuntimeError:
                    pass
                self._state_manager.state_changed.connect(self._on_state_manager_state_changed)
                print("Successfully connected state_manager state_changed signal.")  # Debug
            except Exception as e:
                print(f"Error connecting state_manager state_changed signal: {e}")  # Debug
        else:
            print("State manager does not have state_changed signal or is None.")  # Debug

    def source_model(self) -> ChestDataModel:
        """
        Returns the underlying source data model.

        Returns:
            ChestDataModel: The source data model.
        """
        return self._source_model

    def set_table_state_manager(self, manager: TableStateManager) -> None:
        """
        Sets the table state manager used for cell state information.

        Args:
            manager (TableStateManager): The table state manager instance.
        """
        self._state_manager = manager
        # TODO: Connect signals if necessary and trigger layout change?
        # self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Returns the number of rows in the model.

        Args:
            parent (QModelIndex): The parent index.

        Returns:
            int: The number of rows.
        """
        # Get row count from the source model's property
        if self._source_model and hasattr(self._source_model, "row_count"):
            return self._source_model.row_count
        return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index.

        Returns:
            int: The number of columns.
        """
        # Get column names from the source model's property
        if self._source_model and hasattr(self._source_model, "column_names"):
            return len(self._source_model.column_names)
        return 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> typing.Any:
        """
        Returns the data stored under the given role for the item referred to by the index.

        Args:
            index (QModelIndex): The model index.
            role (int): The data role.

        Returns:
            typing.Any: The data for the given index and role.
        """
        if not index.isValid() or not self._source_model:
            return None

        row = index.row()
        col = index.column()

        # Get column name for accessing source model
        # Use the defined EXPECTED_COLUMNS order from ChestDataModel for consistency
        expected_columns = self._source_model.EXPECTED_COLUMNS
        if col >= len(expected_columns):
            return None
        column_name = expected_columns[col]

        full_state = self._state_manager.get_full_cell_state(row, col)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            # Get data from source model using its method
            value = self._source_model.get_cell_value(row, column_name)
            return value
        elif role == self.ValidationStateRole:
            return full_state.validation_status if full_state else CellState.NORMAL
        elif role == self.CorrectionStateRole:
            # Could return a specific state or bool indicating correctability
            return bool(full_state and full_state.correction_suggestions)
        elif role == self.ErrorDetailsRole:
            return full_state.error_details if full_state else None
        elif role == self.CorrectionSuggestionsRole:
            return full_state.correction_suggestions if full_state else []
        elif role == Qt.BackgroundRole:
            # Use full_state for background logic
            status = full_state.validation_status if full_state else CellState.NORMAL
            if status == CellState.INVALID:
                return QColor("#ffb6b6")  # Light red
            elif status == CellState.CORRECTABLE:
                return QColor("#fff3b6")  # Light yellow
            elif status == CellState.WARNING:
                return QColor("#ffe4b6")  # Light orange
            elif status == CellState.INFO:
                return QColor("#b6e4ff")  # Light blue
            return None  # Default background
        elif role == Qt.ToolTipRole:
            # Use full_state for tooltip logic
            tooltip_parts = []
            if full_state:
                if full_state.error_details:
                    tooltip_parts.append(f"Issue: {full_state.error_details}")
                if full_state.correction_suggestions:
                    # Maybe just indicate suggestions are available?
                    tooltip_parts.append(
                        f"Corrections Available ({len(full_state.correction_suggestions)})"
                    )
            return "\n".join(tooltip_parts) if tooltip_parts else None

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> typing.Any:
        """
        Returns the data for the given role and section in the header.

        Args:
            section (int): The section index.
            orientation (Qt.Orientation): The header orientation.
            role (int): The data role.

        Returns:
            typing.Any: The header data.
        """
        if (
            orientation == Qt.Horizontal
            and role == Qt.DisplayRole
            and self._source_model
            and hasattr(self._source_model, "column_names")
        ):
            column_names = self._source_model.column_names
            if 0 <= section < len(column_names):
                return column_names[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Returns the item flags for the given index.

        Args:
            index (QModelIndex): The model index.

        Returns:
            Qt.ItemFlags: The flags for the item.
        """
        if not index.isValid():
            return Qt.NoItemFlags

        # Make items selectable, enabled, and editable by default
        # Delegate to source model's flags and potentially modify them
        default_flags = super().flags(index)
        source_flags = self._source_model.flags(index) if self._source_model else default_flags
        # Example: Add editability
        source_flags |= Qt.ItemIsEditable
        return source_flags

    def setData(self, index: QModelIndex, value: typing.Any, role: int = Qt.EditRole) -> bool:
        """
        Sets the role data for the item at index to value.

        Args:
            index (QModelIndex): The model index.
            value (typing.Any): The new value.
            role (int): The data role (usually Qt.EditRole).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        # Delegate setData to the source model
        if self._source_model and self._source_model.setData(index, value, role):
            # Emit dataChanged signal to notify views
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    @Slot()
    def _on_source_data_changed(self):
        """
        Slot to handle data changes in the source ChestDataModel.

        Resets the model to reflect the changes.
        """
        print(f"DataViewModel received source data_changed signal. Resetting model.")  # Debug
        self.beginResetModel()
        # Optionally, update internal caches or states if needed
        self.endResetModel()

    @Slot(set)  # Expecting a set of (row, col) tuples
    def _on_state_manager_state_changed(self, changed_indices: set):
        """
        Slot to handle state changes from the TableStateManager.

        Emits dataChanged for the specific indices and relevant roles.
        """
        print(f"DataViewModel received state_changed for {len(changed_indices)} indices.")  # Debug
        if not changed_indices:
            return

        # Define roles affected by state changes
        # These roles derive their data from the TableStateManager state
        affected_roles = [
            self.ValidationStateRole,
            self.CorrectionStateRole,
            self.ErrorDetailsRole,
            self.CorrectionSuggestionsRole,
            Qt.BackgroundRole,
            Qt.ToolTipRole,
        ]

        # Emit dataChanged for each affected index individually
        # This explicitly tells the view which cells and roles need refreshing.
        for r, c in changed_indices:
            idx = self.index(r, c)
            if idx.isValid():
                self.dataChanged.emit(idx, idx, affected_roles)

        # Emit a general signal if needed (though dataChanged is standard)
        # self.validation_updated.emit()

    # --- Direct access to state details (can be used by delegates/view) ---
    def get_cell_details(self, row: int, col: int) -> typing.Optional[str]:
        """Get error details for a cell directly from the state manager."""
        full_state = self._state_manager.get_full_cell_state(row, col)
        return full_state.error_details if full_state else None

    def get_correction_suggestions(
        self, row: int, col: int
    ) -> typing.Optional[typing.List[CorrectionSuggestion]]:
        """Get correction suggestions for a cell directly from the state manager."""
        full_state = self._state_manager.get_full_cell_state(row, col)
        return full_state.correction_suggestions if full_state else []

    # --- Sorting --- #

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Sort the model by the specified column and order.

        Args:
            column (int): The column index to sort by.
            order (Qt.SortOrder): The sort order (Ascending or Descending).
        """
        if self._source_model and hasattr(self._source_model, "sort_data"):
            column_name = self.headerData(column, Qt.Horizontal)
            if column_name:
                self.layoutAboutToBeChanged.emit()
                self._sort_column = column
                self._sort_order = order
                try:
                    # Delegate sorting to the source model if possible
                    self._source_model.sort_data(column_name, order == Qt.AscendingOrder)
                except Exception as e:
                    print(f"Error sorting source model: {e}")
                # Emit layoutChanged signal after sorting
                self.layoutChanged.emit()
            else:
                print(f"Could not get header data for column {column}")
        else:
            print("Source model does not support sorting or is not set.")

    def current_sort_column(self) -> int:
        """Returns the index of the column currently used for sorting."""
        return self._sort_column

    def current_sort_order(self) -> Qt.SortOrder:
        """Returns the current sort order."""
        return self._sort_order

    # TODO: Add methods for sorting and filtering support
    # def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
    #     pass

    # def setFilterKeyColumn(self, column: int):
    #     pass

    # def setFilterRegularExpression(self, pattern: str):
    #     pass
