"""
Tests for correction-related actions.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox, QDialog

from chestbuddy.ui.data.actions.correction_actions import (
    ApplyCorrectionAction,
    AddToCorrectionListAction,
    BatchApplyCorrectionAction,
)
from chestbuddy.ui.data.context.action_context import ActionContext
from chestbuddy.ui.data.models.data_view_model import DataViewModel  # Need Role
from chestbuddy.core.table_state_manager import CellState  # Need Enum
from chestbuddy.ui.dialogs.add_correction_rule_dialog import AddCorrectionRuleDialog
from chestbuddy.ui.dialogs.batch_add_correction_dialog import (
    BatchAddCorrectionDialog,
)  # Import batch dialog
from chestbuddy.ui.widgets.correction_preview_dialog import CorrectionPreviewDialog

# Import the dialog to patch it
CORRECTION_DIALOG_PATH = "chestbuddy.ui.data.actions.correction_actions.AddCorrectionRuleDialog"
BATCH_CORRECTION_DIALOG_PATH = (
    "chestbuddy.ui.data.actions.correction_actions.BatchAddCorrectionDialog"
)
# Add path for the preview dialog
PREVIEW_DIALOG_PATH = "chestbuddy.ui.data.actions.correction_actions.CorrectionPreviewDialog"

SERVICE_ADD_PATH = "chestbuddy.ui.data.actions.correction_actions.AddToCorrectionListAction._call_correction_service_add"

# --- Mock Objects & Fixtures ---


@pytest.fixture
def mock_suggestion():
    """Creates a mock suggestion object."""
    suggestion = MagicMock()
    suggestion.corrected_value = "CorrectedValue"
    # Add other attributes if needed by the action
    return suggestion


class MockModelWithCorrection(MagicMock):
    """Mock model that can return validation state and suggestions per cell."""

    def __init__(self, cell_data=None, setData_success=True, **kwargs):
        super().__init__(spec=DataViewModel, **kwargs)
        # cell_data format: {(row, col): {"state": CellState, "suggestions": [], "display": value}}
        self._cell_data = cell_data or {}
        self.setData_success = setData_success
        self.setData_calls = []
        self._rows = max([r for r, c in self._cell_data.keys()], default=-1) + 1
        self._cols = max([c for r, c in self._cell_data.keys()], default=-1) + 1

    def rowCount(self, parent=QModelIndex()):
        return self._rows

    def columnCount(self, parent=QModelIndex()):
        return self._cols

    def data(self, index, role):
        key = (index.row(), index.column())
        cell_info = self._cell_data.get(key, {})

        if role == DataViewModel.ValidationStateRole:
            return cell_info.get("state", CellState.VALID)
        if role == Qt.DisplayRole:
            return cell_info.get("display", None)
        if role == DataViewModel.CorrectionSuggestionsRole:
            return cell_info.get("suggestions", None)
        return None

    def get_correction_suggestions(self, row, col):
        key = (row, col)
        return self._cell_data.get(key, {}).get("suggestions", None)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            key = (index.row(), index.column())
            self.setData_calls.append((key, value, role))
            # Update internal data for consistency if needed
            if key in self._cell_data:
                self._cell_data[key]["display"] = value
                self._cell_data[key]["state"] = CellState.VALID  # Assume correction validates
                self._cell_data[key]["suggestions"] = None
            return self.setData_success
        return False

    # index method remains the same
    def index(self, row, col, parent=QModelIndex()):
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.isValid.return_value = True
        mock_index.row.return_value = row
        mock_index.column.return_value = col
        mock_index.parent.return_value = QModelIndex()  # Assume top-level
        mock_index.model.return_value = self  # Link back to model
        return mock_index


@pytest.fixture
def mock_correction_service():
    """Fixture for a mock CorrectionService."""
    service = MagicMock()
    # Assume add_rule exists and returns True by default
    service.add_rule = MagicMock(return_value=True)
    return service


@pytest.fixture
def mock_context_factory(mock_correction_service):
    """Creates a function to easily generate ActionContext."""

    def _create_context(
        model,
        clicked_row=0,
        clicked_col=0,
        selection_coords=None,
        parent=None,
        correction_service=mock_correction_service,
        validation_service=None,  # Add validation service arg for completeness
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
            validation_service=validation_service,
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
        model_valid = MockModelWithCorrection(cell_data={(0, 0): {"state": CellState.VALID}})
        model_invalid = MockModelWithCorrection(cell_data={(0, 0): {"state": CellState.INVALID}})
        model_correctable = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.CORRECTABLE}}
        )

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
            cell_data={(0, 0): {"state": CellState.CORRECTABLE}}
        )
        model_with_suggestions = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.CORRECTABLE, "suggestions": [mock_suggestion]}}
        )
        model_not_correctable = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.INVALID, "suggestions": [mock_suggestion]}}
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

    @patch(PREVIEW_DIALOG_PATH)  # Patch the preview dialog
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_success_with_preview_accept(
        self, mock_qmessagebox, mock_preview_dialog_class, mock_context_factory, mock_suggestion
    ):
        """Test execute success path when preview dialog is accepted."""
        action = ApplyCorrectionAction()
        model = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.CORRECTABLE, "suggestions": [mock_suggestion]}}
        )
        ctx = mock_context_factory(model=model)

        # Configure the mocked preview dialog to simulate accept
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = (
            QMessageBox.StandardButton.Ok
        )  # Use QMessageBox const for example
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify PreviewDialog was instantiated and shown
        mock_preview_dialog_class.assert_called_once()
        mock_preview_instance.exec.assert_called_once()

        # Verify setData was called because dialog was accepted
        assert len(model.setData_calls) == 1
        _, set_value, set_role = model.setData_calls[0]
        assert set_value == mock_suggestion.corrected_value
        assert set_role == Qt.EditRole

        # Verify success message box was shown
        mock_qmessagebox.information.assert_called_once()
        mock_qmessagebox.warning.assert_not_called()

    @patch(PREVIEW_DIALOG_PATH)  # Patch the preview dialog
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_success_with_preview_reject(
        self, mock_qmessagebox, mock_preview_dialog_class, mock_context_factory, mock_suggestion
    ):
        """Test execute path when preview dialog is rejected."""
        action = ApplyCorrectionAction()
        model = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.CORRECTABLE, "suggestions": [mock_suggestion]}}
        )
        ctx = mock_context_factory(model=model)

        # Configure the mocked preview dialog to simulate reject
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = (
            QMessageBox.StandardButton.Cancel
        )  # Use QMessageBox const
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify PreviewDialog was instantiated and shown
        mock_preview_dialog_class.assert_called_once()
        mock_preview_instance.exec.assert_called_once()

        # Verify setData was NOT called because dialog was rejected
        assert len(model.setData_calls) == 0

        # Verify no message box was shown (or maybe an info that it was cancelled? depends on spec)
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()

    # Test execute_failure path (setData fails after preview accept)
    @patch(PREVIEW_DIALOG_PATH)  # Patch the preview dialog
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_failure_after_preview_accept(
        self, mock_qmessagebox, mock_preview_dialog_class, mock_context_factory, mock_suggestion
    ):
        """Test execute failure path when setData fails after preview is accepted."""
        action = ApplyCorrectionAction()
        # Simulate setData failing
        model = MockModelWithCorrection(
            cell_data={(0, 0): {"state": CellState.CORRECTABLE, "suggestions": [mock_suggestion]}}
        )
        ctx = mock_context_factory(model=model)

        # Configure the mocked preview dialog to simulate accept
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = QMessageBox.StandardButton.Ok
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify PreviewDialog was instantiated and shown
        mock_preview_dialog_class.assert_called_once()
        mock_preview_instance.exec.assert_called_once()

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
        model = MockModelWithCorrection(cell_data={(0, 0): {"state": CellState.CORRECTABLE}})
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
        mock_qmessagebox.warning.assert_not_called()


class TestAddToCorrectionListAction:
    def test_properties(self):
        action = AddToCorrectionListAction()
        assert action.id == "add_correction"
        assert action.text == "Add to Correction List"
        assert action.icon is not None
        assert action.shortcut is None

    def test_is_applicable(self, mock_context_factory):
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        ctx = mock_context_factory(model)
        ctx_no_model = mock_context_factory(None)
        assert action.is_applicable(ctx)
        assert not action.is_applicable(ctx_no_model)

    def test_is_enabled(self, mock_context_factory):
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        ctx_no_selection = mock_context_factory(model)
        ctx_with_selection = mock_context_factory(model, selection_coords=[(0, 0)])
        assert not action.is_enabled(ctx_no_selection)
        assert action.is_enabled(ctx_with_selection)

    # Test execution scenarios
    @patch(CORRECTION_DIALOG_PATH)
    @patch(BATCH_CORRECTION_DIALOG_PATH)  # Also patch batch dialog
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_single_success(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_dialog_class,
        mock_context_factory,
        mock_correction_service,
    ):
        """Test successful execution for single selection."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        from_value = "Value1"
        model._cell_data = {(0, 0): {"state": CellState.VALID, "display": from_value}}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], correction_service=mock_correction_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        dialog_details = {
            "from_value": from_value,
            "to_value": "Corrected",
            "category": "Player",
            "enabled": True,
        }
        mock_dialog_instance.get_rule_details.return_value = dialog_details
        mock_correction_service.add_rule.return_value = True

        action.execute(ctx)

        mock_dialog_class.assert_called_once_with(
            default_from_value=from_value, parent=ctx.parent_widget
        )
        mock_batch_dialog_class.assert_not_called()  # Ensure batch dialog not called
        mock_dialog_instance.get_rule_details.assert_called_once()
        mock_correction_service.add_rule.assert_called_once_with(**dialog_details)
        mock_qmessagebox.information.assert_called_once()
        assert "Successfully added 1 rule(s)" in mock_qmessagebox.information.call_args[0][2]

    @patch(BATCH_CORRECTION_DIALOG_PATH)
    @patch(CORRECTION_DIALOG_PATH)  # Also patch single dialog
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_batch_success(
        self,
        mock_qmessagebox,
        mock_dialog_class,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_correction_service,
    ):
        """Test successful execution for batch selection."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        values_to_add = ["FromVal1", "FromVal2", "FromVal1"]  # Include duplicate
        unique_sorted_values = sorted(list(set(values_to_add)))
        model._cell_data = {
            (0, 0): {"state": CellState.VALID, "display": values_to_add[0]},
            (1, 1): {"state": CellState.VALID, "display": values_to_add[1]},
            (2, 0): {"state": CellState.VALID, "display": values_to_add[2]},
        }
        ctx = mock_context_factory(
            model,
            selection_coords=[(0, 0), (1, 1), (2, 0)],
            correction_service=mock_correction_service,
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        dialog_details = {
            "from_values": unique_sorted_values,
            "to_value": "BatchCorrected",
            "category": "General",
            "enabled": True,
        }
        mock_batch_dialog_instance.get_batch_details.return_value = dialog_details
        mock_correction_service.add_rule.return_value = True  # Assume success for all calls

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once_with(unique_sorted_values, ctx.parent_widget)
        mock_dialog_class.assert_not_called()  # Ensure single dialog not called
        mock_batch_dialog_instance.get_batch_details.assert_called_once()
        # Check add_rule was called for each unique value
        assert mock_correction_service.add_rule.call_count == len(unique_sorted_values)
        mock_correction_service.add_rule.assert_any_call(
            from_value=unique_sorted_values[0],
            to_value=dialog_details["to_value"],
            category=dialog_details["category"],
            enabled=dialog_details["enabled"],
        )
        mock_correction_service.add_rule.assert_any_call(
            from_value=unique_sorted_values[1],
            to_value=dialog_details["to_value"],
            category=dialog_details["category"],
            enabled=dialog_details["enabled"],
        )
        mock_qmessagebox.information.assert_called_once()
        assert (
            f"Successfully added {len(unique_sorted_values)} rule(s)"
            in mock_qmessagebox.information.call_args[0][2]
        )

    @patch(BATCH_CORRECTION_DIALOG_PATH)
    @patch(CORRECTION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_batch_partial_success(
        self,
        mock_qmessagebox,
        mock_dialog_class,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_correction_service,
    ):
        """Test batch execution where some service calls fail."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        values_to_add = ["ValA", "ValB"]
        unique_sorted_values = sorted(values_to_add)
        model._cell_data = {
            (0, 0): {"state": CellState.VALID, "display": values_to_add[0]},
            (1, 1): {"state": CellState.VALID, "display": values_to_add[1]},
        }
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0), (1, 1)], correction_service=mock_correction_service
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        dialog_details = {
            "from_values": unique_sorted_values,
            "to_value": "Correct",
            "category": "Player",
            "enabled": True,
        }
        mock_batch_dialog_instance.get_batch_details.return_value = dialog_details

        # Simulate one success, one failure
        mock_correction_service.add_rule.side_effect = [True, False]

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once()
        assert mock_correction_service.add_rule.call_count == 2
        mock_qmessagebox.warning.assert_called_once()
        assert "Successfully added 1 out of 2 rule(s)" in mock_qmessagebox.warning.call_args[0][2]
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch(BATCH_CORRECTION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_batch_dialog_cancel(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_correction_service,
    ):
        """Test cancelling the batch dialog."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        values_to_add = ["ValA", "ValB"]
        unique_sorted_values = sorted(values_to_add)
        model._cell_data = {
            (0, 0): {"state": CellState.VALID, "display": values_to_add[0]},
            (1, 1): {"state": CellState.VALID, "display": values_to_add[1]},
        }
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0), (1, 1)], correction_service=mock_correction_service
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        mock_batch_dialog_instance.get_batch_details.return_value = None  # Simulate cancel

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once_with(unique_sorted_values, ctx.parent_widget)
        mock_batch_dialog_instance.get_batch_details.assert_called_once()
        mock_correction_service.add_rule.assert_not_called()
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    # --- General Tests (Applicable to both single/batch) ---
    @patch(CORRECTION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_dialog_cancel_single(
        self, mock_qmessagebox, mock_dialog_class, mock_context_factory, mock_correction_service
    ):
        """Test execution when the user cancels the single rule dialog."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        value_to_add = "Value1"
        model._cell_data = {(0, 0): {"state": CellState.VALID, "display": value_to_add}}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], correction_service=mock_correction_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_rule_details.return_value = None

        action.execute(ctx)

        mock_dialog_class.assert_called_once_with(
            default_from_value=value_to_add, parent=ctx.parent_widget
        )
        mock_dialog_instance.get_rule_details.assert_called_once()
        mock_correction_service.add_rule.assert_not_called()
        # No message boxes expected on cancel
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch(CORRECTION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_service_failure_single(
        self, mock_qmessagebox, mock_dialog_class, mock_context_factory, mock_correction_service
    ):
        """Test execution when the service call fails for single rule."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        from_value = "Value1"
        model._cell_data = {(0, 0): {"state": CellState.VALID, "display": from_value}}
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0)], correction_service=mock_correction_service
        )

        mock_dialog_instance = mock_dialog_class.return_value
        dialog_details = {
            "from_value": from_value,
            "to_value": "Corrected",
            "category": "Player",
            "enabled": True,
        }
        mock_dialog_instance.get_rule_details.return_value = dialog_details
        mock_correction_service.add_rule.return_value = False  # Simulate failure

        action.execute(ctx)

        mock_dialog_class.assert_called_once()
        mock_dialog_instance.get_rule_details.assert_called_once()
        mock_correction_service.add_rule.assert_called_once()
        mock_qmessagebox.warning.assert_called_once()
        assert "Successfully added 0 out of 1 rule(s)" in mock_qmessagebox.warning.call_args[0][2]
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_no_service(self, mock_qmessagebox, mock_context_factory):
        """Test execution when correction service is not available."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        model._cell_data = {(0, 0): {"state": CellState.VALID, "display": "Value1"}}
        ctx = mock_context_factory(model, selection_coords=[(0, 0)], correction_service=None)

        action.execute(ctx)

        mock_qmessagebox.critical.assert_called_once()
        assert "Correction service is unavailable" in mock_qmessagebox.critical.call_args[0][2]

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_no_selection(self, mock_qmessagebox, mock_context_factory):
        """Test execution with no cells selected."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        ctx = mock_context_factory(model)

        action.execute(ctx)

        mock_qmessagebox.information.assert_called_once()
        assert "No cell selected" in mock_qmessagebox.information.call_args[0][2]

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_no_unique_values(self, mock_qmessagebox, mock_context_factory):
        """Test execution when selected cells contain no unique non-empty values."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        model._cell_data = {
            (0, 0): {"state": CellState.VALID, "display": "A"},
            (1, 1): {"state": CellState.VALID, "display": "B"},
        }
        ctx = mock_context_factory(model, selection_coords=[(0, 0), (1, 1)])

        action.execute(ctx)

        mock_qmessagebox.information.assert_called_once()
        assert "No non-empty values selected" in mock_qmessagebox.information.call_args[0][2]

    @patch(BATCH_CORRECTION_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    def test_execute_batch_service_exception(
        self,
        mock_qmessagebox,
        mock_batch_dialog_class,
        mock_context_factory,
        mock_correction_service,
    ):
        """Test batch execution when the service call raises an exception."""
        action = AddToCorrectionListAction()
        model = MockModelWithCorrection()
        values_to_add = ["ValA", "ValB"]
        unique_sorted_values = sorted(values_to_add)
        model._cell_data = {
            (0, 0): {"state": CellState.VALID, "display": values_to_add[0]},
            (1, 1): {"state": CellState.VALID, "display": values_to_add[1]},
        }
        ctx = mock_context_factory(
            model, selection_coords=[(0, 0), (1, 1)], correction_service=mock_correction_service
        )

        mock_batch_dialog_instance = mock_batch_dialog_class.return_value
        dialog_details = {
            "from_values": unique_sorted_values,
            "to_value": "Correct",
            "category": "Player",
            "enabled": True,
        }
        mock_batch_dialog_instance.get_batch_details.return_value = dialog_details

        # Simulate service exception
        error_message = "Database connection lost"
        mock_correction_service.add_rule.side_effect = Exception(error_message)

        action.execute(ctx)

        mock_batch_dialog_class.assert_called_once()
        # Service call was attempted
        assert mock_correction_service.add_rule.call_count > 0
        mock_qmessagebox.critical.assert_called_once()
        assert (
            f"An error occurred while adding rule(s): {error_message}"
            in mock_qmessagebox.critical.call_args[0][2]
        )
        mock_qmessagebox.information.assert_not_called()
        # No warning for partial success if exception occurred on first attempt
        # mock_qmessagebox.warning.assert_not_called()


class TestBatchApplyCorrectionAction:
    """Tests for the BatchApplyCorrectionAction class."""

    def test_properties(self):
        action = BatchApplyCorrectionAction()
        assert action.id == "batch_apply_correction"
        assert action.text == "Batch Apply Corrections"
        assert action.icon is not None

    def test_is_applicable(self, mock_context_factory):
        action = BatchApplyCorrectionAction()
        model = MockModelWithCorrection(cell_data={(0, 0): {}})
        ctx_with_model = mock_context_factory(model)
        ctx_no_model = mock_context_factory(None)
        assert action.is_applicable(ctx_with_model)
        assert not action.is_applicable(ctx_no_model)

    # is_enabled is optimistically True if applicable, so test might be trivial now
    def test_is_enabled(self, mock_context_factory):
        action = BatchApplyCorrectionAction()
        model = MockModelWithCorrection(cell_data={(0, 0): {}})
        ctx_with_model = mock_context_factory(model)
        ctx_no_model = mock_context_factory(None)
        assert action.is_enabled(ctx_with_model)
        assert not action.is_enabled(ctx_no_model)

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    @patch(PREVIEW_DIALOG_PATH)
    def test_execute_no_correctable_cells(
        self, mock_preview_dialog, mock_qmessagebox, mock_context_factory
    ):
        action = BatchApplyCorrectionAction()
        # Model with no correctable cells
        model = MockModelWithCorrection(
            cell_data={
                (0, 0): {"state": CellState.VALID, "display": "A"},
                (1, 1): {"state": CellState.INVALID, "display": "B"},
            }
        )
        ctx = mock_context_factory(model=model)

        action.execute(ctx)

        # Verify preview dialog was NOT called
        mock_preview_dialog.assert_not_called()
        # Verify info message was shown
        mock_qmessagebox.information.assert_called_once()
        assert "No correctable cells" in mock_qmessagebox.information.call_args[0][2]
        # Verify model was not changed
        assert len(model.setData_calls) == 0

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    @patch(PREVIEW_DIALOG_PATH)
    def test_execute_preview_accept_all_success(
        self, mock_preview_dialog_class, mock_qmessagebox, mock_context_factory, mock_suggestion
    ):
        action = BatchApplyCorrectionAction()
        # Model with two correctable cells
        cell_data = {
            (0, 0): {"state": CellState.VALID, "display": "OK"},
            (1, 1): {
                "state": CellState.CORRECTABLE,
                "suggestions": [mock_suggestion],
                "display": "Orig1",
            },
            (2, 2): {
                "state": CellState.CORRECTABLE,
                "suggestions": [mock_suggestion],
                "display": "Orig2",
            },
            (3, 0): {"state": CellState.INVALID, "display": "Bad"},
        }
        model = MockModelWithCorrection(cell_data=cell_data, setData_success=True)
        ctx = mock_context_factory(model=model)

        # Mock preview dialog accept
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = QDialog.Accepted
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify preview dialog was called with 2 changes
        mock_preview_dialog_class.assert_called_once()
        assert len(mock_preview_dialog_class.call_args[0][0]) == 2  # Check number of changes passed
        mock_preview_instance.exec.assert_called_once()

        # Verify setData was called twice with correct values
        assert len(model.setData_calls) == 2
        # Note: Order might not be guaranteed depending on dict iteration
        call_args_1 = model.setData_calls[0]
        call_args_2 = model.setData_calls[1]
        assert call_args_1[0] in [(1, 1), (2, 2)]  # Check key exists
        assert call_args_1[1] == mock_suggestion.corrected_value
        assert call_args_1[2] == Qt.EditRole
        assert call_args_2[0] in [(1, 1), (2, 2)]  # Check key exists
        assert call_args_1[0] != call_args_2[0]  # Ensure keys are different
        assert call_args_2[1] == mock_suggestion.corrected_value
        assert call_args_2[2] == Qt.EditRole

        # Verify success message
        mock_qmessagebox.information.assert_called_once()
        assert "Applied 2 correction(s)" in mock_qmessagebox.information.call_args[0][2]
        mock_qmessagebox.warning.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    @patch(PREVIEW_DIALOG_PATH)
    def test_execute_preview_accept_partial_success(
        self, mock_preview_dialog_class, mock_qmessagebox, mock_context_factory, mock_suggestion
    ):
        action = BatchApplyCorrectionAction()
        # Model with two correctable cells, one setData will fail
        cell_data = {
            (1, 1): {
                "state": CellState.CORRECTABLE,
                "suggestions": [mock_suggestion],
                "display": "Orig1",
            },
            (2, 2): {
                "state": CellState.CORRECTABLE,
                "suggestions": [mock_suggestion],
                "display": "Orig2",
            },
        }
        # Simulate failure for the second setData call
        model = MockModelWithCorrection(cell_data=cell_data)
        model.setData = MagicMock(side_effect=[True, False])  # First succeeds, second fails
        ctx = mock_context_factory(model=model)

        # Mock preview dialog accept
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = QDialog.Accepted
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify preview dialog was called
        mock_preview_dialog_class.assert_called_once()
        mock_preview_instance.exec.assert_called_once()

        # Verify setData was called twice
        assert model.setData.call_count == 2

        # Verify warning message for partial success
        mock_qmessagebox.warning.assert_called_once()
        assert "Applied 1 correction(s)" in mock_qmessagebox.warning.call_args[0][2]
        assert "Failed to apply 1 correction(s)" in mock_qmessagebox.warning.call_args[0][2]
        mock_qmessagebox.information.assert_not_called()

    @patch("chestbuddy.ui.data.actions.correction_actions.QMessageBox")
    @patch(PREVIEW_DIALOG_PATH)
    def test_execute_preview_reject(
        self, mock_preview_dialog_class, mock_qmessagebox, mock_context_factory, mock_suggestion
    ):
        action = BatchApplyCorrectionAction()
        # Model with correctable cells
        cell_data = {
            (1, 1): {
                "state": CellState.CORRECTABLE,
                "suggestions": [mock_suggestion],
                "display": "Orig1",
            },
        }
        model = MockModelWithCorrection(cell_data=cell_data)
        ctx = mock_context_factory(model=model)

        # Mock preview dialog reject
        mock_preview_instance = MagicMock()
        mock_preview_instance.exec.return_value = QDialog.Rejected
        mock_preview_dialog_class.return_value = mock_preview_instance

        action.execute(ctx)

        # Verify preview dialog was called
        mock_preview_dialog_class.assert_called_once()
        mock_preview_instance.exec.assert_called_once()

        # Verify setData was NOT called
        assert len(model.setData_calls) == 0

        # Verify no message boxes shown
        mock_qmessagebox.information.assert_not_called()
        mock_qmessagebox.warning.assert_not_called()
        mock_qmessagebox.critical.assert_not_called()
