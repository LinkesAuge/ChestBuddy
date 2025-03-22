"""
data_view_adapter.py

Description: Adapter to integrate the existing DataView with the new BaseView structure
Usage:
    data_view = DataViewAdapter(data_model)
    main_window.add_view(data_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.views.base_view import BaseView


class DataViewAdapter(BaseView):
    """
    Adapter that wraps the existing DataView component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        data_view (DataView): The wrapped DataView instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing DataView component
        - Provides the same functionality as DataView but with the new UI styling
    """

    def __init__(self, data_model: ChestDataModel, parent: QWidget = None):
        """
        Initialize the DataViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to display
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model

        # Create the underlying DataView
        self._data_view = DataView(data_model)

        # Initialize the base view
        super().__init__("Data View", parent)
        self.setObjectName("DataViewAdapter")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the DataView to the content widget
        self.get_content_layout().addWidget(self._data_view)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect any signals from the DataView if needed
        pass

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common data operations
        self.add_header_action("filter", "Filter")
        self.add_header_action("clear", "Clear Filters")
        self.add_header_action("refresh", "Refresh")
