"""
chart_tab.py

Description: Provides the Chart Tab UI component for visualizing data with various chart types
Usage:
    chart_tab = ChartTab(data_model, chart_service)
    main_window.add_tab(chart_tab, "Charts")
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

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
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService


class ChartTab(QWidget):
    """
    Tab for visualizing data with various chart types.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        chart_service (ChartService): Service for generating charts

    Implementation Notes:
        - Uses QtCharts for chart visualization
        - Supports bar, pie, and line charts
        - Allows exporting charts to image files
    """

    def __init__(self, data_model: ChestDataModel, chart_service: ChartService):
        """
        Initialize the chart tab.

        Args:
            data_model (ChestDataModel): The data model containing chest data
            chart_service (ChartService): Service for generating charts
        """
        super().__init__()
        self.data_model = data_model
        self.chart_service = chart_service

        # Keep track of the current chart
        self._current_chart = None

        # Initialize UI components
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout()

        # Options layout
        options_layout = QGridLayout()

        # Chart type selection group
        chart_type_group = QGroupBox("Chart Type")
        chart_type_layout = QVBoxLayout()

        # Chart type combobox
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Bar Chart", "Pie Chart", "Line Chart"])
        chart_type_layout.addWidget(self.chart_type_combo)

        chart_type_group.setLayout(chart_type_layout)
        options_layout.addWidget(chart_type_group, 0, 0)

        # Data selection group
        data_selection_group = QGroupBox("Data Selection")
        data_selection_layout = QFormLayout()

        # X-axis column selection
        self.x_axis_combo = QComboBox()
        data_selection_layout.addRow("X-Axis Column:", self.x_axis_combo)

        # Y-axis column selection
        self.y_axis_combo = QComboBox()
        data_selection_layout.addRow("Y-Axis Column:", self.y_axis_combo)

        # Group by column selection (optional)
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("None")  # Default option
        data_selection_layout.addRow("Group By (optional):", self.group_by_combo)

        data_selection_group.setLayout(data_selection_layout)
        options_layout.addWidget(data_selection_group, 0, 1)

        # Chart options group
        chart_options_group = QGroupBox("Chart Options")
        chart_options_layout = QFormLayout()

        # Chart title
        self.chart_title_input = QComboBox()
        self.chart_title_input.setEditable(True)
        self.chart_title_input.addItems(
            ["Chest Data Visualization", "Value Distribution", "Value Trends"]
        )
        chart_options_layout.addRow("Chart Title:", self.chart_title_input)

        # Create button
        self.create_chart_button = QPushButton("Create Chart")
        chart_options_layout.addRow("", self.create_chart_button)

        chart_options_group.setLayout(chart_options_layout)
        options_layout.addWidget(chart_options_group, 0, 2)

        # Add options layout to main layout
        main_layout.addLayout(options_layout)

        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(400)

        # Add chart view to main layout
        main_layout.addWidget(self.chart_view)

        # Export button layout
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.setEnabled(False)  # Disabled until a chart is created
        export_layout.addWidget(self.export_button)

        # Add export layout to main layout
        main_layout.addLayout(export_layout)

        # Set the main layout
        self.setLayout(main_layout)

        # Update column selection combos
        self._update_column_combos()

    def _connect_signals(self):
        """Connect signals to slots."""
        # Chart type selection
        self.chart_type_combo.currentTextChanged.connect(self._on_chart_type_changed)

        # Create chart button
        self.create_chart_button.clicked.connect(self._create_chart)

        # Export button
        self.export_button.clicked.connect(self._export_chart)

        # Data model changes
        self.data_model.data_changed.connect(self._on_data_changed)

    def _on_chart_type_changed(self, chart_type: str):
        """
        Handle chart type selection change.

        Args:
            chart_type (str): The selected chart type
        """
        # Enable/disable appropriate controls based on chart type
        is_line_chart = chart_type == "Line Chart"

        # Group by is primarily useful for line charts
        self.group_by_combo.setEnabled(is_line_chart)

        # Create a new chart if possible
        if self.data_model.data is not None and not self.data_model.data.empty:
            self._create_chart()

    def _on_data_changed(self):
        """Handle data model changes."""
        # Update column selection combos
        self._update_column_combos()

        # Refresh the chart if one exists
        if self._current_chart is not None:
            self._create_chart()

    def _update_column_combos(self):
        """Update column selection comboboxes based on current data."""
        # Save current selections
        x_axis_col = self.x_axis_combo.currentText()
        y_axis_col = self.y_axis_combo.currentText()
        group_by_col = self.group_by_combo.currentText()

        # Clear combos
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        self.group_by_combo.clear()
        self.group_by_combo.addItem("None")  # Always keep None as an option

        # Get dataframe columns
        df = self.data_model.data
        if df is not None and not df.empty:
            columns = df.columns.tolist()

            # Add columns to combos
            self.x_axis_combo.addItems(columns)
            self.y_axis_combo.addItems(columns)
            self.group_by_combo.addItems(columns)

            # Try to restore previous selections if they still exist
            x_index = self.x_axis_combo.findText(x_axis_col)
            if x_index >= 0:
                self.x_axis_combo.setCurrentIndex(x_index)
            elif "date" in columns:
                # Set default x-axis to 'date' if available
                self.x_axis_combo.setCurrentText("date")

            y_index = self.y_axis_combo.findText(y_axis_col)
            if y_index >= 0:
                self.y_axis_combo.setCurrentIndex(y_index)
            elif "chest_value" in columns:
                # Set default y-axis to 'chest_value' if available
                self.y_axis_combo.setCurrentText("chest_value")

            group_index = self.group_by_combo.findText(group_by_col)
            if group_index >= 0:
                self.group_by_combo.setCurrentIndex(group_index)
            else:
                # Default to "None" for group by
                self.group_by_combo.setCurrentText("None")

    def create_chart_for_testing(self):
        """
        Test-safe method to create a chart based on current selections.

        Returns:
            The created chart object if successful, None otherwise.

        Note:
            This method is primarily for testing. It avoids UI operations
            that might cause access violations in tests.
        """
        df = self.data_model.data

        if df is None or df.empty:
            return None

        try:
            chart_type = self.chart_type_combo.currentText()
            x_column = self.x_axis_combo.currentText()
            y_column = self.y_axis_combo.currentText()
            chart_title = self.chart_title_input.currentText()

            # Get group by if not "None"
            group_by = None
            if self.group_by_combo.currentText() != "None":
                group_by = self.group_by_combo.currentText()

            # Create chart based on type
            if chart_type == "Bar Chart":
                return self.chart_service.create_bar_chart(
                    category_column=x_column,
                    value_column=y_column,
                    title=chart_title,
                    x_axis_title=x_column,
                    y_axis_title=y_column,
                )
            elif chart_type == "Pie Chart":
                return self.chart_service.create_pie_chart(
                    category_column=x_column, value_column=y_column, title=chart_title
                )
            elif chart_type == "Line Chart":
                return self.chart_service.create_line_chart(
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    x_axis_title=x_column,
                    y_axis_title=y_column,
                    group_by=group_by,
                )

        except Exception as e:
            print(f"Error creating chart for testing: {e}")
            return None

    def _create_chart(self):
        """Create a chart based on current selections."""
        df = self.data_model.data

        if df is None or df.empty:
            return

        try:
            chart_type = self.chart_type_combo.currentText()
            x_column = self.x_axis_combo.currentText()
            y_column = self.y_axis_combo.currentText()
            chart_title = self.chart_title_input.currentText()

            # Get group by if not "None"
            group_by = None
            if self.group_by_combo.currentText() != "None":
                group_by = self.group_by_combo.currentText()

            # Create chart based on type
            if chart_type == "Bar Chart":
                self._current_chart = self.chart_service.create_bar_chart(
                    category_column=x_column,
                    value_column=y_column,
                    title=chart_title,
                    x_axis_title=x_column,
                    y_axis_title=y_column,
                )
            elif chart_type == "Pie Chart":
                self._current_chart = self.chart_service.create_pie_chart(
                    category_column=x_column, value_column=y_column, title=chart_title
                )
            elif chart_type == "Line Chart":
                self._current_chart = self.chart_service.create_line_chart(
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    x_axis_title=x_column,
                    y_axis_title=y_column,
                    group_by=group_by,
                )

            # Set the chart in the view
            self.chart_view.setChart(self._current_chart)

            # Enable export button
            self.export_button.setEnabled(True)

        except Exception as e:
            # Show error message
            self._current_chart = None
            self.chart_view.setChart(None)
            self.export_button.setEnabled(False)
            print(f"Error creating chart: {e}")

    def _export_chart(self):
        """Export the current chart to an image file."""
        if self._current_chart is None:
            return

        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            str(Path.home()),
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)",
        )

        if file_path:
            # Save the chart
            success = self.chart_service.save_chart(self._current_chart, file_path)
            if not success:
                print("Failed to export chart")

    def export_chart_for_testing(self, file_path: str) -> bool:
        """
        Test-safe method to export a chart to a file.

        Args:
            file_path (str): Path where the chart should be saved

        Returns:
            bool: True if export was successful, False otherwise

        Note:
            This method is primarily for testing. It avoids UI operations
            that might cause access violations in tests.
        """
        if self._current_chart is None:
            return False

        try:
            return self.chart_service.save_chart(self._current_chart, file_path)
        except Exception as e:
            print(f"Error exporting chart for testing: {e}")
            return False
