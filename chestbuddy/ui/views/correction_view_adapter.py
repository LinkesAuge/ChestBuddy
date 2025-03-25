"""
correction_view_adapter.py

Description: Adapter to integrate the existing CorrectionTab with the new BaseView structure
Usage:
    correction_view = CorrectionViewAdapter(data_model, correction_service)
    main_window.add_view(correction_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.ui.views.base_view import BaseView


class CorrectionViewAdapter(BaseView):
    """
    Adapter that wraps the existing CorrectionTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        correction_service (CorrectionService): The service for data correction
        correction_tab (CorrectionTab): The wrapped CorrectionTab instance
        _controller (DataViewController): The controller for correction operations

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing CorrectionTab component
        - Provides the same functionality as CorrectionTab but with the new UI styling
        - Uses DataViewController for correction operations
    """

    # Define signals
    correction_requested = Signal(str)  # Strategy name
    history_requested = Signal()

    def __init__(
        self,
        data_model: ChestDataModel,
        correction_service: CorrectionService,
        parent: QWidget = None,
    ):
        """
        Initialize the CorrectionViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to correct
            correction_service (CorrectionService): The correction service to use
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model
        self._correction_service = correction_service
        self._controller = None

        # Create the underlying CorrectionTab
        self._correction_tab = CorrectionTab(data_model, correction_service)

        # Initialize the base view
        super().__init__("Data Correction", parent)
        self.setObjectName("CorrectionViewAdapter")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this adapter.

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

            print("CorrectionViewAdapter: Controller set and signals connected")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the CorrectionTab to the content widget
        self.get_content_layout().addWidget(self._correction_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect header action buttons
        self.header_action_clicked.connect(self._on_action_clicked)

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common correction operations
        self.add_header_action("apply", "Apply Correction")
        self.add_header_action("history", "View History")
        self.add_header_action("refresh", "Refresh")

    def refresh(self) -> None:
        """Refresh the correction view."""
        if hasattr(self._correction_tab, "_update_view"):
            self._correction_tab._update_view()

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
        """Handle apply correction button click."""
        if self._controller:
            # Since we need parameters from the CorrectionTab, we have to call its method
            # This is less than ideal, but necessary given the current structure
            self._correction_tab._apply_correction()
            # The tab's method already calls the correction_service which the controller listens to
        else:
            # Fallback to direct apply if controller not set
            if hasattr(self._correction_tab, "_apply_correction"):
                self._correction_tab._apply_correction()

    def _on_history_clicked(self) -> None:
        """Handle view history button click."""
        # Get correction history from the controller if available
        if self._controller:
            history = self._controller.get_correction_history()

            # If the correction tab has a method to update its history view, use it
            if hasattr(self._correction_tab, "_update_history"):
                self._correction_tab._update_history()
        else:
            # Fallback to direct history update if controller not set
            if hasattr(self._correction_tab, "_update_history"):
                self._correction_tab._update_history()

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

        # Refresh the correction tab to show the latest results
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
