"""
Common fixtures for DataView UI tests.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication

# Placeholder types until actual classes are importable/defined
import typing

ChestDataModel = typing.NewType("ChestDataModel", object)
TableStateManager = typing.NewType("TableStateManager", object)
ValidationService = typing.NewType("ValidationService", object)
CorrectionService = typing.NewType("CorrectionService", object)


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
    service = mocker.MagicMock(spec=ValidationService)
    return service


@pytest.fixture
def mock_correction_service(mocker):
    """Create a mock CorrectionService for testing."""
    service = mocker.MagicMock(spec=CorrectionService)
    return service


@pytest.fixture
def mock_table_state_manager(mocker):
    """Create a mock TableStateManager for testing."""
    manager = mocker.MagicMock(spec=TableStateManager)
    manager.get_cell_state.return_value = "NORMAL"  # Default state
    # Add other necessary methods if DataViewModel interacts with them
    # manager.update_cell_states_from_validation = mocker.Mock()
    # manager.cell_states_changed = Signal() # Need to mock signals if used
    return manager
