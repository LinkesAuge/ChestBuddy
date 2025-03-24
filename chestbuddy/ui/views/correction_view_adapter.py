"""
correction_view_adapter.py

Description: Adapter to integrate the BlockableCorrectionTab with the new BaseView structure
Usage:
    correction_view = CorrectionViewAdapter(data_model, correction_service)
    main_window.add_view(correction_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService
from chestbuddy.ui.views.blockable import BlockableCorrectionTab
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.resources.icons import Icons


class CorrectionViewAdapter(BaseView):
    """
    Adapter that wraps the BlockableCorrectionTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        correction_service (CorrectionService): The service for data correction
        correction_tab (BlockableCorrectionTab): The wrapped BlockableCorrectionTab instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the BlockableCorrectionTab component
        - Provides the same functionality as CorrectionTab but with the new UI styling
        - Uses BlockableCorrectionTab for automatic integration with UI State Management
    """

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

        # Create the underlying BlockableCorrectionTab
        self._correction_tab = BlockableCorrectionTab(
            data_model,
            correction_service,
            parent=None,  # Will be reparented when added to layout
            element_id=f"correction_tab_adapter_{id(self)}",
        )

        # Initialize the base view
        super().__init__("Data Correction", parent, data_required=True)
        self.setObjectName("CorrectionViewAdapter")

        # Set custom empty state properties
        self.set_empty_state_props(
            title="No Data to Correct",
            message="Import CSV files to correct your chest data.",
            action_text="Import Data",
            icon=Icons.get_icon(Icons.CORRECT),
        )

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the BlockableCorrectionTab to the content widget
        self.get_content_layout().addWidget(self._correction_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect any signals from the CorrectionTab if needed
        pass

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common correction operations
        self.add_header_action("apply", "Apply Corrections", "primary")
        self.add_header_action("clear", "Clear Corrections")
        self.add_header_action("refresh", "Refresh")
