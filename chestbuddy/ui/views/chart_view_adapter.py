"""
chart_view_adapter.py

Description: Adapter to integrate the existing ChartTab with the new BaseView structure
Usage:
    chart_view = ChartViewAdapter(data_model, chart_service)
    chart_view.set_data_view_controller(data_view_controller)
    main_window.add_view(chart_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.chart_tab import ChartTab
from chestbuddy.ui.views.base_view import BaseView


class ChartViewAdapter(BaseView):
    """
    Adapter that wraps the existing ChartTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        chart_service (ChartService): The service for chart generation
        chart_tab (ChartTab): The wrapped ChartTab instance
        data_view_controller (DataViewController): Controller for data operations

    Signals:
        chart_creation_started: Emitted when chart creation starts
        chart_creation_completed: Emitted when chart creation completes successfully
        chart_creation_error: Emitted when chart creation encounters an error
        chart_export_started: Emitted when chart export starts
        chart_export_completed: Emitted when chart export completes successfully
        chart_export_error: Emitted when chart export encounters an error

    Implementation Notes:
        - Inherits from BaseView to maintain UI consistency
        - Wraps the existing ChartTab component
        - Uses DataViewController for data operations when available
        - Falls back to direct data_model/chart_service interaction when controller not available
    """

    # Signals
    chart_creation_started = Signal()
    chart_creation_completed = Signal(str)  # chart type
    chart_creation_error = Signal(str)  # error message
    chart_export_started = Signal()
    chart_export_completed = Signal(str)  # file path
    chart_export_error = Signal(str)  # error message

    def __init__(
        self,
        data_model: ChestDataModel,
        chart_service: ChartService,
        data_view_controller: DataViewController = None,
        parent: QWidget = None,
    ):
        """
        Initialize the ChartViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to visualize
            chart_service (ChartService): The chart service to use
            data_view_controller (DataViewController, optional): Controller for data operations. Defaults to None.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model
        self._chart_service = chart_service
        self._data_view_controller = data_view_controller

        # Create the underlying ChartTab
        self._chart_tab = ChartTab(data_model, chart_service)

        # Initialize the base view
        super().__init__("Chart View", parent)
        self.setObjectName("ChartViewAdapter")

    def set_data_view_controller(self, controller: DataViewController):
        """
        Set the data view controller for this adapter.

        Args:
            controller (DataViewController): The controller to use
        """
        self._data_view_controller = controller
        self._connect_controller_signals()

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

        # Connect ChartTab signals
        self._chart_tab.create_chart_button.clicked.connect(self._on_create_chart)
        self._chart_tab.export_button.clicked.connect(self._on_export_chart)

        # Connect header action signals
        self.header_action_clicked.connect(self._on_header_action_clicked)

        # Connect to controller signals if controller is set
        if self._data_view_controller:
            self._connect_controller_signals()

    def _connect_controller_signals(self):
        """Connect to data view controller signals."""
        if self._data_view_controller:
            self._data_view_controller.operation_started.connect(self._on_operation_started)
            self._data_view_controller.operation_completed.connect(self._on_operation_completed)
            self._data_view_controller.operation_error.connect(self._on_operation_error)

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common chart operations
        self.add_header_action("create", "Create Chart")
        self.add_header_action("export", "Export Chart")
        self.add_header_action("refresh", "Refresh")

    @Slot(str)
    def _on_header_action_clicked(self, action_id: str):
        """
        Handle header action button clicks.

        Args:
            action_id (str): The ID of the action button clicked
        """
        if action_id == "create":
            self._on_create_chart()
        elif action_id == "export":
            self._on_export_chart()
        elif action_id == "refresh":
            self._chart_tab._update_column_combos()
            if self._chart_tab._current_chart is not None:
                self._on_create_chart()

    @Slot()
    def _on_create_chart(self):
        """Handle chart creation request."""
        try:
            # Emit signal to indicate chart creation started
            self.chart_creation_started.emit()

            # Get chart parameters from UI
            chart_type = self._chart_tab.chart_type_combo.currentText()
            x_column = self._chart_tab.x_axis_combo.currentText()
            y_column = self._chart_tab.y_axis_combo.currentText()
            chart_title = self._chart_tab.chart_title_input.currentText()
            group_by = self._chart_tab.group_by_combo.currentText()
            if group_by == "None":
                group_by = None

            # Use controller if available, otherwise fallback to direct chart creation
            if self._data_view_controller:
                # Delegate to controller
                self._data_view_controller.create_chart(
                    chart_type=chart_type,
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    group_by=group_by,
                )
            else:
                # Direct chart creation
                self._chart_tab._create_chart()
                self.chart_creation_completed.emit(chart_type)

        except Exception as e:
            # Handle errors
            error_message = f"Error creating chart: {str(e)}"
            self.chart_creation_error.emit(error_message)

    @Slot()
    def _on_export_chart(self):
        """Handle chart export request."""
        try:
            # Emit signal to indicate export started
            self.chart_export_started.emit()

            # Use controller if available, otherwise fallback to direct export
            if self._data_view_controller:
                # Delegate to controller
                self._data_view_controller.export_chart()
            else:
                # Direct export
                self._chart_tab._export_chart()

        except Exception as e:
            # Handle errors
            error_message = f"Error exporting chart: {str(e)}"
            self.chart_export_error.emit(error_message)

    @Slot(str)
    def _on_operation_started(self, operation: str):
        """
        Handle operation started signal from controller.

        Args:
            operation (str): The operation that started
        """
        if operation == "chart_creation":
            self.chart_creation_started.emit()
        elif operation == "chart_export":
            self.chart_export_started.emit()

    @Slot(str, str)
    def _on_operation_completed(self, operation: str, result: str):
        """
        Handle operation completed signal from controller.

        Args:
            operation (str): The operation that completed
            result (str): Operation result information
        """
        if operation == "chart_creation":
            self.chart_creation_completed.emit(result)
        elif operation == "chart_export":
            self.chart_export_completed.emit(result)

    @Slot(str, str)
    def _on_operation_error(self, operation: str, error_message: str):
        """
        Handle operation error signal from controller.

        Args:
            operation (str): The operation that encountered an error
            error_message (str): Error message
        """
        if operation == "chart_creation":
            self.chart_creation_error.emit(error_message)
        elif operation == "chart_export":
            self.chart_export_error.emit(error_message)
