"""
Tests for standard edit actions.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from PySide6.QtCore import QModelIndex, Qt, QMimeData
from PySide6.QtGui import QKeySequence, QGuiApplication, QClipboard
from PySide6.QtWidgets import QTableView, QMessageBox  # Added QMessageBox

from chestbuddy.ui.data.actions.edit_actions import (
    CopyAction,
    PasteAction,
    CutAction,
    DeleteAction,
    EditCellAction,
    ShowEditDialogAction,
)

# Correct import for ActionContext (assuming it's in context dir)
from chestbuddy.ui.data.context.action_context import ActionContext


# --- Mock Objects & Fixtures ---


class MockModel:  # Renamed from MockModelEditable for clarity
    """Mock DataViewModel for testing actions."""

    def __init__(self, is_editable=True):
        self._is_editable = is_editable
        self._data = {
            (0, 0): "A1",
            (0, 1): "B1",
            (1, 0): "A2",
            (1, 1): "B2",
        }
        self.rowCount = MagicMock(return_value=2)
        self.columnCount = MagicMock(return_value=2)
        self.setData_calls = []  # Track setData calls

    def index(self, row, col, parent=QModelIndex()):
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.row.return_value = row
        mock_index.column.return_value = col
        # Make it valid only if row/col are within bounds
        mock_index.isValid.return_value = (
            0 <= row < self.rowCount() and 0 <= col < self.columnCount()
        )
        return mock_index

    def flags(self, index):
        if not index or not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._is_editable:
            flags |= Qt.ItemIsEditable
        return flags

    def data(self, index, role):
        if not index or not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._data.get((index.row(), index.column()), None)
        return None

    def setData(self, index, value, role):
        if not index or not index.isValid() or role != Qt.EditRole:
            return False
        if not (self.flags(index) & Qt.ItemIsEditable):
            return False
        key = (index.row(), index.column())
        self._data[key] = value
        self.setData_calls.append({"index": key, "value": value, "role": role})
        return True


@pytest.fixture
def mock_model_editable():
    return MockModel(is_editable=True)


@pytest.fixture
def mock_model_readonly():
    return MockModel(is_editable=False)


@pytest.fixture
def mock_context_factory(mock_model_editable):
    """Creates a function to easily generate ActionContext for edit tests."""

    def _create_context(
        clicked_row=-1,
        clicked_col=-1,
        selection_coords=None,
        model=mock_model_editable,
        parent=None,
    ):
        # Ensure model is valid if not explicitly None
        actual_model = model
        if model is None:
            # If model is explicitly None, clicked_index shouldn't use it
            clicked_index = QModelIndex()
            selection = []  # No selection possible without a model
        else:
            clicked_index = (
                model.index(clicked_row, clicked_col) if clicked_row >= 0 else QModelIndex()
            )
            selection = []
            if selection_coords:
                selection = [model.index(r, c) for r, c in selection_coords]

        # Handle parent widget explicitly
        actual_parent = (
            parent if parent is not None else MagicMock()
        )  # Default to MagicMock if None for other tests
        if parent is None:
            actual_parent = None  # Ensure parent passed to ActionContext is None if specified

        # ActionContext for edit actions doesn't need services yet
        return ActionContext(
            clicked_index=clicked_index,
            selection=selection,
            model=actual_model,  # Pass the potentially None model
            parent_widget=actual_parent,  # Pass the potentially None parent
            correction_service=None,
            validation_service=None,
        )

    return _create_context


@pytest.fixture
def mock_clipboard(mocker):
    """Fixture for mocking the clipboard."""
    clipboard_instance = MagicMock(spec=QClipboard)
    clipboard_instance.text.return_value = ""  # Default empty
    mocker.patch.object(QGuiApplication, "clipboard", return_value=clipboard_instance)
    return clipboard_instance


@pytest.fixture
def mock_view(mocker):
    """Fixture for a mock QTableView."""
    view = mocker.MagicMock(spec=QTableView)
    view.edit = mocker.MagicMock()  # Mock the edit slot
    return view


# --- Test Classes ---


class TestCopyAction:
    def test_properties(self):
        action = CopyAction()
        assert action.id == "copy"
        assert action.text == "Copy"
        assert action.shortcut == QKeySequence.StandardKey.Copy
        assert action.icon is not None

    def test_enabled_state(self, mock_context_factory):
        action = CopyAction()
        ctx_no_selection = mock_context_factory()
        ctx_with_selection = mock_context_factory(selection_coords=[(0, 0)])
        assert not action.is_enabled(ctx_no_selection)
        assert action.is_enabled(ctx_with_selection)

    def test_execute(self, mock_context_factory, mock_clipboard):
        action = CopyAction()
        ctx = mock_context_factory(selection_coords=[(0, 0), (0, 1), (1, 0)])
        # Setup expected data in mock model
        ctx.model._data = {
            (0, 0): "A1",
            (0, 1): "B1",
            (1, 0): "A2",
            (1, 1): "B2",
        }
        action.execute(ctx)
        # Expected: A1\tB1\nA2\t""
        expected_text = "A1\tB1\nA2\t"
        mock_clipboard.setText.assert_called_once_with(expected_text)


class TestPasteAction:
    def test_properties(self):
        action = PasteAction()
        assert action.id == "paste"
        assert action.text == "Paste"
        assert action.shortcut == QKeySequence.StandardKey.Paste
        assert action.icon is not None

    def test_enabled_state(self, mock_context_factory, mock_clipboard, mock_model_readonly):
        action = PasteAction()
        # Case 1: No clipboard text
        mock_clipboard.text.return_value = ""
        ctx1 = mock_context_factory(clicked_row=0, clicked_col=0)
        assert not action.is_enabled(ctx1)

        # Case 2: Clipboard text, editable target
        mock_clipboard.text.return_value = "pasted text"
        ctx2 = mock_context_factory(clicked_row=0, clicked_col=0)
        assert action.is_enabled(ctx2)

        # Case 3: Clipboard text, readonly target
        ctx3 = mock_context_factory(clicked_row=0, clicked_col=0, model=mock_model_readonly)
        assert not action.is_enabled(ctx3)

        # Case 4: Clipboard text, no valid target
        ctx4 = mock_context_factory()  # No clicked index
        assert not action.is_enabled(ctx4)

    def test_execute(self, mock_context_factory, mock_clipboard):
        action = PasteAction()
        mock_clipboard.text.return_value = "Pasted1\tPasted2\nPasted3"
        ctx = mock_context_factory(clicked_row=0, clicked_col=0)
        action.execute(ctx)

        # Verify model setData was called correctly
        assert len(ctx.model.setData_calls) == 3
        assert ctx.model.setData_calls[0]["index"] == (0, 0)
        assert ctx.model.setData_calls[0]["value"] == "Pasted1"
        assert ctx.model.setData_calls[1]["index"] == (0, 1)
        assert ctx.model.setData_calls[1]["value"] == "Pasted2"
        assert ctx.model.setData_calls[2]["index"] == (1, 0)
        assert ctx.model.setData_calls[2]["value"] == "Pasted3"


class TestDeleteAction:
    def test_properties(self):
        action = DeleteAction()
        assert action.id == "delete"
        assert action.text == "Delete"
        assert action.shortcut == QKeySequence.StandardKey.Delete
        assert action.icon is not None

    def test_enabled_state(self, mock_context_factory, mock_model_readonly):
        action = DeleteAction()
        ctx_no_selection = mock_context_factory()
        ctx_editable_selection = mock_context_factory(selection_coords=[(0, 0)])
        ctx_readonly_selection = mock_context_factory(
            selection_coords=[(0, 0)], model=mock_model_readonly
        )

        assert not action.is_enabled(ctx_no_selection)
        assert action.is_enabled(ctx_editable_selection)
        assert not action.is_enabled(ctx_readonly_selection)

    def test_execute(self, mock_context_factory):
        action = DeleteAction()
        ctx = mock_context_factory(selection_coords=[(0, 0), (1, 1)])
        action.execute(ctx)

        assert len(ctx.model.setData_calls) == 2
        assert ctx.model.setData_calls[0]["index"] == (0, 0)
        assert ctx.model.setData_calls[0]["value"] == ""
        assert ctx.model.setData_calls[1]["index"] == (1, 1)
        assert ctx.model.setData_calls[1]["value"] == ""


class TestCutAction:
    def test_properties(self):
        action = CutAction()
        assert action.id == "cut"
        assert action.text == "Cut"
        assert action.shortcut == QKeySequence.StandardKey.Cut
        assert action.icon is not None

    def test_enabled_state(self, mock_context_factory, mock_model_readonly):
        action = CutAction()
        ctx_no_selection = mock_context_factory()
        ctx_editable_selection = mock_context_factory(selection_coords=[(0, 0)])
        ctx_readonly_selection = mock_context_factory(
            selection_coords=[(0, 0)], model=mock_model_readonly
        )

        assert not action.is_enabled(ctx_no_selection)
        assert action.is_enabled(ctx_editable_selection)
        assert not action.is_enabled(ctx_readonly_selection)

    def test_execute(self, mock_context_factory, mock_clipboard):
        action = CutAction()
        ctx = mock_context_factory(selection_coords=[(0, 0)])
        ctx.model._data[(0, 0)] = "CutMe"
        action.execute(ctx)

        # Verify clipboard got the text
        mock_clipboard.setText.assert_called_once_with("CutMe")

        # Verify model cell was cleared (Delete was called)
        assert len(ctx.model.setData_calls) == 1
        assert ctx.model.setData_calls[0]["index"] == (0, 0)
        assert ctx.model.setData_calls[0]["value"] == ""


# --- EditCellAction Tests ---


class TestEditCellAction:
    """Tests for the EditCellAction."""

    def test_properties(self):
        action = EditCellAction()
        assert action.id == "edit_cell"
        assert action.text == "Edit Cell"
        assert action.icon is not None
        assert action.shortcut == QKeySequence(Qt.Key_F2)

    def test_is_applicable(self, mock_context_factory, mock_model_editable):
        action = EditCellAction()
        # Applicable: model exists, exactly one selection
        ctx_applicable = mock_context_factory(model=mock_model_editable, selection_coords=[(0, 0)])
        assert action.is_applicable(ctx_applicable)

        # Not applicable: no model
        ctx_no_model = mock_context_factory(model=None, selection_coords=[(0, 0)])
        assert not action.is_applicable(ctx_no_model)

        # Not applicable: no selection
        ctx_no_selection = mock_context_factory(model=mock_model_editable, selection_coords=[])
        assert not action.is_applicable(ctx_no_selection)

        # Not applicable: multiple selections
        ctx_multi_selection = mock_context_factory(
            model=mock_model_editable, selection_coords=[(0, 0), (1, 1)]
        )
        assert not action.is_applicable(ctx_multi_selection)

    def test_is_enabled(self, mock_context_factory, mock_model_editable, mock_model_readonly):
        action = EditCellAction()

        # Enabled: single selection, editable flag
        ctx_enabled = mock_context_factory(model=mock_model_editable, selection_coords=[(0, 0)])
        assert action.is_enabled(ctx_enabled)

        # Disabled: single selection, not editable
        ctx_disabled_flag = mock_context_factory(
            model=mock_model_readonly, selection_coords=[(0, 0)]
        )
        assert not action.is_enabled(ctx_disabled_flag)

        # Disabled: multiple selections (even if editable)
        ctx_disabled_multi = mock_context_factory(
            model=mock_model_editable, selection_coords=[(0, 0), (1, 1)]
        )
        assert not action.is_enabled(ctx_disabled_multi)  # is_enabled also checks len(selection)

    def test_execute_success(self, mock_context_factory, mock_view, mock_model_editable):
        """Test successful execution calls view.edit()."""
        action = EditCellAction()
        ctx = mock_context_factory(
            model=mock_model_editable, parent=mock_view, selection_coords=[(0, 0)]
        )
        index_to_edit = ctx.selection[0]

        action.execute(ctx)

        # Verify the parent view's edit slot was called with the correct index
        mock_view.edit.assert_called_once_with(index_to_edit)

    def test_execute_not_applicable_multi(
        self, mock_context_factory, mock_view, mock_model_editable
    ):
        """Test execute does nothing if not applicable (multi-select)."""
        action = EditCellAction()
        ctx = mock_context_factory(
            model=mock_model_editable, parent=mock_view, selection_coords=[(0, 0), (1, 1)]
        )
        action.execute(ctx)
        mock_view.edit.assert_not_called()

    def test_execute_not_enabled(self, mock_context_factory, mock_view, mock_model_readonly):
        """Test execute does nothing if not enabled (not editable)."""
        action = EditCellAction()
        ctx = mock_context_factory(
            model=mock_model_readonly, parent=mock_view, selection_coords=[(0, 0)]
        )
        action.execute(ctx)
        mock_view.edit.assert_not_called()

    @patch("chestbuddy.ui.data.actions.edit_actions.QMessageBox")
    def test_execute_no_view(self, mock_qmessagebox, mock_context_factory, mock_model_editable):
        """Test execute shows warning if parent widget is not a view."""
        action = EditCellAction()
        # Create context with parent=None
        ctx = mock_context_factory(
            model=mock_model_editable, parent=None, selection_coords=[(0, 0)]
        )
        action.execute(ctx)
        mock_qmessagebox.warning.assert_called_once()
        assert "Cannot initiate edit operation" in mock_qmessagebox.warning.call_args[0][2]

    @patch("chestbuddy.ui.data.actions.edit_actions.QMessageBox")
    def test_execute_view_no_edit_method(
        self, mock_qmessagebox, mock_context_factory, mock_view, mock_model_editable
    ):
        """Test execute shows warning if parent view lacks edit method."""
        action = EditCellAction()
        # Remove the edit method from the mock view
        del mock_view.edit
        ctx = mock_context_factory(
            model=mock_model_editable, parent=mock_view, selection_coords=[(0, 0)]
        )
        action.execute(ctx)
        mock_qmessagebox.warning.assert_called_once()
        assert "Cannot initiate edit operation" in mock_qmessagebox.warning.call_args[0][2]


# --- ShowEditDialogAction Tests ---

# Path for patching the complex edit dialog
COMPLEX_EDIT_DIALOG_PATH = "chestbuddy.ui.data.actions.edit_actions.ComplexEditDialog"


class TestShowEditDialogAction:
    """Tests for the ShowEditDialogAction."""

    def test_properties(self):
        action = ShowEditDialogAction()
        assert action.id == "show_edit_dialog"
        assert action.text == "Edit in Dialog..."
        assert action.icon is not None
        assert action.shortcut is None  # No shortcut initially

    def test_is_applicable(self, mock_context_factory, mock_model_editable):
        action = ShowEditDialogAction()
        # Applicable: model exists, exactly one selection
        ctx_applicable = mock_context_factory(model=mock_model_editable, selection_coords=[(0, 0)])
        assert action.is_applicable(ctx_applicable)

        # Not applicable: no model
        ctx_no_model = mock_context_factory(model=None, selection_coords=[(0, 0)])
        assert not action.is_applicable(ctx_no_model)

        # Not applicable: no selection
        ctx_no_selection = mock_context_factory(model=mock_model_editable, selection_coords=[])
        assert not action.is_applicable(ctx_no_selection)

        # Not applicable: multiple selections
        ctx_multi_selection = mock_context_factory(
            model=mock_model_editable, selection_coords=[(0, 0), (1, 1)]
        )
        assert not action.is_applicable(ctx_multi_selection)

    def test_is_enabled(self, mock_context_factory, mock_model_editable, mock_model_readonly):
        action = ShowEditDialogAction()

        # Enabled: single selection, editable flag
        ctx_enabled = mock_context_factory(model=mock_model_editable, selection_coords=[(0, 0)])
        assert action.is_enabled(ctx_enabled)

        # Disabled: single selection, not editable
        ctx_disabled_flag = mock_context_factory(
            model=mock_model_readonly, selection_coords=[(0, 0)]
        )
        assert not action.is_enabled(ctx_disabled_flag)

        # Disabled: multiple selections (even if editable)
        ctx_disabled_multi = mock_context_factory(
            model=mock_model_editable, selection_coords=[(0, 0), (1, 1)]
        )
        assert not action.is_enabled(ctx_disabled_multi)

    @patch(COMPLEX_EDIT_DIALOG_PATH)
    def test_execute_success(self, mock_dialog_class, mock_context_factory, mock_model_editable):
        """Test successful execution shows dialog and calls setData."""
        action = ShowEditDialogAction()
        initial_value = "Initial"
        new_value = "Edited Value"
        model = mock_model_editable
        model._data[(0, 0)] = initial_value  # Set initial data
        ctx = mock_context_factory(model=model, selection_coords=[(0, 0)])
        index_to_edit = ctx.selection[0]

        # Configure mock dialog
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_new_value.return_value = new_value

        action.execute(ctx)

        # Verify dialog was shown
        mock_dialog_class.assert_called_once_with(initial_value, ctx.parent_widget)
        mock_dialog_instance.get_new_value.assert_called_once()

        # Verify model.setData was called
        assert len(model.setData_calls) == 1
        call_args = model.setData_calls[0]
        assert call_args["index"] == (index_to_edit.row(), index_to_edit.column())
        assert call_args["value"] == new_value
        assert call_args["role"] == Qt.EditRole

    @patch(COMPLEX_EDIT_DIALOG_PATH)
    def test_execute_dialog_cancel(
        self, mock_dialog_class, mock_context_factory, mock_model_editable
    ):
        """Test execute does nothing if the dialog is cancelled."""
        action = ShowEditDialogAction()
        initial_value = "Initial"
        model = mock_model_editable
        model._data[(0, 0)] = initial_value
        ctx = mock_context_factory(model=model, selection_coords=[(0, 0)])

        # Configure mock dialog to return None (cancel)
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_new_value.return_value = None

        action.execute(ctx)

        # Verify dialog was shown
        mock_dialog_class.assert_called_once_with(initial_value, ctx.parent_widget)
        mock_dialog_instance.get_new_value.assert_called_once()

        # Verify model.setData was NOT called
        assert len(model.setData_calls) == 0

    @patch(COMPLEX_EDIT_DIALOG_PATH)
    def test_execute_value_not_changed(
        self, mock_dialog_class, mock_context_factory, mock_model_editable
    ):
        """Test execute does nothing if the value is not changed in the dialog."""
        action = ShowEditDialogAction()
        initial_value = "Initial"
        model = mock_model_editable
        model._data[(0, 0)] = initial_value
        ctx = mock_context_factory(model=model, selection_coords=[(0, 0)])

        # Configure mock dialog to return the initial value
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_new_value.return_value = initial_value

        action.execute(ctx)

        # Verify dialog was shown
        mock_dialog_class.assert_called_once_with(initial_value, ctx.parent_widget)
        mock_dialog_instance.get_new_value.assert_called_once()

        # Verify model.setData was NOT called
        assert len(model.setData_calls) == 0

    @patch(COMPLEX_EDIT_DIALOG_PATH)
    @patch("chestbuddy.ui.data.actions.edit_actions.QMessageBox")
    def test_execute_set_data_failure(
        self, mock_qmessagebox, mock_dialog_class, mock_context_factory, mock_model_editable
    ):
        """Test execute shows warning if model.setData fails."""
        action = ShowEditDialogAction()
        initial_value = "Initial"
        new_value = "Edited Value"
        model = mock_model_editable
        model._data[(0, 0)] = initial_value
        model.setData = MagicMock(return_value=False)  # Simulate setData failure
        ctx = mock_context_factory(model=model, selection_coords=[(0, 0)])

        # Configure mock dialog
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.get_new_value.return_value = new_value

        action.execute(ctx)

        # Verify dialog was shown
        mock_dialog_class.assert_called_once()
        mock_dialog_instance.get_new_value.assert_called_once()

        # Verify model.setData was called
        model.setData.assert_called_once()

        # Verify warning message box was shown
        mock_qmessagebox.warning.assert_called_once()
        assert "Failed to update cell value" in mock_qmessagebox.warning.call_args[0][2]

    def test_execute_not_applicable_multi(self, mock_context_factory, mock_model_editable):
        """Test execute does nothing if not applicable (multi-select)."""
        action = ShowEditDialogAction()
        ctx = mock_context_factory(model=mock_model_editable, selection_coords=[(0, 0), (1, 1)])

        # We need to patch the dialog class to ensure it's not called
        with patch(COMPLEX_EDIT_DIALOG_PATH) as mock_dialog_class:
            action.execute(ctx)
            mock_dialog_class.assert_not_called()
            assert len(mock_model_editable.setData_calls) == 0

    def test_execute_not_enabled(self, mock_context_factory, mock_model_readonly):
        """Test execute does nothing if not enabled (not editable)."""
        action = ShowEditDialogAction()
        ctx = mock_context_factory(model=mock_model_readonly, selection_coords=[(0, 0)])

        with patch(COMPLEX_EDIT_DIALOG_PATH) as mock_dialog_class:
            action.execute(ctx)
            mock_dialog_class.assert_not_called()
            assert len(mock_model_readonly.setData_calls) == 0
