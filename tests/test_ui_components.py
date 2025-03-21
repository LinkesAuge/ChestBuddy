"""
Tests for UI components of the ChestBuddy application.
"""

import os
import sys
import unittest.mock as mock
from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock, patch

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab

import numpy as np


class SignalCatcher(QObject):
    """Utility class to catch Qt signals."""

    def __init__(self):
        super().__init__()
        self.signal_received = False
        self.signal_count = 0
        self.signal_args = None

    def signal_handler(self, *args):
        """Handle signal emission."""
        self.signal_received = True
        self.signal_count += 1
        self.signal_args = args


@pytest.fixture
def app():
    """Create a QApplication instance."""
    # Check if there's already a QApplication instance
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    # Create sample data
    data = pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Player Name": ["Player1", "Player2", "Player3"],
            "Source/Location": ["Location1", "Location2", "Location3"],
            "Chest Type": ["Wood", "Silver", "Gold"],
            "Value": [100, 250, 500],
            "Clan": ["Clan1", "Clan2", "Clan3"],
        }
    )
    return data


@pytest.fixture
def data_model(app, sample_data):
    """Create a data model with sample data."""
    model = ChestDataModel()
    model.update_data(sample_data)
    return model


@pytest.fixture
def validation_service(data_model):
    """Create a validation service."""
    return ValidationService(data_model)


@pytest.fixture
def correction_service(data_model):
    """Create a correction service."""
    return CorrectionService(data_model)


@pytest.fixture
def corrections_file():
    """Path to standard corrections file."""
    return Path("data/corrections/standard_corrections.csv")


class TestDataView:
    """Tests for the DataView class."""

    def test_initialization(self, app, data_model):
        """Test that DataView initializes correctly."""
        data_view = DataView(data_model)
        assert data_view is not None

        # Test that the model was set
        assert data_view._data_model == data_model

        # Test that the table is populated
        assert data_view._table_model.rowCount() == data_model.row_count

    def test_update_view(self, app, data_model):
        """Test that the view updates when the model changes."""
        data_view = DataView(data_model)

        # Create a signal catcher
        signal_catcher = SignalCatcher()
        data_model.data_changed.connect(signal_catcher.signal_handler)

        # Update the data
        new_data = pd.DataFrame(
            {
                "Date": ["2023-02-01"],
                "Player Name": ["Player4"],
                "Source/Location": ["Location4"],
                "Chest Type": ["Platinum"],
                "Value": [1000],
                "Clan": ["Clan4"],
            }
        )
        data_model.update_data(new_data)

        # Check if the signal was received
        assert signal_catcher.signal_received

        # Check if the table was updated
        assert data_view._table_model.rowCount() == 1

    def test_filtering(self, app, data_model):
        """Test filtering the data view."""
        data_view = DataView(data_model)

        # Set filter text in the filter field
        data_view._filter_text.setText("Player1")
        data_view._on_filter_changed()

        # Check that filtering was applied
        assert data_view._filtered_rows is not None
        assert len(data_view._filtered_rows) == 1

        # Clear filter
        data_view._filter_text.setText("")
        data_view._on_filter_changed()

        # Check that filter was cleared
        assert data_view._filtered_rows is None


class TestValidationTab:
    """Tests for ValidationTab class."""

    def test_initialization(self, app, data_model, validation_service):
        """Test that ValidationTab initializes correctly."""
        with patch.object(ValidationTab, "_update_view") as mock_update:
            validation_tab = ValidationTab(data_model, validation_service)
            assert validation_tab is not None
            assert validation_tab._data_model == data_model
            assert validation_tab._validation_service == validation_service
            mock_update.assert_called_once()

    def test_validate_data(self, app, data_model, validation_service):
        """Test validating data."""
        with (
            patch.object(ValidationTab, "_update_view"),
            patch.object(validation_service, "validate_data") as mock_validate,
        ):
            validation_tab = ValidationTab(data_model, validation_service)

            # Create a signal catcher
            signal_catcher = SignalCatcher()
            data_model.validation_changed.connect(signal_catcher.signal_handler)

            # Trigger validation
            validation_tab._validate_button.click()

            # Check if validation was called
            mock_validate.assert_called_once()


class TestCorrectionTab:
    """Tests for CorrectionTab class."""

    def test_initialization(self, app, data_model, correction_service):
        """Test that CorrectionTab initializes correctly."""
        with patch.object(CorrectionTab, "_update_view") as mock_update:
            correction_tab = CorrectionTab(data_model, correction_service)
            assert correction_tab is not None
            assert correction_tab._data_model == data_model
            assert correction_tab._correction_service == correction_service
            mock_update.assert_called_once()

    def test_apply_correction(self, app, data_model, correction_service):
        """Test applying a correction."""
        with (
            patch.object(CorrectionTab, "_update_view"),
            patch.object(correction_service, "apply_correction") as mock_apply,
        ):
            correction_tab = CorrectionTab(data_model, correction_service)

            # Create a signal catcher
            signal_catcher = SignalCatcher()
            data_model.correction_applied.connect(signal_catcher.signal_handler)

            # Select column and correction strategy
            correction_tab._column_combo.setCurrentText(data_model.column_names[0])
            correction_tab._strategy_combo.setCurrentText("Standardize Format")

            # Patch the _get_selected_rows method to return some rows
            with patch.object(correction_tab, "_get_selected_rows", return_value=[0]):
                # Apply correction
                correction_tab._apply_button.click()

                # Check if correction was applied
                mock_apply.assert_called_once()

    def test_load_corrections(self, app, data_model, correction_service, corrections_file):
        """Test loading corrections."""
        if not corrections_file.exists():
            pytest.skip("Corrections file not found")

        with (
            patch.object(CorrectionTab, "_update_view"),
            patch.object(correction_service, "load_correction_templates") as mock_load,
        ):
            tab = CorrectionTab(data_model, correction_service)

            # Mock the file dialog to return our test file
            with patch(
                "PySide6.QtWidgets.QFileDialog.getOpenFileName",
                return_value=(str(corrections_file), ""),
            ):
                # Load corrections
                tab._load_corrections_action.trigger()

                # Check if load_correction_templates was called
                mock_load.assert_called_once_with(corrections_file)
