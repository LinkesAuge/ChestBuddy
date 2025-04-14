"""Tests for correction actions."""

import pytest
from PySide6.QtWidgets import QMenu
from unittest.mock import MagicMock, patch

from chestbuddy.ui.data.actions.correction_actions import (
    ApplyCorrectionAction,
    BatchApplyCorrectionAction,
    AddToCorrectionListAction,
)
from chestbuddy.ui.data.context import DataTableContext
from chestbuddy.ui.data.widgets.batch_correction_dialog import CorrectionItem


class TestApplyCorrectionAction:
    """Test cases for the ApplyCorrectionAction."""

    def test_is_applicable(self):
        """Test the is_applicable method."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.is_cell_selected = True
        context.cell_correction = "Corrected Value"
        action = ApplyCorrectionAction()

        # Test with a valid context (cell selected and correction available)
        assert action.is_applicable(context)

        # Test with no cell selected
        context.is_cell_selected = False
        assert not action.is_applicable(context)

        # Test with no correction available
        context.is_cell_selected = True
        context.cell_correction = None
        assert not action.is_applicable(context)

    def test_execute(self):
        """Test the execute method."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.correction_service = MagicMock()
        context.selected_row = 1
        context.selected_column = 2
        context.cell_correction = "Corrected Value"

        action = ApplyCorrectionAction()

        # Execute the action
        action.execute(context)

        # Verify the correction was applied
        context.correction_service.apply_correction.assert_called_once_with(1, 2, "Corrected Value")


class TestBatchApplyCorrectionAction:
    """Test cases for the BatchApplyCorrectionAction."""

    def test_is_applicable(self):
        """Test the is_applicable method."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.selection_count = 5
        context.correction_service = MagicMock()
        context.correction_service.get_available_corrections.return_value = [
            ("Original", "Corrected")
        ]
        action = BatchApplyCorrectionAction()

        # Test with a valid context (multiple cells selected and corrections available)
        assert action.is_applicable(context)

        # Test with no corrections available
        context.correction_service.get_available_corrections.return_value = []
        assert not action.is_applicable(context)

        # Test with only one cell selected
        context.selection_count = 1
        context.correction_service.get_available_corrections.return_value = [
            ("Original", "Corrected")
        ]
        assert not action.is_applicable(context)

    @patch("chestbuddy.ui.data.actions.correction_actions.BatchCorrectionDialog")
    def test_execute(self, mock_dialog):
        """Test the execute method with the batch dialog."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.correction_service = MagicMock()
        context.selection_model = MagicMock()
        context.model = MagicMock()

        # Setup mock data
        context.selected_cells = [(1, 2), (3, 4)]
        mock_corrections = [
            CorrectionItem(1, 2, "Column1", "OrigValue1", "CorrValue1"),
            CorrectionItem(3, 4, "Column2", "OrigValue2", "CorrValue2"),
        ]
        context.correction_service.get_corrections_for_cells.return_value = mock_corrections

        # Setup mock dialog response
        mock_dialog.show_dialog.return_value = (mock_corrections, True)

        # Create action and execute
        action = BatchApplyCorrectionAction()
        action.execute(context)

        # Verify dialog was shown with corrections
        mock_dialog.show_dialog.assert_called_once_with(mock_corrections)

        # Verify corrections were applied
        assert context.correction_service.apply_correction.call_count == 2
        context.correction_service.apply_correction.assert_any_call(1, 2, "CorrValue1")
        context.correction_service.apply_correction.assert_any_call(3, 4, "CorrValue2")

    @patch("chestbuddy.ui.data.actions.correction_actions.BatchCorrectionDialog")
    def test_execute_cancelled(self, mock_dialog):
        """Test the execute method when the dialog is cancelled."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.correction_service = MagicMock()

        # Setup mock data
        context.selected_cells = [(1, 2), (3, 4)]
        mock_corrections = [
            CorrectionItem(1, 2, "Column1", "OrigValue1", "CorrValue1"),
            CorrectionItem(3, 4, "Column2", "OrigValue2", "CorrValue2"),
        ]
        context.correction_service.get_corrections_for_cells.return_value = mock_corrections

        # Setup mock dialog response (cancelled)
        mock_dialog.show_dialog.return_value = ([], False)

        # Create action and execute
        action = BatchApplyCorrectionAction()
        action.execute(context)

        # Verify dialog was shown
        mock_dialog.show_dialog.assert_called_once_with(mock_corrections)

        # Verify no corrections were applied
        context.correction_service.apply_correction.assert_not_called()


class TestAddToCorrectionListAction:
    """Test cases for the AddToCorrectionListAction."""

    def test_is_applicable(self):
        """Test the is_applicable method."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.is_cell_selected = True
        action = AddToCorrectionListAction()

        # Test with a valid context (cell selected)
        assert action.is_applicable(context)

        # Test with no cell selected
        context.is_cell_selected = False
        assert not action.is_applicable(context)

    def test_execute(self):
        """Test the execute method."""
        # Setup
        context = MagicMock(spec=DataTableContext)
        context.correction_service = MagicMock()
        context.selected_row = 1
        context.selected_column = 2
        context.selected_value = "Original Value"
        context.model.get_header_name.return_value = "Column Name"

        # Mock input dialog to return "Corrected Value"
        with patch(
            "chestbuddy.ui.data.actions.correction_actions.QInputDialog.getText",
            return_value=("Corrected Value", True),
        ):
            action = AddToCorrectionListAction()
            action.execute(context)

            # Verify correction was added
            context.correction_service.add_correction.assert_called_once_with(
                "Original Value", "Corrected Value"
            )
