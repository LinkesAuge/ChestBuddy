"""
filter_bar.py

Description: A search and filter bar for table views in ChestBuddy
Usage:
    filter_bar = FilterBar()
    filter_bar.search_changed.connect(on_search_text_changed)
    filter_bar.filter_changed.connect(on_filter_changed)

    # Get current search text
    search_text = filter_bar.search_text()

    # Get current filters
    filters = filter_bar.current_filters()
"""

from typing import Optional, Dict, Any, List, Callable

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFrame,
    QComboBox,
    QLabel,
    QToolButton,
    QSizePolicy,
)


class FilterBar(QWidget):
    """
    A search and filter bar for table views in ChestBuddy.

    Provides a consistent interface for searching and filtering data
    displayed in tables throughout the application.

    Attributes:
        search_changed (Signal): Signal emitted when search text changes (str)
        filter_changed (Signal): Signal emitted when filters change (dict)
        filter_expanded (Signal): Signal emitted when the filter section is expanded (bool)
    """

    # Signals
    search_changed = Signal(str)
    filter_changed = Signal(dict)
    filter_expanded = Signal(bool)

    def __init__(
        self,
        parent=None,
        placeholder_text: str = "Search...",
        filters: Optional[Dict[str, List[str]]] = None,
        show_advanced_filters: bool = True,
        expanded: bool = False,
    ):
        """
        Initialize a new FilterBar.

        Args:
            parent: Parent widget
            placeholder_text (str): Placeholder text for the search box
            filters (Dict[str, List[str]], optional): Dictionary of filter categories and options
            show_advanced_filters (bool): Whether to show the advanced filters section
            expanded (bool): Whether the advanced filters section is initially expanded
        """
        super().__init__(parent)

        # Store properties
        self._placeholder_text = placeholder_text
        self._filters = filters or {}
        self._show_advanced_filters = show_advanced_filters
        self._expanded = expanded
        self._current_filters = {}

        # Init UI components as None
        self._search_field = None
        self._expand_button = None
        self._filter_frame = None
        self._filter_widgets = {}

        # Set up the UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Search and expand button row
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(8)

        # Search field
        self._search_field = QLineEdit(self)
        self._search_field.setPlaceholderText(self._placeholder_text)
        self._search_field.setClearButtonEnabled(True)
        self._search_field.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_field)

        # Expand button (if we have filters to show)
        if self._show_advanced_filters and self._filters:
            self._expand_button = QToolButton(self)
            self._expand_button.setText("Filters")

            # Toggle the icon based on expanded state
            expand_icon = (
                QIcon(":/icons/chevron_down.svg")
                if not self._expanded
                else QIcon(":/icons/chevron_up.svg")
            )
            self._expand_button.setIcon(expand_icon)
            self._expand_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self._expand_button.setCheckable(True)
            self._expand_button.setChecked(self._expanded)
            self._expand_button.clicked.connect(self._toggle_filters)

            search_row.addWidget(self._expand_button)

        main_layout.addLayout(search_row)

        # Filter frame (initially hidden if not expanded)
        if self._show_advanced_filters and self._filters:
            self._filter_frame = QFrame(self)
            filter_layout = QVBoxLayout(self._filter_frame)
            filter_layout.setContentsMargins(0, 8, 0, 0)
            filter_layout.setSpacing(8)

            # Add filter widgets for each category
            for category, options in self._filters.items():
                filter_row = QHBoxLayout()
                filter_row.setContentsMargins(0, 0, 0, 0)
                filter_row.setSpacing(8)

                # Category label
                label = QLabel(f"{category}:", self)
                filter_row.addWidget(label)

                # Category dropdown
                combo = QComboBox(self)
                combo.addItem("All")
                for option in options:
                    combo.addItem(option)

                combo.setProperty("category", category)
                combo.currentIndexChanged.connect(self._on_filter_changed)

                filter_row.addWidget(combo)
                filter_row.addStretch(1)

                filter_layout.addLayout(filter_row)

                # Store the widget for later access
                self._filter_widgets[category] = combo

            main_layout.addWidget(self._filter_frame)

            # Hide if not initially expanded
            self._filter_frame.setVisible(self._expanded)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def _on_search_changed(self, text: str):
        """
        Handle search text changes.

        Args:
            text (str): Current search text
        """
        self.search_changed.emit(text)

    def _on_filter_changed(self):
        """Handle filter changes from any combo box."""
        # Build a dictionary of current filter values
        filters = {}

        for category, combo in self._filter_widgets.items():
            current_text = combo.currentText()

            # Only include non-"All" selections
            if current_text != "All":
                filters[category] = current_text

        # Update current filters
        self._current_filters = filters

        # Emit the signal with the updated filters
        self.filter_changed.emit(filters)

    def _toggle_filters(self, checked: bool):
        """
        Toggle the visibility of the filter section.

        Args:
            checked (bool): Whether the expand button is checked
        """
        if self._filter_frame:
            self._expanded = checked
            self._filter_frame.setVisible(checked)

            # Update icon
            if self._expand_button:
                expand_icon = (
                    QIcon(":/icons/chevron_up.svg")
                    if checked
                    else QIcon(":/icons/chevron_down.svg")
                )
                self._expand_button.setIcon(expand_icon)

            # Emit the signal
            self.filter_expanded.emit(checked)

    def search_text(self) -> str:
        """
        Get the current search text.

        Returns:
            str: Current search text
        """
        return self._search_field.text() if self._search_field else ""

    def set_search_text(self, text: str):
        """
        Set the search text.

        Args:
            text (str): New search text
        """
        if self._search_field:
            self._search_field.setText(text)

    def clear_search(self):
        """Clear the search field."""
        if self._search_field:
            self._search_field.clear()

    def current_filters(self) -> Dict[str, str]:
        """
        Get the current filter selections.

        Returns:
            Dict[str, str]: Dictionary of current filter values by category
        """
        return self._current_filters.copy()

    def set_filter(self, category: str, value: str):
        """
        Set a specific filter value.

        Args:
            category (str): Filter category
            value (str): Filter value to select
        """
        if category in self._filter_widgets:
            combo = self._filter_widgets[category]

            # Find the index of the value
            index = combo.findText(value)

            if index >= 0:
                combo.setCurrentIndex(index)

    def clear_filters(self):
        """Reset all filters to their default 'All' state."""
        for combo in self._filter_widgets.values():
            combo.setCurrentIndex(0)  # "All" is at index 0

    def is_expanded(self) -> bool:
        """
        Check if the filter section is expanded.

        Returns:
            bool: True if expanded, False otherwise
        """
        return self._expanded

    def set_expanded(self, expanded: bool):
        """
        Set the expanded state of the filter section.

        Args:
            expanded (bool): Whether the filter section should be expanded
        """
        if self._expand_button:
            self._expand_button.setChecked(expanded)
            self._toggle_filters(expanded)
