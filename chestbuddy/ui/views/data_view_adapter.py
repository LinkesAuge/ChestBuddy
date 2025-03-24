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
from chestbuddy.ui.views.blockable import BlockableDataView
from chestbuddy.ui.views.base_view import BaseView


class DataViewAdapter(BaseView):
    """
    Adapter that wraps the existing DataView component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        data_view (BlockableDataView): The wrapped BlockableDataView instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the BlockableDataView component
        - Provides the same functionality as DataView but with the new UI styling
        - Uses BlockableDataView for automatic integration with UI State Management
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

        # Create the underlying DataView (now using BlockableDataView)
        self._data_view = BlockableDataView(
            parent=None,  # Will be reparented when added to layout
            element_id=f"data_view_adapter_{id(self)}",
        )

        # Initialize the base view
        super().__init__("Data View", parent, data_required=True)
        self.setObjectName("DataViewAdapter")

        # Set custom empty state properties
        self.set_empty_state_props(
            title="No Data Loaded",
            message="Import CSV files to view and manage your chest data.",
            action_text="Import Data",
        )

        # Make sure the data view is also registered explicitly with the UI State Manager
        try:
            from chestbuddy.utils.ui_state import UIStateManager, UIElementGroups

            ui_manager = UIStateManager()

            # Check if properly registered
            if not ui_manager.is_element_in_group(self._data_view, UIElementGroups.DATA_VIEW):
                # Register it explicitly
                ui_manager.register_element(self._data_view, groups=[UIElementGroups.DATA_VIEW])
                import logging

                logging.getLogger(__name__).debug(
                    f"Explicitly registered DataView with UIElementGroups.DATA_VIEW"
                )
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error registering DataView with UI state manager: {e}"
            )

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
        self.add_header_action("refresh", "Refresh", "default")
