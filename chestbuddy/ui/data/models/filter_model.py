"""
filter_model.py

Description: Implements a proxy model for filtering and sorting data from DataViewModel.
Usage:
    source_model = DataViewModel(...)
    filter_model = FilterModel()
    filter_model.setSourceModel(source_model)
    filter_model.set_filter_text("some text")
"""

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, Qt, Slot
from typing import Any, Dict, Optional


class FilterModel(QSortFilterProxyModel):
    """
    A QSortFilterProxyModel subclass for filtering data in the DataView.

    Provides filtering based on text input across specified columns.
    Handles sorting delegation to the source model.
    """

    def __init__(self, parent=None):
        """
        Initialize the FilterModel.

        Args:
            parent: Optional parent object.
        """
        super().__init__(parent)
        self._filter_text = ""
        self._filter_columns = []  # List of column indices to filter on
        # Set dynamicSortFilter to False because we handle sorting in DataViewModel
        self.setDynamicSortFilter(False)

    def set_filter_text(self, text: str):
        """
        Set the text used for filtering rows.

        Args:
            text: The filter string. Case-insensitive matching.
        """
        self._filter_text = text.lower()
        self.invalidateFilter()  # Trigger re-filtering

    def set_filter_columns(self, columns: list[int]):
        """
        Set the column indices to apply the filter text to.

        Args:
            columns: A list of logical column indices.
        """
        self._filter_columns = columns
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determines whether a row from the source model should be included.

        Args:
            source_row: The row number in the source model.
            source_parent: The parent index in the source model.

        Returns:
            True if the row should be included, False otherwise.
        """
        if not self._filter_text:
            return True  # Accept all rows if no filter text

        source_model = self.sourceModel()
        if not source_model:
            return False

        # Filter based on specified columns or all columns if none specified
        columns_to_check = self._filter_columns or range(source_model.columnCount())

        for col_index in columns_to_check:
            index = source_model.index(source_row, col_index, source_parent)
            cell_data = source_model.data(index, Qt.DisplayRole)
            if cell_data is not None and self._filter_text in str(cell_data).lower():
                return True  # Row accepted if text found in any specified column

        return False  # Row rejected if text not found in any specified column

    # Override sort to delegate to DataViewModel if it handles sorting
    # If DataViewModel does not handle sorting itself, remove this override
    # and set setDynamicSortFilter(True) in __init__
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """
        Overrides the sort method.

        If the source model (DataViewModel) handles sorting, delegate to it.
        Otherwise, rely on the default QSortFilterProxyModel implementation.
        """
        source_model = self.sourceModel()
        if source_model and hasattr(source_model, "sort"):
            # Delegate sorting to the source DataViewModel
            # The source model should emit layoutChanged signals
            source_model.sort(column, order)
        else:
            # Fallback to default QSortFilterProxyModel sorting if source doesn't handle it
            # This requires setDynamicSortFilter(True) in __init__
            super().sort(column, order)

    # Optionally, override lessThan if custom sorting logic is needed here
    # def lessThan(self, source_left: QModelIndex, source_right: QModelIndex) -> bool:
    #    pass
