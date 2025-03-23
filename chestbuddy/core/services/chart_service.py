"""
chart_service.py

Description: Provides functionality for generating and exporting charts from ChestBuddy data
Usage:
    chart_service = ChartService(data_model)
    chart = chart_service.create_bar_chart("category", "chest_value", "Category Distribution")
    chart_service.save_chart(chart, "my_chart.png")
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import pandas as pd
from PySide6.QtCharts import (
    QChart,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QPieSeries,
    QLineSeries,
    QValueAxis,
    QChartView,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsTextItem

from chestbuddy.core.models.chest_data_model import ChestDataModel


class ChartService:
    """
    Service for generating and exporting charts from chest data.

    Attributes:
        _data_model (ChestDataModel): The data model containing chest data

    Implementation Notes:
        - Uses QtCharts for chart generation
        - Supports bar, pie, and line charts
        - Allows exporting charts to image files
    """

    def __init__(self, data_model: ChestDataModel):
        """
        Initialize the chart service with a data model.

        Args:
            data_model (ChestDataModel): The data model containing chest data
        """
        self._data_model = data_model
        self._colors = [
            QColor("#1f77b4"),  # blue
            QColor("#ff7f0e"),  # orange
            QColor("#2ca02c"),  # green
            QColor("#d62728"),  # red
            QColor("#9467bd"),  # purple
            QColor("#8c564b"),  # brown
            QColor("#e377c2"),  # pink
            QColor("#7f7f7f"),  # gray
            QColor("#bcbd22"),  # olive
            QColor("#17becf"),  # teal
        ]

    def create_bar_chart(
        self,
        category_column: str,
        value_column: str,
        title: str = "Bar Chart",
        x_axis_title: Optional[str] = None,
        y_axis_title: Optional[str] = None,
    ) -> QChart:
        """
        Create a bar chart from the data.

        Args:
            category_column (str): Column to use for categories
            value_column (str): Column to use for values
            title (str, optional): Chart title. Defaults to "Bar Chart".
            x_axis_title (str, optional): X-axis title. Defaults to category_column.
            y_axis_title (str, optional): Y-axis title. Defaults to value_column.

        Returns:
            QChart: The created bar chart

        Raises:
            ValueError: If data is empty or required columns don't exist
        """
        df = self._data_model.data

        if df.empty:
            raise ValueError("Cannot create chart from empty data")

        if category_column not in df.columns or value_column not in df.columns:
            raise ValueError(f"Columns {category_column} and/or {value_column} not found in data")

        # Group by category and sum values
        grouped_data = df.groupby(category_column)[value_column].sum().reset_index()

        # Create a bar series
        bar_series = QBarSeries()

        # Create a bar set
        bar_set = QBarSet(value_column)

        # Add values to the bar set
        for value in grouped_data[value_column]:
            bar_set.append(value)

        # Set bar color
        bar_set.setColor(self._colors[0])

        # Add the bar set to the series
        bar_series.append(bar_set)

        # Create the chart
        chart = QChart()
        chart.addSeries(bar_series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # Create the axes
        axis_x = QBarCategoryAxis()
        categories = [str(cat) for cat in grouped_data[category_column]]
        axis_x.append(categories)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(grouped_data[value_column]) * 1.1)  # Add 10% margin

        # Set axis titles
        if x_axis_title:
            axis_x.setTitleText(x_axis_title)
        else:
            axis_x.setTitleText(category_column)

        if y_axis_title:
            axis_y.setTitleText(y_axis_title)
        else:
            axis_y.setTitleText(value_column)

        # Attach axes to the chart
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)

        # Attach series to axes
        bar_series.attachAxis(axis_x)
        bar_series.attachAxis(axis_y)

        # Set legend visibility
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        return chart

    def create_pie_chart(
        self, category_column: str, value_column: str, title: str = "Pie Chart"
    ) -> QChart:
        """
        Create a pie chart from the data.

        Args:
            category_column (str): Column to use for pie slices
            value_column (str): Column to use for slice values
            title (str, optional): Chart title. Defaults to "Pie Chart".

        Returns:
            QChart: The created pie chart

        Raises:
            ValueError: If data is empty or required columns don't exist
        """
        df = self._data_model.data

        if df.empty:
            raise ValueError("Cannot create chart from empty data")

        if category_column not in df.columns or value_column not in df.columns:
            raise ValueError(f"Columns {category_column} and/or {value_column} not found in data")

        # Group by category and sum values
        grouped_data = df.groupby(category_column)[value_column].sum().reset_index()

        # Create a pie series
        pie_series = QPieSeries()

        # Add slices to the pie
        for i, (_, row) in enumerate(grouped_data.iterrows()):
            slice = pie_series.append(
                f"{row[category_column]}: {row[value_column]}", row[value_column]
            )
            slice.setBrush(self._colors[i % len(self._colors)])

        # Create the chart
        chart = QChart()
        chart.addSeries(pie_series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # Set legend visibility
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)

        # Customize slices
        for i, slice in enumerate(pie_series.slices()):
            # Set slice labels visible
            slice.setLabelVisible(True)

            # Set the slice to explode slightly
            if i == 0:  # Explode the first slice
                slice.setExploded(True)
                # PySide6 version might not support this feature
                # slice.setLabelPosition(Qt.AlignRight)

        return chart

    def create_line_chart(
        self,
        x_column: str,
        y_column: str,
        title: str = "Line Chart",
        x_axis_title: Optional[str] = None,
        y_axis_title: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> QChart:
        """
        Create a line chart from the data.

        Args:
            x_column (str): Column to use for x-axis
            y_column (str): Column to use for y-axis
            title (str, optional): Chart title. Defaults to "Line Chart".
            x_axis_title (str, optional): X-axis title. Defaults to x_column.
            y_axis_title (str, optional): Y-axis title. Defaults to y_column.
            group_by (str, optional): Column to group by for multiple lines.

        Returns:
            QChart: The created line chart

        Raises:
            ValueError: If data is empty or required columns don't exist
        """
        df = self._data_model.data

        if df.empty:
            raise ValueError("Cannot create chart from empty data")

        if x_column not in df.columns or y_column not in df.columns:
            raise ValueError(f"Columns {x_column} and/or {y_column} not found in data")

        # Convert date column to datetime if needed
        if df[x_column].dtype == "object" and pd.api.types.is_string_dtype(df[x_column]):
            try:
                df[x_column] = pd.to_datetime(df[x_column], format="mixed")
            except:
                pass  # If conversion fails, continue with original data

        # Sort by x values for proper line plotting
        df = df.sort_values(by=x_column)

        # Create the chart
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # Create series based on grouping
        if group_by and group_by in df.columns:
            # Create a series for each group
            groups = df[group_by].unique()

            for i, group in enumerate(groups):
                group_data = df[df[group_by] == group]

                # Create a line series
                series = QLineSeries()
                series.setName(f"{group}")

                # Set series color
                color = self._colors[i % len(self._colors)]
                pen = QPen(color)
                pen.setWidth(2)
                series.setPen(pen)

                # Add data points
                for _, row in group_data.iterrows():
                    x_val = row[x_column]
                    y_val = row[y_column]

                    # Convert x to numeric for plotting if it's a date
                    if pd.api.types.is_datetime64_any_dtype(x_val) or isinstance(
                        x_val, pd.Timestamp
                    ):
                        # Convert to days since epoch for plotting
                        try:
                            if hasattr(x_val, "timestamp"):
                                x_numeric = x_val.timestamp()
                            else:
                                x_numeric = pd.Timestamp(x_val).timestamp()
                            series.append(x_numeric, float(y_val))
                        except Exception as e:
                            # If conversion fails, skip this point
                            print(f"Error converting timestamp: {e}")
                    else:
                        try:
                            series.append(float(x_val), float(y_val))
                        except Exception as e:
                            # If conversion fails, skip this point
                            print(f"Error converting values: {e}")

                chart.addSeries(series)
        else:
            # Create a single line series
            series = QLineSeries()
            series.setName(y_column)

            # Set series color
            pen = QPen(self._colors[0])
            pen.setWidth(2)
            series.setPen(pen)

            # Add data points
            for _, row in df.iterrows():
                x_val = row[x_column]
                y_val = row[y_column]

                # Convert x to numeric for plotting if it's a date
                if pd.api.types.is_datetime64_any_dtype(x_val) or isinstance(x_val, pd.Timestamp):
                    # Convert to days since epoch for plotting
                    try:
                        if hasattr(x_val, "timestamp"):
                            x_numeric = x_val.timestamp()
                        else:
                            x_numeric = pd.Timestamp(x_val).timestamp()
                        series.append(x_numeric, float(y_val))
                    except Exception as e:
                        # If conversion fails, skip this point
                        print(f"Error converting timestamp: {e}")
                else:
                    try:
                        series.append(float(x_val), float(y_val))
                    except Exception as e:
                        # If conversion fails, skip this point
                        print(f"Error converting values: {e}")

            chart.addSeries(series)

        # Create axes
        axis_x = QValueAxis()
        axis_y = QValueAxis()

        # Set axis titles
        if x_axis_title:
            axis_x.setTitleText(x_axis_title)
        else:
            axis_x.setTitleText(x_column)

        if y_axis_title:
            axis_y.setTitleText(y_axis_title)
        else:
            axis_y.setTitleText(y_column)

        # Add axes to chart
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)

        # Attach series to axes
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        # Set axis ranges
        min_x, max_x, min_y, max_y = float("inf"), float("-inf"), float("inf"), float("-inf")

        # Find min/max values across all series
        for series in chart.series():
            for i in range(series.count()):
                point = series.at(i)
                min_x = min(min_x, point.x())
                max_x = max(max_x, point.x())
                min_y = min(min_y, point.y())
                max_y = max(max_y, point.y())

        # Add some margin to the ranges
        x_margin = (max_x - min_x) * 0.05 if max_x > min_x else 1.0
        y_margin = (max_y - min_y) * 0.1 if max_y > min_y else 1.0

        axis_x.setRange(min_x - x_margin, max_x + x_margin)
        axis_y.setRange(min_y - y_margin, max_y + y_margin)

        # Set legend visibility
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        return chart

    def save_chart(self, chart: QChart, file_path: str) -> bool:
        """
        Save the chart to an image file.

        Args:
            chart (QChart): The chart to save
            file_path (str): Path where to save the chart

        Returns:
            bool: True if saved successfully, False otherwise

        Raises:
            ValueError: If chart is None or file_path is invalid
        """
        if chart is None:
            raise ValueError("Cannot save a None chart")

        if not file_path:
            raise ValueError("Invalid file path")

        try:
            # Create a QChartView with the chart
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)

            # Set a reasonable size for the output image
            chart_view.resize(800, 600)

            # Create a pixmap and render the chart to it
            pixmap = chart_view.grab()

            # Save the pixmap to file
            return pixmap.save(file_path)
        except Exception as e:
            print(f"Error saving chart: {e}")
            return False

    def create_player_distribution_chart(self, title: str = "Top Players") -> QChart:
        """
        Create a bar chart showing the distribution of players in the dataset.

        Args:
            title (str, optional): Chart title. Defaults to "Top Players".

        Returns:
            QChart: The created bar chart

        Raises:
            ValueError: If data is empty or player column doesn't exist
        """
        try:
            # Identify the player/user column - this might need adjustment based on your data structure
            player_column = next(
                (
                    col
                    for col in self._data_model.data.columns
                    if col.lower() in ["player", "user", "username", "name"]
                ),
                None,
            )

            if not player_column:
                # Fallback to first column if no player column is found
                player_column = self._data_model.data.columns[0]

            # Create a bar chart of the top 5-10 players by frequency
            df = self._data_model.data

            if df.empty:
                # Return empty chart if data is empty
                chart = QChart()
                chart.setTitle(title)
                return chart

            # Count occurrences of each player
            player_counts = df[player_column].value_counts().head(10)

            # Create bar chart with this data
            # Create a bar series
            bar_series = QBarSeries()

            # Create a bar set
            bar_set = QBarSet("Count")

            # Add values to the bar set
            for value in player_counts.values:
                bar_set.append(value)

            # Set bar color
            bar_set.setColor(self._colors[0])

            # Add the bar set to the series
            bar_series.append(bar_set)

            # Create the chart
            chart = QChart()
            chart.addSeries(bar_series)
            chart.setTitle(title)
            chart.setAnimationOptions(QChart.SeriesAnimations)

            # Create the axes
            axis_x = QBarCategoryAxis()
            categories = [str(player) for player in player_counts.index]
            axis_x.append(categories)

            axis_y = QValueAxis()
            max_value = max(player_counts.values) if not player_counts.empty else 10
            axis_y.setRange(0, max_value * 1.1)  # Add 10% margin

            # Set axis titles
            axis_x.setTitleText("Player")
            axis_y.setTitleText("Entries")

            # Attach axes to the chart
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)

            # Attach series to axes
            bar_series.attachAxis(axis_x)
            bar_series.attachAxis(axis_y)

            # Set legend visibility
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            return chart

        except Exception as e:
            # In case of error, return empty chart
            chart = QChart()
            chart.setTitle(f"{title} (Error: {str(e)})")
            return chart

    def create_chest_sources_chart(self, title: str = "Chest Sources") -> QChart:
        """
        Create a pie chart showing the distribution of chest sources in the dataset.

        Args:
            title (str, optional): Chart title. Defaults to "Chest Sources".

        Returns:
            QChart: The created pie chart

        Raises:
            ValueError: If data is empty or source column doesn't exist
        """
        try:
            # Identify the source column - this might need adjustment based on your data structure
            source_column = next(
                (
                    col
                    for col in self._data_model.data.columns
                    if col.lower() in ["source", "chest_source", "origin", "type"]
                ),
                None,
            )

            if not source_column:
                # Fallback to second column if no source column is found
                source_column = self._data_model.data.columns[
                    min(1, len(self._data_model.data.columns) - 1)
                ]

            # Create a pie chart of the chest sources
            df = self._data_model.data

            if df.empty:
                # Return empty chart if data is empty
                chart = QChart()
                chart.setTitle(title)
                return chart

            # Count occurrences of each source
            source_counts = df[source_column].value_counts()

            # Create pie chart with this data
            # Create a pie series
            pie_series = QPieSeries()

            # Add slices to the pie
            for i, (source, count) in enumerate(source_counts.items()):
                slice = pie_series.append(f"{source}: {count}", count)
                slice.setBrush(self._colors[i % len(self._colors)])

            # Create the chart
            chart = QChart()
            chart.addSeries(pie_series)
            chart.setTitle(title)
            chart.setAnimationOptions(QChart.SeriesAnimations)

            # Set legend visibility
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignRight)

            # Customize slices
            for i, slice in enumerate(pie_series.slices()):
                # Set slice labels visible
                slice.setLabelVisible(True)

                # Set the first slice to explode slightly
                if i == 0:
                    slice.setExploded(True)

            return chart

        except Exception as e:
            # In case of error, return empty chart
            chart = QChart()
            chart.setTitle(f"{title} (Error: {str(e)})")
            return chart
