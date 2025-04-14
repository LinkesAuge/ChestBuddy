"""
test_validation_integration.py

Integration tests for the validation workflow involving:
- ChestDataModel
- ValidationService
- ValidationAdapter
- TableStateManager
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from PySide6.QtCore import (
    QObject,
    Signal,
    QCoreApplication,
)  # Import QCoreApplication for event loop

# Import necessary classes (adjust paths if needed based on actual structure)
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.utils.config import ConfigManager  # May need mock or temp config


# --- Fixtures ---


@pytest.fixture(scope="function")
def qt_app():
    """Create a QCoreApplication instance for signal processing."""
    app = QCoreApplication.instance()
    if app is None:
        # Create a new instance if one doesn't exist
        # Using sys.argv or an empty list is common practice
        import sys

        app = QCoreApplication(sys.argv if hasattr(sys, "argv") else [])
    yield app
    # Cleanup if necessary, though usually not needed for QCoreApplication in tests
    # QCoreApplication.quit()


@pytest.fixture
def mock_config_manager():
    """Provides a mock ConfigManager."""
    # Mock essential methods if ValidationService uses them during init/validation
    mock = MagicMock(spec=ConfigManager)
    mock.get_bool.side_effect = lambda section, key, default: default  # Return defaults
    mock.get.return_value = None  # Default for paths etc.
    # Add mocks for set/save if needed by tests
    mock.set = MagicMock()
    mock.save = MagicMock()
    return mock


@pytest.fixture
def chest_data_model():
    """Provides an empty ChestDataModel instance."""
    return ChestDataModel()


@pytest.fixture
def table_state_manager(chest_data_model):
    """Provides a TableStateManager linked to the data model."""
    return TableStateManager(chest_data_model)


@pytest.fixture
def validation_service(chest_data_model, mock_config_manager):
    """Provides a ValidationService instance."""
    # Pass the mock config manager
    service = ValidationService(data_model=chest_data_model, config_manager=mock_config_manager)
    # Reset validation lists for isolated tests (important!)
    # You might need to mock _resolve_validation_path or ensure test files exist
    # For simplicity, let's mock list models directly for now
    service._player_list_model = MagicMock()
    service._player_list_model.contains.return_value = True  # Assume all valid by default
    service._player_list_model.get_entries.return_value = ["ValidPlayer1"]

    service._chest_type_list_model = MagicMock()
    service._chest_type_list_model.contains.return_value = True
    service._chest_type_list_model.get_entries.return_value = ["ValidChest1"]

    service._source_list_model = MagicMock()
    service._source_list_model.contains.return_value = True
    service._source_list_model.get_entries.return_value = ["ValidSource1"]

    return service


@pytest.fixture
def validation_adapter(validation_service, table_state_manager):
    """Provides a ValidationAdapter connecting the service and state manager."""
    adapter = ValidationAdapter(
        validation_service=validation_service,
        table_state_manager=table_state_manager,
    )
    yield adapter
    # Cleanup: Disconnect signals after test finishes
    adapter.disconnect_signals()


# --- Test Cases ---


def test_validation_flow_updates_state_manager(
    qt_app,  # Include qt_app fixture to ensure event loop runs for signals
    chest_data_model,
    validation_service,
    validation_adapter,
    table_state_manager,
):
    """
    Test the full flow: data load -> validate -> adapter -> state manager update.
    """
    # 1. Arrange: Load sample data into the model
    sample_data = pd.DataFrame(
        {
            "PLAYER": ["ValidPlayer1", "InvalidPlayer", "ValidPlayer1"],
            "CHEST": ["ValidChest1", "ValidChest1", "InvalidChest"],
            "SOURCE": ["ValidSource1", "InvalidSource", "ValidSource1"],
            # Add other columns if validation rules depend on them
        }
    )
    chest_data_model.update_data(sample_data)
    # Ensure headers map is updated after loading data
    table_state_manager.update_headers_map()

    # Configure mock validation lists for this specific test scenario
    validation_service._player_list_model.contains = lambda x: x == "ValidPlayer1"
    validation_service._chest_type_list_model.contains = lambda x: x == "ValidChest1"
    validation_service._source_list_model.contains = lambda x: x == "ValidSource1"

    # We ONLY expect updates for cells whose state *changed* from NORMAL to INVALID
    # Indices must match the actual column order: DATE(0), PLAYER(1), SOURCE(2), CHEST(3), ...
    expected_updated_states = {
        # Row 1: Invalid Player(1) and Source(2)
        (1, 1): CellFullState(
            validation_status=CellState.INVALID,
            error_details="Invalid player name: InvalidPlayer",
            correction_suggestions=[],
        ),
        (1, 2): CellFullState(
            validation_status=CellState.INVALID,
            error_details="Invalid source: InvalidSource",
            correction_suggestions=[],
        ),
        # Row 2: Invalid Chest(3)
        (2, 3): CellFullState(
            validation_status=CellState.INVALID,
            error_details="Invalid chest type: InvalidChest",
            correction_suggestions=[],
        ),
    }

    # Use patch.object to spy on update_states while letting it execute
    with patch.object(
        table_state_manager, "update_states", wraps=table_state_manager.update_states
    ) as update_states_spy:
        # 2. Act: Trigger validation for specific list rules only
        validation_service.validate_data(
            specific_rules=["player_validation", "chest_type_validation", "source_validation"]
        )

        # Allow signals to be processed by the Qt event loop
        qt_app.processEvents()

        # 3. Assert: Check if the spy was called correctly
        assert update_states_spy.call_count == 1, (
            f"Expected update_states to be called once, but was called {update_states_spy.call_count} times."
        )

        # Get the actual argument passed to the update_states spy
        call_args, _ = update_states_spy.call_args
        actual_updated_states = call_args[0]  # The dictionary passed to update_states

        # Assert the dictionary passed to update_states matches the expected changes
        assert actual_updated_states == expected_updated_states, (
            f"Mismatch in updated states.\nExpected: {expected_updated_states}\nActual: {actual_updated_states}"
        )

    # Assert outside the patch context, after the original method has run
    # Ensure the ones that changed are INVALID (using correct indices)
    assert (
        table_state_manager.get_full_cell_state(1, 1).validation_status == CellState.INVALID
    )  # Player
    assert (
        table_state_manager.get_full_cell_state(1, 1).error_details
        == "Invalid player name: InvalidPlayer"
    )
    assert (
        table_state_manager.get_full_cell_state(1, 2).validation_status == CellState.INVALID
    )  # Source
    assert (
        table_state_manager.get_full_cell_state(1, 2).error_details
        == "Invalid source: InvalidSource"
    )
    assert (
        table_state_manager.get_full_cell_state(2, 3).validation_status == CellState.INVALID
    )  # Chest
    assert (
        table_state_manager.get_full_cell_state(2, 3).error_details
        == "Invalid chest type: InvalidChest"
    )

    # Ensure the ones that were valid according to list rules were NOT added to _cell_states
    # and thus get_full_cell_state returns None (representing the default NORMAL state implicitly)
    assert table_state_manager.get_full_cell_state(0, 0) is None  # DATE
    assert table_state_manager.get_full_cell_state(0, 1) is None  # PLAYER
    assert table_state_manager.get_full_cell_state(0, 2) is None  # SOURCE
    assert table_state_manager.get_full_cell_state(0, 3) is None  # CHEST
    assert table_state_manager.get_full_cell_state(0, 4) is None  # SCORE
    assert table_state_manager.get_full_cell_state(0, 5) is None  # CLAN
    assert table_state_manager.get_full_cell_state(1, 3) is None  # Valid Chest
    assert table_state_manager.get_full_cell_state(2, 1) is None  # Valid Player
    assert table_state_manager.get_full_cell_state(2, 2) is None  # Valid Source


# Add more integration tests:
# - Test with different validation rules (missing values, duplicates, etc.)
# - Test interaction with CorrectionService if relevant
# - Test edge cases (empty data, data with only invalid values, etc.)
# - Test case sensitivity if configured
