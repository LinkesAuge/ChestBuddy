"""
test_validation_format.py

Description: Test script for validating the fix for handling 'validationstatus.invalid' format
Usage:
    python -m scripts.test_validation_format
"""

import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_validation_format():
    """Test the fix for handling different validation status formats."""
    logger.info("Starting validation format test")

    # Create a data model with sample data
    data_model = ChestDataModel()
    sample_data = pd.DataFrame(
        {
            "PLAYER": ["John", "Alice", "Bob", "Charlie"],
            "CHEST": ["Gold", "Silver", "Bronze", "Diamond"],
            "SOURCE": ["Quest", "Daily", "Season", "Event"],
            "SCORE": [100, 75, 50, 125],
        }
    )
    data_model.update_data(sample_data)
    logger.info(f"Created data model with {len(sample_data)} rows")

    # Create a TableStateManager
    manager = TableStateManager(data_model)
    logger.info("Created TableStateManager")

    # Create a validation status DataFrame with our format to test
    validation_status = pd.DataFrame(
        {
            "PLAYER_status": ["validationstatus.invalid", "True", "True", "True"],
            "CHEST_status": ["True", "validationstatus.invalid", "True", "True"],
            "SOURCE_status": ["True", "True", "validationstatus.invalid", "True"],
            "SCORE_status": ["True", "True", "True", "validationstatus.correctable"],
        },
        index=range(4),
    )

    logger.info("Created validation status with 'validationstatus.invalid' format")
    logger.info(f"Validation status columns: {validation_status.columns.tolist()}")
    logger.info(f"Validation status sample:\n{validation_status}")

    # Update cell states from validation
    manager.update_cell_states_from_validation(validation_status)
    logger.info("Updated cell states from validation status")

    # Check results
    invalid_cells = manager.get_cells_by_state(CellState.INVALID)
    correctable_cells = manager.get_cells_by_state(CellState.CORRECTABLE)

    logger.info(f"Invalid cells: {invalid_cells}")
    logger.info(f"Correctable cells: {correctable_cells}")

    # Test if the expected cells are marked as invalid
    expected_invalid = [(0, 1), (1, 3), (2, 2)]  # Row, Col (DataModel indexing)
    expected_correctable = [(3, 4)]

    success = True

    # Check invalid cells
    for cell in expected_invalid:
        if cell not in invalid_cells:
            logger.error(f"Expected cell {cell} to be invalid, but it was not")
            success = False

    # Check correctable cells
    for cell in expected_correctable:
        if cell not in correctable_cells:
            logger.error(f"Expected cell {cell} to be correctable, but it was not")
            success = False

    # Final result
    if success:
        logger.info("TEST PASSED: All cells were correctly marked with their expected states")
    else:
        logger.error("TEST FAILED: Some cells were not correctly marked")

    return success


if __name__ == "__main__":
    test_result = test_validation_format()
    sys.exit(0 if test_result else 1)
