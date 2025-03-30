"""
correction_view.py

Description: Main correction view for the ChestBuddy application
Usage:
    correction_view = CorrectionView(data_model, correction_service)
    main_window.add_view(correction_view)
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.views.correction_rule_view import CorrectionRuleView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionView(UpdatableView):
    """
    Main correction view for the ChestBuddy application.

    This view provides an interface for users to manage correction rules
    and apply them to the data.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        correction_service (CorrectionService): The service for data correction
        _rule_view (CorrectionRuleView): The view for managing correction rules
        _controller (DataViewController): The controller for data view operations
        _correction_controller (CorrectionController): The controller for correction operations

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Uses CorrectionRuleView for managing correction rules
        - Provides correction functionality through the correction controller
        - Uses DataViewController for data view operations
    """

    # Define signals (same as the adapter for compatibility)
    correction_requested = Signal(str)  # Strategy name
    history_requested = Signal()

    def __init__(
        self,
        data_model: ChestDataModel,
        correction_service: CorrectionService,
        parent: Optional[QWidget] = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the CorrectionView.

        Args:
            data_model (ChestDataModel): The data model for correction
            correction_service (CorrectionService): The correction service
            parent (Optional[QWidget]): Parent widget
            debug_mode (bool): Enable debug mode for signal connections
        """
        # Store references
        self._data_model = data_model
        self._correction_service = correction_service
        self._controller = None
        self._correction_controller = None
        self._rule_view = None  # Initialize to None, will create when correction_controller is set
        self._rule_view_placeholder = None  # Placeholder widget until rule view is created

        # Initialize the base view
        super().__init__("Data Correction", parent, debug_mode=debug_mode)
        self.setObjectName("CorrectionView")

        # Initialize components after the base view is set up
        self._initialize_components()

    def _initialize_components(self):
        """Initialize view-specific components after the base UI is set up."""
        # Create a placeholder widget instead of the actual CorrectionRuleView
        # We'll replace this with the real CorrectionRuleView when the correction_controller is set
        self._rule_view_placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self._rule_view_placeholder)
        placeholder_layout.addWidget(QLabel("Initializing correction rules view..."))

        # Add the placeholder to the content layout
        self.get_content_layout().addWidget(self._rule_view_placeholder)

        logger.debug("CorrectionView placeholder initialized")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this view.

        Args:
            controller: The DataViewController instance to use
        """
        self._controller = controller

        # Connect controller signals
        if self._controller:
            self._controller.correction_started.connect(self._on_correction_started)
            self._controller.correction_completed.connect(self._on_correction_completed)
            self._controller.correction_error.connect(self._on_correction_error)
            self._controller.operation_error.connect(self._on_operation_error)

            logger.info("CorrectionView: Controller set and signals connected")

    def set_correction_controller(self, controller: CorrectionController) -> None:
        """
        Set the correction controller for this view.

        Args:
            controller: The CorrectionController instance to use
        """
        self._correction_controller = controller

        # Set the view in the controller
        if self._correction_controller:
            self._correction_controller.set_view(self)

            # Now that we have the correction controller, create the real CorrectionRuleView
            # Replace the placeholder with the actual rule view
            if self._rule_view_placeholder:
                # Remove the placeholder from layout
                self.get_content_layout().removeWidget(self._rule_view_placeholder)
                self._rule_view_placeholder.hide()  # Hide to prevent visual glitches
                self._rule_view_placeholder.deleteLater()  # Schedule for deletion
                self._rule_view_placeholder = None

            # Create the actual CorrectionRuleView with the controller
            self._rule_view = CorrectionRuleView(
                correction_controller=self._correction_controller,
                parent=self,  # Explicitly set parent to self (CorrectionView)
                debug_mode=self._debug_mode,
            )

            # Add the rule view to layout
            self.get_content_layout().addWidget(self._rule_view)

            # Connect the rule view to the correction controller
            if self._rule_view:
                self._rule_view.apply_corrections_requested.connect(
                    self._correction_controller.apply_corrections
                )
                self._rule_view.rule_added.connect(self._correction_controller.add_rule)
                self._rule_view.rule_edited.connect(self._correction_controller.update_rule)
                self._rule_view.rule_deleted.connect(self._correction_controller.delete_rule)

            # Connect correction controller signals to this view
            self._correction_controller.correction_completed.connect(self._on_corrections_completed)
            self._correction_controller.correction_error.connect(self._on_correction_error)

            logger.info("CorrectionView: Correction controller set and rule view created")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Don't add the rule view here - it will be added in _initialize_components
        # and/or set_correction_controller when the controller is available

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
                logger.debug("Connected data_model.data_changed to CorrectionView.request_update")
            except Exception as e:
                logger.error(f"Error connecting data model signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common correction operations
        self.add_header_action("apply", "Apply Corrections")
        self.add_header_action("history", "View History")
        self.add_header_action("refresh", "Refresh")

    def _update_view_content(self) -> None:
        """Update the view content based on data from the controllers."""
        self._show_status_message("Updating correction rules...")
        if self._correction_controller:
            self._show_placeholder(False)
            if not self._rule_view:
                self._initialize_rule_view()
            self._refresh_view_content()
        else:
            self._show_placeholder(True)
        self._show_status_message("Correction rules updated")

    def _show_status_message(self, message: str) -> None:
        """
        Display a status message for the view.

        Args:
            message (str): The message to display
        """
        if hasattr(self, "statusBar") and callable(self.statusBar):
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(message, 3000)  # Show for 3 seconds
        # Log the message as a fallback
        logger.debug(f"CorrectionView status: {message}")

    def _refresh_view_content(self) -> None:
        """Refresh the view content without changing the underlying data."""
        # Refresh the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "refresh")
            and callable(getattr(self._rule_view, "refresh", None))
        ):
            self._rule_view.refresh()

        logger.debug("CorrectionView: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        # Initial population of the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "populate")
            and callable(getattr(self._rule_view, "populate", None))
        ):
            self._rule_view.populate()

        logger.debug("CorrectionView: View content populated")

    def _reset_view_content(self) -> None:
        """Reset the view content to its initial state."""
        # Reset the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "reset")
            and callable(getattr(self._rule_view, "reset", None))
        ):
            self._rule_view.reset()

        logger.debug("CorrectionView: View content reset")

    @Slot(str)
    def _on_action_clicked(self, action_id: str) -> None:
        """
        Handle action button clicks.

        Args:
            action_id: The ID of the clicked action
        """
        if action_id == "apply":
            self._on_apply_clicked()
        elif action_id == "history":
            self._on_history_clicked()
        elif action_id == "refresh":
            self.refresh()

    def _on_apply_clicked(self) -> None:
        """Handle apply corrections button click."""
        # Emit signal for tracking
        self.correction_requested.emit("rules")

        # Apply corrections using the correction controller
        if self._correction_controller:
            self._correction_controller.apply_corrections(recursive=False, selected_only=False)
        else:
            logger.error("Cannot apply corrections: Correction controller not available")

    def _on_history_clicked(self) -> None:
        """Handle view history button click."""
        # Emit signal for tracking
        self.history_requested.emit()

        # Show correction history using the correction controller
        if self._correction_controller:
            history = self._correction_controller.get_history()
            # TODO: Display history in a dialog or update the view to show history
        else:
            logger.error("Cannot view history: Correction controller not available")

    @Slot(str)
    def _on_correction_started(self, strategy_name: str) -> None:
        """
        Handle correction started event.

        Args:
            strategy_name: The strategy being applied
        """
        # Update UI to show correction in progress
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Applying {strategy_name} correction...")

    @Slot(str, int)
    def _on_correction_completed(self, strategy_name: str, affected_rows: int) -> None:
        """
        Handle correction completed event.

        Args:
            strategy_name: The strategy that was applied
            affected_rows: Number of rows affected by the correction
        """
        # Update UI to show correction results
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Correction complete: {affected_rows} rows affected")

        # Refresh the view to show the latest results
        self.refresh()

    @Slot(object)
    def _on_corrections_completed(self, stats):
        """
        Handle completion of corrections from the correction controller.

        Args:
            stats: Statistics about applied corrections
        """
        # Convert stats to a dict if it's not already
        affected_rows = stats.get("affected_rows", 0) if isinstance(stats, dict) else 0

        if affected_rows > 0:
            self._show_status_message(f"Corrections completed: {affected_rows} rows affected")
        else:
            self._show_status_message("Corrections completed: No changes were needed")

        # Refresh data view if needed
        if hasattr(self._controller, "refresh_data_view"):
            self._controller.refresh_data_view()

        # Also update this view
        self.refresh()

    @Slot(str)
    def _on_correction_error(self, error_msg: str) -> None:
        """
        Handle correction error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Correction error: {error_msg}")

    @Slot(str)
    def _on_operation_error(self, error_msg: str) -> None:
        """
        Handle operation error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Error: {error_msg}")
