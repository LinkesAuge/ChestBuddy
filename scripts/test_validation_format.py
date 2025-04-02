"""
test_validation_format.py

Description: Test script for verifying TableStateManager's handling of validation status formats
Usage:
    python scripts/test_validation_format.py
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from PySide6.QtWidgets import QApplication
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager

# Use the correct ValidationStatus enum that has CORRECTABLE
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger()


class TestValidationFormat:
    """Test class for validation format handling."""

    def __init__(self):
        """Initialize the test environment."""
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.config_manager = ConfigManager()
        logger.debug("Starting validation format test")

        # Create ChestDataModel instance
        self.data_model = ChestDataModel()

        # Create TableStateManager instance
        self.table_state_manager = TableStateManager(self.data_model)

        # Create test data
        self._create_test_data()

        # Create validation status using ValidationStatus.INVALID enum values
        self._create_validation_status_with_enum()

        # Test update_cell_states_from_validation
        self._test_update_cell_states()

    def _create_test_data(self):
        """Create test data for the ChestDataModel."""
        # Create a small DataFrame for testing
        data = {
            "PLAYER": ["Player1", "Player2", "Player3", "Player4"],
            "SOURCE": ["Source1", "Source2", "Source3", "Source4"],
            "CHEST": ["Chest1", "Chest2", "Chest3", "Chest4"],
            "SCORE": [100, 200, 300, 400],
        }
        df = pd.DataFrame(data)
        self.data_model.update_data(df)
        logger.debug(f"Created test data with shape: {df.shape}")

    def _create_validation_status_with_enum(self):
        """Create validation status DataFrame with ValidationStatus enum values."""
        # Create validation status
        validation_data = {
            "PLAYER_status": [
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
            ],
            "CHEST_status": [
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
            ],
            "SOURCE_status": [
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
            ],
            "SCORE_status": [
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.CORRECTABLE,
            ],
        }
        self.validation_status = pd.DataFrame(validation_data)
        logger.debug(f"Created validation status with enum values")
        logger.debug(f"Validation status sample: {self.validation_status.iloc[0].to_dict()}")

    def _test_update_cell_states(self):
        """Test the update_cell_states_from_validation method."""
        try:
            # Log the validation status details
            logger.debug(f"Calling update_cell_states_from_validation with validation status")
            logger.debug(f"Validation status DataFrame shape: {self.validation_status.shape}")
            logger.debug(f"Validation status columns: {self.validation_status.columns.tolist()}")

            # Update cell states
            self.table_state_manager.update_cell_states_from_validation(self.validation_status)

            # Verify results
            invalid_cells = self.table_state_manager.get_cells_by_state(CellState.INVALID)
            correctable_cells = self.table_state_manager.get_cells_by_state(CellState.CORRECTABLE)

            logger.debug(f"Invalid cells: {invalid_cells}")
            logger.debug(f"Correctable cells: {correctable_cells}")

            # Check if cells are properly marked
            expected_invalid = [
                (0, 1),
                (1, 3),
                (2, 2),
            ]  # (row, col) for PLAYER, CHEST, SOURCE columns
            expected_correctable = [(3, 4)]  # (row, col) for SCORE column

            all_correct = True
            for cell in expected_invalid:
                if cell not in invalid_cells:
                    logger.error(f"Cell {cell} should be INVALID but it's not")
                    all_correct = False

            for cell in expected_correctable:
                if cell not in correctable_cells:
                    logger.error(f"Cell {cell} should be CORRECTABLE but it's not")
                    all_correct = False

            if all_correct:
                logger.debug("All cells are correctly marked with their expected states")
            else:
                logger.error("Some cells are not correctly marked")
                raise AssertionError("Validation status not properly applied")

        except Exception as e:
            logger.error(f"Error testing update_cell_states_from_validation: {e}")
            raise


if __name__ == "__main__":
    test = TestValidationFormat()
    sys.exit(0)
