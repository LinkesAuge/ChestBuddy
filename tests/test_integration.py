"""
Integration tests for cross-component workflows in the ChestBuddy application.

This module contains tests that verify interactions between multiple components,
ensuring that data flows correctly and signals propagate appropriately.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QFileDialog
from pytestqt.qtbot import QtBot

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab


class SignalCatcher(QObject):
    """Utility class to catch Qt signals."""

    def __init__(self, signal=None):
        """Initialize the signal catcher."""
        super().__init__()
        self.signal_received = False
        self.signal_count = 0
        self.signal_args = None

        if signal:
            signal.connect(self.signal_handler)

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
def validation_data():
    """Create sample data with validation errors for testing."""
    # Create sample data with validation errors
    data = pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Player Name": ["Player1", "Player2", "Player3"],
            "Source/Location": ["Location1", "Location2", "Location3"],
            "Chest Type": ["Wood", "Silver", "Go ld"],  # Space in "Go ld" - validation error
            "Value": [
                100,
                250,
                "five hundred",
            ],  # "five hundred" is not a valid number - validation error
            "Clan": ["Clan1", "Clan2", "Clan3"],
        }
    )
    return data


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def test_csv_path(temp_dir, sample_data):
    """Create a test CSV file and return its path."""
    csv_path = temp_dir / "test_data.csv"
    sample_data.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def data_model(app):
    """Create and return a ChestDataModel instance."""
    model = ChestDataModel()
    yield model


@pytest.fixture
def csv_service(data_model):
    """Create and return a CSVService instance."""
    service = CSVService(data_model)
    yield service


@pytest.fixture
def validation_service(data_model):
    """Create and return a ValidationService instance."""
    service = ValidationService(data_model)
    yield service


@pytest.fixture
def correction_service(data_model):
    """Create and return a CorrectionService instance."""
    service = CorrectionService(data_model)
    yield service


@pytest.fixture
def config_mock():
    """Create a mock ConfigManager."""
    config = MagicMock()

    # Mock methods to return reasonable defaults
    config.get.return_value = ""
    config.get_path.return_value = Path.home()
    config.get_recent_files.return_value = []

    # Mock set and save methods
    config.set = MagicMock()
    config.save = MagicMock()

    return config


@pytest.fixture
def main_window(qtbot, app, data_model, validation_service, correction_service, config_mock):
    """Create and return a fully configured MainWindow instance."""
    with patch("chestbuddy.ui.main_window.ConfigManager", return_value=config_mock):
        window = MainWindow(data_model, validation_service, correction_service)
        qtbot.addWidget(window)
        window.show()
        yield window
        window.close()


class TestDataLoadingWorkflow:
    """Tests for the data loading workflow."""

    def test_load_data_updates_all_components(self, qtbot, main_window, test_csv_path, sample_data):
        """Test that loading data updates all UI components when a file is loaded."""
        # Setup signal catchers for data model and UI components
        data_model_signal_catcher = SignalCatcher(main_window._data_model.dataChanged)

        # Mock QFileDialog.getOpenFileName to return our test CSV path
        with patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName",
            return_value=(str(test_csv_path), "CSV Files (*.csv)"),
        ):
            # Trigger the load action using the menu or toolbar
            if hasattr(main_window, "load_action"):
                qtbot.mouseClick(main_window.load_action.toolButtons()[0], Qt.LeftButton)
            else:
                # Find the load action in the file menu
                file_menu = [
                    menu for menu in main_window.menuBar().actions() if menu.text() == "&File"
                ][0].menu()
                load_action = [action for action in file_menu.actions() if "Load" in action.text()][
                    0
                ]
                load_action.trigger()

            # Wait for signals to be emitted
            qtbot.wait(200)  # Small delay to ensure signals propagate

            # Verify signal was emitted
            assert data_model_signal_catcher.signal_received

            # Verify data is correctly displayed in the UI
            # Get the data view component, which should be in a tab or directly in the window
            data_view = main_window.findChild(DataView)
            assert data_view is not None

            # Check that the table view has the correct number of rows and columns
            table_view = data_view.findChild(QTableView)
            assert table_view is not None
            assert table_view.model().rowCount() == len(sample_data)
            assert table_view.model().columnCount() == len(sample_data.columns)

            # Check the validation tab is updated
            validation_tab = main_window.findChild(ValidationTab)
            assert validation_tab is not None

            # Check the correction tab is updated
            correction_tab = main_window.findChild(CorrectionTab)
            assert correction_tab is not None

            # Check window title includes the filename
            assert os.path.basename(test_csv_path) in main_window.windowTitle()

    def test_data_changes_propagate(self, qtbot, main_window, sample_data):
        """Test that changes to the data model propagate to all components."""
        # First update the data model with sample data
        main_window._data_model.update_data(sample_data)

        # Set up signal catchers
        data_view_signal_catcher = SignalCatcher()
        data_view = main_window.findChild(DataView)
        if hasattr(data_view, "dataUpdated"):
            data_view.dataUpdated.connect(data_view_signal_catcher.signal_handler)

        # Modify data in the model
        updated_data = sample_data.copy()
        updated_data.at[0, "Player Name"] = "NewPlayer1"

        # Update the model
        main_window._data_model.update_data(updated_data)

        # Wait for signals to propagate
        qtbot.wait(200)

        # Verify UI components reflect the changes
        table_view = data_view.findChild(QTableView)
        model = table_view.model()

        # Find the column index for 'Player Name'
        player_name_col = next(
            i
            for i in range(model.columnCount())
            if model.headerData(i, Qt.Horizontal, Qt.DisplayRole) == "Player Name"
        )

        # Check the cell value in the first row
        index = model.index(0, player_name_col)
        cell_value = model.data(index, Qt.DisplayRole)
        assert cell_value == "NewPlayer1"


class TestValidationWorkflow:
    """Tests for the validation workflow."""

    def test_validation_updates_data_model_and_ui(self, qtbot, main_window, validation_data):
        """Test that running validation updates both the data model and UI components."""
        # First, load data with validation errors
        main_window._data_model.update_data(validation_data)

        # Set up signal catchers
        validation_tab = main_window.findChild(ValidationTab)
        assert validation_tab is not None

        validation_status_changed_catcher = SignalCatcher()
        if hasattr(main_window._data_model, "validationStatusChanged"):
            main_window._data_model.validationStatusChanged.connect(
                validation_status_changed_catcher.signal_handler
            )

        # Find and click the validate button
        validate_button = None
        for button in validation_tab.findChildren(QtBot.findAllButtons(validation_tab).__class__):
            if button.text() in ["Validate", "Run Validation", "Check"]:
                validate_button = button
                break

        assert validate_button is not None

        # Click the validate button
        qtbot.mouseClick(validate_button, Qt.LeftButton)

        # Wait for validation to complete
        qtbot.wait(500)  # Validation might take some time

        # Verify validation results in the data model
        assert hasattr(main_window._data_model, "get_validation_status")
        validation_status = main_window._data_model.get_validation_status()
        assert validation_status is not None

        # Check if at least some rows are invalid
        assert not validation_status.all().all()

        # Verify UI reflects validation errors
        error_list = None
        for widget in validation_tab.findChildren(
            QtBot.findAllListWidgets(validation_tab).__class__
        ):
            if "error" in widget.objectName().lower():
                error_list = widget
                break

        assert error_list is not None
        assert error_list.count() > 0  # Should show at least the two errors we introduced

        # Verify errors are related to our test data
        errors_text = "".join([error_list.item(i).text() for i in range(error_list.count())])
        assert "Go ld" in errors_text or "five hundred" in errors_text


class TestCorrectionWorkflow:
    """Tests for the correction workflow."""

    def test_correction_updates_data_model_and_ui(self, qtbot, main_window, validation_data):
        """Test that applying a correction updates both the data model and UI components."""
        # First, load data with errors
        main_window._data_model.update_data(validation_data)

        # Set up signal catchers
        correction_tab = main_window.findChild(CorrectionTab)
        assert correction_tab is not None

        data_changed_catcher = SignalCatcher()
        if hasattr(main_window._data_model, "dataChanged"):
            main_window._data_model.dataChanged.connect(data_changed_catcher.signal_handler)

        # Find the error value and correction value input fields
        error_value_edit = None
        correction_value_edit = None

        for widget in correction_tab.findChildren(QtBot.findAllLineEdits(correction_tab).__class__):
            if "error" in widget.objectName().lower():
                error_value_edit = widget
            elif "correction" in widget.objectName().lower():
                correction_value_edit = widget

        assert error_value_edit is not None
        assert correction_value_edit is not None

        # Set up a correction
        qtbot.keyClicks(error_value_edit, "Go ld")
        qtbot.keyClicks(correction_value_edit, "Gold")

        # Find and click the apply correction button
        apply_button = None
        for button in correction_tab.findChildren(QtBot.findAllButtons(correction_tab).__class__):
            if "apply" in button.text().lower():
                apply_button = button
                break

        assert apply_button is not None

        # Apply the correction
        qtbot.mouseClick(apply_button, Qt.LeftButton)

        # Wait for correction to apply
        qtbot.wait(500)

        # Verify data was corrected in the model
        corrected_data = main_window._data_model.get_data()
        assert "Go ld" not in corrected_data["Chest Type"].values
        assert "Gold" in corrected_data["Chest Type"].values

        # Verify correction is in history
        history_list = None
        for widget in correction_tab.findChildren(
            QtBot.findAllListWidgets(correction_tab).__class__
        ):
            if "history" in widget.objectName().lower():
                history_list = widget
                break

        assert history_list is not None
        assert history_list.count() > 0

        # Verify history entry contains the correction
        history_text = history_list.item(0).text()
        assert "Go ld" in history_text
        assert "Gold" in history_text


class TestFilterWorkflow:
    """Tests for the filtering workflow."""

    def test_filter_updates_all_views(self, qtbot, main_window, sample_data):
        """Test that applying a filter updates all views appropriately."""
        # First, load sample data
        main_window._data_model.update_data(sample_data)

        # Find the data view component
        data_view = main_window.findChild(DataView)
        assert data_view is not None

        # Set up signal catchers
        filtered_data_changed_catcher = SignalCatcher()
        if hasattr(main_window._data_model, "filteredDataChanged"):
            main_window._data_model.filteredDataChanged.connect(
                filtered_data_changed_catcher.signal_handler
            )

        # Find the filter components
        filter_column_combo = None
        filter_value_edit = None
        apply_filter_button = None

        for combo in data_view.findChildren(QtBot.findAllComboBoxes(data_view).__class__):
            if "filter" in combo.objectName().lower() and "column" in combo.objectName().lower():
                filter_column_combo = combo
                break

        for edit in data_view.findChildren(QtBot.findAllLineEdits(data_view).__class__):
            if "filter" in edit.objectName().lower() and "value" in edit.objectName().lower():
                filter_value_edit = edit
                break

        for button in data_view.findChildren(QtBot.findAllButtons(data_view).__class__):
            if "apply" in button.text().lower() and "filter" in button.text().lower():
                apply_filter_button = button
                break

        assert filter_column_combo is not None
        assert filter_value_edit is not None
        assert apply_filter_button is not None

        # Set up a filter for "Chest Type = Gold"
        filter_column_combo.setCurrentText("Chest Type")
        qtbot.keyClicks(filter_value_edit, "Gold")
        qtbot.mouseClick(apply_filter_button, Qt.LeftButton)

        # Wait for filter to apply
        qtbot.wait(200)

        # Verify only Gold chest is displayed in the table
        table_view = data_view.findChild(QTableView)
        assert table_view is not None
        model = table_view.model()

        # Should show only 1 row (the Gold chest)
        assert model.rowCount() == 1

        # Find the column index for 'Chest Type'
        chest_type_col = next(
            i
            for i in range(model.columnCount())
            if model.headerData(i, Qt.Horizontal, Qt.DisplayRole) == "Chest Type"
        )

        # Verify the visible row has "Gold" chest type
        index = model.index(0, chest_type_col)
        cell_value = model.data(index, Qt.DisplayRole)
        assert cell_value == "Gold"

    def test_clear_filter_resets_views(self, qtbot, main_window, sample_data):
        """Test that clearing a filter resets all views."""
        # First, load sample data
        main_window._data_model.update_data(sample_data)

        # Find the data view component
        data_view = main_window.findChild(DataView)
        assert data_view is not None

        # Set up a filter first
        filter_column_combo = None
        filter_value_edit = None
        apply_filter_button = None
        clear_filter_button = None

        for combo in data_view.findChildren(QtBot.findAllComboBoxes(data_view).__class__):
            if "filter" in combo.objectName().lower() and "column" in combo.objectName().lower():
                filter_column_combo = combo
                break

        for edit in data_view.findChildren(QtBot.findAllLineEdits(data_view).__class__):
            if "filter" in edit.objectName().lower() and "value" in edit.objectName().lower():
                filter_value_edit = edit
                break

        for button in data_view.findChildren(QtBot.findAllButtons(data_view).__class__):
            if "apply" in button.text().lower() and "filter" in button.text().lower():
                apply_filter_button = button
            elif "clear" in button.text().lower() and "filter" in button.text().lower():
                clear_filter_button = button

        assert filter_column_combo is not None
        assert filter_value_edit is not None
        assert apply_filter_button is not None
        assert clear_filter_button is not None

        # Apply a filter for "Chest Type = Gold"
        filter_column_combo.setCurrentText("Chest Type")
        qtbot.keyClicks(filter_value_edit, "Gold")
        qtbot.mouseClick(apply_filter_button, Qt.LeftButton)
        qtbot.wait(200)

        # Verify filter was applied (should show only 1 row)
        table_view = data_view.findChild(QTableView)
        assert table_view is not None
        model = table_view.model()
        assert model.rowCount() == 1

        # Set up signal catcher for filter cleared
        filtered_data_changed_catcher = SignalCatcher()
        if hasattr(main_window._data_model, "filteredDataChanged"):
            main_window._data_model.filteredDataChanged.connect(
                filtered_data_changed_catcher.signal_handler
            )

        # Clear the filter
        qtbot.mouseClick(clear_filter_button, Qt.LeftButton)
        qtbot.wait(200)

        # Verify all rows are visible again
        assert model.rowCount() == len(sample_data)

        # Verify filter status in UI (if there's an indicator)
        active_filter_label = None
        for label in data_view.findChildren(QtBot.findAllLabels(data_view).__class__):
            if "active" in label.objectName().lower() and "filter" in label.objectName().lower():
                active_filter_label = label
                break

        if active_filter_label is not None:
            assert "No" in active_filter_label.text() or "None" in active_filter_label.text()
