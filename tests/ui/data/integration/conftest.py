import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication  # Needed for qtbot
from PySide6.QtCore import Signal  # Import Signal
from unittest.mock import MagicMock

# Import the necessary classes
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager
from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.ui.data.models.filter_model import FilterModel

# Import services
from chestbuddy.core.services import CorrectionService, ValidationService

# Import ServiceLocator
from chestbuddy.utils.service_locator import ServiceLocator


# Fixture to automatically clear ServiceLocator before/after tests
@pytest.fixture(autouse=True)
def clear_service_locator():
    ServiceLocator.clear()
    yield
    ServiceLocator.clear()


@pytest.fixture(scope="function")
def mock_validation_service(qtbot):
    """Provides a mock ValidationService instance."""
    # Create a mock that behaves like a QObject for signals
    mock_service = MagicMock(spec=ValidationService)
    mock_service.validation_changed = MagicMock(spec=Signal)
    mock_service.status_message_changed = MagicMock(spec=Signal)
    mock_service.validate_data = MagicMock()
    # Add other methods/attributes as needed by tests
    return mock_service


@pytest.fixture(scope="function")
def mock_correction_service(qtbot):
    """Provides a mock CorrectionService instance."""
    mock_service = MagicMock(spec=CorrectionService)
    mock_service.correction_suggestions_available = MagicMock(spec=Signal)
    mock_service.apply_ui_correction = MagicMock(return_value=True)  # Assume success
    mock_service.find_and_emit_suggestions = MagicMock()
    # Add other methods/attributes as needed by tests
    return mock_service


@pytest.fixture(scope="function")
def data_model(qtbot):
    """Provides a fresh ChestDataModel instance for each test."""
    return ChestDataModel()


@pytest.fixture(scope="function")
def table_state_manager(qtbot, data_model):
    """Provides a fresh TableStateManager instance linked to the data_model."""
    manager = TableStateManager(data_model)
    # Connect necessary signals if needed for tests, e.g.:
    # data_model.data_changed.connect(manager.handle_data_change)
    return manager


@pytest.fixture(scope="function")
def data_view_model(qtbot, data_model, table_state_manager):
    """Provides a fresh DataViewModel instance."""
    # Pass the state_manager to the view_model constructor
    view_model = DataViewModel(source_model=data_model, state_manager=table_state_manager)
    return view_model


@pytest.fixture(scope="function")
def filter_model(qtbot, data_view_model):
    """Provides a FilterModel wrapping the DataViewModel."""
    f_model = FilterModel()
    f_model.setSourceModel(data_view_model)
    return f_model


@pytest.fixture(scope="function")
def data_table_view(
    qtbot,
    filter_model,
    data_view_model,
    table_state_manager,
    mock_validation_service,
    mock_correction_service,
):
    """Provides a fresh DataTableView instance linked to the models and registers mock services."""
    # Register mock services BEFORE creating the view
    ServiceLocator.register("validation_service", mock_validation_service)
    ServiceLocator.register("correction_service", mock_correction_service)

    # Create the container view widget
    view_widget = DataTableView()
    # Set the model on the *internal* QTableView instance
    view_widget.table_view.setModel(filter_model)

    qtbot.addWidget(view_widget)
    view_widget.show()
    return view_widget
