"""
Tests for validation-related actions.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox

from chestbuddy.ui.data.actions.validation_actions import ViewErrorAction
from chestbuddy.ui.data.context.action_context import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel  # Need Role
from chestbuddy.core.table_state_manager import CellState  # Need Enum

# --- Mock Objects & Fixtures ---


class MockModelWithError(MagicMock):
    """Mock model that can return validation state and error details."""

    def __init__(self, validation_state=None, error_details=None, **kwargs):
        super().__init__(spec=DataViewModel, **kwargs)
        self._validation_state = validation_state
        self._error_details = error_details
        self.index = MagicMock(return_value=MagicMock(spec=QModelIndex))  # Basic mock index
        self.index.return_value.isValid.return_value = True
        self.index.return_value.row.return_value = 0  # Default row/col for simplicity
        self.index.return_value.column.return_value = 0

    def data(self, index, role):
        if role == DataViewModel.ValidationStateRole:
            return self._validation_state
        return None

    def get_cell_details(self, row, col):
        # Simple mock: return details if coords match default index (0,0)
        if row == 0 and col == 0:
            return self._error_details
        return None


@pytest.fixture
def mock_context_factory():
    """Creates a function to easily generate ActionContext."""

    def _create_context(model, clicked_row=0, clicked_col=0, selection_coords=None, parent=None):
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
        assert call_args[1] == "Validation Error"  # Check title
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
