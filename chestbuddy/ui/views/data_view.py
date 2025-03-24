import logging
from PySide6.QtCore import QItemSelectionModel, QModelIndex, Qt, QTimer
from PySide6.QtWidgets import (
    QHeaderView,
    QLineEdit,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from chestbuddy.models.filtering import FilterProxyModel
from chestbuddy.ui.views.base_view import BaseView

logger = logging.getLogger(__name__)


class DataView(BaseView):
    def __init__(self, parent=None) -> None:
        """Initialize the DataView."""
        super().__init__(parent)
        self._data_view = DataViewAdapter(parent=self)
        self._layout.addWidget(self._data_view)

    def set_data_available(self, available: bool) -> None:
        """
        Update the view based on data availability.

        Args:
            available: Whether data is available
        """
        logger.debug(f"[DATA_VIEW] Setting data available: {available}")
        super().set_data_available(available)

    def update(self, force_rescan: bool = False) -> None:
        """
        Update the view with the latest data.

        Args:
            force_rescan: Whether to force a rescan
        """
        self._data_view.update_data(force_rescan)


class DataViewAdapter(QWidget):
    def _populate_table_view(self) -> None:
        """Populate the table view with the model."""
        logger.debug("[DATA_TABLE] Starting table population")

        # Log the initial state of the table
        initial_enabled = self._table_view.isEnabled()
        initial_sorting = self._table_view.isSortingEnabled()
        logger.debug(
            f"[DATA_TABLE] Initial state - Enabled: {initial_enabled}, Sorting: {initial_sorting}"
        )

        # Temporarily disable the table view and sorting while setting the model
        logger.debug("[DATA_TABLE] Temporarily disabling table and sorting")
        self._table_view.setEnabled(False)
        self._table_view.setSortingEnabled(False)

        # Set the model and update column widths
        logger.debug("[DATA_TABLE] Setting model and updating columns")
        self._table_view.setModel(self._filter_proxy_model)
        self._update_column_widths()

        # Re-enable sorting and the table
        logger.debug("[DATA_TABLE] Re-enabling sorting and table")
        self._table_view.setSortingEnabled(True)
        self._table_view.setEnabled(True)

        # Log the final state of the table
        final_enabled = self._table_view.isEnabled()
        final_sorting = self._table_view.isSortingEnabled()
        logger.debug(
            f"[DATA_TABLE] Final state - Enabled: {final_enabled}, Sorting: {final_sorting}"
        )

        logger.debug("[DATA_TABLE] Table population complete")

    def update_data(self, force_rescan: bool = False) -> None:
        """Update the data in the view."""
        logger.debug(f"[DATA_VIEW] Updating data (force_rescan: {force_rescan})")

        # Only proceed if parent has changed
        if self._parent is None or not self._parent.has_changed(force_rescan):
            logger.debug("[DATA_VIEW] No changes detected, skipping update")
            return

        logger.debug("[DATA_VIEW] Changes detected, refreshing data")

        # Reset the filter
        self._search_input.setText("")

        # Populate the table
        self._populate_table_view()

        # Focus on the table
        logger.debug("[DATA_VIEW] Setting focus to table view")
        self._table_view.setFocus()

        logger.debug("[DATA_VIEW] Data update complete")
