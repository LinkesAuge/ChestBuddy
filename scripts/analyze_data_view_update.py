"""
analyze_data_view_update.py

Description: Analyzes the data update and highlighting process in DataView
Usage:
    python -m scripts.analyze_data_view_update
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
        logging.FileHandler(os.path.join(project_root, "scripts", "analyze_dataview.log")),
    ],
)

# Import required modules
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from chestbuddy.core.data.data_model import ChestDataModel
from chestbuddy.ui.views.data_view import DataView
from chestbuddy.core.table_state_manager import TableStateManager, CellState

logger = logging.getLogger("analyze_dataview")


class AnalysisWindow(QMainWindow):
    """Test window for analyzing DataView updates."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataView Update Analysis")
        self.resize(1200, 800)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create control panel
        self.control_panel = QWidget()
        self.control_layout = QHBoxLayout(self.control_panel)
        self.layout.addWidget(self.control_panel)

        # Create test components
        self._setup_components()

        # Create control buttons
        self._setup_controls()

    def _setup_components(self):
        """Set up the test components."""
        logger.info("Setting up test components")

        # Create data model
        self._data_model = ChestDataModel()
        logger.info("Created data model")

        # Create TableStateManager
        self._table_state_manager = TableStateManager(self._data_model)
        logger.info(f"Created TableStateManager with ID: {id(self._table_state_manager)}")

        # Monitor TableStateManager state changes
        self._table_state_manager.state_changed.connect(self._on_state_changed)

        # Create DataView
        self._data_view = DataView(self._data_model)
        logger.info(f"Created DataView with ID: {id(self._data_view)}")

        # Set table state manager on data view
        self._data_view.set_table_state_manager(self._table_state_manager)
        logger.info("Set TableStateManager on DataView")

        # Add data view to layout
        self.layout.addWidget(self._data_view)

        # Load initial test data
        self._load_test_data()

    def _setup_controls(self):
        """Set up the control buttons."""
        # Create buttons
        self.highlight_btn = QPushButton("Highlight Cells")
        self.highlight_btn.clicked.connect(self._highlight_test_cells)

        self.clear_btn = QPushButton("Clear Highlights")
        self.clear_btn.clicked.connect(self._clear_highlights)

        self.update_data_btn = QPushButton("Update Data")
        self.update_data_btn.clicked.connect(self._update_test_data)

        self.analyze_btn = QPushButton("Analyze Model")
        self.analyze_btn.clicked.connect(self._analyze_model)

        # Add buttons to control panel
        self.control_layout.addWidget(self.highlight_btn)
        self.control_layout.addWidget(self.clear_btn)
        self.control_layout.addWidget(self.update_data_btn)
        self.control_layout.addWidget(self.analyze_btn)

    def _load_test_data(self):
        """Load initial test data into the model."""
        try:
            # Create simple test data
            import pandas as pd
            import numpy as np

            # Create test data with multiple columns
            test_data = pd.DataFrame(
                {
                    "A": [f"A{i}" for i in range(20)],
                    "B": [i * 10 for i in range(20)],
                    "C": [f"C{i}" for i in range(20)],
                    "D": np.random.randint(0, 100, 20),
                    "E": [f"E{i}" for i in range(20)],
                }
            )

            # Load into model
            self._data_model.update_data(test_data)
            logger.info(
                f"Loaded test data with {len(test_data)} rows, {len(test_data.columns)} columns"
            )

            # Populate the table
            if hasattr(self._data_view, "populate_table"):
                self._data_view.populate_table()
                logger.info("Populated data view")

                # Schedule analysis for after UI updates
                QTimer.singleShot(500, self._initial_model_analysis)
        except Exception as e:
            logger.error(f"Error loading test data: {e}", exc_info=True)

    def _initial_model_analysis(self):
        """Perform initial analysis of model structure."""
        try:
            # Analyze model
            self._analyze_model()
        except Exception as e:
            logger.error(f"Error in initial model analysis: {e}", exc_info=True)

    def _highlight_test_cells(self):
        """Highlight test cells via TableStateManager."""
        try:
            logger.info("Setting test cell states")

            # Set some test states in different patterns
            # Some individual cells
            self._table_state_manager.set_cell_state(0, 0, CellState.INVALID)
            self._table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)
            self._table_state_manager.set_cell_state(2, 2, CellState.CORRECTED)
            self._table_state_manager.set_cell_state(3, 3, CellState.PROCESSING)

            # A full column
            for row in range(5, 10):
                self._table_state_manager.set_cell_state(row, 0, CellState.INVALID)

            # A full row
            for col in range(5):
                self._table_state_manager.set_cell_state(15, col, CellState.CORRECTABLE)

            # Some cell details for tooltips
            self._table_state_manager.set_cell_detail(0, 0, "Invalid cell at 0,0")
            self._table_state_manager.set_cell_detail(1, 1, "Correctable cell at 1,1")
            self._table_state_manager.set_cell_detail(2, 2, "Corrected cell at 2,2")

            # Emit the state changed signal
            self._table_state_manager.state_changed.emit()
            logger.info("Cell states set and signal emitted")

            # Force the view to update
            if hasattr(self._data_view, "update_cell_highlighting_from_state"):
                self._data_view.update_cell_highlighting_from_state()
                logger.info("Called update_cell_highlighting_from_state")

            # Schedule analysis for after UI updates
            QTimer.singleShot(500, self._post_highlight_analysis)
        except Exception as e:
            logger.error(f"Error highlighting test cells: {e}", exc_info=True)

    def _clear_highlights(self):
        """Clear all cell highlighting."""
        try:
            logger.info("Clearing all cell states")

            # Reset all cell states
            self._table_state_manager.reset_cell_states()
            logger.info("Cell states reset and signal emitted automatically")

            # Schedule analysis for after UI updates
            QTimer.singleShot(500, self._post_clear_analysis)
        except Exception as e:
            logger.error(f"Error clearing highlights: {e}", exc_info=True)

    def _update_test_data(self):
        """Update the test data to see how it affects highlighting."""
        try:
            logger.info("Updating test data")

            # Create updated test data
            import pandas as pd
            import numpy as np

            # New data with same structure but different values
            updated_data = pd.DataFrame(
                {
                    "A": [f"Updated-A{i}" for i in range(20)],
                    "B": [i * 5 for i in range(20)],
                    "C": [f"Updated-C{i}" for i in range(20)],
                    "D": np.random.randint(100, 200, 20),
                    "E": [f"Updated-E{i}" for i in range(20)],
                }
            )

            # Update model
            self._data_model.update_data(updated_data)
            logger.info(f"Updated test data with {len(updated_data)} rows")

            # Schedule analysis for after UI updates
            QTimer.singleShot(500, self._post_update_analysis)
        except Exception as e:
            logger.error(f"Error updating test data: {e}", exc_info=True)

    def _analyze_model(self):
        """Analyze the current table model structure."""
        try:
            logger.info("Analyzing current table model")

            # Check if we have the table model from the DataView
            if hasattr(self._data_view, "_table_model") and self._data_view._table_model:
                model = self._data_view._table_model

                # Get model dimensions
                row_count = model.rowCount()
                col_count = model.columnCount()
                logger.info(f"Table model dimensions: {row_count} rows x {col_count} columns")

                # Check a few sample cells
                sample_cells = [(0, 0), (1, 1), (5, 0), (15, 3)]
                for row, col in sample_cells:
                    if row < row_count and col < col_count:
                        # Get model index
                        index = model.index(row, col)

                        # Get item
                        item = model.itemFromIndex(index)

                        if item:
                            # Check data
                            display_data = item.data(Qt.DisplayRole)
                            bg_color = item.data(Qt.BackgroundRole)
                            bg_color_name = (
                                bg_color.name() if isinstance(bg_color, QColor) else "None"
                            )

                            logger.info(
                                f"Cell ({row}, {col}): Data='{display_data}', Background={bg_color_name}"
                            )
                        else:
                            logger.warning(f"No item found for cell ({row}, {col})")

                # Check TableStateManager state
                invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
                correctable_cells = self._table_state_manager.get_cells_by_state(
                    CellState.CORRECTABLE
                )
                corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

                logger.info(
                    f"TableStateManager state: {len(invalid_cells)} invalid, "
                    f"{len(correctable_cells)} correctable, "
                    f"{len(corrected_cells)} corrected"
                )

                # Check cells that should be highlighted
                if invalid_cells:
                    for row, col in invalid_cells[:5]:  # Only check first 5 cells
                        if row < row_count and col < col_count:
                            index = model.index(row, col)
                            item = model.itemFromIndex(index)

                            if item:
                                bg_color = item.data(Qt.BackgroundRole)
                                bg_color_name = (
                                    bg_color.name() if isinstance(bg_color, QColor) else "None"
                                )

                                logger.info(
                                    f"Invalid cell ({row}, {col}) has background: {bg_color_name}"
                                )
            else:
                logger.warning("DataView doesn't have a _table_model attribute or it's None")
        except Exception as e:
            logger.error(f"Error analyzing model: {e}", exc_info=True)

    def _post_highlight_analysis(self):
        """Analyze after highlighting."""
        logger.info("Post-highlight analysis")
        self._analyze_model()

    def _post_clear_analysis(self):
        """Analyze after clearing highlights."""
        logger.info("Post-clear analysis")
        self._analyze_model()

    def _post_update_analysis(self):
        """Analyze after data update."""
        logger.info("Post-update analysis")
        self._analyze_model()

    def _on_state_changed(self):
        """Handle TableStateManager state_changed signal."""
        logger.info("TableStateManager state_changed signal received")

        # Log current states
        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

        logger.info(
            f"Current cell states: {len(invalid_cells)} invalid, "
            f"{len(correctable_cells)} correctable, "
            f"{len(corrected_cells)} corrected"
        )


def main():
    """Main function for the analysis script."""
    logger.info("Starting DataView update analysis script")

    # Create Qt application
    app = QApplication([])

    # Create and show window
    window = AnalysisWindow()
    window.show()

    # Run the application
    logger.info("Running application event loop")
    app.exec()

    logger.info("Analysis script completed")


if __name__ == "__main__":
    main()
