"""
Test script to verify the DataView cell highlighting fix.

This script tests that cell highlighting persists and doesn't trigger unwanted events.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# Add the parent directory to the path to import chestbuddy
sys.path.append(str(Path(__file__).parent.parent))

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.ui.data_view import DataView

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_dataview_fix.log", mode="w")],
)

logger = logging.getLogger("test_dataview_fix")


class TestApplication(QMainWindow):
    """Test application for the DataView cell highlighting fix."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataView Highlighting Fix Test")
        self.resize(1000, 800)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Add test control buttons
        self.create_controls()

        # Setup data components
        self.setup_components()

        # Schedule initial population
        QTimer.singleShot(500, self.populate_data)
        QTimer.singleShot(1500, self.apply_validation_highlighting)
        QTimer.singleShot(2500, self.check_highlights_persist)

    def create_controls(self):
        """Create control buttons for testing."""
        # Status label
        self.status_label = QLabel("Status: Initializing...")
        self.layout.addWidget(self.status_label)

        # Highlight test button
        self.highlight_test_button = QPushButton("Test Direct Highlighting")
        self.highlight_test_button.clicked.connect(self.test_direct_highlighting)
        self.layout.addWidget(self.highlight_test_button)

        # Check highlight persistence button
        self.check_highlight_button = QPushButton("Check Highlight Persistence")
        self.check_highlight_button.clicked.connect(self.check_highlights_persist)
        self.layout.addWidget(self.check_highlight_button)

        # Apply validation highlight button
        self.validation_button = QPushButton("Apply Validation Highlighting")
        self.validation_button.clicked.connect(self.apply_validation_highlighting)
        self.layout.addWidget(self.validation_button)

        # Apply correction highlight button
        self.correction_button = QPushButton("Apply Correction Highlighting")
        self.correction_button.clicked.connect(self.apply_correction_highlighting)
        self.layout.addWidget(self.correction_button)

    def setup_components(self):
        """Set up the data components for testing."""
        logger.info("Setting up test components")

        # Create sample data
        self.sample_data = pd.DataFrame(
            {
                "PLAYER": ["player1", "player2", "player3", "player4"],
                "CHEST": ["gold", "silver", "bronze", "diamond"],
                "SOURCE": ["daily", "quest", "clan", "tournament"],
                "SCORE": [100, 200, 300, 400],
                "CLAN": ["clan1", "clan2", "clan3", "clan4"],
                "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            }
        )
        logger.info(f"Created sample data with shape: {self.sample_data.shape}")

        # Create data model
        self.data_model = ChestDataModel()
        # Set data directly
        self.data_model._data = self.sample_data.copy()

        # Create status dataframes manually
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

        # Set up signal tracking
        self.data_changed_count = 0
        self.validation_changed_count = 0
        self.correction_applied_count = 0

        # Connect signals to counters
        self.data_model.data_changed.connect(self.on_data_changed)
        self.data_model.validation_changed.connect(self.on_validation_changed)
        self.data_model.correction_applied.connect(self.on_correction_applied)

        # Create table state manager
        self.table_state_manager = TableStateManager(self.data_model)

        # Create data view
        self.data_view = DataView(self.data_model)
        self.data_view.set_table_state_manager(self.table_state_manager)

        # Add to layout
        self.layout.addWidget(self.data_view)

        logger.info("Components initialized successfully")

    def on_data_changed(self, data_state):
        """Track data_changed signals."""
        self.data_changed_count += 1
        logger.info(f"Data changed signal received ({self.data_changed_count})")

    def on_validation_changed(self, validation_status):
        """Track validation_changed signals."""
        self.validation_changed_count += 1
        logger.info(f"Validation changed signal received ({self.validation_changed_count})")

    def on_correction_applied(self):
        """Track correction_applied signals."""
        self.correction_applied_count += 1
        logger.info(f"Correction applied signal received ({self.correction_applied_count})")

    def populate_data(self):
        """Populate the DataView with the sample data."""
        logger.info("Populating DataView with sample data")
        self.data_view.populate_table()
        self.status_label.setText("Status: Data populated")
        logger.info("DataView populated successfully")

    def apply_validation_highlighting(self):
        """Apply validation highlighting to cells."""
        logger.info("Applying validation highlighting")

        # Create validation status
        validation_status = pd.DataFrame(
            {
                "ROW_IDX": [0, 1, 2],
                "COL_IDX": [0, 1, 2],
                "STATUS": ["invalid", "invalid", "invalid"],
            }
        )

        # Update cell states
        self.table_state_manager.update_cell_states_from_validation(validation_status)

        # Update cell highlighting
        self.data_view.update_cell_highlighting_from_state()

        # Log results
        invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
        logger.info(f"Applied validation highlighting to {len(invalid_cells)} cells")
        self.status_label.setText(f"Status: {len(invalid_cells)} cells highlighted as invalid")

    def apply_correction_highlighting(self):
        """Apply correction highlighting to cells."""
        logger.info("Applying correction highlighting")

        # Create correction status
        correction_status = {
            "corrected_cells": [(0, 1), (1, 2)],
            "original_values": {"(0, 1)": "gold", "(1, 2)": "quest"},
            "new_values": {"(0, 1)": "Gold", "(1, 2)": "Quest"},
        }

        # Update cell states
        self.table_state_manager.update_cell_states_from_correction(correction_status)

        # Update cell highlighting
        self.data_view.update_cell_highlighting_from_state()

        # Log results
        corrected_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTED)
        logger.info(f"Applied correction highlighting to {len(corrected_cells)} cells")
        self.status_label.setText(f"Status: {len(corrected_cells)} cells highlighted as corrected")

    def test_direct_highlighting(self):
        """Test direct highlighting using _highlight_cell."""
        logger.info("Testing direct cell highlighting")

        # Store initial signal counts
        initial_data_changed = self.data_changed_count

        # Apply direct highlighting
        red = QColor(255, 0, 0)
        green = QColor(0, 255, 0)
        blue = QColor(0, 0, 255)

        success_count = 0
        if self.data_view._highlight_cell(0, 0, red):
            success_count += 1
        if self.data_view._highlight_cell(1, 1, green):
            success_count += 1
        if self.data_view._highlight_cell(2, 2, blue):
            success_count += 1

        # Check if data_changed was called
        data_changed_triggered = self.data_changed_count > initial_data_changed
        logger.info(f"Direct highlighting triggered data_changed: {data_changed_triggered}")

        # Update status
        self.status_label.setText(
            f"Status: Direct highlighting of {success_count}/3 cells - "
            f"data_changed {'triggered' if data_changed_triggered else 'NOT triggered'}"
        )

    def check_highlights_persist(self):
        """Check if highlighting persists."""
        logger.info("Checking if highlights persist")

        # Check table view cells for highlighting
        if not hasattr(self.data_view, "_table_model"):
            logger.error("No table model in DataView")
            return

        model = self.data_view._table_model

        # Check some cells that should be highlighted
        highlighted_cells = []
        for row, col in [(0, 0), (1, 1), (2, 2), (0, 1), (1, 2)]:
            item = model.item(row, col)
            if item:
                bg_role = item.data(Qt.BackgroundRole)
                if bg_role:
                    highlighted_cells.append((row, col))
                    logger.info(f"Cell ({row}, {col}) has background color: {bg_role}")
                else:
                    logger.warning(f"Cell ({row}, {col}) has NO background color!")
            else:
                logger.error(f"No item found for cell ({row}, {col})")

        # Update status
        self.status_label.setText(f"Status: Found {len(highlighted_cells)} highlighted cells")

        # Log signal counts
        logger.info(
            f"Signal counts: data_changed={self.data_changed_count}, "
            f"validation_changed={self.validation_changed_count}, "
            f"correction_applied={self.correction_applied_count}"
        )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = TestApplication()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
