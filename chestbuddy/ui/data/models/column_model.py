"""
column_model.py

Description: Manages the state and visibility of columns in the DataView.
Usage:
    model = ColumnModel()
    model.set_columns(['Player', 'Chest', 'Score'])
    model.set_column_visible('Score', False)
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import List, Dict, Optional


class ColumnModel(QObject):
    """
    Manages the visibility and potentially the order of columns.

    Emits signals when column visibility changes.

    Attributes:
        column_visibility_changed (Signal): Emitted when a column's visibility changes.
                                          Signature: (column_name: str, visible: bool)
        columns_changed (Signal): Emitted when the set of columns changes.
                                Signature: (columns: List[str])
    """

    column_visibility_changed = Signal(str, bool)
    columns_changed = Signal(list)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the ColumnModel.

        Args:
            parent: Optional parent object.
        """
        super().__init__(parent)
        self._columns: List[str] = []
        self._visibility: Dict[str, bool] = {}
        self._source_model = None  # Add reference to the source model

    def set_model(self, model) -> None:
        """
        Set the source data model.

        Args:
            model: The source data model (e.g., DataViewModel).
        """
        self._source_model = model
        if model:
            # Initialize columns based on the model
            try:
                # Use headerData to get columns if available, assuming horizontal orientation
                columns = [
                    model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                    for i in range(model.columnCount())
                ]
                self.set_columns([col for col in columns if col is not None])
            except Exception as e:
                print(f"Error initializing columns from model: {e}")
                self.set_columns([])  # Set to empty if error
        else:
            self.set_columns([])

    def set_columns(self, columns: List[str]) -> None:
        """
        Set the list of columns managed by the model.

        Resets visibility to True for all columns.

        Args:
            columns: A list of column names.
        """
        self._columns = list(columns)
        self._visibility = {col: True for col in self._columns}
        self.columns_changed.emit(self._columns)

    def get_columns(self) -> List[str]:
        """
        Get the list of all managed column names.

        Returns:
            A list of column names.
        """
        return list(self._columns)

    def get_visible_columns(self) -> List[str]:
        """
        Get the list of currently visible column names.

        Returns:
            A list of visible column names.
        """
        return [col for col in self._columns if self._visibility.get(col, False)]

    def is_column_visible(self, column_name: str) -> bool:
        """
        Check if a specific column is visible.

        Args:
            column_name: The name of the column.

        Returns:
            True if the column is visible, False otherwise.
        """
        return self._visibility.get(column_name, False)

    def set_column_visible(self, column_name: str, visible: bool) -> None:
        """
        Set the visibility of a specific column.

        Args:
            column_name: The name of the column.
            visible: True to make the column visible, False to hide it.

        Raises:
            ValueError: If the column_name is not managed by this model.
        """
        if column_name not in self._visibility:
            raise ValueError(f"Column '{column_name}' not found in the model.")

        if self._visibility[column_name] != visible:
            self._visibility[column_name] = visible
            self.column_visibility_changed.emit(column_name, visible)

    def toggle_column_visibility(self, column_name: str) -> None:
        """
        Toggle the visibility of a specific column.

        Args:
            column_name: The name of the column.
        """
        if column_name in self._visibility:
            self.set_column_visible(column_name, not self._visibility[column_name])

    def get_visibility_state(self) -> Dict[str, bool]:
        """
        Get the current visibility state of all columns.

        Returns:
            A dictionary mapping column names to their visibility status (bool).
        """
        return self._visibility.copy()

    def set_visibility_state(self, state: Dict[str, bool]) -> None:
        """
        Set the visibility state for multiple columns.

        Args:
            state: A dictionary mapping column names to visibility status.
                   Columns not in the state dictionary retain their current visibility.
        """
        changed = False
        for col, visible in state.items():
            if col in self._visibility and self._visibility[col] != visible:
                self._visibility[col] = visible
                self.column_visibility_changed.emit(col, visible)
                changed = True
        # If needed, emit a general signal if any change occurred
        # if changed:
        #     self.some_general_state_change_signal.emit() # Example
