import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from chestbuddy.ui.widgets.recent_files_list import RecentFilesList, FileCard


class TestRecentFilesList:
    """Test suite for the RecentFilesList component."""

    @pytest.fixture
    def sample_files(self):
        """Fixture providing sample file data."""
        return [
            {"path": "/path/to/file1.csv", "date": "2023-01-01", "size": 1024, "rows": 100},
            {"path": "/path/to/file2.csv", "date": "2023-01-02", "size": 2048, "rows": 200},
            {"path": "/path/to/file3.csv", "date": "2023-01-03", "size": 4096, "rows": 300},
        ]

    @pytest.fixture
    def recent_files_widget(self, qtbot):
        """Fixture providing a RecentFilesList instance."""
        widget = RecentFilesList()
        qtbot.addWidget(widget)
        return widget

    def test_initialization(self, recent_files_widget):
        """Test widget initialization with default values."""
        # Check widget is properly initialized
        assert recent_files_widget._files == []
        assert recent_files_widget._file_cards == {}

        # Empty state should be hidden initially
        assert not recent_files_widget._empty_state.isVisible()

    def test_set_files_empty(self, recent_files_widget):
        """Test setting an empty file list."""
        # Set empty file list
        recent_files_widget.set_files([])

        # Empty state should be visible
        assert recent_files_widget._empty_state.isVisible()

        # No file cards should be created
        assert not recent_files_widget._file_cards

    def test_set_files(self, recent_files_widget, sample_files):
        """Test setting a list of files."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Empty state should be hidden
        assert not recent_files_widget._empty_state.isVisible()

        # File cards should be created
        assert len(recent_files_widget._file_cards) == 3

        # Check file cards contain correct paths
        for file_data in sample_files:
            path = file_data["path"]
            assert path in recent_files_widget._file_cards

    def test_file_selected_signal(self, recent_files_widget, sample_files, qtbot):
        """Test file_selected signal emission when a file is clicked."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Create signal spy
        signals_received = []

        # Connect signal
        recent_files_widget.file_selected.connect(lambda path: signals_received.append(path))

        # Get the first file card
        file_path = sample_files[0]["path"]
        file_card = recent_files_widget._file_cards[file_path]

        # Simulate file card click
        file_card.file_clicked.emit(file_path)

        # Check signal was emitted with the correct path
        assert len(signals_received) == 1
        assert signals_received[0] == file_path

    def test_file_action_signal(self, recent_files_widget, sample_files, qtbot):
        """Test file_action signal emission when an action button is clicked."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Create signal spy
        signals_received = []

        # Connect signal
        recent_files_widget.file_action.connect(
            lambda action, path: signals_received.append((action, path))
        )

        # Get the first file card
        file_path = sample_files[0]["path"]
        file_card = recent_files_widget._file_cards[file_path]

        # Simulate action button click
        file_card.action_clicked.emit("open", file_path)

        # Check signal was emitted with the correct action and path
        assert len(signals_received) == 1
        assert signals_received[0] == ("open", file_path)

        # Simulate another action
        file_card.action_clicked.emit("validate", file_path)

        # Check signal was emitted again
        assert len(signals_received) == 2
        assert signals_received[1] == ("validate", file_path)

    def test_remove_file(self, recent_files_widget, sample_files, qtbot):
        """Test removing a file from the list."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Create signal spy
        signals_received = []

        # Connect signal
        recent_files_widget.file_action.connect(
            lambda action, path: signals_received.append((action, path))
        )

        # Initial count
        assert len(recent_files_widget._file_cards) == 3

        # Get the first file card
        file_path = sample_files[0]["path"]
        file_card = recent_files_widget._file_cards[file_path]

        # Simulate remove action
        file_card.action_clicked.emit("remove", file_path)

        # Check card was removed
        assert len(recent_files_widget._file_cards) == 2
        assert file_path not in recent_files_widget._file_cards

        # Check file was removed from files list
        assert len(recent_files_widget._files) == 2
        assert all(f.get("path") != file_path for f in recent_files_widget._files)

        # Check signal was emitted
        assert len(signals_received) == 1
        assert signals_received[0] == ("remove", file_path)

    def test_clear_all(self, recent_files_widget, sample_files, qtbot):
        """Test clearing all files."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Create signal spy
        signals_received = []

        # Connect signal
        recent_files_widget.file_action.connect(
            lambda action, path: signals_received.append((action, path))
        )

        # Initial count
        assert len(recent_files_widget._file_cards) == 3

        # Click clear all button
        qtbot.mouseClick(recent_files_widget._clear_all_button, Qt.LeftButton)

        # Check all cards were removed
        assert len(recent_files_widget._file_cards) == 0
        assert len(recent_files_widget._files) == 0

        # Empty state should be visible
        assert recent_files_widget._empty_state.isVisible()

        # Check signal was emitted
        assert len(signals_received) == 1
        assert signals_received[0] == ("clear_all", "")

    def test_update_file(self, recent_files_widget, sample_files):
        """Test updating file information."""
        # Set file list
        recent_files_widget.set_files(sample_files)

        # Get the first file card
        file_path = sample_files[0]["path"]
        file_card = recent_files_widget._file_cards[file_path]

        # Get initial row count
        initial_rows = sample_files[0]["rows"]

        # Updated file data
        updated_data = sample_files[0].copy()
        updated_data["rows"] = 500  # Changed row count

        # Update file
        recent_files_widget.update_file(file_path, updated_data)

        # Check file data was updated in files list
        for file in recent_files_widget._files:
            if file.get("path") == file_path:
                assert file["rows"] == 500
                break

        # Card should still exist
        assert file_path in recent_files_widget._file_cards

        # File card should have updated information
        updated_card = recent_files_widget._file_cards[file_path]
        assert "500" in updated_card._rows_label.text()

    def test_empty_state_action(self, recent_files_widget, qtbot):
        """Test action from empty state."""
        # Set empty file list
        recent_files_widget.set_files([])

        # Create signal spy
        signals_received = []

        # Connect signal
        recent_files_widget.file_action.connect(
            lambda action, path: signals_received.append((action, path))
        )

        # Simulate empty state action
        recent_files_widget._empty_state.action_clicked.emit("import")

        # Check signal was emitted
        assert len(signals_received) == 1
        assert signals_received[0] == ("import", "")


class TestFileCard:
    """Test suite for the FileCard component."""

    @pytest.fixture
    def sample_file_data(self):
        """Fixture providing sample file data."""
        return {"path": "/path/to/test_file.csv", "date": "2023-01-01", "size": 1024, "rows": 100}

    @pytest.fixture
    def file_card(self, sample_file_data, qtbot):
        """Fixture providing a FileCard instance."""
        card = FileCard(sample_file_data)
        qtbot.addWidget(card)
        return card

    def test_initialization(self, file_card, sample_file_data):
        """Test card initialization with file data."""
        # Check file data is stored
        assert file_card._file_data == sample_file_data
        assert file_card._file_path == sample_file_data["path"]

        # Check UI elements
        assert "test_file.csv" in file_card._file_name.text()
        assert "Jan 01, 2023" in file_card._file_date.text()
        assert "1.0 KB" in file_card._size_label.text()
        assert "100" in file_card._rows_label.text()

    def test_file_clicked_signal(self, file_card, qtbot):
        """Test file_clicked signal emission."""
        # Create signal spy
        signals_received = []

        # Connect signal
        file_card.file_clicked.connect(lambda path: signals_received.append(path))

        # Simulate file card click
        file_card._on_mouse_press(type("obj", (object,), {"button": lambda: Qt.LeftButton}))

        # Check signal was emitted with the correct path
        assert len(signals_received) == 1
        assert signals_received[0] == file_card._file_path

    def test_action_clicked_signal(self, file_card, qtbot):
        """Test action_clicked signal emission."""
        # Create signal spy
        signals_received = []

        # Connect signal
        file_card.action_clicked.connect(
            lambda action, path: signals_received.append((action, path))
        )

        # Simulate action button clicks
        file_card._on_action_clicked("open")
        file_card._on_action_clicked("validate")
        file_card._on_action_clicked("remove")

        # Check signals were emitted
        assert len(signals_received) == 3
        assert signals_received[0] == ("open", file_card._file_path)
        assert signals_received[1] == ("validate", file_card._file_path)
        assert signals_received[2] == ("remove", file_card._file_path)

    def test_update_file_data(self, file_card):
        """Test updating file data."""
        # Updated file data
        updated_data = {
            "path": "/path/to/updated_file.csv",
            "date": "2023-02-01",
            "size": 2048,
            "rows": 200,
        }

        # Update file data
        file_card.update_file_data(updated_data)

        # Check file data is updated
        assert file_card._file_data == updated_data
        assert file_card._file_path == updated_data["path"]

        # Check UI elements are updated
        assert "updated_file.csv" in file_card._file_name.text()
        assert "Feb 01, 2023" in file_card._file_date.text()
        assert "2.0 KB" in file_card._size_label.text()
        assert "200" in file_card._rows_label.text()

    def test_format_size(self, file_card):
        """Test file size formatting."""
        assert file_card._format_size(100) == "100 B"
        assert file_card._format_size(1024) == "1.0 KB"
        assert file_card._format_size(1024 * 1024) == "1.0 MB"
        assert file_card._format_size(1024 * 1024 * 1024) == "1.0 GB"
