"""
chart_view_adapter.py

Description: Adapter to integrate the existing ChartTab with the new BaseView structure
Usage:
    chart_view = ChartViewAdapter(data_model, chart_service)
    main_window.add_view(chart_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.ui.chart_tab import ChartTab
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.resources.icons import Icons


class ChartViewAdapter(BaseView):
    """
    Adapter that wraps the existing ChartTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        chart_service (ChartService): The service for chart generation
        chart_tab (ChartTab): The wrapped ChartTab instance

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing ChartTab component
        - Provides the same functionality as ChartTab but with the new UI styling
    """

    def __init__(
        self, data_model: ChestDataModel, chart_service: ChartService, parent: QWidget = None
    ):
        """
        Initialize the ChartViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to visualize
            chart_service (ChartService): The chart service to use
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model
        self._chart_service = chart_service

        # Create the underlying ChartTab
        self._chart_tab = ChartTab(data_model, chart_service)

        # Initialize the base view
        super().__init__("Chart View", parent, data_required=True)
        self.setObjectName("ChartViewAdapter")

        # Set custom empty state properties
        self.set_empty_state_props(
            title="No Data to Visualize",
            message="Import CSV files to create charts and analyze your chest data.",
            action_text="Import Data",
            icon=Icons.get_icon(Icons.CHART),
        )

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the ChartTab to the content widget
        self.get_content_layout().addWidget(self._chart_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect any signals from the ChartTab if needed
        pass

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common chart operations
        self.add_header_action("export_chart", "Export Chart", "secondary")
        self.add_header_action("refresh", "Refresh")
