"""
debug_table_state_manager.py

Description: Debugging script for TableStateManager integration with DataView
Usage:
    python -m scripts.debug_table_state_manager
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, "scripts", "debug_tsm.log")),
    ],
)

# Import required modules
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from chestbuddy.core.data.data_model import ChestDataModel
from chestbuddy.ui.views.data_view import DataView
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.core.table_state_manager import TableStateManager, CellState

logger = logging.getLogger("debug_tsm")


class DebugWindow(QMainWindow):
    """Test window for debugging TableStateManager."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TableStateManager Debug")
        self.resize(1200, 800)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create components
        self._setup_components()

    def _setup_components(self):
        """Set up the components for testing."""
        logger.info("Setting up test components")

        # Create data model
        self._data_model = ChestDataModel()
        logger.info("Created data model")

        # Create TableStateManager
        self._table_state_manager = TableStateManager(self._data_model)
        logger.info(f"Created TableStateManager with ID: {id(self._table_state_manager)}")

        # Create DataView directly first to test basic functionality
        self._direct_data_view = DataView(self._data_model)
        logger.info(f"Created direct DataView with ID: {id(self._direct_data_view)}")

        # Set table state manager on the direct data view
        self._direct_data_view.set_table_state_manager(self._table_state_manager)
        logger.info("Set TableStateManager on direct DataView")

        # Create DataViewAdapter to test the adapter pattern
        self._data_view_adapter = DataViewAdapter(self._data_model)
        logger.info(f"Created DataViewAdapter with ID: {id(self._data_view_adapter)}")

        # Log the internal DataView inside the adapter
        if hasattr(self._data_view_adapter, "_data_view"):
            logger.info(f"Adapter's internal DataView ID: {id(self._data_view_adapter._data_view)}")
        else:
            logger.warning("Adapter doesn't have an internal DataView")

        # Set table state manager on the adapter
        self._data_view_adapter.set_table_state_manager(self._table_state_manager)
        logger.info("Set TableStateManager on DataViewAdapter")

        # Add the data view to the layout
        # self.layout.addWidget(self._direct_data_view)  # Comment one or the other to test
        self.layout.addWidget(self._data_view_adapter)
        logger.info("Added view to layout")

        # Load test data
        self._load_test_data()

        # Test cell state setting
        self._test_cell_states()

    def _load_test_data(self):
        """Load test data into the model."""
        try:
            # Create simple test data
            import pandas as pd

            test_data = pd.DataFrame(
                {
                    "Column1": [f"Value {i}" for i in range(20)],
                    "Column2": [i * 10 for i in range(20)],
                    "Column3": [f"Test {i}" for i in range(20)],
                }
            )

            # Load into model
            self._data_model.update_data(test_data)
            logger.info(f"Loaded test data with {len(test_data)} rows")

            # Populate the table
            if hasattr(self._direct_data_view, "populate_table"):
                self._direct_data_view.populate_table()
                logger.info("Populated direct data view")

            if hasattr(self._data_view_adapter, "_data_view") and hasattr(
                self._data_view_adapter._data_view, "populate_table"
            ):
                self._data_view_adapter._data_view.populate_table()
                logger.info("Populated adapter's data view")
        except Exception as e:
            logger.error(f"Error loading test data: {e}", exc_info=True)

    def _test_cell_states(self):
        """Test setting cell states."""
        try:
            # Set some test states
            self._table_state_manager.set_cell_state(0, 0, CellState.INVALID)
            self._table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)
            self._table_state_manager.set_cell_state(2, 2, CellState.CORRECTED)
            self._table_state_manager.set_cell_state(3, 0, CellState.PROCESSING)

            # Set some cell details for tooltips
            self._table_state_manager.set_cell_detail(0, 0, "This is an invalid cell")
            self._table_state_manager.set_cell_detail(1, 1, "This cell can be corrected")
            self._table_state_manager.set_cell_detail(2, 2, "This cell has been corrected")

            # Emit the state changed signal
            self._table_state_manager.state_changed.emit()
            logger.info("Set test cell states and emitted state_changed signal")

            # Log the states
            invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
            correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
            corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

            logger.info(
                f"Current cell states: {len(invalid_cells)} invalid, "
                f"{len(correctable_cells)} correctable, "
                f"{len(corrected_cells)} corrected"
            )
        except Exception as e:
            logger.error(f"Error setting test cell states: {e}", exc_info=True)


def main():
    """Main function for the debugging script."""
    logger.info("Starting TableStateManager debug script")

    # Create Qt application
    app = QApplication([])

    # Create and show window
    window = DebugWindow()
    window.show()

    # Run the application
    logger.info("Running application event loop")
    app.exec()

    logger.info("Debug script completed")


if __name__ == "__main__":
    main()
