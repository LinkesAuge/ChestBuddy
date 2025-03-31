"""
Tests for the correctable status detection in ValidationService.

Verifies that the validation service can detect cells that have available corrections.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.models.correction_rule import CorrectionRule


@pytest.fixture
def mock_data_model():
    """Create a mock ChestDataModel with test data."""
    model = MagicMock(spec=ChestDataModel)

    # Create test data
    data = pd.DataFrame(
        {
            "PLAYER": ["player1", "player2", "player3", "player4"],
            "CHEST": ["Gold", "Silver", "Bronze", "Platinum"],
            "SOURCE": ["daily", "weekly", "river", "race"],
        }
    )

    # Set up model mock to return the data
    model.data = data
    model.EXPECTED_COLUMNS = ["PLAYER", "CHEST", "SOURCE"]

    return model


@pytest.fixture
def mock_correction_service():
    """Create a mock CorrectionService."""
    service = MagicMock(spec=CorrectionService)

    # Set up the correction service mock
    service.get_cells_with_available_corrections.return_value = [
        (0, 0),  # player1 -> Player One
        (1, 1),  # Silver -> Silver Chest
    ]

    return service


def test_detect_correctable_entries(mock_data_model, mock_correction_service):
    """Test the dedicated method for detecting correctable entries."""
    # Create validation service
    validation_service = ValidationService(mock_data_model)

    # Patch the correction service
    validation_service._correction_service = mock_correction_service

    # Call the method
    correctable_cells = validation_service.detect_correctable_entries()

    # Verify the result matches what the correction service returns
    expected_cells = mock_correction_service.get_cells_with_available_corrections()
    assert correctable_cells == expected_cells, (
        "Should correctly identify cells with available corrections"
    )


def test_get_validation_summary_includes_correctables(mock_data_model, mock_correction_service):
    """Test that get_validation_summary includes correctable status."""
    # Create validation service with mock dependencies
    validation_service = ValidationService(mock_data_model)
    validation_service._correction_service = mock_correction_service

    # Create a mock validation status DataFrame for the data model to return
    status_df = pd.DataFrame(index=range(4))
    for col in mock_data_model.EXPECTED_COLUMNS:
        status_df[f"{col}_valid"] = True
        status_df[f"{col}_status"] = ValidationStatus.VALID

    # Set some specific statuses for testing
    status_df.at[0, "PLAYER_status"] = ValidationStatus.CORRECTABLE
    status_df.at[1, "CHEST_status"] = ValidationStatus.CORRECTABLE
    status_df.at[2, "PLAYER_status"] = ValidationStatus.INVALID

    # Patch the model to return our mock status
    with patch.object(mock_data_model, "get_validation_status", return_value=status_df):
        with patch("chestbuddy.core.services.validation_service.logger"):
            # Get the validation summary
            summary = validation_service.get_validation_summary()

            # Check that the summary includes the correctable count
            assert "correctable" in summary, "Summary should include correctable count"
            assert summary["correctable"] == 2, "Summary should show 2 correctable cells"


def test_mark_correctable_entries(mock_data_model, mock_correction_service):
    """Test that validation service correctly marks entries as correctable."""
    # Create validation service
    validation_service = ValidationService(mock_data_model)

    # Set up the data model
    mock_data = pd.DataFrame(
        {
            "PLAYER": ["player1", "player2", "player3", "player4"],
            "CHEST": ["Gold", "Silver", "Bronze", "Platinum"],
            "SOURCE": ["daily", "weekly", "river", "race"],
        }
    )
    mock_data_model.data = mock_data

    # Set up the correction service
    validation_service._correction_service = mock_correction_service

    # Create a basic validation status DataFrame with some cells marked as invalid
    status_df = pd.DataFrame(index=range(4))
    columns = ["PLAYER", "CHEST", "SOURCE"]

    for col in columns:
        status_df[f"{col}_valid"] = True
        status_df[f"{col}_status"] = ValidationStatus.VALID
        status_df[f"{col}_message"] = ""

    # Mark a specific cell as invalid
    status_df.at[0, "PLAYER_status"] = ValidationStatus.INVALID
    status_df.at[0, "PLAYER_valid"] = False

    # Mock the get_cells_with_available_corrections method
    correctable_cells = [(0, 0), (1, 1)]  # (row, col) pairs
    mock_correction_service.get_cells_with_available_corrections.return_value = correctable_cells

    # Make sure validation_service._data_model.data is not empty
    validation_service._data_model = mock_data_model

    # Call the method to mark correctable entries
    updated_df = validation_service._mark_correctable_entries(status_df)

    # Check that the correctable cells are marked as such
    assert updated_df.at[0, "PLAYER_status"] == ValidationStatus.CORRECTABLE
    assert updated_df.at[1, "CHEST_status"] == ValidationStatus.CORRECTABLE
    assert "Corrections available" in updated_df.at[0, "PLAYER_message"]
    assert "Corrections available" in updated_df.at[1, "CHEST_message"]
