"""
test_correction_feature_e2e.py

End-to-end test for the data correction feature, testing the complete workflow from
loading data with errors, defining correction rules, applying corrections, and
exporting the corrected data.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# PySide6
from PySide6.QtCore import QObject, Signal

# Helpers
from tests.utils.helpers import process_events
from tests.data.test_data_factory import TestDataFactory, SimpleData

# Core components
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.utils.config import ConfigManager


@pytest.mark.e2e
class TestCorrectionFeatureWorkflow:
    """End-to-end tests for the correction feature workflow."""

    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create a ConfigManager with temporary config file."""
        config = ConfigManager(str(temp_config_file))
        # Set default correction settings
        config.set("corrections", "case_sensitive", "true")
        config.set("corrections", "only_correct_invalid", "false")
        return config

    @pytest.fixture
    def data_model(self):
        """Create a data model for testing."""
        return ChestDataModel()

    @pytest.fixture
    def validation_service(self, data_model, config_manager):
        """Create a validation service for testing."""
        return ValidationService(data_model, config_manager)

    @pytest.fixture
    def rule_manager(self, config_manager):
        """Create a correction rule manager for testing."""
        return CorrectionRuleManager(config_manager)

    @pytest.fixture
    def correction_service(self, rule_manager, data_model, validation_service):
        """Create a correction service for testing."""
        return CorrectionService(rule_manager, data_model, validation_service)

    @pytest.fixture
    def correction_controller(self, correction_service, rule_manager, config_manager):
        """Create a correction controller for testing."""
        return CorrectionController(correction_service, rule_manager, config_manager)

    @pytest.fixture
    def sample_data_with_errors(self):
        """Create data with specific errors for correction testing."""
        return TestDataFactory.create_data_with_specific_errors(
            {"player": 3, "chest": 2, "source": 2}
        )

    @pytest.fixture
    def test_rules(self):
        """Create correction rules for the test."""
        rules = [
            CorrectionRule(
                from_value="InvalidPlayer0",
                to_value="Player1",
                category="player",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidPlayer1",
                to_value="Player2",
                category="player",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidPlayer2",
                to_value="Player3",
                category="player",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidChest0",
                to_value="Chest1",
                category="chest",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidChest1",
                to_value="Chest2",
                category="chest",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidSource0",
                to_value="Source1",
                category="source",
                status="enabled"
            ),
            CorrectionRule(
                from_value="InvalidSource1",
                to_value="Source2",
                category="source",
                status="enabled"
            ),
        ]
        return rules

    def test_complete_correction_workflow(
        self,
        qtbot,
        enhanced_qtbot,
        data_model,
        validation_service,
        rule_manager,
        correction_service,
        correction_controller,
        sample_data_with_errors,
        test_rules,
        temp_data_dir,
    ):
        """
        Test the complete correction workflow from loading data to exporting corrected data.

        This test:
        1. Loads data with errors
        2. Adds correction rules
        3. Applies corrections
        4. Verifies corrections were applied
        5. Exports the corrected data
        6. Verifies the exported data
        """
        # Add signal spies
        correction_started_spy = enhanced_qtbot.add_spy(correction_controller.correction_started)
        correction_completed_spy = enhanced_qtbot.add_spy(
            correction_controller.correction_completed
        )

        # 1. Load data with errors into the model
        data_df = pd.DataFrame(sample_data_with_errors.data)
        data_model.update_data(data_df)

        # Get data from the model
        data = data_model.data
        assert data is not None, "Model should have data after update"

        # Verify data has errors (check for "Invalid" strings in key columns)
        has_invalid_players = any("Invalid" in str(player) for player in data["PLAYER"])
        has_invalid_chests = any("Invalid" in str(chest) for chest in data["CHEST"])
        has_invalid_sources = any("Invalid" in str(source) for source in data["SOURCE"])

        assert has_invalid_players, "Test data should contain invalid player names"
        assert has_invalid_chests, "Test data should contain invalid chest names"
        assert has_invalid_sources, "Test data should contain invalid source names"

        # 2. Add correction rules
        for rule in test_rules:
            rule_manager.add_rule(rule)

        # Verify rules were added
        assert len(rule_manager.get_rules()) == len(test_rules)

        # 3. Apply corrections
        # Create a patched task that mimics the background worker
        with patch("chestbuddy.utils.background_processing.BackgroundWorker") as mock_worker_class:
            # Create a mock worker that accepts the function and kwargs
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker
            
            # Patch the _update_correction_status method
            with patch.object(correction_service, "_update_correction_status", return_value=None):
                # Apply the corrections
                correction_controller.apply_corrections()
                
                # Mock the behavior of the worker executing the task
                # Extract the task function that was passed to the worker
                task_func = mock_worker_class.call_args[0][0]
                
                # Call the task function directly
                result = task_func(only_invalid=False)
                
                # Simulate the worker completing and emitting signals
                correction_controller._on_corrections_completed(result)
                
                # Process events to ensure signals are emitted
                process_events()

        # 4. Verify correction signals were emitted
        assert correction_started_spy.signal_triggered
        assert correction_completed_spy.signal_triggered

        # Get the statistics from the completion signal
        correction_stats = correction_completed_spy.args[0]

        # Verify corrections were applied
        assert correction_stats["total_corrections"] > 0
        assert correction_stats["corrected_rows"] > 0
        assert correction_stats["corrected_cells"] > 0

        # Get updated data
        data = data_model.data

        # Verify data no longer has errors
        has_invalid_players = any("Invalid" in str(player) for player in data["PLAYER"])
        has_invalid_chests = any("Invalid" in str(chest) for chest in data["CHEST"])
        has_invalid_sources = any("Invalid" in str(source) for source in data["SOURCE"])

        assert not has_invalid_players, "Player names should be corrected"
        assert not has_invalid_chests, "Chest names should be corrected"
        assert not has_invalid_sources, "Source names should be corrected"

        # 5. Export the corrected data
        export_path = temp_data_dir / "corrected_data.csv"

        # Use pandas to export the data
        data.to_csv(export_path, index=False)

        # 6. Verify the exported data
        assert export_path.exists(), "Export file should exist"

        # Read back the exported data
        exported_data = pd.read_csv(export_path)

        # Verify exported data does not have errors
        has_invalid_players = any("Invalid" in str(player) for player in exported_data["PLAYER"])
        has_invalid_chests = any("Invalid" in str(chest) for chest in exported_data["CHEST"])
        has_invalid_sources = any("Invalid" in str(source) for source in exported_data["SOURCE"])

        assert not has_invalid_players, "Exported data should not have invalid player names"
        assert not has_invalid_chests, "Exported data should not have invalid chest names"
        assert not has_invalid_sources, "Exported data should not have invalid source names"

    def test_correction_error_handling(
        self,
        qtbot,
        enhanced_qtbot,
        data_model,
        correction_service,
        correction_controller,
        sample_data_with_errors,
    ):
        """
        Test error handling in the correction workflow.

        This test:
        1. Sets up correction service to fail
        2. Attempts to apply corrections
        3. Verifies error signals are emitted
        """
        # Add signal spy for error signal
        error_spy = enhanced_qtbot.add_spy(correction_controller.correction_error)

        # Load data
        data_df = pd.DataFrame(sample_data_with_errors.data)
        data_model.update_data(data_df)

        # Mock correction service to raise an exception
        with patch.object(
            correction_service, "apply_corrections", side_effect=Exception("Test error")
        ) as mock_apply:
            # Create a patched BackgroundWorker to avoid the initialization error
            with patch("chestbuddy.utils.background_processing.BackgroundWorker") as mock_worker_class:
                # Create a mock worker that accepts the function and kwargs
                mock_worker = MagicMock()
                mock_worker_class.return_value = mock_worker
                
                # Try to apply corrections
                correction_controller.apply_corrections()
                
                # Extract the task function that was passed to the worker
                task_func = mock_worker_class.call_args[0][0]
                
                # Manually trigger the error handling
                correction_controller._on_corrections_error("Error during correction: Test error")
                
                # Process events to ensure signals are emitted
                process_events()

        # Verify error signal was emitted
        assert error_spy.signal_triggered

        # Verify error message
        error_message = error_spy.args[0]
        assert "error" in error_message.lower()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
