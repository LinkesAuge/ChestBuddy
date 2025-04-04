"""
correction_view.py

Description: Main correction view for the ChestBuddy application
Usage:
    correction_view = CorrectionView(data_model, correction_service)
    main_window.add_view(correction_view)
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
)

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.views.correction_rule_view import CorrectionRuleView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionView(UpdatableView):
    """
    Main correction view for the ChestBuddy application.

    This view provides an interface for users to manage correction rules
    and apply them to the data.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        correction_service (CorrectionService): The service for data correction
        _rule_view (CorrectionRuleView): The view for managing correction rules
        _controller (DataViewController): The controller for data view operations
        _correction_controller (CorrectionController): The controller for correction operations

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Uses CorrectionRuleView for managing correction rules
        - Provides correction functionality through the correction controller
        - Uses DataViewController for data view operations
    """

    # Define signals (same as the adapter for compatibility)
    correction_requested = Signal(str)  # Strategy name
    history_requested = Signal()

    def __init__(
        self,
        data_model: ChestDataModel,
        correction_service: CorrectionService,
        parent: Optional[QWidget] = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the CorrectionView.

        Args:
            data_model (ChestDataModel): The data model for correction
            correction_service (CorrectionService): The correction service
            parent (Optional[QWidget]): Parent widget
            debug_mode (bool): Enable debug mode for signal connections
        """
        # Store references
        self._data_model = data_model
        self._correction_service = correction_service
        self._controller = None
        self._correction_controller = None
        self._rule_view = None  # Initialize to None, will create when correction_controller is set
        self._rule_view_placeholder = None  # Placeholder widget until rule view is created

        # Initialize the base view
        super().__init__("Data Correction", parent, debug_mode=debug_mode)
        self.setObjectName("CorrectionView")

        # Initialize components after the base view is set up
        self._initialize_components()

    def _initialize_components(self):
        """Initialize view-specific components after the base UI is set up."""
        # Create a placeholder widget instead of the actual CorrectionRuleView
        # We'll replace this with the real CorrectionRuleView when the correction_controller is set
        self._rule_view_placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self._rule_view_placeholder)
        placeholder_layout.addWidget(QLabel("Initializing correction rules view..."))

        # Add the placeholder to the content layout
        self.get_content_layout().addWidget(self._rule_view_placeholder)

        logger.debug("CorrectionView placeholder initialized")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this view.

        Args:
            controller: The DataViewController instance to use
        """
        self._controller = controller

        # Connect controller signals
        if self._controller:
            self._controller.correction_started.connect(self._on_correction_started)
            self._controller.correction_completed.connect(self._on_correction_completed)
            self._controller.correction_error.connect(self._on_correction_error)
            self._controller.operation_error.connect(self._on_operation_error)

            logger.info("CorrectionView: Controller set and signals connected")

    def set_correction_controller(self, controller: CorrectionController) -> None:
        """
        Set the correction controller for this view.

        Args:
            controller: The CorrectionController instance to use
        """
        self._correction_controller = controller

        # Set the view in the controller
        if self._correction_controller:
            self._correction_controller.set_view(self)

            # Now that we have the correction controller, create the real CorrectionRuleView
            # Replace the placeholder with the actual rule view
            if self._rule_view_placeholder:
                # Remove the placeholder from layout
                self.get_content_layout().removeWidget(self._rule_view_placeholder)
                self._rule_view_placeholder.hide()  # Hide to prevent visual glitches
                self._rule_view_placeholder.deleteLater()  # Schedule for deletion
                self._rule_view_placeholder = None

            # Create the actual CorrectionRuleView with the controller
            self._rule_view = CorrectionRuleView(
                controller=self._correction_controller,
                parent=self,  # Explicitly set parent to self (CorrectionView)
            )

            # Add the rule view to layout
            self.get_content_layout().addWidget(self._rule_view)

            # Connect the rule view to the correction controller
            if self._rule_view:
                self._rule_view.apply_corrections_requested.connect(
                    lambda recursive, only_invalid: self._correction_controller.apply_corrections(
                        only_invalid=only_invalid, recursive=recursive, selected_only=False
                    )
                )
                self._rule_view.rule_added.connect(self._correction_controller.add_rule)
                self._rule_view.rule_edited.connect(self._correction_controller.update_rule)
                self._rule_view.rule_deleted.connect(self._correction_controller.delete_rule)

            # Connect correction controller signals to this view
            self._correction_controller.correction_completed.connect(self._on_corrections_completed)
            self._correction_controller.correction_error.connect(self._on_correction_error)

            logger.info("CorrectionView: Correction controller set and rule view created")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Don't add the rule view here - it will be added in _initialize_components
        # and/or set_correction_controller when the controller is available

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect header action buttons
        self.header_action_clicked.connect(self._on_action_clicked)

        # Connect to data model if available
        if hasattr(self._data_model, "data_changed") and hasattr(self, "request_update"):
            try:
                self._signal_manager.connect(
                    self._data_model, "data_changed", self, "request_update"
                )
                logger.debug("Connected data_model.data_changed to CorrectionView.request_update")
            except Exception as e:
                logger.error(f"Error connecting data model signals: {e}")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common correction operations
        self.add_header_action("apply", "Apply Corrections")
        self.add_header_action("history", "View History")
        self.add_header_action("refresh", "Refresh")

    def _update_view_content(self, data=None) -> None:
        """Update the view content based on data from the controllers.

        Args:
            data: Optional data to update the view with (ignored in this implementation)
        """
        try:
            self._show_status_message("Updating correction rules...")
            if self._correction_controller:
                self._show_placeholder(False)
                if not self._rule_view:
                    self._initialize_rule_view()
                self._refresh_view_content()
            else:
                self._show_placeholder(True)
            self._show_status_message("Correction rules updated")
        except Exception as e:
            logger.error(f"Error updating CorrectionView: {e}")
            # Still try to show a status message even if the update failed
            try:
                self._show_status_message(f"Error updating rules: {str(e)}")
            except Exception:
                pass

    def _show_status_message(self, message: str) -> None:
        """
        Display a status message for the view.

        Args:
            message (str): The message to display
        """
        if hasattr(self, "statusBar") and callable(self.statusBar):
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(message, 3000)  # Show for 3 seconds
        # Log the message as a fallback
        logger.debug(f"CorrectionView status: {message}")

    def _show_placeholder(self, show: bool) -> None:
        """
        Show or hide the placeholder message when correction controller is not available.
        When showing, display a complete UI mockup based on our correction feature design.

        Args:
            show (bool): Whether to show the placeholder
        """
        if not self._rule_view_placeholder and show:
            # Create a comprehensive placeholder with the complete UI structure
            self._rule_view_placeholder = QWidget()
            placeholder_layout = QVBoxLayout(self._rule_view_placeholder)
            placeholder_layout.setContentsMargins(10, 10, 10, 10)
            placeholder_layout.setSpacing(10)

            # 1. Filter Controls Section
            filter_group = QWidget()
            filter_layout = QHBoxLayout(filter_group)
            filter_layout.setContentsMargins(0, 0, 0, 0)

            filter_layout.addWidget(QLabel("Category:"))
            filter_layout.addWidget(
                self._create_disabled_combobox(["All", "general", "player", "chest_type", "source"])
            )

            filter_layout.addWidget(QLabel("Status:"))
            filter_layout.addWidget(self._create_disabled_combobox(["All", "enabled", "disabled"]))

            filter_layout.addWidget(QLabel("Search:"))
            search_box = self._create_disabled_line_edit()
            filter_layout.addWidget(search_box)

            placeholder_layout.addWidget(filter_group)

            # 2. Rules Table
            rules_table = QTableWidget(5, 6)  # 5 rows, 6 columns
            rules_table.setHorizontalHeaderLabels(["Order", "From", "To", "Category", "Status", ""])
            rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            rules_table.setEnabled(False)

            # Sample data for the table
            sample_data = [
                ["1", "Cheist", "Chest", "general", "enabled", "⋮"],
                ["2", "PLyer", "Player", "player", "enabled", "⋮"],
                ["3", "Wepon", "Weapon", "chest", "enabled", "⋮"],
                ["4", "Sorce", "Source", "source", "disabled", "⋮"],
                ["5", "Chst", "Chest", "general", "enabled", "⋮"],
            ]

            for row, row_data in enumerate(sample_data):
                for col, text in enumerate(row_data):
                    item = QTableWidgetItem(text)
                    rules_table.setItem(row, col, item)

            placeholder_layout.addWidget(rules_table)

            # 3. Rule Controls
            controls_group = QWidget()
            controls_layout = QHBoxLayout(controls_group)
            controls_layout.setContentsMargins(0, 0, 0, 0)

            for button_text in ["Add", "Edit", "Delete", "Move ▲", "Move ▼", "Toggle Status"]:
                button = self._create_disabled_button(button_text)
                controls_layout.addWidget(button)

            placeholder_layout.addWidget(controls_group)

            # 4. Settings Panel
            settings_group = QGroupBox("Settings Panel")
            settings_layout = QVBoxLayout(settings_group)

            for setting in [
                "Auto-correct after validation",
                "Correct only invalid entries",
                "Auto-enable imported rules",
                "Export only enabled rules",
            ]:
                checkbox = QCheckBox(setting)
                checkbox.setEnabled(False)
                checkbox.setChecked(True)  # Default to checked
                settings_layout.addWidget(checkbox)

            placeholder_layout.addWidget(settings_group)

            # Add note about controller initialization
            info_label = QLabel(
                "This is a preview of the correction rules interface. "
                "Please initialize the correction controller to enable functionality."
            )
            info_label.setStyleSheet("color: #1E3A5F; font-weight: bold;")
            info_label.setAlignment(Qt.AlignCenter)
            placeholder_layout.addWidget(info_label)

            # Add the placeholder to the content layout
            self.get_content_layout().addWidget(self._rule_view_placeholder)
            logger.debug("CorrectionView comprehensive UI placeholder shown")
        elif self._rule_view_placeholder and not show:
            # Hide placeholder
            self.get_content_layout().removeWidget(self._rule_view_placeholder)
            self._rule_view_placeholder.hide()
            self._rule_view_placeholder.deleteLater()
            self._rule_view_placeholder = None
            logger.debug("CorrectionView placeholder hidden")

    def _create_disabled_combobox(self, items):
        """Create a disabled combobox with the given items."""
        combobox = QComboBox()
        for item in items:
            combobox.addItem(item)
        combobox.setEnabled(False)
        return combobox

    def _create_disabled_line_edit(self):
        """Create a disabled line edit."""
        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        line_edit.setPlaceholderText("Search terms...")
        return line_edit

    def _create_disabled_button(self, text):
        """Create a disabled button with the given text."""
        button = QPushButton(text)
        button.setEnabled(False)
        return button

    def _initialize_rule_view(self) -> None:
        """
        Initialize the correction rule view if it doesn't exist yet.
        This is called when update_view_content is called and the rule view hasn't been created.
        """
        if self._rule_view is None and self._correction_controller is not None:
            # Create the rule view with the controller
            self._rule_view = CorrectionRuleView(
                controller=self._correction_controller,
                parent=self,
            )

            # Add the rule view to layout
            self.get_content_layout().addWidget(self._rule_view)

            # Connect the rule view to the correction controller
            self._rule_view.apply_corrections_requested.connect(
                lambda recursive, only_invalid: self._correction_controller.apply_corrections(
                    only_invalid=only_invalid, recursive=recursive, selected_only=False
                )
            )
            self._rule_view.rule_added.connect(self._correction_controller.add_rule)
            self._rule_view.rule_edited.connect(self._correction_controller.update_rule)
            self._rule_view.rule_deleted.connect(self._correction_controller.delete_rule)

            logger.debug("CorrectionView: Rule view initialized")

    def _refresh_view_content(self) -> None:
        """Refresh the view content without changing the underlying data."""
        # Refresh the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "refresh")
            and callable(getattr(self._rule_view, "refresh", None))
        ):
            self._rule_view.refresh()

        logger.debug("CorrectionView: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        # Initial population of the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "populate")
            and callable(getattr(self._rule_view, "populate", None))
        ):
            self._rule_view.populate()

        logger.debug("CorrectionView: View content populated")

    def _reset_view_content(self) -> None:
        """Reset the view content to its initial state."""
        # Reset the rule view
        if (
            self._rule_view
            and hasattr(self._rule_view, "reset")
            and callable(getattr(self._rule_view, "reset", None))
        ):
            self._rule_view.reset()

        logger.debug("CorrectionView: View content reset")

    @Slot(str)
    def _on_action_clicked(self, action_id: str) -> None:
        """
        Handle action button clicks.

        Args:
            action_id: The ID of the clicked action
        """
        if action_id == "apply":
            self._on_apply_clicked()
        elif action_id == "history":
            self._on_history_clicked()
        elif action_id == "refresh":
            self.refresh()

    def _on_apply_clicked(self) -> None:
        """Handle apply corrections button click."""
        # Emit signal for tracking
        self.correction_requested.emit("rules")

        # Apply corrections using the correction controller
        if self._correction_controller:
            self._correction_controller.apply_corrections(recursive=False, selected_only=False)
        else:
            logger.error("Cannot apply corrections: Correction controller not available")

    def _on_history_clicked(self) -> None:
        """Handle view history button click."""
        # Emit signal for tracking
        self.history_requested.emit()

        # Show correction history using the correction controller
        if self._correction_controller:
            history = self._correction_controller.get_history()
            # TODO: Display history in a dialog or update the view to show history
        else:
            logger.error("Cannot view history: Correction controller not available")

    @Slot(str)
    def _on_correction_started(self, strategy_name: str) -> None:
        """
        Handle correction started event.

        Args:
            strategy_name: The strategy being applied
        """
        # Update UI to show correction in progress
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Applying {strategy_name} correction...")

    @Slot(str, int)
    def _on_correction_completed(self, strategy_name: str, affected_rows: int) -> None:
        """
        Handle correction completed event.

        Args:
            strategy_name: The strategy that was applied
            affected_rows: Number of rows affected by the correction
        """
        # Update UI to show correction results
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Correction complete: {affected_rows} rows affected")

        # Refresh the view to show the latest results
        self.refresh()

    @Slot(object)
    def _on_corrections_completed(self, stats):
        """
        Handle completion of corrections from the correction controller.

        Args:
            stats: Statistics about applied corrections
        """
        # Convert stats to a dict if it's not already
        affected_rows = stats.get("affected_rows", 0) if isinstance(stats, dict) else 0

        if affected_rows > 0:
            self._show_status_message(f"Corrections completed: {affected_rows} rows affected")
        else:
            self._show_status_message("Corrections completed: No changes were needed")

        # Refresh data view if needed
        if hasattr(self._controller, "refresh_data_view"):
            self._controller.refresh_data_view()

        # Also update this view
        self.refresh()

    @Slot(str)
    def _on_correction_error(self, error_msg: str) -> None:
        """
        Handle correction error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Correction error: {error_msg}")

    @Slot(str)
    def _on_operation_error(self, error_msg: str) -> None:
        """
        Handle operation error event.

        Args:
            error_msg: The error message
        """
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Error: {error_msg}")
