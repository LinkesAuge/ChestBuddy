"""
data_view_adapter.py

Description: Adapter to integrate the existing DataView with the new BaseView structure
Usage:
    data_view = DataViewAdapter(data_model)
    main_window.add_view(data_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout
import time

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

    # Add signals for data operations
    import_requested = Signal()
    export_requested = Signal()

    def __init__(self, data_model: ChestDataModel, parent: QWidget = None):
        """
        Initialize the DataViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to display
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        # Store references
        self._data_model = data_model

        # State tracking to prevent unnecessary refreshes
        self._last_data_state = {
            "row_count": 0,
            "column_count": 0,
            "data_hash": self._data_model.data_hash,
            "last_update_time": 0,
        }

        # Flag to track if the table needs population when shown
        self._needs_population = False

        # Create the underlying DataView
        self._data_view = DataView(data_model)

        # Initialize the base view
        super().__init__("Data View", parent)
        self.setObjectName("DataViewAdapter")

    @property
    def needs_population(self) -> bool:
        """Get whether the view needs table population when shown."""
        return self._needs_population

    @needs_population.setter
    def needs_population(self, value: bool) -> None:
        """Set whether the view needs table population when shown."""
        self._needs_population = value

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

        # Connect DataView's action buttons to our signals
        try:
            # Get action toolbar from DataView
            import_button = self._data_view._action_toolbar.get_button_by_name("import")
            export_button = self._data_view._action_toolbar.get_button_by_name("export")

            if import_button:
                import_button.clicked.disconnect()  # Disconnect any existing connections
                import_button.clicked.connect(self.import_requested.emit)

            if export_button:
                export_button.clicked.disconnect()  # Disconnect any existing connections
                export_button.clicked.connect(self.export_requested.emit)

            # Connect data model signals to update our state tracking
            self._data_model.data_changed.connect(self._on_data_changed)
        except (AttributeError, Exception) as e:
            # Handle the case where the DataView structure might be different
            print(f"Error connecting DataView signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # We'll not add our own action buttons since the DataView already has them
        # in its ActionToolbar
        pass

    def _on_data_changed(self):
        """Handle data model changes to update our state tracking."""
        # Update our state tracking
        self._update_data_state()

    def _update_data_state(self):
        """Update our state tracking with the current data model state."""
        if not self._data_model.is_empty:
            self._last_data_state = {
                "row_count": len(self._data_model.data),
                "column_count": len(self._data_model.column_names),
                "data_hash": self._data_model.data_hash,
                "last_update_time": int(time.time() * 1000),
            }
        else:
            self._last_data_state = {
                "row_count": 0,
                "column_count": 0,
                "data_hash": self._data_model.data_hash,
                "last_update_time": int(time.time() * 1000),
            }

    def needs_refresh(self) -> bool:
        """
        Check if the view needs refreshing based on data state.

        Returns:
            bool: True if the view needs to be refreshed, False otherwise
        """
        # Check if data has changed by comparing with our tracked state
        current_state = {"row_count": 0, "column_count": 0, "data_hash": ""}

        if not self._data_model.is_empty:
            current_state = {
                "row_count": len(self._data_model.data),
                "column_count": len(self._data_model.column_names),
                "data_hash": self._data_model.data_hash,
            }

        # Check for dimension changes or data content changes via hash
        dimensions_changed = (
            current_state["row_count"] != self._last_data_state["row_count"]
            or current_state["column_count"] != self._last_data_state["column_count"]
        )

        content_changed = current_state["data_hash"] != self._last_data_state.get("data_hash", "")

        needs_refresh = dimensions_changed or content_changed

        if needs_refresh:
            print(
                f"DataViewAdapter.needs_refresh: TRUE - Data changed. Old: {self._last_data_state}, New: {current_state}"
            )
        else:
            print(f"DataViewAdapter.needs_refresh: FALSE - No data changes detected")

        return needs_refresh

    def refresh(self):
        """
        Refresh the data view only if the data has changed since the last refresh.
        This prevents unnecessary table repopulation when switching views.
        """
        # Use the needs_refresh method to check if we need to update
        if self.needs_refresh():
            print(f"DataViewAdapter.refresh: Data changed, updating view.")
            if hasattr(self._data_view, "_update_view"):
                self._data_view._update_view()

            # Update our state tracking
            self._update_data_state()
        else:
            print("DataViewAdapter.refresh: No data changes, skipping view update")

    def populate_table(self) -> None:
        """
        Explicitly populate the table with current data.
        This should be called once after data loading is complete.
        """
        if hasattr(self._data_view, "populate_table"):
            self._data_view.populate_table()
        else:
            # Fallback to update_view if populate_table doesn't exist
            self._data_view._update_view()

        # Update our state tracking
        self._update_data_state()

    def enable_auto_update(self) -> None:
        """Enable automatic table updates on data changes."""
        if hasattr(self._data_view, "enable_auto_update"):
            self._data_view.enable_auto_update()

    def disable_auto_update(self) -> None:
        """Disable automatic table updates on data changes."""
        if hasattr(self._data_view, "disable_auto_update"):
            self._data_view.disable_auto_update()
