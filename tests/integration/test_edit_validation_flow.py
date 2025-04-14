import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt, QModelIndex, QTimer
from PySide6.QtTest import QSignalSpy

# Assuming imports for necessary classes are correct
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.delegates.text_edit_delegate import TextEditDelegate
from chestbuddy.core.controllers.data_view_controller import DataViewController


# Fixtures (Consider moving to conftest.py if reused)
@pytest.fixture
def mock_config_manager():
    mock = MagicMock(spec=ConfigManager)
    mock.get_bool.side_effect = lambda section, key, default: default
    mock.get.side_effect = lambda section, key, fallback=None: fallback
    return mock


@pytest.fixture
def chest_data_model():
    model = ChestDataModel()
    # Load some sample data if needed for the tests
    # Example:
    # sample_df = pd.DataFrame({'PLAYER': ['PlayerA', 'PlayerB'], 'CHEST': ['Gold', 'Silver'], 'SOURCE': ['Titan', 'Event']})
    # model.set_data(sample_df)
    return model


@pytest.fixture
def validation_service(chest_data_model, mock_config_manager):
    service = ValidationService(chest_data_model, mock_config_manager)
    # Mock the validation list models within the service for controlled testing
    service._player_list_model = MagicMock(spec=ValidationListModel)
    service._chest_type_list_model = MagicMock(spec=ValidationListModel)
    service._source_list_model = MagicMock(spec=ValidationListModel)
    return service


@pytest.fixture
def table_state_manager():
    return TableStateManager()


@pytest.fixture
def data_view_model(chest_data_model, table_state_manager):
    model = DataViewModel(chest_data_model, table_state_manager)
    table_state_manager.set_model(model)  # Ensure manager knows model
    return model


@pytest.fixture
def data_table_view(qtbot, data_view_model, table_state_manager):
    view = DataTableView()
    view.setModel(data_view_model)
    view.set_state_manager(table_state_manager)
    # Set a default delegate (TextEditDelegate) for relevant columns
    # Assuming column 0 is PLAYER, 1 is CHEST, 2 is SOURCE
    delegate = TextEditDelegate(view)
    view.setItemDelegateForColumn(0, delegate)
    view.setItemDelegateForColumn(1, delegate)
    view.setItemDelegateForColumn(2, delegate)
    # IMPORTANT: Connect delegate signals AFTER setting them
    view.connect_delegate_signals()
    qtbot.addWidget(view)
    return view


@pytest.fixture
def data_view_controller(data_view_model, table_state_manager, validation_service, data_table_view):
    # Mock dependencies for the controller if they are complex
    controller = DataViewController(data_view_model, table_state_manager, validation_service)
    # Assume controller connects to view signals internally or via a separate method
    # controller.connect_view(data_table_view)
    return controller


# --- Test Class ---


class TestEditValidationFlow:
    def test_valid_edit_triggers_validation_and_updates_state(
        self,
        qtbot,
        data_table_view,
        data_view_model,
        validation_service,
        table_state_manager,
        data_view_controller,
    ):
        """Test editing a cell with valid data triggers validation and sets VALID state."""
        # Arrange: Mock service to return VALID
        validation_service._player_list_model.validate.return_value = (ValidationStatus.VALID, "")

        # Add some data to the model to ensure index is valid
        sample_df = pd.DataFrame(
            {"PLAYER": ["PlayerA"], "CHEST": ["Gold"], "SOURCE": ["Titan"], "OTHER": ["data"]}
        )
        data_view_model._source_model.set_data(sample_df)
        data_view_model.refresh_model()  # Ensure view model updates
        assert data_view_model.rowCount() > 0

        delegate = data_table_view.itemDelegateForColumn(0)  # PLAYER column
        index = data_view_model.index(0, 0)  # Row 0, Col 0 (PLAYER)
        assert index.isValid()
        editor = delegate.createEditor(data_table_view, None, index)
        new_value = "ValidPlayerName"
        editor.setText(new_value)

        state_spy = QSignalSpy(table_state_manager.state_changed)
        service_spy = MagicMock(wraps=validation_service.validate_single_entry)
        validation_service.validate_single_entry = service_spy

        # Act: Trigger setModelData which should emit validation_requested
        # Need to ensure the controller slot is connected - Assuming it is via fixture or setup
        delegate.setModelData(editor, data_view_model, index)

        # Allow signals to process
        qtbot.wait(50)  # Small wait for signal processing

        # Assert
        # 1. Service was called
        service_spy.assert_called_once_with(ValidationService.PLAYER_COLUMN, new_value)

        # 2. StateManager was updated
        assert state_spy.count() > 0, "TableStateManager.state_changed signal was not emitted."
        # Check the arguments of the last signal emission
        changed_indices_set = state_spy[-1][0]  # First argument is the set
        assert (0, 0) in changed_indices_set, (
            "Affected cell index not in state_changed signal args."
        )

        # 3. Final cell state is VALID
        final_state = table_state_manager.get_full_cell_state(0, 0)
        assert final_state is not None
        assert final_state.validation_status == CellState.VALID
        assert final_state.error_details == ""

    def test_invalid_edit_triggers_validation_and_updates_state(
        self,
        qtbot,
        data_table_view,
        data_view_model,
        validation_service,
        table_state_manager,
        data_view_controller,
    ):
        """Test editing a cell with invalid data triggers validation and sets INVALID state."""
        # Arrange: Mock service to return INVALID
        error_msg = "Player not in list"
        validation_service._player_list_model.validate.return_value = (
            ValidationStatus.INVALID,
            error_msg,
        )

        # Add data
        sample_df = pd.DataFrame(
            {"PLAYER": ["PlayerA"], "CHEST": ["Gold"], "SOURCE": ["Titan"], "OTHER": ["data"]}
        )
        data_view_model._source_model.set_data(sample_df)
        data_view_model.refresh_model()
        assert data_view_model.rowCount() > 0

        delegate = data_table_view.itemDelegateForColumn(0)  # PLAYER column
        index = data_view_model.index(0, 0)
        assert index.isValid()
        editor = delegate.createEditor(data_table_view, None, index)
        new_value = "InvalidPlayerName"
        editor.setText(new_value)

        state_spy = QSignalSpy(table_state_manager.state_changed)
        service_spy = MagicMock(wraps=validation_service.validate_single_entry)
        validation_service.validate_single_entry = service_spy

        # Act
        delegate.setModelData(editor, data_view_model, index)
        qtbot.wait(50)

        # Assert
        service_spy.assert_called_once_with(ValidationService.PLAYER_COLUMN, new_value)
        assert state_spy.count() > 0
        changed_indices_set = state_spy[-1][0]
        assert (0, 0) in changed_indices_set

        final_state = table_state_manager.get_full_cell_state(0, 0)
        assert final_state is not None
        assert final_state.validation_status == CellState.INVALID
        assert final_state.error_details == error_msg

    def test_edit_non_validatable_column_skips_validation(
        self,
        qtbot,
        data_table_view,
        data_view_model,
        validation_service,
        table_state_manager,
        data_view_controller,
    ):
        """Test editing a column not in the validatable list skips service call."""
        # Arrange: Assume column 3 ('OTHER') is not PLAYER, CHEST, or SOURCE
        NON_VALIDATABLE_COL_INDEX = 3

        # Add data with the non-validatable column
        sample_df = pd.DataFrame(
            {"PLAYER": ["PlayerA"], "CHEST": ["Gold"], "SOURCE": ["Titan"], "OTHER": ["data"]}
        )
        data_view_model._source_model.set_data(sample_df)
        data_view_model.refresh_model()
        assert data_view_model.columnCount() > NON_VALIDATABLE_COL_INDEX
        assert data_view_model.rowCount() > 0

        # Set delegate for the non-validatable column if needed
        delegate = data_table_view.itemDelegateForColumn(NON_VALIDATABLE_COL_INDEX)
        if delegate is None:
            delegate = TextEditDelegate(data_table_view)
            data_table_view.setItemDelegateForColumn(NON_VALIDATABLE_COL_INDEX, delegate)
            # Manually connect the signal if connect_delegate_signals wasn't called again or didn't cover this late addition
            try:
                delegate.validation_requested.disconnect(
                    data_table_view._handle_cell_validation_request
                )
            except (TypeError, RuntimeError):
                pass
            delegate.validation_requested.connect(data_table_view._handle_cell_validation_request)

        index = data_view_model.index(0, NON_VALIDATABLE_COL_INDEX)
        assert index.isValid()
        editor = delegate.createEditor(data_table_view, None, index)
        new_value = "SomeOtherValue"
        editor.setText(new_value)

        state_spy = QSignalSpy(table_state_manager.state_changed)
        service_spy = MagicMock(wraps=validation_service.validate_single_entry)
        validation_service.validate_single_entry = service_spy

        # Act
        delegate.setModelData(editor, data_view_model, index)
        qtbot.wait(50)

        # Assert
        service_spy.assert_not_called()  # Service validation should be skipped
        assert state_spy.count() == 0  # State manager should not be updated for validation
