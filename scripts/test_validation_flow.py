"""
Test script for the complete validation flow.

This script tests the entire validation flow from validation service through
TableStateManager to cell highlighting in DataView.
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
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.ui.data_view import DataView
from chestbuddy.utils.config import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("validation_flow_test")


class TestWindow(QMainWindow):
    """Test window for validation flow."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Validation Flow Test")
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

        # Create configuration manager
        self.config_manager = ConfigManager("chestbuddy")
        logger.info("Config manager initialized")

        # Create data model
        self.data_model = ChestDataModel()

        # Create sample data with invalid values
        sample_data = pd.DataFrame(
            {
                "PLAYER": ["John123", "Alice", "Bob", "Charlie"],  # Invalid player name
                "CHEST": ["Golden", "Silver", "Bronze", "Diamond"],  # Invalid chest type
                "SOURCE": ["Quest", "Daily", "Seasonal", "Event"],  # Invalid source
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

        # Initialize ValidationService
        self.validation_service = ValidationService(self.data_model, self.config_manager)
        logger.info("ValidationService initialized")

        # Create lists of valid values for validation
        self.validation_service._lists = {
            "players": ["John", "Alice", "Bob", "Charlie"],
            "chest_types": ["Gold", "Silver", "Bronze", "Diamond"],
            "sources": ["Quest", "Daily", "Season", "Event"],
        }
        logger.info("Set up validation lists")

        # Create DataView
        self.data_view = DataView(self.data_model)

        # Set the table state manager
        self.data_view.set_table_state_manager(self.table_state_manager)
        logger.info("Set TableStateManager on DataView")

        # Add DataView to layout
        self.layout.addWidget(self.data_view)

        # Populate the table
        self.data_view.populate_table()
        logger.info("Table populated with data")

        # Connect data model signals to DataView
        self.data_model.validation_changed.connect(self.data_view._on_validation_changed)
        logger.info("Connected validation_changed signal")

    def setup_buttons(self):
        """Set up test buttons."""
        # Run validation
        validate_button = QPushButton("Run Validation")
        validate_button.clicked.connect(self.run_validation)
        self.button_layout.addWidget(validate_button)

        # Check validation status
        check_button = QPushButton("Check Validation Status")
        check_button.clicked.connect(self.check_validation_status)
        self.button_layout.addWidget(check_button)

        # Force update highlighting
        update_button = QPushButton("Force Update Highlighting")
        update_button.clicked.connect(self.force_update_highlighting)
        self.button_layout.addWidget(update_button)

        # Check cell highlighting
        highlight_button = QPushButton("Check Cell Highlighting")
        highlight_button.clicked.connect(self.check_cell_highlighting)
        self.button_layout.addWidget(highlight_button)

        # Emit validation status
        emit_button = QPushButton("Emit Validation Status")
        emit_button.clicked.connect(self.emit_validation_status)
        self.button_layout.addWidget(emit_button)

    def run_validation(self):
        """Run validation on the data."""
        logger.info("Running validation")

        try:
            # Run validation
            self.validation_service.validate_data()
            logger.info("Validation completed")

            # Check for validation results
            validation_status = self.data_model.get_validation_status()
            if validation_status is not None and not validation_status.empty:
                logger.info(
                    f"Validation results: {validation_status.shape} rows with validation data"
                )
            else:
                logger.warning("No validation results returned")
        except Exception as e:
            logger.error(f"Error during validation: {e}")

    def check_validation_status(self):
        """Check validation status in the model."""
        try:
            # Get validation status from the data model, not the validation service
            validation_status = self.data_model.get_validation_status()
            if validation_status is not None and not validation_status.empty:
                logger.info(f"Validation status shape: {validation_status.shape}")
                logger.info(f"Validation status columns: {validation_status.columns.tolist()}")
                logger.info(f"Sample validation status:\n{validation_status.head()}")
            else:
                logger.warning("No validation status available")

            # Check table state manager
            invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
            logger.info(f"Invalid cells in TableStateManager: {invalid_cells}")
        except Exception as e:
            logger.error(f"Error checking validation status: {e}")

    def force_update_highlighting(self):
        """Force update cell highlighting in the DataView."""
        logger.info("Forcing update of cell highlighting")

        try:
            # Force update highlighting
            self.data_view.update_cell_highlighting_from_state()
            logger.info("Cell highlighting updated")
        except Exception as e:
            logger.error(f"Error updating cell highlighting: {e}")

    def check_cell_highlighting(self):
        """Check cell highlighting in the DataView."""
        logger.info("Checking cell highlighting")

        try:
            if not hasattr(self.data_view, "_table_model") or self.data_view._table_model is None:
                logger.error("No table model in DataView")
                return

            # Get model
            model = self.data_view._table_model

            # Check cells
            invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
            logger.info(f"Invalid cells: {invalid_cells}")

            for row, col in invalid_cells:
                if row < model.rowCount() and col < model.columnCount():
                    item = model.item(row, col)
                    if item:
                        bg_color = item.data(Qt.BackgroundRole)
                        logger.info(f"Cell ({row}, {col}) background: {bg_color}")
                    else:
                        logger.warning(f"No item at ({row}, {col})")
                else:
                    logger.warning(
                        f"Cell ({row}, {col}) out of bounds: {model.rowCount()}x{model.columnCount()}"
                    )
        except Exception as e:
            logger.error(f"Error checking cell highlighting: {e}")

    def emit_validation_status(self):
        """Manually emit validation status."""
        logger.info("Manually emitting validation status")

        try:
            # Get validation status from the data model
            validation_status = self.data_model.get_validation_status()
            if validation_status is not None and not validation_status.empty:
                # Emit validation changed signal
                self.data_model.validation_changed.emit(validation_status)
                logger.info("Validation changed signal emitted")
            else:
                logger.warning("No validation status to emit")
        except Exception as e:
            logger.error(f"Error emitting validation status: {e}")


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
