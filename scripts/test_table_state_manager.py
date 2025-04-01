"""
test_table_state_manager.py

Description: Test script for TableStateManager functionality
Usage:
    python -m scripts.test_table_state_manager
"""

import os
import sys
import logging
import unittest
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
        logging.FileHandler(os.path.join(project_root, "scripts", "test_tsm.log")),
    ],
)

# Import required modules
import pandas as pd
from PySide6.QtCore import QObject, Signal

from chestbuddy.core.data.data_model import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState

logger = logging.getLogger("test_tsm")


class SignalCatcher(QObject):
    """Utility class to catch signals for testing."""

    def __init__(self):
        super().__init__()
        self.signal_received = False
        self.signal_count = 0

    def reset(self):
        """Reset the signal flags."""
        self.signal_received = False
        self.signal_count = 0

    def slot(self):
        """Slot to receive signals."""
        self.signal_received = True
        self.signal_count += 1
        logger.debug(f"Signal received in SignalCatcher, count: {self.signal_count}")


class TableStateManagerTests(unittest.TestCase):
    """Test cases for TableStateManager."""

    def setUp(self):
        """Set up the test environment."""
        logger.info("Setting up test environment")

        # Create a data model
        self.data_model = ChestDataModel()

        # Create a test data frame
        test_data = pd.DataFrame(
            {
                "Column1": [f"Value {i}" for i in range(10)],
                "Column2": [i * 10 for i in range(10)],
                "Column3": [f"Test {i}" for i in range(10)],
            }
        )

        # Load the data into the model
        self.data_model.update_data(test_data)

        # Create the TableStateManager
        self.manager = TableStateManager(self.data_model)

        # Create a signal catcher
        self.signal_catcher = SignalCatcher()

        # Connect to the state_changed signal
        self.manager.state_changed.connect(self.signal_catcher.slot)

        logger.info("Test environment set up")

    def test_initialization(self):
        """Test the initialization of TableStateManager."""
        logger.info("Testing initialization")

        # Check the data model is correctly set
        self.assertEqual(self.manager._data_model, self.data_model)

        # Check cell states are empty
        self.assertEqual(len(self.manager._cell_states), 0)

        # Check default batch size
        self.assertEqual(self.manager.BATCH_SIZE, 100)

        logger.info("Initialization test passed")

    def test_set_get_cell_state(self):
        """Test setting and getting cell states."""
        logger.info("Testing set_cell_state and get_cell_state")

        # Initial state should be NORMAL
        self.assertEqual(self.manager.get_cell_state(0, 0), CellState.NORMAL)

        # Set cell state
        self.manager.set_cell_state(0, 0, CellState.INVALID)

        # Check it was set correctly
        self.assertEqual(self.manager.get_cell_state(0, 0), CellState.INVALID)

        # Set another cell state
        self.manager.set_cell_state(1, 1, CellState.CORRECTABLE)

        # Check it was set correctly
        self.assertEqual(self.manager.get_cell_state(1, 1), CellState.CORRECTABLE)

        # Check signal is not emitted for individual set_cell_state calls
        self.assertFalse(self.signal_catcher.signal_received)

        logger.info("set_cell_state and get_cell_state tests passed")

    def test_reset_cell_states(self):
        """Test resetting cell states."""
        logger.info("Testing reset_cell_states")

        # Set some cell states
        self.manager.set_cell_state(0, 0, CellState.INVALID)
        self.manager.set_cell_state(1, 1, CellState.CORRECTABLE)

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Reset cell states
        self.manager.reset_cell_states()

        # Check all states are reset
        self.assertEqual(self.manager.get_cell_state(0, 0), CellState.NORMAL)
        self.assertEqual(self.manager.get_cell_state(1, 1), CellState.NORMAL)

        # Check signal is emitted
        self.assertTrue(self.signal_catcher.signal_received)

        logger.info("reset_cell_states test passed")

    def test_reset_rows(self):
        """Test resetting specific rows."""
        logger.info("Testing reset_rows")

        # Set cell states in multiple rows
        self.manager.set_cell_state(0, 0, CellState.INVALID)
        self.manager.set_cell_state(0, 1, CellState.INVALID)
        self.manager.set_cell_state(1, 0, CellState.CORRECTABLE)
        self.manager.set_cell_state(1, 1, CellState.CORRECTABLE)
        self.manager.set_cell_state(2, 0, CellState.CORRECTED)

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Reset row 0
        self.manager.reset_rows([0])

        # Check row 0 is reset
        self.assertEqual(self.manager.get_cell_state(0, 0), CellState.NORMAL)
        self.assertEqual(self.manager.get_cell_state(0, 1), CellState.NORMAL)

        # Check other rows are not affected
        self.assertEqual(self.manager.get_cell_state(1, 0), CellState.CORRECTABLE)
        self.assertEqual(self.manager.get_cell_state(1, 1), CellState.CORRECTABLE)
        self.assertEqual(self.manager.get_cell_state(2, 0), CellState.CORRECTED)

        # Check signal is emitted
        self.assertTrue(self.signal_catcher.signal_received)

        logger.info("reset_rows test passed")

    def test_get_cells_by_state(self):
        """Test getting cells by state."""
        logger.info("Testing get_cells_by_state")

        # Set cell states
        self.manager.set_cell_state(0, 0, CellState.INVALID)
        self.manager.set_cell_state(0, 1, CellState.INVALID)
        self.manager.set_cell_state(1, 0, CellState.CORRECTABLE)
        self.manager.set_cell_state(1, 1, CellState.CORRECTED)

        # Get cells by state
        invalid_cells = self.manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self.manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self.manager.get_cells_by_state(CellState.CORRECTED)
        normal_cells = self.manager.get_cells_by_state(CellState.NORMAL)

        # Check the results
        self.assertEqual(len(invalid_cells), 2)
        self.assertEqual(len(correctable_cells), 1)
        self.assertEqual(len(corrected_cells), 1)
        self.assertEqual(len(normal_cells), 0)  # No normal cells set explicitly

        # Check specific cell coordinates
        self.assertIn((0, 0), invalid_cells)
        self.assertIn((0, 1), invalid_cells)
        self.assertIn((1, 0), correctable_cells)
        self.assertIn((1, 1), corrected_cells)

        logger.info("get_cells_by_state test passed")

    def test_cell_details(self):
        """Test setting and getting cell details."""
        logger.info("Testing cell details")

        # Set cell details
        self.manager.set_cell_detail(0, 0, "Test detail")

        # Get cell details
        detail = self.manager.get_cell_details(0, 0)

        # Check the result
        self.assertEqual(detail, "Test detail")

        # Check default value for undefined cell
        default_detail = self.manager.get_cell_details(1, 1)
        self.assertEqual(default_detail, "")

        logger.info("cell details test passed")

    def test_update_cell_states_from_validation(self):
        """Test updating cell states from validation status."""
        logger.info("Testing update_cell_states_from_validation")

        # Create a mock validation status
        validation_status = pd.DataFrame(
            [
                {"row": 0, "column": "Column1", "status": "invalid", "message": "Test error"},
                {"row": 1, "column": "Column2", "status": "invalid", "message": "Another error"},
            ]
        )

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Update cell states
        self.manager.update_cell_states_from_validation(validation_status)

        # Check cell states
        self.assertEqual(self.manager.get_cell_state(0, 0), CellState.INVALID)  # Column1 is index 0
        self.assertEqual(self.manager.get_cell_state(1, 1), CellState.INVALID)  # Column2 is index 1

        # Check signal is emitted
        self.assertTrue(self.signal_catcher.signal_received)

        logger.info("update_cell_states_from_validation test passed")

    def test_update_cell_states_from_correction(self):
        """Test updating cell states from correction status."""
        logger.info("Testing update_cell_states_from_correction")

        # Create a mock correction status
        correction_status = pd.DataFrame(
            [
                {
                    "row": 0,
                    "column": "Column1",
                    "status": "corrected",
                    "message": "Test correction",
                },
                {
                    "row": 1,
                    "column": "Column2",
                    "status": "correctable",
                    "message": "Can be corrected",
                },
            ]
        )

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Update cell states
        self.manager.update_cell_states_from_correction(correction_status)

        # Check cell states
        self.assertEqual(
            self.manager.get_cell_state(0, 0), CellState.CORRECTED
        )  # Column1 is index 0
        self.assertEqual(
            self.manager.get_cell_state(1, 1), CellState.CORRECTABLE
        )  # Column2 is index 1

        # Check signal is emitted
        self.assertTrue(self.signal_catcher.signal_received)

        logger.info("update_cell_states_from_correction test passed")

    def test_signal_emission(self):
        """Test signal emission behavior."""
        logger.info("Testing signal emission")

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Set cell state - no signal should be emitted
        self.manager.set_cell_state(0, 0, CellState.INVALID)
        self.assertFalse(self.signal_catcher.signal_received)

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Manually emit the signal
        self.manager.state_changed.emit()
        self.assertTrue(self.signal_catcher.signal_received)

        # Reset the signal catcher
        self.signal_catcher.reset()

        # Reset cell states - signal should be emitted automatically
        self.manager.reset_cell_states()
        self.assertTrue(self.signal_catcher.signal_received)

        logger.info("signal emission test passed")


def run_tests():
    """Run the tests."""
    logger.info("Starting TableStateManager tests")
    unittest.main(argv=["first-arg-is-ignored"], exit=False)


if __name__ == "__main__":
    run_tests()
