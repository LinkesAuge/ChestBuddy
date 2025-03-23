"""
validation_view_adapter.py

Description: Adapter to integrate the existing ValidationTab with the new BaseView structure
Usage:
    validation_view = ValidationViewAdapter(data_model, validation_service)
    main_window.add_view(validation_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.resources.icons import Icons


class ValidationViewAdapter(BaseView):
    """
    Adapter that wraps the existing ValidationTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        validation_service (ValidationService): The service for data validation
        validation_tab (ValidationTab): The wrapped ValidationTab instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing ValidationTab component
        - Provides the same functionality as ValidationTab but with the new UI styling
    """

    def __init__(
        self,
        data_model: ChestDataModel,
        validation_service: ValidationService,
        parent: QWidget = None,
    ):
        """
        Initialize the ValidationViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to validate
            validation_service (ValidationService): The validation service to use
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model
        self._validation_service = validation_service

        # Create the underlying ValidationTab
        self._validation_tab = ValidationTab(data_model, validation_service)

        # Initialize the base view
        super().__init__("Data Validation", parent, data_required=True)
        self.setObjectName("ValidationViewAdapter")

        # Set custom empty state properties
        self.set_empty_state_props(
            title="No Data to Validate",
            message="Import CSV files to validate your chest data.",
            action_text="Import Data",
            icon=Icons.get_icon(Icons.VALIDATE),
        )

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

        # Connect any signals from the ValidationTab if needed
        pass

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common validation operations
        self.add_header_action("validate", "Validate", "primary")
        self.add_header_action("clear", "Clear Validation")
        self.add_header_action("refresh", "Refresh")
