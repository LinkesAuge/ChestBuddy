"""
data_view_model.py

This module contains the DataViewModel class, which serves as an adapter between
the ChestDataModel and the DataTableView, providing data access, sorting, and filtering.
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
import typing

# Placeholder for ChestDataModel and TableStateManager if needed
# from chestbuddy.core.models import ChestDataModel
# from chestbuddy.core.managers import TableStateManager
ChestDataModel = typing.NewType("ChestDataModel", object)  # Placeholder type
TableStateManager = typing.NewType("TableStateManager", object)  # Placeholder type


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

    def __init__(self, data_model: ChestDataModel, parent=None):
        """
        Initializes the DataViewModel.

        Args:
            data_model (ChestDataModel): The underlying data model.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self._data_model = data_model
        self._table_state_manager: typing.Optional[TableStateManager] = None

    def source_model(self) -> ChestDataModel:
        """
        Returns the underlying source data model.

        Returns:
            ChestDataModel: The source data model.
        """
        return self._data_model

    def set_table_state_manager(self, manager: TableStateManager) -> None:
        """
        Sets the table state manager used for cell state information.

        Args:
            manager (TableStateManager): The table state manager instance.
        """
        self._table_state_manager = manager
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
        # Delegate to the source model's rowCount
        return self._data_model.rowCount(parent) if self._data_model else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index.

        Returns:
            int: The number of columns.
        """
        # Delegate to the source model's columnCount
        return self._data_model.columnCount(parent) if self._data_model else 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> typing.Any:
        """
        Returns the data stored under the given role for the item referred to by the index.

        Args:
            index (QModelIndex): The model index.
            role (int): The data role.

        Returns:
            typing.Any: The data for the given index and role.
        """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            # Delegate to the source model's data for DisplayRole
            return self._data_model.data(index, role)
        elif role == Qt.EditRole:
            # Delegate EditRole to source model as well (can be customized later)
            return self._data_model.data(index, role)
        elif role == DataViewModel.ValidationStateRole:
            if self._table_state_manager:
                # Retrieve validation state from the manager
                # Placeholder: Actual implementation will depend on TableStateManager API
                return self._table_state_manager.get_cell_state(index.row(), index.column())
            return None  # Or a default state like 'UNKNOWN'
        elif role == Qt.BackgroundRole:
            # Placeholder: Determine background color based on validation state
            if self._table_state_manager:
                state = self._table_state_manager.get_cell_state(index.row(), index.column())
                # Example mapping (will need refinement based on actual states)
                if state == "INVALID":
                    return QColor("#ffb6b6")  # Light red
                elif state == "CORRECTABLE":
                    return QColor("#fff3b6")  # Light yellow
            return None  # Default background
        elif role == Qt.ToolTipRole:
            # Placeholder: Provide tooltips for validation/correction states
            if self._table_state_manager:
                state = self._table_state_manager.get_cell_state(index.row(), index.column())
                # Example tooltips
                if state == "INVALID":
                    return f"Invalid data in cell ({index.row()}, {index.column()})"
                elif state == "CORRECTABLE":
                    return f"Correctable data in cell ({index.row()}, {index.column()})"
            return None

        # Handle other roles as needed

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
        # Delegate header data requests to the source model
        return self._data_model.headerData(section, orientation, role)

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
        source_flags = self._data_model.flags(index) if self._data_model else default_flags
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
        if self._data_model and self._data_model.setData(index, value, role):
            # Emit dataChanged signal to notify views
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    # --- Placeholder methods for future implementation ---

    def on_cell_states_changed(self, changes: dict):
        """
        Slot to handle updates from the TableStateManager.

        Args:
            changes (dict): Dictionary describing the state changes.
                           Example: {(row, col): new_state, ...}
        """
        # This needs to trigger updates for the affected cells/roles
        # For simplicity, might initially trigger a layoutChanged or update specific indices

        # Find min/max row/col for dataChanged signal
        if not changes:
            return

        min_row = min(r for r, c in changes.keys())
        max_row = max(r for r, c in changes.keys())
        min_col = min(c for r, c in changes.keys())
        max_col = max(c for r, c in changes.keys())

        top_left_index = self.index(min_row, min_col)
        bottom_right_index = self.index(max_row, max_col)

        # Emit dataChanged for the affected range and relevant roles
        # (ValidationStateRole, BackgroundRole, ToolTipRole, etc.)
        roles_to_update = [DataViewModel.ValidationStateRole, Qt.BackgroundRole, Qt.ToolTipRole]
        self.dataChanged.emit(top_left_index, bottom_right_index, roles_to_update)

        # print(f"DataViewModel received state changes: {changes}")
        # TODO: Implement more granular updates if needed

    # TODO: Add methods for sorting and filtering support
    # def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
    #     pass

    # def setFilterKeyColumn(self, column: int):
    #     pass

    # def setFilterRegularExpression(self, pattern: str):
    #     pass
