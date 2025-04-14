import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtCore import QPoint, QModelIndex, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu  # Added import

from chestbuddy.ui.data.views.data_table_view import DataTableView
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import TableStateManager, CellFullState, CellState
from chestbuddy.ui.data.context.action_context import ActionContext  # Added import
from chestbuddy.ui.data.menus.context_menu_factory import ContextMenuFactory  # Added import
from chestbuddy.ui.data.actions.correction_actions import (
    ApplyCorrectionAction,
    PreviewCorrectionAction,
)  # Added import

# Assume standard fixtures like qtbot, sample_data etc. are in conftest.py
# or imported explicitly if needed.


# Fixture to provide a basic populated model and state manager
@pytest.fixture
def setup_correctable_cell(data_model, table_state_manager):
    # Add some basic data if model is empty
    if data_model.row_count == 0:
        # Create a sample DataFrame
        import pandas as pd

        sample_df = pd.DataFrame({"col0": ["r0c0", "r1c0"], "col1": ["OriginalValue", "r1c1"]})
        # Use update_data to load the DataFrame into the model
        data_model.update_data(sample_df)
        # Update the headers map *after* data is loaded
        table_state_manager.update_headers_map()

    row_idx, col_idx = 0, 1  # Target cell for correction
    # Get column name from index - requires the headers map to be updated first
    col_name = None
    for name, idx in table_state_manager._headers_map.items():
        if idx == col_idx:
            col_name = name
            break
    if not col_name:
        pytest.fail(
            f"Could not find column name for index {col_idx} in state manager map: {table_state_manager._headers_map}"
        )

    original_value = "OriginalValue"
    suggested_value = "CorrectedValue"

    # Use update_cell with column name
    data_model.update_cell(row_idx, col_name, original_value)

    # Set the state in the state manager
    state = CellFullState(
        validation_status=CellState.CORRECTABLE, correction_suggestions=[suggested_value]
    )
    table_state_manager.update_states({(row_idx, col_idx): state})
    return row_idx, col_idx, original_value, suggested_value


# Need to mock the actual dialog class used by the action
@patch("chestbuddy.ui.data.actions.correction_actions.CorrectionPreviewDialog")
@patch(
    "chestbuddy.ui.data.actions.correction_actions.ApplyCorrectionAction"
)  # Also mock ApplyCorrectionAction for now
def test_context_menu_preview_correction(
    mock_apply_action_cls,
    mock_preview_dialog_cls,
    qtbot,
    data_table_view,
    data_model,
    table_state_manager,
    setup_correctable_cell,
    mock_correction_service,
    mock_validation_service,
):
    """
    Test triggering the Correction Preview dialog from the context menu.
    """
    # Arrange: Get info from fixture
    row_idx, col_idx, original_value, suggested_value = setup_correctable_cell

    # Mock the ApplyCorrectionAction instance behavior if needed (optional)
    mock_apply_action_instance = mock_apply_action_cls.return_value
    mock_apply_action_instance.is_applicable.return_value = True  # Assume it's applicable

    # Find the index for the cell in the view
    # Use the model associated with the view
    # Get the model from the internal QTableView instance
    view_model = data_table_view.table_view.model()
    cell_index = view_model.index(row_idx, col_idx)
    if not cell_index.isValid():
        pytest.fail(f"Could not get valid model index for ({row_idx}, {col_idx})")

    # Get the visual rectangle of the cell to calculate the click position
    # Use the internal table_view for visual calculations
    cell_rect = data_table_view.table_view.visualRect(cell_index)
    if cell_rect.isNull():
        # Try viewport mapping if visualRect fails initially
        viewport_pos = data_table_view.table_view.visualIndex(cell_index)
        cell_rect = data_table_view.table_view.viewport().rect()
        click_pos = data_table_view.table_view.viewport().mapToGlobal(
            viewport_pos.topLeft() + QPoint(5, 5)
        )  # Click inside cell
        click_pos = data_table_view.mapFromGlobal(click_pos)  # Map to the QWidget coordinates
        # Check indexAt on the internal table_view
        if not data_table_view.table_view.indexAt(click_pos).isValid():
            pytest.fail(f"Could not get valid cell rect or click position for index {cell_index}")
    else:
        click_pos = cell_rect.center()

    # --- Act: Simulate context menu request and trigger action --- #

    # 1. Create the context needed by the factory
    # We need the model from the view (which might be a proxy)
    action_context = ActionContext(
        clicked_index=cell_index,  # Use view's model index
        selection=[cell_index],  # Single cell selection
        model=view_model,  # Use view's model
        state_manager=table_state_manager,
        correction_service=mock_correction_service,
        validation_service=mock_validation_service,
        parent_widget=data_table_view,
    )

    # 2. Create the menu using the factory
    menu, created_actions = ContextMenuFactory.create_context_menu(action_context)
    data_table_view.last_context_menu = menu  # Store for potential checking

    # 3. Find the specific QAction for Preview Correction
    preview_qaction = created_actions.get("preview_correction")
    if not preview_qaction:
        # Try finding by text as fallback (less robust)
        for action in menu.actions():
            if "Preview Correction" in action.text():
                preview_qaction = action
                break
        if not preview_qaction:
            pytest.fail("Could not find 'Preview Correction' QAction in created menu")

    # 4. Ensure the action is enabled (it should be based on our setup)
    assert preview_qaction.isEnabled(), "Preview Correction action should be enabled"

    # 5. Trigger the action
    # We need to ensure the lambda connecting the action executes
    # Use qtbot.wait() for simple event processing when no signals are expected
    preview_qaction.trigger()
    qtbot.wait(100)  # Allow event loop to process the trigger

    # --- Assert: Check if the dialog was initialized correctly --- #
    # Check if the dialog's constructor was called once
    mock_preview_dialog_cls.assert_called_once()

    # Check the arguments passed to the dialog's constructor
    # Signature: __init__(self, original_value: str, corrected_value: str, parent: QWidget = None)
    call_args, call_kwargs = mock_preview_dialog_cls.call_args

    # call_args will be (dialog_instance, original_value, corrected_value, parent_widget)
    # when called via `dialog = CorrectionPreviewDialog(...)` inside the action's execute
    print(f"Dialog Call Args: {call_args}")  # Debug output
    print(f"Dialog Call Kwargs: {call_kwargs}")  # Debug output

    assert len(call_args) >= 3  # self, original, corrected expected (+ parent)
    assert call_args[1] == original_value  # Check original value
    assert call_args[2] == suggested_value  # Check suggested value
    assert call_kwargs.get("parent") is data_table_view  # Check parent widget

    # Optional: Check if ApplyCorrectionAction was NOT triggered yet
    mock_apply_action_instance.execute.assert_not_called()

    # --- Add Assert for Accepted Dialog -> Apply Trigger --- #
    # Simulate the dialog being accepted
    mock_dialog_instance = mock_preview_dialog_cls.return_value
    mock_dialog_instance.exec.return_value = QDialog.DialogCode.Accepted

    # Re-trigger the action to simulate the flow after dialog accept
    # Reset mocks before re-triggering to ensure clean state for call count checks
    mock_preview_dialog_cls.reset_mock()
    mock_apply_action_instance.reset_mock()
    mock_dialog_instance.exec.return_value = QDialog.DialogCode.Accepted  # Ensure accept result

    # Use qtbot.wait() here too
    preview_qaction.trigger()
    qtbot.wait(100)

    # Assert that ApplyCorrectionAction's execute method was called
    # It should be called once *after* the dialog is accepted
    # Note: If trigger() is called twice, assert_called_once() might fail if not reset.
    # We might need a more robust way to check the *second* trigger's effect.
    # Let's check the total calls for now.
    # assert mock_apply_action_instance.execute.call_count >= 1  # Should be called at least once

    # Refined check: Reset mock and trigger again
    # mock_preview_dialog_cls.reset_mock()
    # mock_apply_action_instance.reset_mock()
    # mock_dialog_instance.exec.return_value = QDialog.DialogCode.Accepted  # Ensure accept result
    #
    # with qtbot.waitSignals([], timeout=1000, raising=False):
    #     preview_qaction.trigger()
    #
    mock_preview_dialog_cls.assert_called_once()  # Dialog shown again
    mock_apply_action_instance.execute.assert_called_once()  # Apply called once this time

    # --- Add Assert for Rejected Dialog -> No Apply Trigger --- #
    mock_preview_dialog_cls.reset_mock()
    mock_apply_action_instance.reset_mock()
    mock_dialog_instance.exec.return_value = QDialog.DialogCode.Rejected  # Simulate Cancel

    # Use qtbot.wait() here too
    preview_qaction.trigger()
    qtbot.wait(100)

    mock_preview_dialog_cls.assert_called_once()  # Dialog shown again
    mock_apply_action_instance.execute.assert_not_called()  # Apply should NOT be called
