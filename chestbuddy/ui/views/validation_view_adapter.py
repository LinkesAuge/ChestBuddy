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
from chestbuddy.ui.views.validation_tab_view import ValidationTabView
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class ValidationViewAdapter(UpdatableView):
    """
    Adapter that wraps the ValidationTabView component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        validation_service (ValidationService): The service for data validation
        validation_tab (ValidationTabView): The wrapped ValidationTabView instance
        _controller (DataViewController): The controller for validation operations
        _is_updating (bool): Flag to prevent recursive updates

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Wraps the ValidationTabView component
        - Provides improved UI with three-column layout, search functionality, and visual indicators
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
        self._is_updating = False  # Flag to prevent recursive updates

        # Create the underlying ValidationTabView
        self._validation_tab = ValidationTabView(validation_service)

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

        # Add the ValidationTabView to the content widget
        self.get_content_layout().addWidget(self._validation_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect header action buttons
        self.header_action_clicked.connect(self._on_action_clicked)

        # Connect validation tab signals
        self._validation_tab.validation_updated.connect(self._on_validation_updated)

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

    @Slot()
    def _on_validation_updated(self):
        """
        Handle validation updated event from the ValidationTabView.

        This method is called when the ValidationTabView signals that validation
        has been updated. To prevent infinite recursion from immediate updates,
        this method schedules a debounced update through the UpdateManager.
        """
        logger.debug("ValidationViewAdapter: Validation updated")

        # Prevent recursive updates
        if self._is_updating:
            logger.debug("ValidationViewAdapter: Update already in progress, skipping")
            return

        # Don't call refresh directly as it causes recursion with the validation tab view
        # Instead, use a debounced update request to avoid infinite recursive calls
        self.schedule_update(
            debounce_ms=100
        )  # Use schedule_update with debounce to prevent recursion

    def _update_view_content(self, data=None) -> None:
        """
        Update the view content with current data.

        This implementation updates the ValidationTabView with current validation results.

        Args:
            data: Optional data to use for update (unused in this implementation)
        """
        # Set updating flag to prevent recursive updates
        self._is_updating = True

        try:
            # Use the ValidationTabView's own refresh method if available
            if hasattr(self._validation_tab, "refresh"):
                self._validation_tab.refresh()
            elif hasattr(self._validation_tab, "_on_reset"):
                self._validation_tab._on_reset()

            logger.debug("ValidationViewAdapter: View content updated")
        finally:
            # Always reset the flag, even if an exception occurs
            self._is_updating = False

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.
        """
        # Set updating flag to prevent recursive updates
        self._is_updating = True

        try:
            if hasattr(self._validation_tab, "refresh"):
                self._validation_tab.refresh()
            elif hasattr(self._validation_tab, "_on_reset"):
                self._validation_tab._on_reset()

            logger.debug("ValidationViewAdapter: View content refreshed")
        finally:
            # Always reset the flag, even if an exception occurs
            self._is_updating = False

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
        elif hasattr(self._validation_tab, "_on_validate_now"):
            self._validation_tab._on_validate_now()

        logger.debug("ValidationViewAdapter: View content populated")

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.
        """
        # Set updating flag to prevent recursive updates
        self._is_updating = True

        try:
            if hasattr(self._validation_tab, "clear_validation"):
                self._validation_tab.clear_validation()
            elif hasattr(self._validation_tab, "_on_reset"):
                self._validation_tab._on_reset()

            logger.debug("ValidationViewAdapter: View content reset")
        finally:
            # Always reset the flag, even if an exception occurs
            self._is_updating = False

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
