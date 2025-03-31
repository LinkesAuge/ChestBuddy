"""
chart_view.py

Description: Main chart view for the ChestBuddy application
Usage:
    chart_view = ChartView(data_model, chart_service)
    main_window.add_view(chart_view)
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QFormLayout,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCharts import QChartView, QChart
from PySide6.QtGui import QPainter

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class ChartView(UpdatableView):
    """
    Main chart view for the ChestBuddy application.

    This view provides an interface for users to visualize data with various chart types.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        chart_service (ChartService): The service for chart generation
        _controller (DataViewController): The controller for data view operations

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Provides chart creation and export functionality
        - Uses QtCharts for chart visualization
        - Uses DataViewController for chart operations when available
    """

    # Define signals (same as the adapter for compatibility)
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
        parent: Optional[QWidget] = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the ChartView.

        Args:
            data_model (ChestDataModel): The data model containing chest data
            chart_service (ChartService): The service for chart generation
            parent (Optional[QWidget]): Parent widget
            debug_mode (bool): Enable debug mode for signal connections
        """
        # Store references
        self._data_model = data_model
        self._chart_service = chart_service
        self._controller = None

        # UI components to be created in _setup_ui
        self._chart_type_combo = None
        self._x_axis_combo = None
        self._y_axis_combo = None
        self._group_by_combo = None
        self._chart_title_input = None
        self._chart_view = None
        self._create_chart_button = None
        self._export_button = None

        # Current chart
        self._current_chart = None

        # Initialize the base view
        super().__init__("Chart View", parent, debug_mode=debug_mode)
        self.setObjectName("ChartView")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this view.

        Args:
            controller: The DataViewController instance to use
        """
        self._controller = controller

        # Connect controller signals
        if self._controller:
            self._controller.operation_started.connect(self._on_operation_started)
            self._controller.operation_completed.connect(self._on_operation_completed)
            self._controller.operation_error.connect(self._on_operation_error)

            logger.info("ChartView: Controller set and signals connected")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Options layout
        options_layout = QGridLayout()

        # Chart type selection group
        chart_type_group = QGroupBox("Chart Type")
        chart_type_layout = QVBoxLayout(chart_type_group)

        # Chart type combobox
        self._chart_type_combo = QComboBox()
        self._chart_type_combo.addItems(["Bar Chart", "Pie Chart", "Line Chart"])
        chart_type_layout.addWidget(self._chart_type_combo)

        options_layout.addWidget(chart_type_group, 0, 0)

        # Data selection group
        data_selection_group = QGroupBox("Data Selection")
        data_selection_layout = QFormLayout(data_selection_group)

        # X-axis column selection
        self._x_axis_combo = QComboBox()
        data_selection_layout.addRow("X-Axis Column:", self._x_axis_combo)

        # Y-axis column selection
        self._y_axis_combo = QComboBox()
        data_selection_layout.addRow("Y-Axis Column:", self._y_axis_combo)

        # Group by column selection (optional)
        self._group_by_combo = QComboBox()
        self._group_by_combo.addItem("None")  # Default option
        data_selection_layout.addRow("Group By (optional):", self._group_by_combo)

        options_layout.addWidget(data_selection_group, 0, 1)

        # Chart options group
        chart_options_group = QGroupBox("Chart Options")
        chart_options_layout = QFormLayout(chart_options_group)

        # Chart title
        self._chart_title_input = QComboBox()
        self._chart_title_input.setEditable(True)
        self._chart_title_input.addItems(
            ["Chest Data Visualization", "Value Distribution", "Value Trends"]
        )
        chart_options_layout.addRow("Chart Title:", self._chart_title_input)

        # Create button
        self._create_chart_button = QPushButton("Create Chart")
        chart_options_layout.addRow("", self._create_chart_button)

        options_layout.addWidget(chart_options_group, 0, 2)

        # Add options layout to main layout
        self.get_content_layout().addLayout(options_layout)

        # Chart view
        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.Antialiasing)
        self._chart_view.setMinimumHeight(400)

        # Add chart view to main layout
        self.get_content_layout().addWidget(self._chart_view)

        # Export button layout
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        # Export button
        self._export_button = QPushButton("Export")
        self._export_button.setEnabled(False)  # Disabled until a chart is created
        export_layout.addWidget(self._export_button)

        # Add export layout to main layout
        self.get_content_layout().addLayout(export_layout)

        # Update column selection combos
        self._update_column_combos()

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect chart type selection
        self._chart_type_combo.currentTextChanged.connect(self._on_chart_type_changed)

        # Connect create chart button
        self._create_chart_button.clicked.connect(self._on_create_chart)

        # Connect export button
        self._export_button.clicked.connect(self._on_export_chart)

        # Connect header action buttons
        self.header_action_clicked.connect(self._on_header_action_clicked)

        # Connect to data model if available
        if hasattr(self._data_model, "data_changed") and hasattr(self, "request_update"):
            try:
                self._signal_manager.connect(
                    self._data_model, "data_changed", self, "request_update"
                )
                logger.debug("Connected data_model.data_changed to ChartView.request_update")
            except Exception as e:
                logger.error(f"Error connecting data model signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common chart operations
        self.add_header_action("create", "Create Chart")
        self.add_header_action("export", "Export Chart")
        self.add_header_action("refresh", "Refresh")

    def _on_create_chart(self):
        """Handle chart creation request."""
        try:
            # Emit signal to indicate chart creation started
            self.chart_creation_started.emit()

            # Get chart parameters from UI
            chart_type = self._chart_type_combo.currentText()
            x_column = self._x_axis_combo.currentText()
            y_column = self._y_axis_combo.currentText()
            chart_title = self._chart_title_input.currentText()
            group_by = self._group_by_combo.currentText()
            if group_by == "None":
                group_by = None

            # Use controller if available, otherwise fallback to direct chart creation
            if self._controller:
                # Delegate to controller
                self._controller.create_chart(
                    chart_type=chart_type,
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    group_by=group_by,
                )
            else:
                # Direct chart creation
                self._create_chart_directly(
                    chart_type=chart_type,
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    group_by=group_by,
                )

        except Exception as e:
            # Handle errors
            error_message = f"Error creating chart: {str(e)}"
            logger.error(error_message)
            self.chart_creation_error.emit(error_message)

    def _create_chart_directly(self, chart_type, x_column, y_column, title, group_by=None):
        """
        Create a chart directly using the chart service.

        Args:
            chart_type (str): Type of chart to create
            x_column (str): X-axis column name
            y_column (str): Y-axis column name
            title (str): Chart title
            group_by (str, optional): Group by column name
        """
        try:
            # Create the chart based on type
            if chart_type == "Bar Chart":
                chart = self._chart_service.create_bar_chart(
                    category_column=x_column, value_column=y_column, title=title
                )
            elif chart_type == "Pie Chart":
                chart = self._chart_service.create_pie_chart(
                    category_column=x_column, value_column=y_column, title=title
                )
            elif chart_type == "Line Chart":
                chart = self._chart_service.create_line_chart(
                    x_column=x_column, y_column=y_column, title=title, group_by=group_by
                )
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")

            # Set the chart in the chart view
            self._current_chart = chart
            self._chart_view.setChart(chart)

            # Enable export button now that we have a chart
            self._export_button.setEnabled(True)

            # Emit signal for successful creation
            self.chart_creation_completed.emit(chart_type)

        except Exception as e:
            error_message = f"Error creating chart: {str(e)}"
            logger.error(error_message)
            self.chart_creation_error.emit(error_message)

    def _on_export_chart(self):
        """Handle chart export request."""
        try:
            # Emit signal to indicate export started
            self.chart_export_started.emit()

            # Make sure we have a chart to export
            if not self._current_chart:
                raise ValueError("No chart to export")

            # Use controller if available, otherwise fallback to direct export
            if self._controller:
                # Delegate to controller
                self._controller.export_chart()
            else:
                # Direct export
                self._export_chart_directly()

        except Exception as e:
            # Handle errors
            error_message = f"Error exporting chart: {str(e)}"
            logger.error(error_message)
            self.chart_export_error.emit(error_message)

    def _export_chart_directly(self):
        """Export the chart directly using the chart service."""
        try:
            # Get the export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Chart", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            )

            if file_path:
                # Save the chart
                success = self._chart_service.save_chart(self._current_chart, file_path)

                if success:
                    # Emit signal for successful export
                    self.chart_export_completed.emit(file_path)
                else:
                    raise ValueError(f"Failed to save chart to {file_path}")

        except Exception as e:
            error_message = f"Error exporting chart: {str(e)}"
            logger.error(error_message)
            self.chart_export_error.emit(error_message)

    def _update_column_combos(self):
        """Update column selection combos with available columns from the data model."""
        try:
            # Get column names from data model
            if (
                not self._data_model
                or not hasattr(self._data_model, "data")
                or self._data_model.is_empty
            ):
                # No data available, disable controls
                self._x_axis_combo.clear()
                self._y_axis_combo.clear()
                self._group_by_combo.clear()
                self._group_by_combo.addItem("None")
                self._create_chart_button.setEnabled(False)
                return

            # Store current selections
            current_x = self._x_axis_combo.currentText() if self._x_axis_combo.count() > 0 else ""
            current_y = self._y_axis_combo.currentText() if self._y_axis_combo.count() > 0 else ""
            current_group = (
                self._group_by_combo.currentText() if self._group_by_combo.count() > 0 else "None"
            )

            # Get column names
            columns = list(self._data_model.data.columns)

            # Update X-axis combo
            self._x_axis_combo.clear()
            self._x_axis_combo.addItems(columns)
            if current_x in columns:
                self._x_axis_combo.setCurrentText(current_x)

            # Update Y-axis combo
            self._y_axis_combo.clear()
            numeric_columns = self._data_model.data.select_dtypes(
                include=["number"]
            ).columns.tolist()
            self._y_axis_combo.addItems(numeric_columns)
            if current_y in numeric_columns:
                self._y_axis_combo.setCurrentText(current_y)

            # Update group by combo
            self._group_by_combo.clear()
            self._group_by_combo.addItem("None")
            categorical_columns = self._data_model.data.select_dtypes(
                include=["object", "category"]
            ).columns.tolist()
            self._group_by_combo.addItems(categorical_columns)
            if current_group in categorical_columns or current_group == "None":
                self._group_by_combo.setCurrentText(current_group)

            # Enable create button now that we have data
            self._create_chart_button.setEnabled(True)

        except Exception as e:
            logger.error(f"Error updating column combos: {str(e)}")
            # Don't disable controls on error, just log and keep current state

    def _on_chart_type_changed(self, chart_type: str):
        """
        Handle chart type selection change.

        Args:
            chart_type (str): The selected chart type
        """
        # Enable/disable appropriate controls based on chart type
        is_line_chart = chart_type == "Line Chart"

        # Group by is primarily useful for line charts
        self._group_by_combo.setEnabled(is_line_chart)

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
            self._update_column_combos()
            if self._current_chart is not None:
                self._on_create_chart()

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

    def _on_operation_completed(self, operation: str, result: str):
        """
        Handle operation completed signal from controller.

        Args:
            operation (str): The operation that completed
            result (str): Operation result information
        """
        if operation == "chart_creation":
            # Update the chart view with the chart from the controller
            if hasattr(self._controller, "get_current_chart"):
                chart = self._controller.get_current_chart()
                if chart:
                    self._current_chart = chart
                    self._chart_view.setChart(chart)
                    self._export_button.setEnabled(True)

            self.chart_creation_completed.emit(result)
        elif operation == "chart_export":
            self.chart_export_completed.emit(result)

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

    def _update_view_content(self, data=None) -> None:
        """
        Update the view content with current data.

        Args:
            data: Optional data for the update (unused in this implementation)
        """
        # Update column combos for data model changes
        self._update_column_combos()

        # If we have a chart, refresh it
        if self._current_chart is not None:
            # Recreate the chart with current parameters
            self._on_create_chart()

        logger.debug("ChartView: View content updated")

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.
        """
        # Just update the column combos to reflect data model changes
        self._update_column_combos()
        logger.debug("ChartView: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        # Update column combos
        self._update_column_combos()

        # If there's a current chart, recreate it
        if self._current_chart is not None:
            self._on_create_chart()

        logger.debug("ChartView: View content populated")

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.
        """
        # Clear the current chart
        self._current_chart = None
        self._chart_view.setChart(None)

        # Reset UI elements to defaults
        self._chart_type_combo.setCurrentIndex(0)
        if self._x_axis_combo.count() > 0:
            self._x_axis_combo.setCurrentIndex(0)
        if self._y_axis_combo.count() > 0:
            self._y_axis_combo.setCurrentIndex(0)
        self._chart_title_input.setCurrentText("")
        self._group_by_combo.setCurrentIndex(0)

        # Disable export button
        self._export_button.setEnabled(False)

        logger.debug("ChartView: View content reset")
