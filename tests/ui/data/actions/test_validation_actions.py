"""
Tests for validation-related actions.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox

from chestbuddy.ui.data.actions.validation_actions import ViewErrorAction, AddToValidationListAction
from chestbuddy.ui.data.context.action_context import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel  # Need Role
from chestbuddy.core.table_state_manager import CellState  # Need Enum

# Paths for patching
VALIDATION_DIALOG_PATH = "chestbuddy.ui.data.actions.validation_actions.AddValidationEntryDialog"
BATCH_VALIDATION_DIALOG_PATH = (
    "chestbuddy.ui.data.actions.validation_actions.BatchAddValidationDialog"
)
# Assuming ValidationService will be accessed via context
# VALIDATION_SERVICE_ADD_PATH = "chestbuddy.ui.data.actions.validation_actions.AddToValidationListAction._call_validation_service_add"

# --- Mock Objects & Fixtures ---


class MockModelWithError(MagicMock):
    """Mock model that can return validation state and error details."""

    def __init__(
        self,
        validation_state=None,
        error_details="Mock error details",
        setData_success=True,
        **kwargs,
    ):
        super().__init__(spec=DataViewModel, **kwargs)
        self._validation_state = validation_state
        self._error_details = error_details
        self.setData_success = setData_success
        self.setData_calls = []
        self.mock_index_instance = MagicMock(spec=QModelIndex)
        self.mock_index_instance.isValid.return_value = True
        self.mock_index_instance.row.return_value = 0  # Default row/col for simplicity
        self.mock_index_instance.column.return_value = 0
        self._data = {}  # Add data store

    def data(self, index, role):
        if role == DataViewModel.ValidationStateRole:
            return self._validation_state
        # Handle DisplayRole
        if role == Qt.DisplayRole:
            key = (index.row(), index.column())
            return self._data.get(key, None)
        # Return error details if specifically asked for the ValidationErrorRole
        if role == DataViewModel.ValidationErrorRole:
            return self._error_details
        return None

    # Override index to return a *new* mock for each call, storing row/col
    def index(self, row, col, parent=QModelIndex()):
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.isValid.return_value = True
        mock_index.row.return_value = row
        mock_index.column.return_value = col
        mock_index.parent.return_value = QModelIndex()  # Assume top-level
        return mock_index


@pytest.fixture
def mock_validation_service():
    """Fixture for a mock ValidationService."""
    service = MagicMock()
    # Assume add_entries exists and returns True by default
    service.add_entries = MagicMock(return_value=True)
    return service


@pytest.fixture
def mock_context_factory(mock_validation_service):  # Add service fixture
    """Creates a function to easily generate ActionContext."""

    def _create_context(
        model,
        clicked_row=0,
        clicked_col=0,
        selection_coords=None,
        parent=None,
        validation_service=mock_validation_service,  # Default to mock service
        correction_service=None,  # Add correction service arg for completeness
    ):
        clicked_index = QModelIndex()
        selection = []
        if model:  # Only create indices if model exists
            clicked_index = model.index(clicked_row, clicked_col)
            if selection_coords:
                selection = [model.index(r, c) for r, c in selection_coords]

        return ActionContext(
            clicked_index=clicked_index,
            selection=selection,
            model=model,
            parent_widget=parent or MagicMock(),
            correction_service=correction_service,
            validation_service=validation_service,  # Pass the service
        )

    return _create_context


# --- Tests ---


class TestViewErrorAction:
    def test_properties(self):
        action = ViewErrorAction()
        assert action.id == "view_error"
        assert action.text == "View Validation Error"
        assert action.icon is not None
        assert action.shortcut is None

    def test_is_applicable(self, mock_context_factory):
        action = ViewErrorAction()
        model_valid = MockModelWithError(validation_state=CellState.VALID)
        model_invalid = MockModelWithError(validation_state=CellState.INVALID)
        model_correctable = MockModelWithError(validation_state=CellState.CORRECTABLE)

        ctx_valid = mock_context_factory(model_valid)
        ctx_invalid = mock_context_factory(model_invalid)
        ctx_correctable = mock_context_factory(model_correctable)
        ctx_no_model = mock_context_factory(None)  # Test with no model

        assert not action.is_applicable(ctx_valid)
        assert action.is_applicable(ctx_invalid)
        assert not action.is_applicable(ctx_correctable)
        assert not action.is_applicable(ctx_no_model)

    def test_is_enabled(self, mock_context_factory):
        action = ViewErrorAction()
        model_invalid = MockModelWithError(validation_state=CellState.INVALID)
        ctx_invalid = mock_context_factory(model_invalid)
        assert action.is_enabled(ctx_invalid)  # Should always be enabled if applicable

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_with_details(self, mock_qmessagebox, mock_context_factory):
        action = ViewErrorAction()
        error_msg = "This is the detailed error."
        model = MockModelWithError(validation_state=CellState.INVALID, error_details=error_msg)
        ctx = mock_context_factory(model=model, clicked_row=0, clicked_col=0)

        action.execute(ctx)

        mock_qmessagebox.warning.assert_called_once()
        call_args = mock_qmessagebox.warning.call_args[0]
        assert call_args[0] == ctx.parent_widget  # Check parent widget
        assert call_args[1] == action.text  # Check title uses action text
        assert f"Error in cell (0, 0):" in call_args[2]  # Check message prefix
        assert error_msg in call_args[2]  # Check detailed message

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_no_details(self, mock_qmessagebox, mock_context_factory):
        action = ViewErrorAction()
        model = MockModelWithError(validation_state=CellState.INVALID, error_details=None)
        ctx = mock_context_factory(model=model, clicked_row=0, clicked_col=0)

        action.execute(ctx)

        mock_qmessagebox.warning.assert_called_once()
        call_args = mock_qmessagebox.warning.call_args[0]
        assert "No specific error details available." in call_args[2]

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_no_model(self, mock_qmessagebox, mock_context_factory):
        action = ViewErrorAction()
        ctx = mock_context_factory(model=None)

        action.execute(ctx)
        mock_qmessagebox.warning.assert_not_called()


class TestAddToValidationListAction:
    def test_properties(self):
        action = AddToValidationListAction()
        assert action.id == "add_validation"
        assert action.text == "Add to Validation List"
        assert action.icon is not None
        assert action.shortcut is None

    def test_is_applicable(self, mock_context_factory):
        action = AddToValidationListAction()
        model = MockModelWithError()
        ctx = mock_context_factory(model)
        ctx_no_model = mock_context_factory(None)
        assert action.is_applicable(ctx)
        assert not action.is_applicable(ctx_no_model)

    def test_is_enabled(self, mock_context_factory):
        action = AddToValidationListAction()
        model = MockModelWithError()
        ctx_no_selection = mock_context_factory(model)
        ctx_with_selection = mock_context_factory(model, selection_coords=[(0, 0)])
        assert not action.is_enabled(ctx_no_selection)
        assert action.is_enabled(ctx_with_selection)

    @patch(VALIDATION_DIALOG_PATH)
    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_single_success(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test successful execution for single selection."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values_to_add = ["Value1"]
        model._data = {(0, 0): values_to_add[0]}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], validation_service=mock_validation_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        dialog_details = {"values": values_to_add, "list_type": "Player"}
        mock_dialog_instance.get_validation_details.return_value = dialog_details
        mock_validation_service.add_entries.return_value = True

        action.execute(ctx)

        mock_dialog_class.assert_called_once_with(values_to_add, ctx.parent_widget)
        mock_batch_dialog_class.assert_not_called()
        mock_dialog_instance.get_validation_details.assert_called_once()
        mock_validation_service.add_entries.assert_called_once_with(
            list_type=dialog_details["list_type"], values=values_to_add
        )
        mock_qmessagebox.information.assert_called_once()
        assert "Successfully added 1 value(s)" in mock_qmessagebox.information.call_args[0][2]

    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch(VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_batch_success(
        self,
        mock_qmessagebox,
        mock_dialog_class,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test successful execution for batch selection."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values = ["ValA", "ValB", "ValA"]  # Include duplicate
        unique_sorted_values = sorted(list(set(values)))
        model._data = {(0, 0): values[0], (1, 1): values[1], (2, 0): values[2]}
        ctx = mock_context_factory(
            model,
            selection_coords=[(0, 0), (1, 1), (2, 0)],
            validation_service=mock_validation_service,
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        dialog_details = {"values": unique_sorted_values, "list_type": "Chest Type"}
        mock_batch_dialog_instance.get_batch_details.return_value = dialog_details
        mock_validation_service.add_entries.return_value = True

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once_with(unique_sorted_values, ctx.parent_widget)
        mock_dialog_class.assert_not_called()
        mock_batch_dialog_instance.get_batch_details.assert_called_once()
        # Service should be called once with all unique values
        mock_validation_service.add_entries.assert_called_once_with(
            list_type=dialog_details["list_type"], values=unique_sorted_values
        )
        mock_qmessagebox.information.assert_called_once()
        assert (
            f"Successfully added {len(unique_sorted_values)} value(s)"
            in mock_qmessagebox.information.call_args[0][2]
        )

    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_batch_dialog_cancel(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test cancelling the batch dialog."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values = ["ValA", "ValB"]
        unique_sorted_values = sorted(values)
        model._data = {(0, 0): values[0], (1, 1): values[1]}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0), (1, 1)], validation_service=mock_validation_service
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        mock_batch_dialog_instance.get_batch_details.return_value = None  # Simulate cancel

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once_with(unique_sorted_values, ctx.parent_widget)
        mock_batch_dialog_instance.get_batch_details.assert_called_once()
        mock_validation_service.add_entries.assert_not_called()
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch(VALIDATION_DIALOG_PATH)
    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_dialog_cancel_single(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test execution when the user cancels the single entry dialog."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values_to_add = ["Value1"]
        model._data = {(0, 0): values_to_add[0]}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], validation_service=mock_validation_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_validation_details.return_value = None

        action.execute(ctx)

        mock_dialog_class.assert_called_once_with(values_to_add, ctx.parent_widget)
        mock_dialog_instance.get_validation_details.assert_called_once()
        mock_validation_service.add_entries.assert_not_called()
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch(VALIDATION_DIALOG_PATH)
    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_service_failure(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test execution when the service call fails (applies to single and batch)."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values_to_add = ["Value1"]
        model._data = {(0, 0): values_to_add[0]}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], validation_service=mock_validation_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        dialog_details = {"values": values_to_add, "list_type": "Player"}
        mock_dialog_instance.get_validation_details.return_value = dialog_details
        mock_validation_service.add_entries.return_value = False  # Simulate failure

        action.execute(ctx)

        mock_dialog_class.assert_called_once()
        mock_dialog_instance.get_validation_details.assert_called_once()
        mock_validation_service.add_entries.assert_called_once()
        mock_qmessagebox.critical.assert_called_once()
        crit_call_args = mock_qmessagebox.critical.call_args[0]
        assert "Failed to add entries" in crit_call_args[2]
        assert dialog_details["list_type"] in crit_call_args[2]
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_no_service(self, mock_qmessagebox, mock_context_factory):
        """Test execution when validation service is not available."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values_to_add = ["Value1"]
        model._data = {(0, 0): values_to_add[0]}
        ctx = mock_context_factory(model, selection_coords=[(0, 0)], validation_service=None)

        action.execute(ctx)

        # Does not need dialog patch because it checks for service first
        mock_qmessagebox.critical.assert_called_once()
        assert "Validation service is unavailable" in mock_qmessagebox.critical.call_args[0][2]
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_no_selection(self, mock_qmessagebox, mock_context_factory):
        """Test execution with no cells selected."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        ctx = mock_context_factory(model)

        action.execute(ctx)

        mock_qmessagebox.information.assert_called_once()
        assert "No cell selected" in mock_qmessagebox.information.call_args[0][2]
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_no_unique_values(self, mock_qmessagebox, mock_context_factory):
        """Test execution when selected cells contain no unique non-empty values."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        model._data = {(0, 0): "", (1, 1): None}  # Empty/None values
        ctx = mock_context_factory(model, selection_coords=[(0, 0), (1, 1)])

        action.execute(ctx)

        mock_qmessagebox.information.assert_called_once()
        assert "No non-empty values selected" in mock_qmessagebox.information.call_args[0][2]
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch(BATCH_VALIDATION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.validation_actions.QMessageBox")
    def test_execute_batch_service_exception(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_validation_service,
    ):
        """Test batch execution when the service call raises an exception."""
        action = AddToValidationListAction()
        model = MockModelWithError()
        values = ["ValA", "ValB"]
        unique_sorted_values = sorted(values)
        model._data = {(0, 0): values[0], (1, 1): values[1]}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0), (1, 1)], validation_service=mock_validation_service
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        dialog_details = {"values": unique_sorted_values, "list_type": "Chest Type"}
        mock_batch_dialog_instance.get_batch_details.return_value = dialog_details

        # Simulate service exception
        error_message = "Network Error"
        mock_validation_service.add_entries.side_effect = Exception(error_message)

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once()
        # Service call was attempted
        mock_validation_service.add_entries.assert_called_once()
        mock_qmessagebox.critical.assert_called_once()
        assert (
            f"An error occurred while adding entries: {error_message}"
            in mock_qmessagebox.critical.call_args[0][2]
        )
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
