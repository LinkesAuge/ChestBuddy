"""
data_dependency.py

Description: Defines the DataDependency class for tracking dependencies between UI components and data.
Usage:
    from chestbuddy.core.state.data_dependency import DataDependency
    from chestbuddy.ui.interfaces import IUpdatable

    # Create a dependency for a component on specific columns
    dependency = DataDependency(component, columns=["PLAYER", "SCORE"])

    # Create a dependency on row count
    dependency = DataDependency(component, row_count_dependency=True)

    # Check if component should update based on changes
    if dependency.should_update(changes):
        component.update()
"""

import logging
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

# Import IUpdatable interface with TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from chestbuddy.ui.interfaces import IUpdatable

logger = logging.getLogger(__name__)


class DataDependency:
    """
    Represents a dependency between a UI component and data state.

    This class tracks which columns or data aspects a component depends on,
    allowing for more targeted updates when data changes.

    Attributes:
        component (IUpdatable): The UI component with the dependency
        columns (List[str]): List of column names the component depends on
        row_count_dependency (bool): Whether the component depends on row count
        column_set_dependency (bool): Whether the component depends on the set of columns

    Implementation Notes:
        - Used to determine if a component should update based on data changes
        - Supports different types of dependencies (columns, row count, column set)
        - Works with the UpdateManager to optimize updates
    """

    def __init__(
        self,
        component: "IUpdatable",
        columns: Optional[List[str]] = None,
        row_count_dependency: bool = False,
        column_set_dependency: bool = False,
        any_change_dependency: bool = False,
    ):
        """
        Initialize a DataDependency object.

        Args:
            component: The UI component with the dependency
            columns: List of column names the component depends on
            row_count_dependency: Whether the component depends on row count
            column_set_dependency: Whether the component depends on the set of columns
            any_change_dependency: Whether the component depends on any data change
        """
        self.component = component
        self.columns = columns or []
        self.row_count_dependency = row_count_dependency
        self.column_set_dependency = column_set_dependency
        self.any_change_dependency = any_change_dependency

        logger.debug(
            f"Created DataDependency for {component.__class__.__name__}: "
            f"columns={self.columns}, row_count={self.row_count_dependency}, "
            f"column_set={self.column_set_dependency}, any_change={self.any_change_dependency}"
        )

    def should_update(self, changes: Dict[str, Any]) -> bool:
        """
        Check if the component should update based on data changes.

        Args:
            changes: Dictionary of changes from DataState.get_changes()

        Returns:
            True if the component should update, False otherwise
        """
        # Quick check for any dependency
        if self.any_change_dependency and changes["has_changes"]:
            logger.debug(
                f"{self.component.__class__.__name__} should update (any change dependency)"
            )
            return True

        # Check structure dependencies
        if self.row_count_dependency and changes["row_count_changed"]:
            logger.debug(f"{self.component.__class__.__name__} should update (row count changed)")
            return True

        if self.column_set_dependency and changes["columns_changed"]:
            logger.debug(f"{self.component.__class__.__name__} should update (column set changed)")
            return True

        # Check column-specific dependencies
        for column in self.columns:
            if column in changes["column_changes"] and changes["column_changes"][column]:
                logger.debug(
                    f"{self.component.__class__.__name__} should update (column {column} changed)"
                )
                return True

            # Check if a column the component depends on was added or removed
            if column in changes["new_columns"] or column in changes["removed_columns"]:
                logger.debug(
                    f"{self.component.__class__.__name__} should update (column {column} added/removed)"
                )
                return True

        logger.debug(f"{self.component.__class__.__name__} does not need to update")
        return False

    def __repr__(self) -> str:
        """
        Get string representation of the dependency.

        Returns:
            String representation
        """
        return (
            f"DataDependency({self.component.__class__.__name__}, "
            f"columns={self.columns}, row_count={self.row_count_dependency}, "
            f"column_set={self.column_set_dependency}, any_change={self.any_change_dependency})"
        )
