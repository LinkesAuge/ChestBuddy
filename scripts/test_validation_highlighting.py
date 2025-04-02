"""
Test script for validation highlighting in DataView.

This script will test the validation highlighting functionality in the DataView/TableStateManager integration.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QTimer

# Add the parent directory to the path to import chestbuddy
sys.path.append(str(Path(__file__).parent.parent))

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.ui.data_view import DataView

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("validation_highlight_test")


class TestWindow(QMainWindow):
    """Test window for validation highlighting."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Validation Highlighting Test")
        self.resize(1200, 800)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create button panel
        self.button_panel = QWidget()
        self.button_layout = QHBoxLayout(self.button_panel)
        self.layout.addWidget(self.button_panel)

        # Set up test components
        self.setup_components()

        # Set up test buttons
        self.setup_buttons()

    def setup_components(self):
        """Set up test components."""
        logger.info("Setting up test components")

        # Create data model
        self.data_model = ChestDataModel()

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "PLAYER": ["John", "Alice", "Bob", "Charlie"],
                "CHEST": ["Gold", "Silver", "Bronze", "Diamond"],
                "SOURCE": ["Quest", "Daily", "Season", "Event"],
                "SCORE": [100, 75, 50, 125],
                "CLAN": ["Alpha", "Beta", "Gamma", "Delta"],
            }
        )

        # Load data into model
        self.data_model.update_data(sample_data)
        logger.info(f"Data model populated with sample data: {sample_data.shape}")

        # Initialize TableStateManager
        self.table_state_manager = TableStateManager(self.data_model)
        logger.info("TableStateManager initialized")

        # Create DataView
        self.data_view = DataView(self.data_model)

        # Add DataView to layout
        self.layout.addWidget(self.data_view)

        # Populate the table
        self.data_view.populate_table()
        logger.info("Table populated with data")

        # Now set the TableStateManager after population
        self.data_view.set_table_state_manager(self.table_state_manager)
        logger.info("DataView connected to TableStateManager")

    def setup_buttons(self):
        """Set up test buttons."""
        # Set invalid cells
        invalid_button = QPushButton("Set Invalid Cells")
        invalid_button.clicked.connect(self.set_invalid_cells)
        self.button_layout.addWidget(invalid_button)

        # Set correctable cells
        correctable_button = QPushButton("Set Correctable Cells")
        correctable_button.clicked.connect(self.set_correctable_cells)
        self.button_layout.addWidget(correctable_button)

        # Set corrected cells
        corrected_button = QPushButton("Set Corrected Cells")
        corrected_button.clicked.connect(self.set_corrected_cells)
        self.button_layout.addWidget(corrected_button)

        # Reset all cells
        reset_button = QPushButton("Reset All Cells")
        reset_button.clicked.connect(self.reset_cells)
        self.button_layout.addWidget(reset_button)

        # Check highlight status
        check_button = QPushButton("Check Highlights")
        check_button.clicked.connect(self.check_highlights)
        self.button_layout.addWidget(check_button)

        # Emit state changed
        emit_button = QPushButton("Emit State Changed")
        emit_button.clicked.connect(self.emit_state_changed)
        self.button_layout.addWidget(emit_button)

        # Force update highlighting
        update_button = QPushButton("Force Update Highlighting")
        update_button.clicked.connect(self.force_update_highlighting)
        self.button_layout.addWidget(update_button)

    def set_invalid_cells(self):
        """Set cells as invalid."""
        logger.info("Setting cells as invalid")
        cells = [(0, 0), (1, 1), (2, 2)]
        for row, col in cells:
            self.table_state_manager.set_cell_state(row, col, CellState.INVALID)
            self.table_state_manager.set_cell_detail(row, col, f"Invalid cell at ({row}, {col})")
            logger.info(f"Set cell ({row}, {col}) as INVALID")

        # Emit state_changed signal
        self.table_state_manager.state_changed.emit()
        logger.info("Emitted state_changed signal")

    def set_correctable_cells(self):
        """Set cells as correctable."""
        logger.info("Setting cells as correctable")
        cells = [(0, 1), (1, 2), (2, 3)]
        for row, col in cells:
            self.table_state_manager.set_cell_state(row, col, CellState.CORRECTABLE)
            self.table_state_manager.set_cell_detail(
                row, col, f"Correctable cell at ({row}, {col})"
            )
            logger.info(f"Set cell ({row}, {col}) as CORRECTABLE")

        # Emit state_changed signal
        self.table_state_manager.state_changed.emit()
        logger.info("Emitted state_changed signal")

    def set_corrected_cells(self):
        """Set cells as corrected."""
        logger.info("Setting cells as corrected")
        cells = [(0, 2), (1, 3), (2, 0)]
        for row, col in cells:
            self.table_state_manager.set_cell_state(row, col, CellState.CORRECTED)
            self.table_state_manager.set_cell_detail(row, col, f"Corrected cell at ({row}, {col})")
            logger.info(f"Set cell ({row}, {col}) as CORRECTED")

        # Emit state_changed signal
        self.table_state_manager.state_changed.emit()
        logger.info("Emitted state_changed signal")

    def reset_cells(self):
        """Reset all cell states."""
        logger.info("Resetting all cell states")
        self.table_state_manager.reset_cell_states()
        logger.info("All cell states reset")

    def check_highlights(self):
        """Check the current highlighting status."""
        logger.info("Checking highlight status")

        # Get cells by state
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)

        logger.info(f"Invalid cells: {invalid_cells}")
        logger.info(f"Correctable cells: {correctable_cells}")
        logger.info(f"Corrected cells: {corrected_cells}")

        # Check actual highlighting in the table
        self.check_cell_highlighting()

    def check_cell_highlighting(self):
        """Check if specified cells have background color set."""
        if not hasattr(self.data_view, "_table_model") or self.data_view._table_model is None:
            logger.error("DataView does not have _table_model attribute")
            return

        model = self.data_view._table_model

        # Check cells by state
        all_cells = []
        all_cells.extend(self.table_state_manager.get_cells_by_state(CellState.INVALID))
        all_cells.extend(self.table_state_manager.get_cells_by_state(CellState.CORRECTABLE))
        all_cells.extend(self.table_state_manager.get_cells_by_state(CellState.CORRECTED))

        # Check each cell
        for row, col in all_cells:
            try:
                if model.rowCount() <= row or model.columnCount() <= col:
                    logger.warning(
                        f"Cell ({row}, {col}) is out of model bounds - "
                        f"model has {model.rowCount()} rows and {model.columnCount()} columns"
                    )
                    continue

                item = model.item(row, col)
                if item:
                    bg_color = item.data(Qt.BackgroundRole)
                    state = self.table_state_manager.get_cell_state(row, col)
                    logger.info(
                        f"Cell ({row}, {col}) - State: {state.name}, Background: {bg_color}"
                    )
                else:
                    logger.warning(f"Cell ({row}, {col}) has no item")
            except Exception as e:
                logger.error(f"Error checking cell ({row}, {col}): {e}")

    def emit_state_changed(self):
        """Manually emit the state_changed signal."""
        logger.info("Manually emitting state_changed signal")
        self.table_state_manager.state_changed.emit()
        logger.info("State changed signal emitted")

    def force_update_highlighting(self):
        """Force update of cell highlighting."""
        logger.info("Forcing update of cell highlighting")
        self.data_view.update_cell_highlighting_from_state()
        logger.info("Cell highlighting updated")


def main():
    """Main function to run the test application."""
    # Create QApplication
    app = QApplication(sys.argv)

    # Create and show test window
    window = TestWindow()
    window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
