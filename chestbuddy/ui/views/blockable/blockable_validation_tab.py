"""
blockable_validation_tab.py

Description: Blockable version of the ValidationTab that integrates with the UI State Management System
Usage:
    Use this class instead of ValidationTab to automatically integrate with UI blocking:

    ```python
    # Create a blockable validation tab
    tab = BlockableValidationTab(data_model, validation_service, parent=some_parent)

    # The tab will be automatically blocked/unblocked with the UI State Manager
    with OperationContext(ui_manager, UIOperations.VALIDATION, groups=[UIElementGroups.VALIDATION]):
        # Long running operation that should block the validation tab
        pass
    ```
"""

import logging
from typing import List, Dict, Any, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTreeWidgetItem

from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.utils.ui_state.elements import BlockableElementMixin
from chestbuddy.utils.ui_state.manager import UIStateManager
from chestbuddy.utils.ui_state.constants import UIElementGroups, UIOperations
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class BlockableValidationTab(ValidationTab, BlockableElementMixin):
    """
    A blockable version of ValidationTab that integrates with the UI State Management System.

    This tab is automatically registered with the UIElementGroups.VALIDATION group
    and can be blocked during operations that affect validation.
    """

    def __init__(
        self,
        data_model: ChestDataModel,
        validation_service: ValidationService,
        parent: Optional[QWidget] = None,
        element_id: Optional[str] = None,
    ):
        """
        Initialize the blockable validation tab.

        Args:
            data_model: The data model to validate
            validation_service: The service used for validation
            parent: The parent widget
            element_id: Optional unique ID for this UI element (generated if not provided)
        """
        # Initialize the ValidationTab first
        ValidationTab.__init__(self, data_model, validation_service, parent=parent)

        # Initialize BlockableElementMixin
        BlockableElementMixin.__init__(self)

        # Set element ID
        self._element_id = element_id or f"blockable_validation_tab_{id(self)}"

        # Add to VALIDATION group by default
        self._ui_element_groups = {UIElementGroups.VALIDATION}

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
        # Register validation results tree if available
        if hasattr(self, "_results_tree") and self._results_tree is not None:
            try:
                self._ui_state_manager.register_element(
                    self._results_tree, groups=[UIElementGroups.VALIDATION]
                )
                logger.debug(f"Registered _results_tree with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register _results_tree: {e}")

        # Register validate button if available
        if hasattr(self, "_validate_button") and self._validate_button is not None:
            try:
                self._ui_state_manager.register_element(
                    self._validate_button, groups=[UIElementGroups.VALIDATION]
                )
                logger.debug(f"Registered _validate_button with UI state manager")
            except Exception as e:
                logger.warning(f"Failed to register _validate_button: {e}")

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
        if hasattr(self, "_validate_button") and self._validate_button is not None:
            self._validate_button.setEnabled(False)

        if hasattr(self, "_results_tree") and self._results_tree is not None:
            self._results_tree.setEnabled(False)

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
        if hasattr(self, "_validate_button") and self._validate_button is not None:
            self._validate_button.setEnabled(True)

        if hasattr(self, "_results_tree") and self._results_tree is not None:
            self._results_tree.setEnabled(True)

    def _validate_data(self) -> None:
        """
        Override the _validate_data method to check if the tab is blocked before validating.
        """
        # Check if the tab is blocked
        if self._ui_state_manager.is_element_blocked(self):
            logger.debug(f"Skipping validation for blocked {self.__class__.__name__}")
            return

        # If not blocked, proceed with normal validation
        super()._validate_data()

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
