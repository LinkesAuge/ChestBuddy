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
from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.ui.views.base_view import BaseView


class CorrectionViewAdapter(BaseView):
    """
    Adapter that wraps the existing CorrectionTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        correction_service (CorrectionService): The service for data correction
        correction_tab (CorrectionTab): The wrapped CorrectionTab instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing CorrectionTab component
        - Provides the same functionality as CorrectionTab but with the new UI styling
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

        # Create the underlying CorrectionTab
        self._correction_tab = CorrectionTab(data_model, correction_service)

        # Initialize the base view
        super().__init__("Data Correction", parent)
        self.setObjectName("CorrectionViewAdapter")

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

        # Connect any signals from the CorrectionTab if needed
        pass

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common correction operations
        self.add_header_action("apply", "Apply Correction")
        self.add_header_action("history", "View History")
        self.add_header_action("refresh", "Refresh")
