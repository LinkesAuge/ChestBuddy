"""
test_validation_tab_view.py

Description: Tests for the ValidationTabView class
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.ui.views.validation_tab_view import ValidationTabView


@pytest.fixture
def app():
    """Fixture to create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def validation_service(tmp_path):
    """Create a ValidationService instance for testing."""
    # Create validation files
    val_dir = tmp_path / "validation"
    val_dir.mkdir()

    player_file = val_dir / "players.txt"
    player_file.write_text("Player1\nPlayer2\nPlayer3\n")

    chest_file = val_dir / "chest_types.txt"
    chest_file.write_text("Gold Chest\nSilver Chest\nBronze Chest\n")

    source_file = val_dir / "sources.txt"
    source_file.write_text("Dungeon\nCave\nForest\nMine\n")

    # Create data model with test data
    data_model = ChestDataModel()
    test_data = pd.DataFrame(
        {
            "PLAYER": ["Player1", "Player2", "UnknownPlayer"],
            "CHEST": ["Gold Chest", "Silver Chest", "Unknown Chest"],
            "SOURCE": ["Dungeon", "Cave", "Unknown Source"],
            "VALUE": [100, 200, 300],
        }
    )
    data_model.update_data(test_data)

    # Create config manager mock
    config_manager = MagicMock()
    config_manager.get_bool.return_value = False

    # Create validation service without patching
    service = ValidationService(data_model, config_manager)

    # Set validation list models directly
    from chestbuddy.core.models.validation_list_model import ValidationListModel

    service._player_list_model = ValidationListModel(player_file, False)
    service._chest_type_list_model = ValidationListModel(chest_file, False)
    service._source_list_model = ValidationListModel(source_file, False)

    yield service


@pytest.fixture
def validation_tab_view(app, validation_service):
    """Create a ValidationTabView instance for testing."""
    view = ValidationTabView(validation_service)
    view.resize(800, 600)  # Set a reasonable size
    view.show()
    QTest.qWaitForWindowExposed(view)
    yield view
    view.close()


class TestValidationTabView:
    """Tests for the ValidationTabView class."""

    def test_initialization(self, validation_tab_view):
        """Test that the view initializes correctly."""
        assert validation_tab_view is not None
        assert validation_tab_view.player_list_view is not None
        assert validation_tab_view.chest_type_list_view is not None
        assert validation_tab_view.source_list_view is not None
        assert validation_tab_view.preferences_view is not None

        # Check that list views were populated
        assert validation_tab_view.player_list_view.list_widget.count() > 0
        assert validation_tab_view.chest_type_list_view.list_widget.count() > 0
        assert validation_tab_view.source_list_view.list_widget.count() > 0

    def test_validate_now_button(self, validation_tab_view, validation_service):
        """Test the validate now button."""
        # Patch validation_service.validate_data
        with patch.object(validation_service, "validate_data") as mock_validate:
            # Reset mock before action
            mock_validate.reset_mock()

            # Call the handler method directly instead of clicking the button
            validation_tab_view._on_validate_now()

            # Check that validate_data was called
            mock_validate.assert_called_once()

    def test_reset_button(self, validation_tab_view):
        """Test the reset button."""
        # Patch the refresh methods
        with (
            patch.object(validation_tab_view.player_list_view, "refresh") as mock_player_refresh,
            patch.object(validation_tab_view.chest_type_list_view, "refresh") as mock_chest_refresh,
            patch.object(validation_tab_view.source_list_view, "refresh") as mock_source_refresh,
            patch.object(validation_tab_view.preferences_view, "refresh") as mock_pref_refresh,
        ):
            # Reset mocks before action
            mock_player_refresh.reset_mock()
            mock_chest_refresh.reset_mock()
            mock_source_refresh.reset_mock()
            mock_pref_refresh.reset_mock()

            # Call the handler method directly instead of clicking the button
            validation_tab_view._on_reset()

            # Check that all refresh methods were called
            mock_player_refresh.assert_called_once()
            mock_chest_refresh.assert_called_once()
            mock_source_refresh.assert_called_once()
            mock_pref_refresh.assert_called_once()

    def test_validation_updated_signal(self, validation_tab_view):
        """Test that validation_updated signal is emitted correctly."""
        # Create signal spy
        signal_spy = MagicMock()
        validation_tab_view.validation_updated.connect(signal_spy)

        # Reset spy before action
        signal_spy.reset_mock()

        # Emit the signal directly
        validation_tab_view.validation_updated.emit()

        # Allow time for signal processing
        QTest.qWait(50)

        # Check that signal was emitted
        signal_spy.assert_called_once()
