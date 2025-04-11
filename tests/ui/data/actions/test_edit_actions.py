"""
Tests for standard edit actions.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QKeySequence, QGuiApplication, QClipboard

from chestbuddy.ui.data.actions.edit_actions import CopyAction, PasteAction, CutAction, DeleteAction

# Assuming ActionContext is defined/accessible
from chestbuddy.ui.data.menus.context_menu_factory import ActionContext

# --- Mock Objects & Fixtures ---


class MockModel:
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
def mock_context_factory():
    """Creates a function to easily generate ActionContext."""

    def _create_context(
        clicked_row=-1, clicked_col=-1, selection_coords=None, model=None, parent=None
    ):
        model = model or MockModel()
        clicked_index = model.index(clicked_row, clicked_col) if clicked_row >= 0 else QModelIndex()
        selection = []
        if selection_coords:
            selection = [model.index(r, c) for r, c in selection_coords]

        return ActionContext(
            clicked_index=clicked_index,
            selection=selection,
            model=model,
            parent_widget=parent or MagicMock(),
        )

    return _create_context


@pytest.fixture
def mock_clipboard(mocker):
    """Fixture for mocking the clipboard."""
    # Use patch from unittest.mock for patching class methods/properties
    clipboard_instance = MagicMock(spec=QClipboard)
    clipboard_instance.text.return_value = ""  # Default empty
    mocker.patch.object(QGuiApplication, "clipboard", return_value=clipboard_instance)
    return clipboard_instance


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
