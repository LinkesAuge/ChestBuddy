"""
data_view_model.py

This module contains the DataViewModel class, which serves as an adapter between
the ChestDataModel and the DataTableView, providing data access, sorting, and filtering.
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, Slot
from PySide6.QtGui import QColor
import typing
import pandas as pd
import logging
import numpy as np

from chestbuddy.core.models import ChestDataModel  # Assuming this is the source model
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState

# Placeholder for ChestDataModel and TableStateManager if needed
# from chestbuddy.core.models import ChestDataModel
# from chestbuddy.core.managers import TableStateManager
ChestDataModel = typing.NewType("ChestDataModel", object)  # Placeholder type
TableStateManager = typing.NewType("TableStateManager", object)  # Placeholder type

# Placeholder for CorrectionSuggestion structure
CorrectionSuggestion = typing.NewType("CorrectionSuggestion", object)

# Add logger setup
logger = logging.getLogger(__name__)


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

    # Color constants for background roles (Can be moved to a central theme/color manager)
    INVALID_COLOR = QColor("#ffb6b6")  # Light Red
    CORRECTABLE_COLOR = QColor("#fff3b6")  # Light Yellow

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

        # Ensure the source model is valid before accessing properties
        if not self._source_model:
            print("Warning: DataViewModel initialized with None source model.")
            # Handle appropriately, maybe raise an error or set defaults

        # Ensure the state manager is valid before accessing properties
        if not self._state_manager:
            print("Warning: DataViewModel initialized with None state manager.")
            # Handle appropriately

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
            except Exception as e:
                print(f"Error connecting source model data_changed signal: {e}")  # Debug
        else:
            print("Source model does not have data_changed signal or is None.")  # Debug

    def _connect_state_manager_signals(self):
        """Connect signals from the TableStateManager."""
        if self._state_manager and hasattr(self._state_manager, "state_changed"):
            try:
                # Attempt to disconnect first, ignore error if not connected
                try:
                    self._state_manager.state_changed.disconnect(
                        self._on_state_manager_state_changed
                    )
                except RuntimeError:
                    pass  # Signal wasn't connected, which is fine

                # Connect the signal
                self._state_manager.state_changed.connect(self._on_state_manager_state_changed)
            except Exception as e:
                print(f"Error connecting state_manager state_changed signal: {e}")  # Debug
        else:
            print("State manager is None or does not have state_changed signal.")  # Debug

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
        # Use the length of the internal DataFrame
        if (
            not parent.isValid()
            and self._source_model
            and hasattr(self._source_model, "_data")
            and self._source_model._data is not None
        ):
            try:
                return len(self._source_model._data)
            except Exception as e:
                print(f"Error getting row count from source model: {e}")
                return 0
        return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index.

        Returns:
            int: The number of columns.
        """
        # Use the length of the column_names property
        if (
            not parent.isValid()
            and self._source_model
            and hasattr(self._source_model, "column_names")
            and self._source_model.column_names is not None
        ):
            try:
                return len(self._source_model.column_names)
            except Exception as e:
                print(f"Error getting column count from source model: {e}")
                return 0
        return 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> typing.Any:
        if not index.isValid() or not self._source_model or not self._state_manager:
            return None

        row = index.row()
        col = index.column()

        try:
            if role == Qt.DisplayRole or role == Qt.EditRole:
                # Access data directly from the source model's DataFrame
                # Assuming ChestDataModel has a way to get value by row/col index
                # Option 1: Direct access (if _data is accessible and reliable)
                if 0 <= row < len(self._source_model._data) and 0 <= col < len(
                    self._source_model._data.columns
                ):
                    value = self._source_model._data.iloc[row, col]
                    # Convert numpy types to standard Python types for Qt if necessary
                    if isinstance(value, np.generic):
                        value = value.item()
                    return str(value) if value is not None else ""  # Ensure string for display
                else:
                    return None  # Index out of bounds
                # Option 2: Using a dedicated method (if exists)
                # return self._source_model.get_value(row, col)

            # Get full state safely
            full_state = self._state_manager.get_full_cell_state(row, col)

            if role == self.ValidationStateRole:
                return (
                    full_state.validation_status
                    if (full_state and hasattr(full_state, "validation_status"))
                    else CellState.NORMAL
                )
            elif role == self.CorrectionStateRole:
                return bool(
                    full_state
                    and hasattr(full_state, "correction_suggestions")
                    and full_state.correction_suggestions
                )
            elif role == self.ErrorDetailsRole:
                return (
                    full_state.error_details
                    if (full_state and hasattr(full_state, "error_details"))
                    else None
                )
            elif role == self.CorrectionSuggestionsRole:
                return (
                    full_state.correction_suggestions
                    if (full_state and hasattr(full_state, "correction_suggestions"))
                    else []
                )
            elif role == Qt.BackgroundRole:
                status = (
                    full_state.validation_status
                    if (full_state and hasattr(full_state, "validation_status"))
                    else CellState.NORMAL
                )
                if status == CellState.INVALID:
                    return self.INVALID_COLOR
                elif status == CellState.CORRECTABLE:
                    return self.CORRECTABLE_COLOR
                return None
            elif role == Qt.ToolTipRole:
                tooltip_parts = []
                if full_state:
                    if (
                        hasattr(full_state, "validation_status")
                        and full_state.validation_status == CellState.INVALID
                        and hasattr(full_state, "error_details")
                        and full_state.error_details
                    ):
                        tooltip_parts.append(full_state.error_details)
                    elif (
                        hasattr(full_state, "validation_status")
                        and full_state.validation_status == CellState.CORRECTABLE
                        and hasattr(full_state, "correction_suggestions")
                        and full_state.correction_suggestions
                    ):
                        suggestions_str = "\n".join(
                            [
                                f"- {getattr(s, 'corrected_value', str(s))}"
                                for s in full_state.correction_suggestions
                            ]
                        )
                        tooltip_parts.append(f"Suggestions:\n{suggestions_str}")
                return "\n".join(tooltip_parts) if tooltip_parts else None

        except IndexError:
            print(f"IndexError in DataViewModel.data(): Index ({row},{col}) out of bounds.")
            return None
        except AttributeError as ae:
            print(
                f"AttributeError in DataViewModel.data() for index ({row},{col}), role {role}: {ae}"
            )  # Debug attribute errors
            return None
        except Exception as e:
            print(f"Error in DataViewModel.data(): {e} for index ({row},{col}), role {role}")
            return None

        return None  # Role not handled

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
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and self._source_model:
            try:
                # Ensure the source model has column_names property and section is valid
                if hasattr(self._source_model, "column_names") and 0 <= section < len(
                    self._source_model.column_names
                ):
                    return self._source_model.column_names[section]
                else:
                    print(
                        f"Warning: Cannot get header data for section {section}. Source model columns: {getattr(self._source_model, 'column_names', 'N/A')}"
                    )
                    return None
            except Exception as e:
                print(f"Error in DataViewModel.headerData(): {e} for section {section}")
                return None

        # Handle vertical header if needed (row numbers)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)  # Return 1-based row number

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Returns the item flags for the given index.

        Args:
            index (QModelIndex): The model index.

        Returns:
            Qt.ItemFlags: The flags for the item.
        """
        if not index.isValid() or not self._source_model:
            return Qt.NoItemFlags

        # Get flags from source model
        source_flags = Qt.NoItemFlags
        if hasattr(self._source_model, "flags"):
            source_flags = self._source_model.flags(index)
        else:
            # Provide sensible defaults if source doesn't have flags
            source_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        # Add editable flag
        return source_flags | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value: typing.Any, role: int = Qt.EditRole) -> bool:
        """
        Sets the role data for the item at index to value.

        Args:
            index (QModelIndex): The model index.
            value (typing.Any): The new value.
            role (int): The data role (typically EditRole).

        Returns:
            bool: True if successful, False otherwise.
        """
        if (
            not index.isValid()
            or role != Qt.EditRole
            or not self._source_model
            or not hasattr(self._source_model, "setData")
        ):
            return False

        success = self._source_model.setData(index, value, role)
        if success:
            self.dataChanged.emit(index, index, [role])
            # Potentially trigger re-validation or state update here
        return success

    @Slot()
    def _on_source_data_changed(self):
        """Slot called when the underlying source model changes."""
        print("DataViewModel received source data_changed")  # Debug
        # This might be too coarse, leading to full view updates.
        # Consider more granular updates if possible from source model.
        # A common pattern is to emit layoutChanged only if dimensions change,
        # and dataChanged otherwise.
        # For now, let's assume the source signals provide enough info
        # or we stick with resetting.
        # IMPORTANT: Check if source_model emits signals BEFORE data is ready.
        self.beginResetModel()  # Signals that the model is about to be reset
        # The actual data update is assumed to happen in the source model
        # and we just need to notify the view(s) that it has happened.
        self.endResetModel()  # Signals that the model has been reset
        print("DataViewModel finished model reset.")  # Debug

    @Slot(set)  # Expecting a set of (row, col) tuples
    def _on_state_manager_state_changed(self, changed_indices: set):
        """
        Slot called when the TableStateManager reports state changes.
        Emits dataChanged for the affected cells/roles.
        """
        print(f"DataViewModel received state_changed for {len(changed_indices)} indices.")  # Debug
        if not changed_indices:
            return

        # Determine the bounding box of changes for signal emission
        min_row = min(r for r, c in changed_indices)
        max_row = max(r for r, c in changed_indices)
        min_col = min(c for r, c in changed_indices)
        max_col = max(c for r, c in changed_indices)

        top_left = self.index(min_row, min_col)
        bottom_right = self.index(max_row, max_col)

        # Emit dataChanged for the affected range and relevant roles
        # Roles affected by state changes: BackgroundRole, ToolTipRole, ValidationStateRole, etc.
        affected_roles = [
            Qt.BackgroundRole,
            Qt.ToolTipRole,
            self.ValidationStateRole,
            self.CorrectionStateRole,
            self.ErrorDetailsRole,
            self.CorrectionSuggestionsRole,
        ]
        self.dataChanged.emit(top_left, bottom_right, affected_roles)
        print(
            f"Emitted dataChanged for range ({min_row},{min_col}) to ({max_row},{max_col})"
        )  # Debug

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
        Delegates sorting to the source model if it supports it.
        """
        print(f"DataViewModel sort called: column={column}, order={order}")  # Debug
        if not self._source_model or not hasattr(self._source_model, "sort_data"):
            print("Source model does not support sorting.")  # Debug
            super().sort(column, order)  # Fallback to default (likely no-op)
            return

        # Get column name from header data for source model's sort method
        column_name = self.headerData(column, Qt.Horizontal, Qt.DisplayRole)
        if column_name is None:
            print(f"Warning: Invalid column index {column} for sorting.")  # Debug
            return

        self._sort_column = column
        self._sort_order = order

        print(f"Sorting by column: {column_name}, order: {order}")  # Debug

        self.layoutAboutToBeChanged.emit()
        try:
            # Call the source model's sorting method
            self._source_model.sort_data(
                column_name=column_name, ascending=(order == Qt.AscendingOrder)
            )
            print("Source model sort_data called successfully.")  # Debug
        except Exception as e:
            print(f"Error during source model sort: {e}")  # Debug
        finally:
            self.layoutChanged.emit()
            print("Layout changed signal emitted after sort.")  # Debug

    def current_sort_column(self) -> int:
        """
        Returns the index of the column currently used for sorting.

        Returns:
            int: The sort column index, or -1 if not sorted.
        """
        return self._sort_column

    def current_sort_order(self) -> Qt.SortOrder:
        """
        Returns the current sort order.

        Returns:
            Qt.SortOrder: The current sort order.
        """
        return self._sort_order

    # --- Helper Methods (Placeholder) ---
    def get_cell_details(self, row: int, col: int) -> typing.Optional[str]:
        """Placeholder: Get detailed information about a cell."""
