"""
test_validation_list_view.py

Description: Tests for the ValidationListView class
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog, QMenu

from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.views.validation_list_view import ValidationListView


@pytest.fixture
def app():
    """Fixture to create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def validation_model(tmp_path):
    """Create a ValidationListModel for testing."""
    file_path = tmp_path / "test_validation.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Entry1\nEntry2\nEntry3\n")

    return ValidationListModel(file_path)


@pytest.fixture
def validation_list_view(app, validation_model):
    """Create a ValidationListView for testing."""
    view = ValidationListView("Test List", validation_model)
    view.resize(400, 500)
    view.show()
    QTest.qWaitForWindowExposed(view)
    yield view
    view.close()


class TestValidationListView:
    """Tests for the ValidationListView class."""

    def test_initialization(self, validation_list_view, validation_model):
        """Test that the view initializes correctly."""
        assert validation_list_view is not None
        assert validation_list_view.title == "Test List"
        assert validation_list_view.validation_model == validation_model

        # Check that list widget was populated
        assert validation_list_view.list_widget.count() == 3
        assert validation_list_view.list_widget.item(0).text() == "Entry1"
        assert validation_list_view.list_widget.item(1).text() == "Entry2"
        assert validation_list_view.list_widget.item(2).text() == "Entry3"

        # Check that status label was updated
        assert "3 entries" in validation_list_view.status_label.text()

    def test_add_button_with_input_dialog(self, validation_list_view, monkeypatch):
        """Test adding an entry via add button and input dialog."""
        # Mock QInputDialog.getText to return a new entry
        monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("NewEntry", True))

        # Clear the search text to ensure we use the input dialog
        validation_list_view.search_input.setText("")

        # Directly call the handler method instead of clicking the button
        validation_list_view._on_add_clicked()

        # Check that entry was added
        assert validation_list_view.list_widget.count() == 4

        # Find the new entry in the list
        items = [
            validation_list_view.list_widget.item(i).text()
            for i in range(validation_list_view.list_widget.count())
        ]
        assert "NewEntry" in items

    def test_add_button_with_search_text(self, validation_list_view):
        """Test adding an entry via add button with search text."""
        # Set search text
        validation_list_view.search_input.setText("NewSearchEntry")

        # Directly call the handler method instead of clicking the button
        validation_list_view._on_add_clicked()

        # Check that entry was added and search was cleared
        assert validation_list_view.list_widget.count() == 4
        assert validation_list_view.search_input.text() == ""

        # Find the new entry in the list
        items = [
            validation_list_view.list_widget.item(i).text()
            for i in range(validation_list_view.list_widget.count())
        ]
        assert "NewSearchEntry" in items

    def test_add_duplicate_entry(self, validation_list_view, monkeypatch):
        """Test attempting to add a duplicate entry."""
        # Mock QMessageBox.information
        mock_info = MagicMock()
        monkeypatch.setattr(QMessageBox, "information", mock_info)

        # Set search text to an existing entry
        validation_list_view.search_input.setText("Entry1")

        # Reset mock before action
        mock_info.reset_mock()

        # Directly call the handler method instead of clicking the button
        validation_list_view._on_add_clicked()

        # Check that entry wasn't added (entry count remains the same)
        assert validation_list_view.list_widget.count() == 3

        # Check that message box was shown
        mock_info.assert_called_once()

    def test_remove_button(self, validation_list_view, monkeypatch):
        """Test removing entries via remove button."""
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(
            QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )

        # Select an item
        validation_list_view.list_widget.setCurrentRow(0)  # Select Entry1

        # Directly call the handler method instead of clicking the button
        validation_list_view._on_remove_clicked()

        # Check that entry was removed
        assert validation_list_view.list_widget.count() == 2
        items = [
            validation_list_view.list_widget.item(i).text()
            for i in range(validation_list_view.list_widget.count())
        ]
        assert "Entry1" not in items
        assert "Entry2" in items
        assert "Entry3" in items

    def test_remove_multiple_entries(self, validation_list_view, monkeypatch):
        """Test removing multiple entries."""
        # Mock the validation model's remove_entry method
        mock_remove = MagicMock(return_value=True)
        validation_list_view.validation_model.remove_entry = mock_remove

        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(
            QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )

        # Add items directly to the list widget
        validation_list_view.list_widget.clear()
        validation_list_view.list_widget.addItem("Entry1")
        validation_list_view.list_widget.addItem("Entry2")

        # Check that the items were added
        assert validation_list_view.list_widget.count() == 2

        # Select the first item
        validation_list_view.list_widget.setCurrentRow(0)

        # Call the remove method directly
        validation_list_view._on_remove_clicked()

        # Verify that the model's remove_entry method was called
        mock_remove.assert_called_once()

    def test_search_filtering(self, validation_list_view):
        """Test that search filtering works."""
        # Set search text
        validation_list_view.search_input.setText("Entry1")

        # Check that list was filtered
        assert validation_list_view.list_widget.count() == 1
        assert validation_list_view.list_widget.item(0).text() == "Entry1"

        # Clear search
        validation_list_view.search_input.clear()

        # Check that all entries are shown again
        assert validation_list_view.list_widget.count() == 3

    def test_context_menu(self, validation_list_view, monkeypatch):
        """Test that context menu works."""
        # Create a mock QMenu to avoid GUI interactions
        mock_menu = MagicMock(spec=QMenu)
        mock_menu.addAction.return_value = MagicMock()
        mock_menu.exec.return_value = None

        # Patch QMenu constructor to return our mock
        monkeypatch.setattr(QMenu, "__new__", lambda cls, *args, **kwargs: mock_menu)

        # Select an item to enable full context menu
        validation_list_view.list_widget.setCurrentRow(0)

        # Call the context menu method directly
        validation_list_view._show_context_menu(validation_list_view.list_widget.rect().center())

        # Verify the menu was created with expected actions
        assert mock_menu.addAction.call_count >= 1  # At least one action added
        mock_menu.exec.assert_called_once()  # Menu was executed

    def test_status_changed_signal(self, validation_list_view):
        """Test that status_changed signal is emitted."""
        # Create signal spy
        signal_spy = MagicMock()
        validation_list_view.status_changed.connect(signal_spy)

        # Reset spy before action
        signal_spy.reset_mock()

        # Trigger signal emission directly
        validation_list_view._update_status()

        # Allow time for signal processing
        QTest.qWait(50)

        # Check that signal was emitted with correct category and count
        signal_spy.assert_called_once()
        args = signal_spy.call_args[0]
        assert args[0] == validation_list_view.title  # Category
        assert isinstance(args[1], int)  # Count
