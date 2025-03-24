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
        except (AttributeError, Exception) as e:
            # Handle the case where the DataView structure might be different
            print(f"Error connecting DataView signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # We'll not add our own action buttons since the DataView already has them
        # in its ActionToolbar
        pass

    def refresh(self):
        """Refresh the data view."""
        if hasattr(self._data_view, "_update_view"):
            self._data_view._update_view()

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

    def enable_auto_update(self) -> None:
        """Enable automatic table updates on data changes."""
        if hasattr(self._data_view, "enable_auto_update"):
            self._data_view.enable_auto_update()

    def disable_auto_update(self) -> None:
        """Disable automatic table updates on data changes."""
        if hasattr(self._data_view, "disable_auto_update"):
            self._data_view.disable_auto_update()
