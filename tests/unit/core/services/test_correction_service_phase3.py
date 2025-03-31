"""
Test cases for the Phase 3 correction service improvements.

This file contains tests specifically for:
1. get_cells_with_available_corrections - Only returning invalid cells with matching rules
2. check_correctable_status - Marking invalid cells with matching rules as correctable
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.enums.validation_enums import ValidationStatus


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return pd.DataFrame(
        {
            "Player": ["player1", "player2", "player3", "unknown"],
            "ChestType": ["chest1", "chest2", "chest3", "legendary chest"],
            "Source": ["source1", "source2", "unknown", "source3"],
            "Date": ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
        }
    )


@pytest.fixture
def sample_rules():
    """Sample correction rules for testing."""
    return [
        CorrectionRule(
            from_value="player1", to_value="Player1", category="player", status="enabled"
        ),
        CorrectionRule(
            from_value="player2", to_value="Player2", category="player", status="enabled"
        ),
        CorrectionRule(
            from_value="player3", to_value="Player3", category="player", status="enabled"
        ),
        CorrectionRule(from_value="chest1", to_value="Chest1", category="chest", status="enabled"),
        CorrectionRule(from_value="chest2", to_value="Chest2", category="chest", status="enabled"),
        CorrectionRule(from_value="chest3", to_value="Chest3", category="chest", status="enabled"),
        CorrectionRule(
            from_value="source1", to_value="Source1", category="source", status="enabled"
        ),
        CorrectionRule(
            from_value="source2", to_value="Source2", category="source", status="enabled"
        ),
        CorrectionRule(
            from_value="source3", to_value="Source3", category="source", status="enabled"
        ),
        CorrectionRule(
            from_value="unknown", to_value="Known", category="general", status="enabled"
        ),
        CorrectionRule(
            from_value="legendary chest",
            to_value="Legendary Chest",
            category="chest",
            status="disabled",
        ),
    ]


@pytest.fixture
def rule_manager(sample_rules):
    """Rule manager with sample rules."""
    manager = MagicMock(spec=CorrectionRuleManager)
    manager.get_rules.return_value = [r for r in sample_rules if r.status == "enabled"]
    return manager


@pytest.fixture
def mock_data_model(sample_data):
    """Mock data model with sample data."""
    model = MagicMock()
    model.data = sample_data
    model.get_data.return_value = sample_data
    return model


@pytest.fixture
def mock_validation_service():
    """Mock validation service."""
    service = MagicMock()

    # Create validation status DataFrame with invalid cells
    validation_status = pd.DataFrame(
        {
            "Player_valid": [
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
            ],
            "ChestType_valid": [
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
            ],
            "Source_valid": [
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.INVALID,
                ValidationStatus.VALID,
            ],
            "Date_valid": [
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
                ValidationStatus.VALID,
            ],
        }
    )
    service.get_validation_status.return_value = validation_status

    return service


class TestCorrectionServicePhase3:
    """Test cases for the Phase 3 correction service improvements."""

    def test_get_correctable_cells(
        self, rule_manager, mock_data_model, mock_validation_service, sample_data
    ):
        """Test that get_cells_with_available_corrections only returns invalid cells with matching rules."""
        # Configure mock data model to return our sample data
        mock_data_model.data = sample_data

        # Create service with data_model only, then set the other attributes
        service = CorrectionService(mock_data_model)
        service._rule_manager = rule_manager
        service._validation_service = mock_validation_service

        # Set up the category mapping
        service._category_mapping = {
            "PLAYER": "player",
            "CHESTTYPE": "chest",
            "SOURCE": "source",
            "DATE": "date",
        }

        # Define a simple values_match method for testing
        service._values_match = lambda a, b: a.lower() == b.lower()

        # Get cells with available corrections
        correctable_cells = service.get_cells_with_available_corrections()

        # These cells are detected based on:
        # 1. player1 (row 0, col 0) - Invalid with matching rule
        # 2. chest2 (row 1, col 1) - Invalid with matching rule
        # 3. player3 (row 2, col 0) - Invalid with matching rule
        # 4. unknown in Source (row 2, col 2) - Invalid with matching rule for 'Known'

        # Should not include:
        # 1. Player2 (row 1, col 0) - Valid with matching rule
        # 2. chest3 (row 2, col 1) - Valid with matching rule
        # 3. legendary chest (row 3, col 1) - Invalid but rule is disabled

        # Assert correctable cells are correct
        assert len(correctable_cells) == 4
        assert (0, 0) in correctable_cells  # player1 in Player
        assert (1, 1) in correctable_cells  # chest2 in ChestType
        assert (2, 0) in correctable_cells  # player3 in Player
        assert (2, 2) in correctable_cells  # unknown in Source

    def test_check_correctable_status_method(self, mock_data_model, mock_validation_service):
        """Test that check_correctable_status correctly updates the validation status."""
        # Create service with data_model only, then set the other attributes
        service = CorrectionService(mock_data_model)
        service._validation_service = mock_validation_service

        # Mock get_cells_with_available_corrections to return our expected correctable cells
        service.get_cells_with_available_corrections = MagicMock(
            return_value=[(0, 0), (1, 1), (2, 0), (2, 2)]
        )

        # Call the method
        correctable_count = service.check_correctable_status()

        # Assert the count is correct
        assert correctable_count == 4

        # Verify validation_service.update_correctable_status was called with the correctable cells
        mock_validation_service.update_correctable_status.assert_called_once_with(
            [(0, 0), (1, 1), (2, 0), (2, 2)]
        )
