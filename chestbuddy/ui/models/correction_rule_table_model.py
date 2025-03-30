"""
CorrectionRuleTableModel.

This module implements a table model for the correction rules in the ChestBuddy application.
It provides a model for displaying correction rules in a tabular format with 5 columns:
Order, From, To, Category, and Status.
"""

from typing import List, Any, Optional
import logging

from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, Signal, QObject

from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.core.models.correction_rule import CorrectionRule


class CorrectionRuleTableModel(QAbstractTableModel):
    """
    Table model for correction rules.

    This model provides data for displaying correction rules in a table view.
    It handles the interaction with the correction controller to get rule data.
    """

    def __init__(self, controller: CorrectionController, parent: Optional[QObject] = None):
        """
        Initialize the model.

        Args:
            controller: Controller for accessing correction rules
            parent: Parent object
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._controller = controller
        self._rules = []
        self._category_filter = ""
        self._status_filter = ""
        self._search_filter = ""
        self._headers = ["Order", "From", "To", "Category", "Status"]

        # Connect to controller signals
        if hasattr(self._controller, "rules_changed"):
            self._controller.rules_changed.connect(self._on_rules_changed)

        # Initial data load
        self._refresh_data()

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        Args:
            parent: Parent index (unused for table models)

        Returns:
            int: Number of rows/rules
        """
        if parent.isValid():
            return 0
        return len(self._rules)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        Args:
            parent: Parent index (unused for table models)

        Returns:
            int: Number of columns (5)
        """
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """
        Get data for a specific index and role.

        Args:
            index: Model index to get data for
            role: Data role (display, decoration, etc.)

        Returns:
            Any: Data for the specified index and role
        """
        if not index.isValid() or index.row() >= len(self._rules):
            return None

        rule = self._rules[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:  # Order
                return str(rule.order)
            elif column == 1:  # From
                return rule.from_value
            elif column == 2:  # To
                return rule.to_value
            elif column == 3:  # Category
                return rule.category
            elif column == 4:  # Status
                return rule.status.capitalize()

        elif role == Qt.TextAlignmentRole:
            if column == 0:  # Order
                return int(Qt.AlignRight | Qt.AlignVCenter)
            else:
                return int(Qt.AlignLeft | Qt.AlignVCenter)

        elif role == Qt.ForegroundRole:
            if column == 4:  # Status
                return Qt.green if rule.status == "enabled" else Qt.red

        elif role == Qt.UserRole:
            # Return the rule index for selection handling
            return index.row()

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """
        Get header data for a section.

        Args:
            section: Section index (row or column)
            orientation: Horizontal or vertical orientation
            role: Data role

        Returns:
            Any: Header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._headers):
                return self._headers[section]

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Get flags for a specific index.

        Args:
            index: Model index

        Returns:
            Qt.ItemFlags: Flags for the index
        """
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def set_filters(self, category: str = "", status: str = "", search: str = ""):
        """
        Set filters for the model.

        Args:
            category: Category filter string
            status: Status filter string
            search: Search filter string
        """
        self._category_filter = category
        self._status_filter = status
        self._search_filter = search
        self._refresh_data()

    def get_rule(self, row: int) -> Optional[CorrectionRule]:
        """
        Get a rule by row index.

        Args:
            row: Row index

        Returns:
            CorrectionRule: The rule at the specified row, or None if invalid
        """
        if 0 <= row < len(self._rules):
            return self._rules[row]
        return None

    def get_rule_index(self, row: int) -> int:
        """
        Get the controller index for a rule by row index.

        Args:
            row: Row index in the filtered model

        Returns:
            int: Index of the rule in the controller, or -1 if invalid
        """
        if 0 <= row < len(self._rules):
            # Find the rule in the controller's full list
            rule = self._rules[row]
            all_rules = self._controller.get_rules()
            for i, r in enumerate(all_rules):
                if r == rule:
                    return i
        return -1

    def _refresh_data(self):
        """Refresh model data from the controller."""
        self.beginResetModel()
        self._rules = self._controller.get_rules(
            category=self._category_filter,
            status=self._status_filter,
            search_term=self._search_filter,
        )
        self.endResetModel()

    def _on_rules_changed(self):
        """Handle rules changed signal from controller."""
        self._refresh_data()
