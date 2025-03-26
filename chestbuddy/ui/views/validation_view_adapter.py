"""
validation_view_adapter.py

Description: Adapter to integrate the existing ValidationTab with the new BaseView structure
Usage:
    validation_view = ValidationViewAdapter(data_model, validation_service)
    main_window.add_view(validation_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout
import logging

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class ValidationViewAdapter(UpdatableView):
    """
    Adapter that wraps the existing ValidationTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        validation_service (ValidationService): The service for data validation
        validation_tab (ValidationTab): The wrapped ValidationTab instance
        _controller (DataViewController): The controller for validation operations

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Wraps the existing ValidationTab component
        - Provides the same functionality as ValidationTab but with the new UI styling
        - Uses DataViewController for validation operations
        - Uses UpdateManager for scheduling updates
    """

    # Define signals
    validation_requested = Signal()
    validation_cleared = Signal()

    def __init__(
        self,
        data_model: ChestDataModel,
        validation_service: ValidationService,
        parent: QWidget = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the ValidationViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to validate
            validation_service (ValidationService): The validation service to use
            parent (QWidget, optional): The parent widget. Defaults to None.
            debug_mode (bool, optional): Enable debug mode for signal connections. Defaults to False.
        """
        # Store references
        self._data_model = data_model
        self._validation_service = validation_service
        self._controller = None

        # Create the underlying ValidationTab
        self._validation_tab = ValidationTab(data_model, validation_service)

        # Initialize the base view
        super().__init__("Data Validation", parent, debug_mode=debug_mode)
        self.setObjectName("ValidationViewAdapter")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this adapter.

        Args:
            controller: The DataViewController instance to use
        """
        self._controller = controller

        # Connect controller signals
        if self._controller:
            self._controller.validation_started.connect(self._on_validation_started)
            self._controller.validation_completed.connect(self._on_validation_completed)
            self._controller.validation_error.connect(self._on_validation_error)
            self._controller.operation_error.connect(self._on_operation_error)

            logger.info("ValidationViewAdapter: Controller set and signals connected")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the ValidationTab to the content widget
        self.get_content_layout().addWidget(self._validation_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect header action buttons
        self.header_action_clicked.connect(self._on_action_clicked)

        # Connect to data model if available
        if hasattr(self._data_model, "data_changed") and hasattr(self, "request_update"):
            try:
                self._signal_manager.connect(
                    self._data_model, "data_changed", self, "request_update"
                )
                logger.debug(
                    "Connected data_model.data_changed to ValidationViewAdapter.request_update"
                )
            except Exception as e:
                logger.error(f"Error connecting data model signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common validation operations
        self.add_header_action("validate", "Validate")
        self.add_header_action("clear", "Clear Validation")
        self.add_header_action("refresh", "Refresh")

    def _update_view_content(self, data=None) -> None:
        """
        Update the view content with current data.

        This implementation updates the ValidationTab with current validation results.

        Args:
            data: Optional data to use for update (unused in this implementation)
        """
        # Use the ValidationTab's own refresh method if available
        if hasattr(self._validation_tab, "refresh"):
            self._validation_tab.refresh()

        logger.debug("ValidationViewAdapter: View content updated")

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.
        """
        if hasattr(self._validation_tab, "refresh"):
            self._validation_tab.refresh()

        logger.debug("ValidationViewAdapter: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        This implementation calls the validate method to fully populate validation results.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        # If controller exists, use it to validate data
        if self._controller:
            self._controller.validate_data()
        # Fallback to direct validation if controller not set
        elif hasattr(self._validation_tab, "validate"):
            self._validation_tab.validate()

        logger.debug("ValidationViewAdapter: View content populated")

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.
        """
        if hasattr(self._validation_tab, "clear_validation"):
            self._validation_tab.clear_validation()

        logger.debug("ValidationViewAdapter: View content reset")

    @Slot(str)
    def _on_action_clicked(self, action_id: str) -> None:
        """
        Handle action button clicks.

        Args:
            action_id: The ID of the clicked action
        """
        if action_id == "validate":
            self._on_validate_clicked()
        elif action_id == "clear":
            self._on_clear_clicked()
        elif action_id == "refresh":
            self.refresh()

    def _on_validate_clicked(self) -> None:
        """Handle validate button click using controller."""
        # Schedule update through UI update system
        self.populate()
        self.validation_requested.emit()

    def _on_clear_clicked(self) -> None:
        """Handle clear validation button click."""
        # Reset the component
        self.reset()
        self.validation_cleared.emit()

    @Slot()
    def _on_validation_started(self) -> None:
        """Handle validation started event."""
        # Update UI to show validation in progress
        if hasattr(self, "_set_header_status"):
            self._set_header_status("Validating data...")

    @Slot(object)
    def _on_validation_completed(self, results) -> None:
        """
        Handle validation completed event.

        Args:
            results: The validation results
        """
        # Update UI to show validation results
        if hasattr(self, "_set_header_status"):
            issue_count = len(results) if results else 0
            self._set_header_status(f"Validation complete: {issue_count} issues found")

        # Refresh the validation tab to show the latest results
        self.refresh()

    @Slot(str)
    def _on_validation_error(self, error_msg: str) -> None:
        """
        Handle validation error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Validation error: {error_msg}")

    @Slot(str)
    def _on_operation_error(self, error_msg: str) -> None:
        """
        Handle operation error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Error: {error_msg}")

    def enable_auto_update(self) -> None:
        """Enable automatic updates when data model changes."""
        if hasattr(self._data_model, "data_changed") and hasattr(self, "request_update"):
            self._signal_manager.connect(self._data_model, "data_changed", self, "request_update")
            logger.debug("Auto-update enabled for ValidationViewAdapter")

    def disable_auto_update(self) -> None:
        """Disable automatic updates when data model changes."""
        if hasattr(self._data_model, "data_changed") and hasattr(self, "request_update"):
            self._signal_manager.disconnect(
                self._data_model, "data_changed", self, "request_update"
            )
            logger.debug("Auto-update disabled for ValidationViewAdapter")
