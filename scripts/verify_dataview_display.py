"""
Verification script for DataView display issues.

This script runs a minimal version of the application focusing on DataView
to verify that it displays properly with all UI elements.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, Qt

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
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("verify_dataview_display.log", mode="w"),
    ],
)

logger = logging.getLogger("verify_dataview_display")


class VerificationWindow(QMainWindow):
    """Main window for verifying the DataView display."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DataView Verification")
        self.resize(1200, 800)

        # Create a central widget with layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Setup components
        logger.info("=== Setting up verification components ===")
        self.setup_components()

        # Schedule tests
        QTimer.singleShot(1000, self.verify_initial_display)
        QTimer.singleShot(2000, self.test_validation_highlighting)
        QTimer.singleShot(3000, self.test_correction_highlighting)
        QTimer.singleShot(4000, self.log_verification_results)

    def setup_components(self):
        """Set up all the components needed for verification."""
        # Create sample data
        logger.info("Creating sample data")
        self.sample_data = pd.DataFrame(
            {
                "PLAYER": ["player1", "player2", "player3", "player4"],
                "CHEST": ["wooden", "silver", "golden", "diamond"],
                "SOURCE": ["daily", "quest", "victory", "tournament"],
                "SCORE": [10, 25, 50, 100],
                "CLAN": ["clan1", "clan2", "clan1", "clan3"],
                "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            }
        )
        logger.info(f"Sample data created with shape: {self.sample_data.shape}")

        # Create data model
        logger.info("Creating ChestDataModel")
        self.data_model = ChestDataModel()

        # Directly set the data to the model
        logger.info("Setting data directly to model")
        self.data_model._data = self.sample_data.copy()

        # Create status dataframes manually
        logger.info("Creating status dataframes manually")
        row_count = len(self.sample_data)
        self.data_model._validation_status = pd.DataFrame(index=range(row_count))
        self.data_model._correction_status = pd.DataFrame(index=range(row_count))

        # Add status columns for each data column
        for col in self.data_model.EXPECTED_COLUMNS:
            # Set validation status
            self.data_model._validation_status[f"{col}_valid"] = True

            # Set correction status
            self.data_model._correction_status[f"{col}_corrected"] = False
            self.data_model._correction_status[f"{col}_original"] = self.sample_data[col].astype(
                str
            )

        # Update data hash
        self.data_model._update_data_hash()

        logger.info(f"Data model created with {self.data_model.row_count} rows")

        # Create TableStateManager
        logger.info("Creating TableStateManager")
        self.table_state_manager = TableStateManager(self.data_model)

        # Create direct DataView first (without adapter)
        logger.info("Creating DataView directly")
        self.data_view = DataView(self.data_model)
        logger.info(f"DataView created with ID: {id(self.data_view)}")

        # Set TableStateManager on DataView
        logger.info("Setting TableStateManager on DataView")
        self.data_view.set_table_state_manager(self.table_state_manager)

        # Add DataView to the layout
        logger.info("Adding DataView to layout")
        self.layout.addWidget(self.data_view)

        # Force DataView to populate
        logger.info("Populating DataView")
        self.data_view.populate_table()

        # Log setup completion
        logger.info("Component setup complete")

    def verify_initial_display(self):
        """Verify the initial display of the DataView."""
        logger.info("=== Verifying initial display ===")

        # Check if table view exists and is visible
        if hasattr(self.data_view, "_table_view"):
            logger.info(f"Table view exists, visible: {self.data_view._table_view.isVisible()}")
            logger.info(f"Table view dimensions: {self.data_view._table_view.size()}")
        else:
            logger.error("DataView does not have _table_view attribute")

        # Check if table model exists and has data
        if hasattr(self.data_view, "_table_model"):
            logger.info(f"Table model exists with {self.data_view._table_model.rowCount()} rows")
            logger.info(f"Table model columns: {self.data_view._table_model.columnCount()}")

            # Check first few cells to verify data
            for row in range(min(3, self.data_view._table_model.rowCount())):
                for col in range(min(3, self.data_view._table_model.columnCount())):
                    item = self.data_view._table_model.item(row, col)
                    if item:
                        logger.info(f"Cell ({row}, {col}) contains: {item.text()}")
                    else:
                        logger.warning(f"Cell ({row}, {col}) has no item")
        else:
            logger.error("DataView does not have _table_model attribute")

        # Check toolbar and filter controls
        logger.info(f"Action toolbar exists: {hasattr(self.data_view, '_action_toolbar')}")
        logger.info(f"Filter input exists: {hasattr(self.data_view, '_filter_text')}")
        logger.info(f"Column selector exists: {hasattr(self.data_view, '_filter_column')}")

        # Log visibility of key UI elements
        if hasattr(self.data_view, "_action_toolbar"):
            logger.info(f"Action toolbar visible: {self.data_view._action_toolbar.isVisible()}")

        if hasattr(self.data_view, "_filter_text"):
            logger.info(f"Filter text input visible: {self.data_view._filter_text.isVisible()}")

        if hasattr(self.data_view, "_color_legend"):
            logger.info(f"Color legend visible: {self.data_view._color_legend.isVisible()}")

    def test_validation_highlighting(self):
        """Test validation state highlighting."""
        logger.info("=== Testing validation highlighting ===")

        # Create validation status with invalid cells
        validation_status = pd.DataFrame(
            {
                "ROW_IDX": [0, 1, 2],
                "COL_IDX": [0, 1, 2],
                "STATUS": ["invalid", "invalid", "invalid"],
            }
        )

        # Update cell states through TableStateManager
        logger.info("Updating cell states from validation")
        self.table_state_manager.update_cell_states_from_validation(validation_status)

        # Verify states were set
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        logger.info(f"Invalid cells after update: {invalid_cells}")

        # Force UI update through DataView
        logger.info("Forcing DataView to update cell highlighting")
        self.data_view.update_cell_highlighting_from_state()

        # Check if cells have background color set
        logger.info("Checking if cells have background color set")
        self.check_cell_highlighting(invalid_cells)

    def test_correction_highlighting(self):
        """Test correction state highlighting."""
        logger.info("=== Testing correction highlighting ===")

        # Create correction status
        correction_status = {
            "corrected_cells": [(0, 1), (1, 2)],
            "original_values": {"(0, 1)": "wooden", "(1, 2)": "quest"},
            "new_values": {"(0, 1)": "Wood", "(1, 2)": "Quest"},
        }

        # Update cell states through TableStateManager
        logger.info("Updating cell states from correction")
        self.table_state_manager.update_cell_states_from_correction(correction_status)

        # Verify states were set
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)
        logger.info(f"Corrected cells after update: {corrected_cells}")

        # Force UI update through DataView
        logger.info("Forcing DataView to update cell highlighting")
        self.data_view.update_cell_highlighting_from_state()

        # Check if cells have background color set
        logger.info("Checking if cells have background color set")
        self.check_cell_highlighting(corrected_cells)

    def check_cell_highlighting(self, cells):
        """Check if specified cells have background color set."""
        if not hasattr(self.data_view, "_table_model"):
            logger.error("DataView does not have _table_model attribute")
            return

        model = self.data_view._table_model

        # Check each cell
        for row, col in cells:
            item = model.item(row, col)
            if item:
                bg_color = item.data(Qt.BackgroundRole)
                if bg_color:
                    logger.info(f"Cell ({row}, {col}) has background color: {bg_color}")
                else:
                    logger.warning(f"Cell ({row}, {col}) has no background color")
            else:
                logger.warning(f"Cell ({row}, {col}) has no item")

    def log_verification_results(self):
        """Log verification results and summary."""
        logger.info("=== Verification Results ===")

        # Check overall state
        logger.info(f"DataView visible: {self.data_view.isVisible()}")
        logger.info(f"TableView populated: {self.data_view._table_model.rowCount() > 0}")

        # Check validation and correction states
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)

        logger.info(f"Invalid cells: {invalid_cells}")
        logger.info(f"Corrected cells: {corrected_cells}")

        # Final status
        if self.data_view.isVisible() and self.data_view._table_model.rowCount() > 0:
            if hasattr(self.data_view, "_table_view") and self.data_view._table_view.isVisible():
                logger.info("VERIFICATION PASSED: DataView is visible and populated")
            else:
                logger.error("VERIFICATION FAILED: TableView is not visible")
        else:
            logger.error("VERIFICATION FAILED: DataView is not visible or not populated")

        # Force one final update for good measure
        if hasattr(self.data_view, "_table_view"):
            self.data_view._table_view.viewport().update()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = VerificationWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
