"""
Common fixtures for DataView UI tests.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, QObject, Signal
from PySide6.QtWidgets import QApplication

# Import real services
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.table_state_manager import (
    TableStateManager,
    CellState,
    CellFullState,
)  # Add CellFullState

# Placeholder types until actual classes are importable/defined
import typing

ChestDataModel = typing.NewType("ChestDataModel", object)
# TableStateManager = typing.NewType("TableStateManager", object) # Use real import
# ValidationService = typing.NewType("ValidationService", object) # Use real import
# CorrectionService = typing.NewType("CorrectionService", object) # Use real import


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        # Use QApplication([]) for non-GUI tests if needed
        # For GUI tests, ensure QApplication exists
        app = QApplication([])
    yield app


@pytest.fixture
def mock_chest_data_model(mocker):
    """Create a mock ChestDataModel for testing."""
    # Removed spec=ChestDataModel to allow adding arbitrary attributes/methods
    model = mocker.MagicMock()
    # Setup default behavior for required methods
    model.data = mocker.Mock(return_value="test_data")
    model.rowCount.return_value = 10
    model.columnCount.return_value = 5
    # Add flags method mock
    model.flags.return_value = Qt.ItemIsEnabled | Qt.ItemIsSelectable
    # Add setData method mock
    model.setData.return_value = True
    # Add headerData method mock
    model.headerData.return_value = "Header"
    # Add createIndex method mock (returns a basic QModelIndex for testing)
    # Use a real QModelIndex for compatibility
    model.createIndex = lambda row, col, parent=None: QModelIndex()  # Needs model instance if used?
    # Add methods required by QAbstractTableModel if ChestDataModel inherits from it
    # model.index = mocker.Mock(return_value=QModelIndex()) # Example if needed

    # Add the missing has_data attribute
    model.has_data = True  # Default to True for most tests

    return model


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(
        {
            "A": ["A1", "A2", "A3", "A4", "A5"],
            "B": ["B1", "B2", "B3", "B4", "B5"],
            "C": [1, 2, 3, 4, 5],
            "D": [10.1, 20.2, 30.3, 40.4, 50.5],
            "E": [True, False, True, False, True],
        }
    )
    return df


@pytest.fixture
def mock_validation_service(mocker):
    """Create a mock ValidationService for testing."""
    # Keep spec for type checking where possible
    service = mocker.MagicMock(spec=ValidationService)
    # Ensure necessary signals exist if services emit signals
    # service.validation_complete = Signal(object) # Example if service has signals
    return service


@pytest.fixture
def mock_correction_service(mocker):
    """Create a mock CorrectionService for testing."""
    # Keep spec for type checking where possible
    service = mocker.MagicMock(spec=CorrectionService)
    # service.correction_available = Signal(object) # Example if service has signals
    return service


@pytest.fixture
def mock_table_state_manager(mocker):
    """Create a mock TableStateManager for testing with the new API."""
    # Use MagicMock without spec to easily add attributes/methods
    manager = mocker.MagicMock()

    # Mock the state_changed signal
    # We need a real QObject to host the signal
    class SignalHost(QObject):
        state_changed = Signal(set)

    manager._signal_host = SignalHost()  # Keep reference
    manager.state_changed = manager._signal_host.state_changed

    # Mock get_full_cell_state method
    # Default to returning None (no specific state)
    manager.get_full_cell_state = mocker.Mock(return_value=None)

    # Mock get_cell_state (can derive from get_full_cell_state mock if needed,
    # but DataViewModel might not call it directly anymore)
    manager.get_cell_state = mocker.Mock(return_value=CellState.NORMAL)

    # Mock get_cell_details (similar to get_cell_state)
    manager.get_cell_details = mocker.Mock(return_value="")

    # Mock update_states (if needed by specific tests, can be spied on)
    manager.update_states = mocker.Mock()

    # Mock get_column_names (needed by adapters)
    manager.get_column_names = mocker.Mock(return_value=["ColA", "ColB"])  # Example

    return manager


# Make sure CellState is imported if used in mocks
from chestbuddy.core.table_state_manager import CellState, CellFullState  # Add CellFullState


# --- Add new fixtures for real services ---
@pytest.fixture
def real_validation_service():
    """Provide a real instance of the ValidationService."""
    # Add any necessary setup for the real service if needed
    # e.g., providing mock dependencies if the service requires them
    return ValidationService()


@pytest.fixture
def real_correction_service():
    """Provide a real instance of the CorrectionService."""
    # Add any necessary setup for the real service if needed
    return CorrectionService()


# --- End of new fixtures ---
