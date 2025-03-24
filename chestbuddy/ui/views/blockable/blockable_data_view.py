"""
blockable_data_view.py

Description: Blockable version of the DataView that integrates with the UI State Management System
Usage:
    Use this class instead of DataView to automatically integrate with UI blocking:

    ```python
    # Create a blockable data view
    view = BlockableDataView(parent=some_parent)

    # The view will be automatically blocked/unblocked with the UI State Manager
    with OperationContext(ui_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]):
        # Long running operation that should block the data view
        pass
    ```
"""

import logging
from typing import List, Dict, Any, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from chestbuddy.ui.views.data_view import DataView
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    UIStateManager,
    UIElementGroups,
    UIOperations,
)

logger = logging.getLogger(__name__)


class BlockableDataView(DataView, BlockableElementMixin):
    """
    A blockable version of DataView that integrates with the UI State Management System.

    This view is automatically registered with the UIElementGroups.DATA_VIEW group
    and can be blocked during operations that affect data views.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        element_id: Optional[str] = None,
    ):
        """
        Initialize the blockable data view.

        Args:
            parent: The parent widget
            element_id: Optional unique ID for this UI element (generated if not provided)
        """
        # Initialize the DataView first
        DataView.__init__(self, parent=parent)

        # Initialize BlockableElementMixin
        BlockableElementMixin.__init__(
            self, element_id=element_id or f"blockable_data_view_{id(self)}"
        )

        # Add to DATA_VIEW group by default
        self._ui_element_groups = {UIElementGroups.DATA_VIEW}

        # Get UI state manager and register
        self._ui_state_manager = UIStateManager()
        self.register_with_manager(self._ui_state_manager, groups=list(self._ui_element_groups))

        # Register child widgets
        self._register_child_widgets()

        logger.debug(f"Initialized {self.__class__.__name__}")

    def _register_child_widgets(self):
        """Register child widgets that should be individually blockable."""
        # Register table view if available
        if hasattr(self, "table_view") and self.table_view is not None:
            try:
                self._ui_state_manager.register_element(
                    self.table_view, groups=[UIElementGroups.DATA_VIEW]
                )
                logger.debug(f"Registered table_view with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register table_view: {e}")

        # Register filter bar if available
        if hasattr(self, "filter_bar") and self.filter_bar is not None:
            try:
                self._ui_state_manager.register_element(
                    self.filter_bar, groups=[UIElementGroups.DATA_VIEW]
                )
                logger.debug(f"Registered filter_bar with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register filter_bar: {e}")

    def _apply_block(self, operation: UIOperations) -> None:
        """
        Apply custom blocking behavior when the view is blocked.

        Args:
            operation: The operation causing the block
        """
        logger.debug(f"Blocking {self.__class__.__name__} for operation {operation}")

        # Disable the view
        self.setEnabled(False)

        # Apply styling
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.05);")

        # Also disable child widgets directly
        if hasattr(self, "table_view") and self.table_view is not None:
            self.table_view.setEnabled(False)

        if hasattr(self, "filter_bar") and self.filter_bar is not None:
            self.filter_bar.setEnabled(False)

    def _apply_unblock(self, operation: UIOperations) -> None:
        """
        Apply custom unblocking behavior when the view is unblocked.

        Args:
            operation: The operation that was causing the block
        """
        logger.debug(f"Unblocking {self.__class__.__name__} for operation {operation}")

        # Enable the view
        self.setEnabled(True)

        # Remove styling
        self.setStyleSheet("")

        # Also enable child widgets directly
        if hasattr(self, "table_view") and self.table_view is not None:
            self.table_view.setEnabled(True)

        if hasattr(self, "filter_bar") and self.filter_bar is not None:
            self.filter_bar.setEnabled(True)

    def _update_view(self):
        """
        Override the _update_view method to check if the view is blocked before updating.

        If the view is blocked by an operation, updating the view will be skipped.
        """
        # Check if the view is blocked
        if self._ui_state_manager.is_element_blocked(self):
            logger.debug(f"Skipping update for blocked {self.__class__.__name__}")
            return

        # If not blocked, proceed with normal update
        super()._update_view()

    def closeEvent(self, event):
        """
        Handle the close event to ensure the view is unregistered.

        Args:
            event: The close event
        """
        # Unregister from the UI state manager
        self.unregister_from_manager()

        # Let the parent class handle the event
        super().closeEvent(event)
