"""
Debug script for DataView display issues.

This script creates a minimal application to test whether the DataView
correctly displays data with TableStateManager integration.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer, Signal, Slot

# Add the parent directory to the path to import chestbuddy
sys.path.append(str(Path(__file__).parent.parent))

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.core.controllers.data_view_controller import DataViewController

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("debug_data_view.log", mode="w")],
)

logger = logging.getLogger("debug_data_view")


class DebugMainWindow(QMainWindow):
    """Main window for debugging the DataView display."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug DataView Display")
        self.resize(1000, 800)
        self.setup()

    def setup(self):
        """Set up the application components."""
        logger.info("=== Setting up debug application ===")

        # Create sample data
        logger.info("Creating sample data")
        data = pd.DataFrame(
            {
                "PLAYER": ["player1", "player2", "player3", "player4"],
                "CHEST": ["Gold", "Silver", "Bronze", "Platinum"],
                "SOURCE": ["daily", "weekly", "river", "race"],
                "SCORE": ["100", "200", "300", "400"],
                "CLAN": ["clan1", "clan2", "clan3", "clan4"],
            }
        )
        logger.info(f"Sample data created with shape: {data.shape}")

        # Create data model
        logger.info("Creating data model")
        self.data_model = ChestDataModel()
        self.data_model._data = data.copy()  # Directly set data to bypass signals

        # Don't call _init_status_dataframes, create empty status DataFrames manually
        row_count = len(data)
        self.data_model._validation_status = pd.DataFrame(index=range(row_count))
        self.data_model._correction_status = pd.DataFrame(index=range(row_count))

        # Manually add status columns for each data column
        for col in data.columns:
            # Set validation status
            self.data_model._validation_status[f"{col}_valid"] = True

            # Set correction status
            self.data_model._correction_status[f"{col}_corrected"] = False
            self.data_model._correction_status[f"{col}_original"] = data[col].astype(str)

        logger.info(f"Data model created, is_empty: {self.data_model.is_empty}")

        # Create table state manager
        logger.info("Creating TableStateManager")
        self.table_state_manager = TableStateManager(self.data_model)
        logger.info("TableStateManager created")

        # Create data view
        logger.info("Creating DataView")
        self.data_view = DataView(self.data_model)
        logger.info(f"DataView created with ID: {id(self.data_view)}")

        # Create data view adapter
        logger.info("Creating DataViewAdapter")
        self.data_view_adapter = DataViewAdapter(self.data_model)
        # For debugging purposes, we'll replace the adapter's internal data view with our instance
        # to ensure we're tracking the same object
        logger.info(
            f"Original DataViewAdapter's DataView ID: {id(self.data_view_adapter._data_view)}"
        )
        self.data_view_adapter._data_view = self.data_view
        logger.info(
            f"DataViewAdapter's DataView replaced with ID: {id(self.data_view_adapter._data_view)}"
        )

        # Set the table state manager
        logger.info("Setting TableStateManager on DataView")
        self.data_view.set_table_state_manager(self.table_state_manager)
        logger.info("TableStateManager set on DataView")

        logger.info("Setting TableStateManager on DataViewAdapter")
        self.data_view_adapter.set_table_state_manager(self.table_state_manager)
        logger.info("TableStateManager set on DataViewAdapter")

        # Create controller
        logger.info("Creating DataViewController")
        self.controller = DataViewController(self.data_model)
        logger.info("Setting view on controller")
        self.controller.set_view(self.data_view_adapter)
        logger.info("Setting controller on adapter")
        self.data_view_adapter.set_controller(self.controller)
        logger.info("Controller setup complete")

        # Set the central widget
        logger.info("Setting DataViewAdapter as central widget")
        self.setCentralWidget(self.data_view_adapter)
        logger.info("Central widget set")

        # Schedule actions for after UI is shown
        QTimer.singleShot(500, self.populate_table)
        QTimer.singleShot(1500, self.add_validation_states)
        QTimer.singleShot(2500, self.add_correction_states)
        QTimer.singleShot(3500, self.log_state)

    def populate_table(self):
        """Populate the table with data."""
        logger.info("Populating table...")

        # Check visibility of components
        logger.info(f"DataViewAdapter visible: {self.data_view_adapter.isVisible()}")
        logger.info(f"DataView visible: {self.data_view.isVisible()}")

        # Populate through adapter
        logger.info("Calling populate_view_content on DataViewAdapter")
        self.data_view_adapter.populate_view_content()
        logger.info("populate_view_content called")

        # Force an update
        logger.info("Requesting update on DataViewAdapter")
        self.data_view_adapter.request_update()
        logger.info("Update requested")

        # Log table model information
        if hasattr(self.data_view, "_table_model"):
            logger.info(f"DataView table model row count: {self.data_view._table_model.rowCount()}")
            logger.info(
                f"DataView table model column count: {self.data_view._table_model.columnCount()}"
            )
        else:
            logger.error("DataView does not have _table_model attribute")

    def add_validation_states(self):
        """Add validation states to cells."""
        logger.info("Adding validation states...")

        # Create validation status
        validation_status = pd.DataFrame(
            {
                "ROW_IDX": [0, 1, 2],
                "COL_IDX": [0, 1, 2],
                "STATUS": ["invalid", "invalid", "invalid"],
            }
        )

        # Update table state manager
        logger.info("Updating cell states from validation")
        self.table_state_manager.update_cell_states_from_validation(validation_status)
        logger.info("Cell states updated from validation")

        # Log states for debugging
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        logger.info(f"Invalid cells after validation: {invalid_cells}")

        # Emit validation changed signal to trigger view updates
        logger.info("Emitting validation_changed signal")
        self.data_model.validation_changed.emit(validation_status)
        logger.info("validation_changed signal emitted")

        # Force an update
        logger.info("Requesting update on DataViewAdapter")
        self.data_view_adapter.request_update()
        logger.info("Update requested")

    def add_correction_states(self):
        """Add correction states to cells."""
        logger.info("Adding correction states...")

        # Create correction status
        correction_status = {
            "corrected_cells": [(0, 0), (1, 1)],
            "original_values": {"(0, 0)": "player1", "(1, 1)": "Silver"},
            "new_values": {"(0, 0)": "Player1", "(1, 1)": "SILVER"},
        }

        # Update table state manager
        logger.info("Updating cell states from correction")
        self.table_state_manager.update_cell_states_from_correction(correction_status)
        logger.info("Cell states updated from correction")

        # Log states for debugging
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)
        logger.info(f"Corrected cells after correction: {corrected_cells}")

        # Emit correction applied signal to trigger view updates
        logger.info("Emitting correction_applied signal")
        self.data_model.correction_applied.emit(correction_status)
        logger.info("correction_applied signal emitted")

        # Force an update
        logger.info("Requesting update on DataViewAdapter")
        self.data_view_adapter.request_update()
        logger.info("Update requested")

        # Force cell highlighting update
        logger.info("Calling update_cell_highlighting_from_state on DataView")
        self.data_view.update_cell_highlighting_from_state()
        logger.info("update_cell_highlighting_from_state called")

    def log_state(self):
        """Log the current state of the application for debugging."""
        logger.info("=== Logging application state ===")

        # Check DataView properties
        logger.info(f"DataView visible: {self.data_view.isVisible()}")

        # Check if the table is populated
        if hasattr(self.data_view, "_table_model"):
            logger.info(f"DataView table model row count: {self.data_view._table_model.rowCount()}")
            logger.info(
                f"DataView table model column count: {self.data_view._table_model.columnCount()}"
            )
        else:
            logger.error("DataView does not have _table_model attribute")

        # Check TableView properties
        if hasattr(self.data_view, "_table_view"):
            logger.info(f"DataView table view visible: {self.data_view._table_view.isVisible()}")
        else:
            logger.error("DataView does not have _table_view attribute")

        # Check DataViewAdapter properties
        logger.info(f"DataViewAdapter visible: {self.data_view_adapter.isVisible()}")
        logger.info(f"DataViewAdapter content size: {self.data_view_adapter.size()}")

        # Check data model properties
        logger.info(f"Data model empty: {self.data_model.is_empty}")
        logger.info(f"Data model row count: {self.data_model.row_count}")

        # Check table state manager
        logger.info(
            f"TableStateManager cell states count: {len(self.table_state_manager._cell_states)}"
        )
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)
        logger.info(f"Invalid cells: {invalid_cells}")
        logger.info(f"Corrected cells: {corrected_cells}")

        # Check the controller
        logger.info(f"Controller view reference ID: {id(self.controller._view)}")

        # Check highlighting
        self.check_highlighting()

    def check_highlighting(self):
        """Check if cell highlighting is working properly."""
        logger.info("=== Checking cell highlighting ===")

        # Verify _highlight_cell method in DataView
        if hasattr(self.data_view, "_highlight_cell"):
            logger.info("DataView has _highlight_cell method")

            # Create a test color
            from PySide6.QtGui import QColor

            test_color = QColor(255, 0, 0)  # Bright red

            # Create a mock for the highlight_cell method to track calls
            original_highlight_cell = self.data_view._highlight_cell
            calls = []

            def mock_highlight_cell(row, col, color):
                calls.append((row, col, color.name()))
                return original_highlight_cell(row, col, color)

            self.data_view._highlight_cell = mock_highlight_cell

            # Try highlighting some cells
            self.data_view._highlight_cell(0, 0, test_color)
            self.data_view._highlight_cell(1, 1, test_color)

            # Log the calls
            logger.info(f"highlight_cell calls: {calls}")

            # Restore the original method
            self.data_view._highlight_cell = original_highlight_cell
        else:
            logger.error("DataView does not have _highlight_cell method")


def main():
    """Main entry point for the debug application."""
    app = QApplication(sys.argv)
    window = DebugMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
