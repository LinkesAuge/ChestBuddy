"""
Tests for UI components.
"""

import os
import sys
import pytest
import pandas as pd
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from pathlib import Path

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab


class SignalCatcher:
    """Utility class to catch Qt signals for testing."""
    def __init__(self):
        self.signal_caught = False
    
    def signal_handler(self):
        self.signal_caught = True


@pytest.fixture(scope="function")
def app():
    """Create a QApplication instance for each test."""
    # Close any existing application
    if QApplication.instance():
        QApplication.instance().quit()
        QApplication.instance().processEvents()
        del QApplication.instance()
    
    # Create a new application
    app = QApplication([])
    yield app
    
    # Clean up
    app.quit()
    app.processEvents()


@pytest.fixture
def data_model():
    """Create a ChestDataModel instance for testing."""
    model = ChestDataModel()
    model.initialize()
    return model


@pytest.fixture
def sample_data():
    """Create sample data for testing that matches our input file structure."""
    return pd.DataFrame(
        {
            "Date": ["2025-03-11", "2025-03-11", "2025-03-11", "2025-03-12"],
            "Player Name": ["Feldjäger", "Krümelmonster", "OsmanlıTorunu", "D4rkBlizZ4rD"],
            "Source/Location": ["Level 25 Crypt", "Level 20 Crypt", "Level 15 rare Crypt", "Level 30 rare Crypt"],
            "Chest Type": ["Fire Chest", "Infernal Chest", "Rare Dragon Chest", "Ancient Bastion Chest"],
            "Value": [275, 84, 350, 550],
            "Clan": ["MY_CLAN", "MY_CLAN", "MY_CLAN", "MY_CLAN"],
        }
    )


@pytest.fixture
def validation_service(data_model):
    """Create a ValidationService instance for testing."""
    return ValidationService(data_model)


@pytest.fixture
def correction_service(data_model):
    """Create a CorrectionService instance for testing."""
    return CorrectionService(data_model)


@pytest.fixture
def validation_lists_dir():
    """Path to validation lists directory for testing."""
    return Path("data/validation")


@pytest.fixture
def corrections_file():
    """Path to standard corrections file for testing."""
    return Path("data/corrections/standard_corrections.csv")


@pytest.fixture
def input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


class TestDataView:
    """Tests for the DataView class."""

    def test_initialization(self, app, data_model):
        """Test that the DataView initializes correctly."""
        view = DataView(data_model)
        assert view is not None

        # Check widget attributes
        assert hasattr(view, "table_view")
        assert hasattr(view, "filter_layout")

    def test_update_view(self, app, data_model, sample_data):
        """Test updating the view with data."""
        view = DataView(data_model)
        data_model.update_data(sample_data)
        # Just verify it doesn't crash - UI testing is limited in unit tests
        assert view is not None

    def test_filter_functionality(self, app, data_model, sample_data):
        """Test the filter functionality."""
        view = DataView(data_model)
        data_model.update_data(sample_data)
        
        # Set a filter
        filter_catcher = SignalCatcher()
        view.filter_applied.connect(filter_catcher.signal_handler)
        
        # Simulate setting a filter
        view._apply_filters({"Chest Type": "Infernal Chest"})
        
        # Check signal was emitted
        assert filter_catcher.signal_caught


class TestValidationTab:
    """Tests for the ValidationTab class."""

    def test_initialization(self, app, data_model, validation_service):
        """Test that the ValidationTab initializes correctly."""
        tab = ValidationTab(data_model, validation_service)
        assert tab is not None

        # Check widget attributes
        assert hasattr(tab, "validation_controls")
        assert hasattr(tab, "validation_results")
        assert hasattr(tab, "rule_checkboxes")
        assert hasattr(tab, "validate_button")
        assert hasattr(tab, "clear_button")

    def test_validation_functionality(self, app, data_model, validation_service, sample_data):
        """Test validation functionality."""
        tab = ValidationTab(data_model, validation_service)
        data_model.update_data(sample_data)
        
        # Mock the validation service
        validation_service.validate_data = MagicMock(return_value={
            "total_issues": 0,
            "rules_applied": 4
        })
        
        # Trigger validation
        tab._on_validate_clicked()
        
        # Verify validation was called
        validation_service.validate_data.assert_called_once()

    def test_load_validation_lists(self, app, data_model, validation_service, validation_lists_dir):
        """Test loading validation lists."""
        if not validation_lists_dir.exists():
            pytest.skip("Validation lists directory not found")
            
        tab = ValidationTab(data_model, validation_service)
        
        # Mock the validation service method
        validation_service.load_validation_lists = MagicMock(return_value=True)
        
        # Simulate loading validation lists
        chest_types_file = validation_lists_dir / "chest_types.txt"
        players_file = validation_lists_dir / "players.txt"
        sources_file = validation_lists_dir / "sources.txt"
        
        if chest_types_file.exists() and players_file.exists() and sources_file.exists():
            # Call method that would trigger loading validation lists
            tab._load_validation_lists(
                str(chest_types_file),
                str(players_file),
                str(sources_file)
            )
            
            # Verify load_validation_lists was called
            validation_service.load_validation_lists.assert_called_once_with(
                str(chest_types_file),
                str(players_file),
                str(sources_file)
            )


class TestCorrectionTab:
    """Tests for the CorrectionTab class."""

    def test_initialization(self, app, data_model, correction_service):
        """Test that the CorrectionTab initializes correctly."""
        tab = CorrectionTab(data_model, correction_service)
        assert tab is not None

        # Check widget attributes
        assert hasattr(tab, "correction_controls")
        assert hasattr(tab, "correction_results")
        assert hasattr(tab, "correction_methods")
        assert hasattr(tab, "apply_button")
        assert hasattr(tab, "clear_button")

    def test_correction_functionality(self, app, data_model, correction_service, sample_data):
        """Test correction functionality."""
        tab = CorrectionTab(data_model, correction_service)
        data_model.update_data(sample_data)
        
        # Mock the correction service method
        correction_service.apply_correction = MagicMock(return_value=(True, None))
        
        # Simulate selecting a correction method and column
        tab.selected_method = "fill_missing_mean"
        tab.selected_column = "Value"
        
        # Trigger correction
        tab._on_apply_correction()
        
        # Verify correction was called
        correction_service.apply_correction.assert_called_once_with(
            "fill_missing_mean", 
            "Value",
            rows=None
        )

    def test_load_corrections(self, app, data_model, correction_service, corrections_file):
        """Test loading corrections."""
        if not corrections_file.exists():
            pytest.skip("Corrections file not found")
            
        tab = CorrectionTab(data_model, correction_service)
        
        # Mock the correction service method
        correction_service.load_corrections = MagicMock(return_value=True)
        
        # Simulate loading corrections
        tab._load_corrections(str(corrections_file))
        
        # Verify load_corrections was called
        correction_service.load_corrections.assert_called_once_with(str(corrections_file))
