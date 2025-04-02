"""
Minimal test script for DataView and TableStateManager.

This script creates a minimal application with only the DataView and TableStateManager
to test table display and cell highlighting.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer, Signal, Slot, Qt, QMetaObject, QObject, QEvent, QPointF
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem

# Add the parent directory to the path to import chestbuddy
sys.path.append(str(Path(__file__).parent.parent))

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.ui.data_view import DataView

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("minimal_data_view_test.log", mode="w")],
)

logger = logging.getLogger("minimal_data_view_test")

# Monkey patch QObject to track signal connections
original_connect = QObject.connect


def connect_with_logging(self, signal, slot):
    logger.debug(
        f"SIGNAL CONNECTION: {self.__class__.__name__}.{signal.__name__} -> {slot.__name__ if hasattr(slot, '__name__') else slot}"
    )
    return original_connect(self, signal, slot)


QObject.connect = connect_with_logging


# Create Event Filter to track events
class EventTracker(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracked_events = {}

    def eventFilter(self, watched, event):
        event_type = event.type()
        event_name = str(event_type).split(".")[-1]
        if event_name not in self.tracked_events:
            self.tracked_events[event_name] = 0
        self.tracked_events[event_name] += 1

        # Log specific events we're interested in
        if event_type == QEvent.Paint:
            logger.debug(f"Paint event on {watched.__class__.__name__}")
        elif event_type == QEvent.UpdateRequest:
            logger.debug(f"UpdateRequest event on {watched.__class__.__name__}")
        elif event_type == QEvent.UpdateLater:
            logger.debug(f"UpdateLater event on {watched.__class__.__name__}")

        return super().eventFilter(watched, event)


class MinimalTestWindow(QMainWindow):
    """Minimal test window with only DataView and TableStateManager."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal DataView Test")
        self.resize(1000, 800)

        # Create main widget and layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.setup()

    def setup(self):
        """Set up the test."""
        logger.info("=== Setting up minimal test ===")

        # Create sample data
        logger.info("Creating sample data")
        self.data = pd.DataFrame(
            {
                "PLAYER": ["player1", "player2", "player3", "player4"],
                "CHEST": ["Gold", "Silver", "Bronze", "Platinum"],
                "SOURCE": ["daily", "weekly", "river", "race"],
                "SCORE": ["100", "200", "300", "400"],
                "CLAN": ["clan1", "clan2", "clan3", "clan4"],
            }
        )
        logger.info(f"Sample data created with shape: {self.data.shape}")

        # Create data model
        logger.info("Creating data model")
        self.data_model = ChestDataModel()
        # Directly set data to bypass signals
        self.data_model._data = self.data.copy()

        # Manually create status dataframes
        row_count = len(self.data)
        self.data_model._validation_status = pd.DataFrame(index=range(row_count))
        self.data_model._correction_status = pd.DataFrame(index=range(row_count))

        # Add status columns
        for col in self.data.columns:
            self.data_model._validation_status[f"{col}_valid"] = True
            self.data_model._correction_status[f"{col}_corrected"] = False
            self.data_model._correction_status[f"{col}_original"] = self.data[col].astype(str)

        logger.info(f"Data model created, is_empty: {self.data_model.is_empty}")

        # Create table state manager
        logger.info("Creating TableStateManager")
        self.table_state_manager = TableStateManager(self.data_model)
        logger.info("TableStateManager created")

        # Create data view
        logger.info("Creating DataView")
        self.data_view = DataView(self.data_model)
        logger.info(f"DataView created with ID: {id(self.data_view)}")

        # Set the table state manager
        logger.info("Setting TableStateManager on DataView")
        self.data_view.set_table_state_manager(self.table_state_manager)
        logger.info("TableStateManager set on DataView")

        # Save a reference to the original highlight_cell method for debugging
        self.original_highlight_cell = self.data_view._highlight_cell

        # Create a button to test direct cell highlighting
        self.test_highlight_button = QPushButton("Test Highlight Cell")
        self.test_highlight_button.clicked.connect(self.test_direct_highlighting)
        self.layout.addWidget(self.test_highlight_button)

        # Create a button to monitor model changes
        self.test_model_button = QPushButton("Test Model Changes")
        self.test_model_button.clicked.connect(self.test_model_changes)
        self.layout.addWidget(self.test_model_button)

        # Status label
        self.status_label = QLabel("Status: Ready")
        self.layout.addWidget(self.status_label)

        # Add data view to layout
        logger.info("Adding DataView to layout")
        self.layout.addWidget(self.data_view)
        logger.info("DataView added to layout")

        # Set up event tracking
        self.event_tracker = EventTracker(self)
        self.data_view.installEventFilter(self.event_tracker)
        if hasattr(self.data_view, "_table_view"):
            self.data_view._table_view.installEventFilter(self.event_tracker)
            self.data_view._table_view.viewport().installEventFilter(self.event_tracker)

        # Monkey patch the data model's _notify_change method to track when it's called
        original_notify_change = self.data_model._notify_change

        def notify_change_with_logging(model, *args, **kwargs):
            print("ChestDataModel._notify_change called")
            logger.debug("ChestDataModel._notify_change called with args: {args}, kwargs: {kwargs}")
            return original_notify_change(model, *args, **kwargs)

        self.data_model._notify_change = lambda *args, **kwargs: notify_change_with_logging(
            self.data_model, *args, **kwargs
        )

        # Monkey patch DataView's _on_data_changed method to track when it's called
        original_on_data_changed = self.data_view._on_data_changed

        def on_data_changed_with_logging(view, data_state):
            print("DataView received _on_data_changed. DataState:", data_state)
            logger.debug(f"DataView received _on_data_changed. DataState: {data_state}")
            return original_on_data_changed(view, data_state)

        self.data_view._on_data_changed = lambda data_state: on_data_changed_with_logging(
            self.data_view, data_state
        )

        # Connect to data_changed signal from data model
        self.data_model.data_changed.connect(lambda ds: print("data_changed signal emitted."))

        # Schedule test actions with a timer
        QTimer.singleShot(500, self.run_test_sequence)

    def run_test_sequence(self):
        """Run a sequence of tests with delays between them."""
        # Populate the table initially
        logger.info("Populating table...")
        logger.info("Calling populate_table on DataView")
        self.data_view.populate_table()
        logger.info("populate_table called")
        logger.info(f"DataView table model row count: {self.data_view._table_model.rowCount()}")
        logger.info(
            f"DataView table model column count: {self.data_view._table_model.columnCount()}"
        )

        # Schedule the validation test after 1 second
        QTimer.singleShot(1000, self.add_validation_states)

        # Schedule the correction test after 2 seconds
        QTimer.singleShot(2000, self.add_correction_states)

        # Schedule log state after 3 seconds
        QTimer.singleShot(3000, self.log_application_state)

    def add_validation_states(self):
        """Add some validation states to test highlighting."""
        logger.info("Adding validation states...")

        # Create a validation status DataFrame with invalid cells
        validation_df = pd.DataFrame(
            [
                {"ROW_IDX": 0, "COL_IDX": 0, "STATUS": "invalid"},
                {"ROW_IDX": 1, "COL_IDX": 1, "STATUS": "invalid"},
                {"ROW_IDX": 2, "COL_IDX": 2, "STATUS": "invalid"},
            ]
        )

        # Update cell states from validation
        logger.info("Updating cell states from validation")
        self.table_state_manager.update_cell_states_from_validation(validation_df)

        # Verify that cells were highlighted
        QTimer.singleShot(500, self.check_validation_highlighting)

    def check_validation_highlighting(self):
        """Check if validation highlighting was applied correctly."""
        # Log current cell states in TableStateManager
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        logger.info(f"TableStateManager invalid cells: {invalid_cells}")

        # Check if the cells are actually highlighted in the UI
        table_view = self.data_view._table_view
        model = self.data_view._table_model

        for row, col in invalid_cells:
            item = model.item(row, col)
            if item:
                bg_role = item.data(Qt.BackgroundRole)
                logger.info(f"Cell ({row}, {col}) background role: {bg_role}")

                if not bg_role:
                    logger.warning(f"Cell ({row}, {col}) is not highlighted!")
            else:
                logger.warning(f"Item not found for cell ({row}, {col})")

    def add_correction_states(self):
        """Add some correction states to test highlighting."""
        logger.info("Adding correction states...")

        # Create a correction status with corrected cells
        correction_status = {
            "corrected_cells": [
                {"row": 0, "col": 2, "old_value": "daily", "new_value": "weekly"},
                {"row": 1, "col": 3, "old_value": "25", "new_value": "30"},
            ]
        }

        # Update cell states from correction
        logger.info("Updating cell states from correction")
        self.table_state_manager.update_cell_states_from_correction(correction_status)

    def log_application_state(self):
        """Log the current state of the application."""
        logger.info("=== Application State ===")

        # Log model state
        logger.info(f"Data model data shape: {self.data_model.get_data().shape}")
        logger.info(
            f"Data model validation status shape: {self.data_model._validation_status.shape}"
        )
        logger.info(
            f"Data model correction status shape: {self.data_model._correction_status.shape}"
        )

        # Log table state manager state
        logger.info(
            f"TableStateManager cell states count: {len(self.table_state_manager._cell_states)}"
        )

        # Log invalid and corrected cells
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)
        logger.info(f"Invalid cells: {invalid_cells}")
        logger.info(f"Corrected cells: {corrected_cells}")

        # Log event counts
        logger.info(f"Event counts: {self.event_tracker.tracked_events}")

    def test_direct_highlighting(self):
        """Test direct highlighting of cells without using TableStateManager."""
        logger.info("=== Testing Direct Cell Highlighting ===")

        # Directly highlight some cells with different colors
        red = QColor(255, 0, 0)
        green = QColor(0, 255, 0)
        blue = QColor(0, 0, 255)

        # Test highlighting specific cells
        success_count = 0
        if self.original_highlight_cell(0, 0, red):
            success_count += 1
        if self.original_highlight_cell(1, 1, green):
            success_count += 1
        if self.original_highlight_cell(2, 2, blue):
            success_count += 1

        logger.info(f"Direct highlighting succeeded for {success_count} of 3 cells")
        self.status_label.setText(f"Direct highlighting: {success_count}/3 cells")

        # Force update of the view
        if hasattr(self.data_view, "_table_view") and self.data_view._table_view:
            self.data_view._table_view.viewport().update()
            logger.info("Forced viewport update")

    def test_model_changes(self):
        """Test how model changes affect the DataView."""
        logger.info("=== Testing Model Changes ===")

        # Make a simple change to the data model
        original_data = self.data_model.get_data().copy()
        new_data = original_data.copy()
        new_data.loc[0, "PLAYER"] = "updated_player1"

        # Set the new data
        logger.info("Setting updated data in model")
        self.data_model.set_data(new_data)

        # Check if the change was reflected in the view
        QTimer.singleShot(500, self.check_model_changes)

    def check_model_changes(self):
        """Check if model changes were reflected in the view."""
        model = self.data_view._table_model

        # Check the value in the view's model
        item = model.item(0, 0)
        if item:
            value = item.data(Qt.DisplayRole)
            logger.info(f"Value in view model at (0, 0): {value}")

            if value == "updated_player1":
                logger.info("Model change was correctly reflected in view")
                self.status_label.setText("Model change test: PASSED")
            else:
                logger.warning(
                    f"Model change not reflected in view. Expected 'updated_player1', got '{value}'"
                )
                self.status_label.setText("Model change test: FAILED")
        else:
            logger.warning("Item not found at (0, 0)")
            self.status_label.setText("Model change test: FAILED (item not found)")


def main():
    """Main entry point for the test application."""
    app = QApplication(sys.argv)
    window = MinimalTestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
