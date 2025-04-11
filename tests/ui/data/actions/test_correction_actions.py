"""
Tests for correction-related actions.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox

from chestbuddy.ui.data.actions.correction_actions import ApplyCorrectionAction
from chestbuddy.ui.data.context.action_context import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel  # Need Role
from chestbuddy.core.table_state_manager import CellState  # Need Enum

# --- Mock Objects & Fixtures ---


@pytest.fixture
def mock_suggestion():
    """Creates a mock suggestion object."""
    suggestion = MagicMock()
    suggestion.corrected_value = "CorrectedValue"
    # Add other attributes if needed by the action
    return suggestion


class MockModelWithCorrection(MagicMock):
    """Mock model that can return validation state and suggestions."""

    def __init__(self, validation_state=None, suggestions=None, setData_success=True, **kwargs):
        super().__init__(spec=DataViewModel, **kwargs)
        self._validation_state = validation_state
        self._suggestions = suggestions or []
        self.setData_success = setData_success
        self.setData_calls = []

        # Basic mock index setup
        self.mock_index_instance = MagicMock(spec=QModelIndex)
        self.mock_index_instance.isValid.return_value = True
        self.mock_index_instance.row.return_value = 0
        self.mock_index_instance.column.return_value = 0
        self.index = MagicMock(return_value=self.mock_index_instance)

    def data(self, index, role):
        if role == DataViewModel.ValidationStateRole:
            return self._validation_state
        return None

    def get_correction_suggestions(self, row, col):
        # Return suggestions only if coords match default index (0,0)
        if row == 0 and col == 0:
            return self._suggestions
        return None

    def setData(self, index, value, role):
        # Simulate setData call
        if index == self.mock_index_instance and role == Qt.EditRole:
            self.setData_calls.append((index, value, role))
            return self.setData_success
        return False


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


class TestApplyCorrectionAction:
    def test_properties(self):
        action = ApplyCorrectionAction()
        assert action.id == "apply_correction"
        assert action.text == "Apply Correction"
        assert action.icon is not None
        assert action.shortcut is None

    def test_is_applicable(self, mock_context_factory):
        action = ApplyCorrectionAction()
        model_valid = MockModelWithCorrection(validation_state=CellState.VALID)
        model_invalid = MockModelWithCorrection(validation_state=CellState.INVALID)
        model_correctable = MockModelWithCorrection(validation_state=CellState.CORRECTABLE)

        ctx_valid = mock_context_factory(model_valid)
        ctx_invalid = mock_context_factory(model_invalid)
        ctx_correctable = mock_context_factory(model_correctable)
        ctx_no_model = mock_context_factory(None)

        assert not action.is_applicable(ctx_valid)
        assert not action.is_applicable(ctx_invalid)
        assert action.is_applicable(ctx_correctable)
        assert not action.is_applicable(ctx_no_model)

    def test_is_enabled(self, mock_context_factory, mock_suggestion):
        action = ApplyCorrectionAction()
        model_no_suggestions = MockModelWithCorrection(
            validation_state=CellState.CORRECTABLE, suggestions=[]
        )
        model_with_suggestions = MockModelWithCorrection(
            validation_state=CellState.CORRECTABLE, suggestions=[mock_suggestion]
        )
        model_not_correctable = MockModelWithCorrection(
            validation_state=CellState.INVALID, suggestions=[mock_suggestion]
        )

        ctx_no_suggestions = mock_context_factory(model_no_suggestions)
        ctx_with_suggestions = mock_context_factory(model_with_suggestions)
        ctx_not_correctable = mock_context_factory(model_not_correctable)
        ctx_no_model = mock_context_factory(None)

        assert not action.is_enabled(ctx_no_suggestions)  # Not enabled if no suggestions
        assert action.is_enabled(ctx_with_suggestions)  # Enabled if correctable and has suggestions
        # is_applicable is implicitly checked by factory, but is_enabled should also check suggestions
        assert not action.is_enabled(ctx_not_correctable)  # Not enabled if not correctable state
        assert not action.is_enabled(ctx_no_model)

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_success(self, mock_qmessagebox, mock_context_factory, mock_suggestion):
        action = ApplyCorrectionAction()
        model = MockModelWithCorrection(
            validation_state=CellState.CORRECTABLE,
            suggestions=[mock_suggestion],
            setData_success=True,
        )
        ctx = mock_context_factory(model=model)

        action.execute(ctx)

        # Verify setData was called with the corrected value
        assert len(model.setData_calls) == 1
        _, set_value, set_role = model.setData_calls[0]
        assert set_value == mock_suggestion.corrected_value
        assert set_role == Qt.EditRole

        # Verify success message box was shown
        mock_qmessagebox.information.assert_called_once()
        call_args = mock_qmessagebox.information.call_args[0]
        assert "Correction applied successfully" in call_args[2]
        mock_qmessagebox.warning.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_failure(self, mock_qmessagebox, mock_context_factory, mock_suggestion):
        action = ApplyCorrectionAction()
        # Simulate setData failing
        model = MockModelWithCorrection(
            validation_state=CellState.CORRECTABLE,
            suggestions=[mock_suggestion],
            setData_success=False,
        )
        ctx = mock_context_factory(model=model)

        action.execute(ctx)

        # Verify setData was called
        assert len(model.setData_calls) == 1

        # Verify failure message box was shown
        mock_qmessagebox.warning.assert_called_once()
        call_args = mock_qmessagebox.warning.call_args[0]
        assert "Failed to apply correction" in call_args[2]
        mock_qmessagebox.information.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_no_suggestions(self, mock_qmessagebox, mock_context_factory):
        action = ApplyCorrectionAction()
        model = MockModelWithCorrection(validation_state=CellState.CORRECTABLE, suggestions=[])
        ctx = mock_context_factory(model=model)

        action.execute(ctx)

        # Verify setData was NOT called
        assert len(model.setData_calls) == 0

        # Verify info message box was shown about no suggestions
        mock_qmessagebox.information.assert_called_once()
        call_args = mock_qmessagebox.information.call_args[0]
        assert "No correction suggestions available" in call_args[2]
        mock_qmessagebox.warning.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_no_model(self, mock_qmessagebox, mock_context_factory):
        action = ApplyCorrectionAction()
        ctx = mock_context_factory(model=None)

        action.execute(ctx)
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
