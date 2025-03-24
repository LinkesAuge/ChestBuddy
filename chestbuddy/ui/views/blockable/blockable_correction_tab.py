"""
blockable_correction_tab.py

Description: Blockable version of the CorrectionTab that integrates with the UI State Management System
Usage:
    Use this class instead of CorrectionTab to automatically integrate with UI blocking:

    ```python
    # Create a blockable correction tab
    tab = BlockableCorrectionTab(data_model, correction_service, parent=some_parent)

    # The tab will be automatically blocked/unblocked with the UI State Manager
    with OperationContext(ui_manager, UIOperations.CORRECTION, groups=[UIElementGroups.CORRECTION]):
        # Long running operation that should block the correction tab
        pass
    ```
"""

import logging
from typing import List, Dict, Any, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTreeWidgetItem

from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.utils.ui_state.elements import BlockableElementMixin
from chestbuddy.utils.ui_state.manager import UIStateManager
from chestbuddy.utils.ui_state.constants import UIElementGroups, UIOperations
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.correction_service import CorrectionService

logger = logging.getLogger(__name__)


class BlockableCorrectionTab(CorrectionTab, BlockableElementMixin):
    """
    A blockable version of CorrectionTab that integrates with the UI State Management System.

    This tab is automatically registered with the UIElementGroups.CORRECTION group
    and can be blocked during operations that affect correction.
    """

    def __init__(
        self,
        data_model: ChestDataModel,
        correction_service: CorrectionService,
        parent: Optional[QWidget] = None,
        element_id: Optional[str] = None,
    ):
        """
        Initialize the blockable correction tab.

        Args:
            data_model: The data model to correct
            correction_service: The service used for correction
            parent: The parent widget
            element_id: Optional unique ID for this UI element (generated if not provided)
        """
        # Initialize the CorrectionTab first
        CorrectionTab.__init__(self, data_model, correction_service, parent=parent)

        # Initialize BlockableElementMixin
        BlockableElementMixin.__init__(self)

        # Set element ID
        self._element_id = element_id or f"blockable_correction_tab_{id(self)}"

        # Add to CORRECTION group by default
        self._ui_element_groups = {UIElementGroups.CORRECTION}

        # Get UI state manager and register
        self._ui_state_manager = UIStateManager()
        self.register_with_manager(self._ui_state_manager)

        # Register this element with the specified groups
        for group in self._ui_element_groups:
            self._ui_state_manager.add_element_to_group(self, group)

        # Register child widgets
        self._register_child_widgets()

        logger.debug(f"Initialized {self.__class__.__name__}")

    def _register_child_widgets(self):
        """Register child widgets that should be individually blockable."""
        # Register correction history tree if available
        if hasattr(self, "_history_tree") and self._history_tree is not None:
            try:
                self._ui_state_manager.register_element(
                    self._history_tree, groups=[UIElementGroups.CORRECTION]
                )
                logger.debug(f"Registered _history_tree with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register _history_tree: {e}")

        # Register apply button if available
        if hasattr(self, "_apply_button") and self._apply_button is not None:
            try:
                self._ui_state_manager.register_element(
                    self._apply_button, groups=[UIElementGroups.CORRECTION]
                )
                logger.debug(f"Registered _apply_button with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register _apply_button: {e}")

    def _apply_block(self, operation: UIOperations) -> None:
        """
        Apply custom blocking behavior when the tab is blocked.

        Args:
            operation: The operation causing the block
        """
        logger.debug(f"Blocking {self.__class__.__name__} for operation {operation}")

        # Disable the tab
        self.setEnabled(False)

        # Apply styling
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.05);")

        # Also disable child widgets directly
        if hasattr(self, "_apply_button") and self._apply_button is not None:
            self._apply_button.setEnabled(False)

        if hasattr(self, "_history_tree") and self._history_tree is not None:
            self._history_tree.setEnabled(False)

        if hasattr(self, "_strategy_combo") and self._strategy_combo is not None:
            self._strategy_combo.setEnabled(False)

    def _apply_unblock(self, operation: UIOperations) -> None:
        """
        Apply custom unblocking behavior when the tab is unblocked.

        Args:
            operation: The operation that was causing the block
        """
        logger.debug(f"Unblocking {self.__class__.__name__} for operation {operation}")

        # Enable the tab
        self.setEnabled(True)

        # Remove styling
        self.setStyleSheet("")

        # Also enable child widgets directly
        if hasattr(self, "_apply_button") and self._apply_button is not None:
            self._apply_button.setEnabled(True)

        if hasattr(self, "_history_tree") and self._history_tree is not None:
            self._history_tree.setEnabled(True)

        if hasattr(self, "_strategy_combo") and self._strategy_combo is not None:
            self._strategy_combo.setEnabled(True)

    def _apply_correction(self) -> None:
        """
        Override the _apply_correction method to check if the tab is blocked before applying.
        """
        # Check if the tab is blocked, but only if _ui_state_manager is properly initialized
        if hasattr(self, "_ui_state_manager") and self._ui_state_manager is not None:
            if self._ui_state_manager.is_element_blocked(self):
                logger.debug(f"Skipping correction for blocked {self.__class__.__name__}")
                return

        # If not blocked, proceed with normal correction
        super()._apply_correction()

    def _update_view(self) -> None:
        """
        Override the _update_view method to check if the tab is blocked before updating.
        """
        # Check if the tab is blocked, but only if _ui_state_manager is properly initialized
        if hasattr(self, "_ui_state_manager") and self._ui_state_manager is not None:
            if self._ui_state_manager.is_element_blocked(self):
                logger.debug(f"Skipping update for blocked {self.__class__.__name__}")
                return

        # If not blocked, proceed with normal update
        super()._update_view()

    def closeEvent(self, event):
        """
        Handle the close event to ensure the tab is unregistered.

        Args:
            event: The close event
        """
        # Unregister from the UI state manager
        self.unregister_from_manager()

        # Let the parent class handle the event
        super().closeEvent(event)
