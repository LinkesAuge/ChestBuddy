"""
blockable_base_view.py

Description: Blockable version of the BaseView class that integrates with the UI State Management System
Usage:
    Inherit from this class to create blockable content views:

    ```python
    class MyView(BlockableBaseView):
        def __init__(self, title, parent=None):
            super().__init__(title, parent)
            # Register with specific groups
            self.register_with_groups([UIElementGroups.DATA_VIEW])
    ```
"""

import logging
from typing import List, Optional, Set, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    UIStateManager,
    UIElementGroups,
    UIOperations,
)

logger = logging.getLogger(__name__)


class BlockableBaseView(BaseView, BlockableElementMixin):
    """
    Base class for all blockable content views in the application.

    This class extends BaseView with the BlockableElementMixin to provide
    automatic integration with the UI State Management System.

    Attributes:
        data_required (bool): Whether this view requires data to be loaded to function
    """

    def __init__(self, title, parent=None, data_required=False):
        """
        Initialize the blockable base view.

        Args:
            title (str): The view title
            parent (QWidget, optional): The parent widget
            data_required (bool): Whether this view requires data to be loaded
        """
        BaseView.__init__(self, title, parent, data_required)
        BlockableElementMixin.__init__(self)

        # Initialize UI state manager
        self._ui_state_manager = UIStateManager()

        # Register with manager
        self.register_with_manager(self._ui_state_manager)

        # Apply custom blocking behavior
        self._register_child_widgets()

    def _register_child_widgets(self):
        """
        Register child widgets that should be individually blockable.

        Override this in subclasses to register specific child widgets.
        """
        # By default, we don't register any specific child widgets
        pass

    def register_with_groups(self, groups: List[UIElementGroups]):
        """
        Register this view with specific UI element groups.

        Args:
            groups: List of UIElementGroups to register with
        """
        if not self._is_registered or not self._ui_state_manager:
            logger.warning(f"View {self} not registered with UI state manager")
            return

        for group in groups:
            self._ui_state_manager.add_element_to_group(self, group)
            logger.debug(f"Added {self} to group {group}")

    def _apply_block(self):
        """
        Apply blocking behavior to this view.

        This implementation blocks the entire view, all action buttons,
        and the content widget.
        """
        # Disable the entire view
        self.setEnabled(False)

        # Update UI to indicate blocked state
        self.setStyleSheet("""
            QWidget {
                opacity: 0.7;
            }
        """)

        logger.debug(f"Blocked view: {self.objectName() or self.__class__.__name__}")

    def _apply_unblock(self):
        """
        Apply unblocking behavior to this view.

        This implementation restores the view to its original state.
        """
        # Re-enable the view
        self.setEnabled(True)

        # Restore normal UI state
        self.setStyleSheet("")

        logger.debug(f"Unblocked view: {self.objectName() or self.__class__.__name__}")

    def closeEvent(self, event):
        """
        Handle the close event.

        This ensures that the view is unregistered from the UI state manager
        when it is closed.

        Args:
            event: The close event
        """
        # Unregister from the UI state manager
        self.unregister_from_manager()

        # Let the parent class handle the event
        super().closeEvent(event)
