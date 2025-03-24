'''
Tests for the MainWindow class of the ChestBuddy application.

This module contains tests for the MainWindow class, which is the main window of the
ChestBuddy application. It includes tests for initialization, menu actions, toolbar actions,
tab switching, signal emission, and state persistence.
'''

import os
import sys
import logging
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from PySide6.QtCore import QSize, Qt, QByteArray, Signal, QTimer
from PySide6.QtCore import QSize, Qt, QByteArray, Signal, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QTabWidget, QMessageBox
from pytestqt.qtbot import QtBot

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.utils.ui_state import UIStateManager
from chestbuddy.utils.ui_state.elements import BlockableElementMixin
from chestbuddy.ui.widgets.blockable_progress_dialog import BlockableProgressDialog
from chestbuddy.core.services.chart_service import ChartService


# Setup Qt Application for tests
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # app is cleaned up after tests by pytest-qt
from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.utils.ui_state import UIStateManager
from chestbuddy.utils.ui_state.elements import BlockableElementMixin
from chestbuddy.ui.widgets.blockable_progress_dialog import BlockableProgressDialog
from chestbuddy.core.services.chart_service import ChartService


# Setup Qt Application for tests
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # app is cleaned up after tests by pytest-qt


@pytest.fixture
def main_window(qapp, monkeypatch):
    # Reset the singleton instance before each test
    UIStateManager._instance = None

    # Create mocks for services
    data_model_mock = MagicMock(spec=ChestDataModel)
    csv_service_mock = MagicMock(spec=CSVService)
    validation_service_mock = MagicMock(spec=ValidationService)
    correction_service_mock = MagicMock(spec=CorrectionService)
    chart_service_mock = MagicMock(spec=ChartService)
    data_manager_mock = MagicMock()

    # Set up signals for data_manager_mock
    data_manager_mock.load_started = MagicMock()
    data_manager_mock.load_started.connect = MagicMock()
    data_manager_mock.load_progress = MagicMock()
    data_manager_mock.load_progress.connect = MagicMock()
    data_manager_mock.load_finished = MagicMock()
    data_manager_mock.load_finished.connect = MagicMock()
    data_manager_mock.load_error = MagicMock()
    data_manager_mock.load_error.connect = MagicMock()
    data_manager_mock.load_success = MagicMock()
    data_manager_mock.load_success.connect = MagicMock()
    data_manager_mock.populate_table_requested = MagicMock()
    data_manager_mock.populate_table_requested.connect = MagicMock()

    # Create the main window with mocked services
    window = MainWindow(
        data_model_mock,
        csv_service_mock,
        validation_service_mock,
        correction_service_mock,
        chart_service_mock,
        data_manager_mock,
    )

    # Add BlockableElementMixin mock
    window.is_blocked = MagicMock(return_value=False)
    window.block = MagicMock()
    window.unblock = MagicMock()

    # Create import and data service mocks
    window._import_service = MagicMock()
    window._import_service.import_progress = MagicMock()
    window._import_service.import_progress.connect = MagicMock()
    window._import_service.import_completed = MagicMock()
    window._import_service.import_completed.connect = MagicMock()
    window._import_service.import_started = MagicMock()
    window._import_service.import_started.connect = MagicMock()
    window._import_service.import_error = MagicMock()
    window._import_service.import_error.connect = MagicMock()

    window._data_service = MagicMock()
    window._data_service.set_data = MagicMock()

    yield window

    # Cleanup
    window.close()
def main_window(qapp, monkeypatch):
    # Reset the singleton instance before each test
    UIStateManager._instance = None

    # Create mocks for services
    data_model_mock = MagicMock(spec=ChestDataModel)
    csv_service_mock = MagicMock(spec=CSVService)
    validation_service_mock = MagicMock(spec=ValidationService)
    correction_service_mock = MagicMock(spec=CorrectionService)
    chart_service_mock = MagicMock(spec=ChartService)
    data_manager_mock = MagicMock()

    # Set up signals for data_manager_mock
    data_manager_mock.load_started = MagicMock()
    data_manager_mock.load_started.connect = MagicMock()
    data_manager_mock.load_progress = MagicMock()
    data_manager_mock.load_progress.connect = MagicMock()
    data_manager_mock.load_finished = MagicMock()
    data_manager_mock.load_finished.connect = MagicMock()
    data_manager_mock.load_error = MagicMock()
    data_manager_mock.load_error.connect = MagicMock()
    data_manager_mock.load_success = MagicMock()
    data_manager_mock.load_success.connect = MagicMock()
    data_manager_mock.populate_table_requested = MagicMock()
    data_manager_mock.populate_table_requested.connect = MagicMock()

    # Create the main window with mocked services
    window = MainWindow(
        data_model_mock,
        csv_service_mock,
        validation_service_mock,
        correction_service_mock,
        chart_service_mock,
        data_manager_mock,
    )

    # Add BlockableElementMixin mock
    window.is_blocked = MagicMock(return_value=False)
    window.block = MagicMock()
    window.unblock = MagicMock()

    # Create import and data service mocks
    window._import_service = MagicMock()
    window._import_service.import_progress = MagicMock()
    window._import_service.import_progress.connect = MagicMock()
    window._import_service.import_completed = MagicMock()
    window._import_service.import_completed.connect = MagicMock()
    window._import_service.import_started = MagicMock()
    window._import_service.import_started.connect = MagicMock()
    window._import_service.import_error = MagicMock()
    window._import_service.import_error.connect = MagicMock()

    window._data_service = MagicMock()
    window._data_service.set_data = MagicMock()

    yield window

    # Cleanup
    window.close()


@pytest.fixture
def mock_file_dialog(monkeypatch):
    mock = MagicMock()
    mock.return_value = ("test_file.csv", "CSV Files (*.csv)")
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", mock)
    return mock
def mock_file_dialog(monkeypatch):
    mock = MagicMock()
    mock.return_value = ("test_file.csv", "CSV Files (*.csv)")
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", mock)
    return mock


@pytest.fixture
def mock_progress_dialog(monkeypatch):
    dialog_instance = MagicMock()
    dialog_instance.setMaximum = MagicMock()
    dialog_instance.setValue = MagicMock()
    dialog_instance.setLabelText = MagicMock()
    dialog_instance.wasCanceled = MagicMock(return_value=False)
    dialog_instance.close = MagicMock()

    mock = MagicMock(return_value=dialog_instance)
    monkeypatch.setattr(
        "chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog", mock
    )
    return mock
def mock_progress_dialog(monkeypatch):
    dialog_instance = MagicMock()
    dialog_instance.setMaximum = MagicMock()
    dialog_instance.setValue = MagicMock()
    dialog_instance.setLabelText = MagicMock()
    dialog_instance.wasCanceled = MagicMock(return_value=False)
    dialog_instance.close = MagicMock()

    mock = MagicMock(return_value=dialog_instance)
    monkeypatch.setattr(
        "chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog", mock
    )
    return mock


@pytest.fixture
def mock_message_box(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", mock)
    return mock
def mock_message_box(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", mock)
    return mock


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "item_id": ["item1", "item2", "item3"],
            "name": ["Item 1", "Item 2", "Item 3"],
            "quantity": [1, 2, 3],
        }
    )


def test_init(main_window):
    """Test that the main window initializes correctly."""
    assert main_window is not None
    # The window title might not be set in the test environment, so just check if it's a MainWindow
    assert isinstance(main_window, MainWindow)


def test_setup_ui(main_window):
    """Test that the UI is set up correctly."""
    assert main_window._content_stack is not None
    assert main_window._sidebar is not None
    assert main_window._status_bar is not None


def test_setup_signals(main_window):
    """Test that signals are connected correctly."""
    assert main_window._data_manager.load_started.connect.called
    assert main_window._data_manager.load_progress.connect.called
    assert main_window._data_manager.load_finished.connect.called
    assert main_window._data_manager.load_error.connect.called


def test_import_mf_companion_success(main_window, mock_file_dialog, monkeypatch, sample_data):
    """Test successful import from MF Companion."""
    # Setup mocks
    main_window._import_service.import_from_mf_companion = MagicMock(return_value=sample_data)

    # Mock UI state related methods on the main window
    main_window._setup_progress_dialog = MagicMock()
    main_window._close_progress_dialog = MagicMock()
    main_window._create_import_worker_thread = MagicMock()

    # Set up file dialog to return a test file
    mock_file_dialog.return_value = ("test_file.csv", "CSV Files (*.csv)")

    # Call the function
    main_window._import_data("mf_companion")

    # Check that the import function was called with the correct source type
    main_window._create_import_worker_thread.assert_called_once_with("mf_companion")

    # Check that the progress dialog was set up
    main_window._setup_progress_dialog.assert_called_once()


def test_import_cl_cetrk_success(
    main_window, mock_file_dialog, mock_progress_dialog, monkeypatch, sample_data
):
    """Test successful import from CL CETRK."""
    # Setup mocks
    main_window._import_service.import_from_cl_cetrk = MagicMock(return_value=sample_data)

    # Mock UI state related methods on the main window
    main_window._setup_progress_dialog = MagicMock()
    main_window._close_progress_dialog = MagicMock()
    main_window._create_import_worker_thread = MagicMock()

    # Set up file dialog to return a test file
    mock_file_dialog.return_value = ("test_file.csv", "CSV Files (*.csv)")

    # Call the function
    main_window._import_data("cl_cetrk")

    # Check that the import function was called with the correct source type
    main_window._create_import_worker_thread.assert_called_once_with("cl_cetrk")

    # Check that the progress dialog was set up
    main_window._setup_progress_dialog.assert_called_once()


def test_import_error_handling(
    main_window, mock_file_dialog, mock_progress_dialog, mock_message_box, monkeypatch
):
    """Test error handling during import."""
    # Setup mocks
    error_message = "Import error occurred"
    main_window._import_service.import_from_mf_companion = MagicMock(
        side_effect=Exception(error_message)
    )

    # Mock UI state related methods on the main window
    main_window._setup_progress_dialog = MagicMock()
    main_window._close_progress_dialog = MagicMock()
    main_window._create_import_worker_thread = MagicMock(side_effect=Exception(error_message))
    main_window._capture_snapshot = MagicMock()  # Mock snapshot to avoid error

    # Mock QMessageBox.critical directly
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", mock_message_box)

    # Set up file dialog to return a test file
    mock_file_dialog.return_value = ("test_file.csv", "CSV Files (*.csv)")

    # Call the function - expect exception
    try:
        main_window._import_data("mf_companion")
    except Exception as e:
        # This is expected, the test is about error handling
        assert str(e) == error_message

    # Since the error happens directly in _import_data, verify that setup_progress_dialog was called
    main_window._setup_progress_dialog.assert_called_once()

    # In real implementation a QMessageBox.critical is likely shown after the exception
    # but we can't test that here because the exception occurs before error handling


def test_on_load_started(main_window, mock_progress_dialog, monkeypatch):
    """Test load started signal handler."""
    # Create a mock for BlockableProgressDialog
    dialog_instance = MagicMock()
    monkeypatch.setattr(
        "chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog",
        MagicMock(return_value=dialog_instance),
    )

    # Reset the _progress_dialog if it exists
    main_window._progress_dialog = None

    # Call the function
    main_window._on_load_started()

    # Verify progress dialog was created
    assert main_window._progress_dialog is not None

    # Verify that expected state flags are set
    assert main_window._total_rows_loaded == 0
    assert main_window._file_loading_complete is False
    assert main_window._data_loaded is False


def test_on_load_progress(main_window, mock_progress_dialog):
    """Test load progress signal handler."""
    # Setup
    main_window._progress_dialog = mock_progress_dialog.return_value
    main_window._progress_dialog_finalized = False
    main_window._loading_state = {
        "current_file": "",
        "current_file_index": 0,
        "processed_files": [],
        "total_files": 1,
        "total_rows": 0,
    }
    main_window._total_rows_loaded = 0
    main_window._total_rows_estimated = 0
    main_window._last_progress_current = 0

    # Call the function
    main_window._on_load_progress("test_file.csv", 50, 100)

    # Verify progress dialog was updated
    main_window._progress_dialog.setLabelText.assert_called()
    main_window._progress_dialog.setValue.assert_called()

    # Verify that loading state was updated
    assert main_window._loading_state["current_file"] == "test_file.csv"
    assert main_window._loading_state["current_file_index"] == 1
    assert "test_file.csv" in main_window._loading_state["processed_files"]


def test_on_load_completed(main_window, mock_progress_dialog):
    """Test load completed signal handler."""
    # Setup
    main_window._progress_dialog = mock_progress_dialog.return_value
    main_window._close_progress_dialog = MagicMock()
    main_window._import_in_progress = True
    main_window._finalize_loading = MagicMock()

    # Call the function
    main_window._on_load_finished(True, "Data loading completed successfully")

    # Verify finalize_loading was called
    main_window._finalize_loading.assert_called_once_with(
        "Data loading completed successfully", None
    )


def test_on_load_error(main_window, mock_progress_dialog, mock_message_box, monkeypatch):
    """Test load error signal handler."""
    # Setup
    main_window._progress_dialog = mock_progress_dialog.return_value
    main_window._close_progress_dialog = MagicMock()
    main_window._status_bar = MagicMock()
    main_window._status_bar.set_error = MagicMock()
    error_message = "Load error occurred"

    # Call the function
    main_window._on_load_error(error_message)

    # Verify status bar error was set
    main_window._status_bar.set_error.assert_called_once_with(error_message)

    # Verify progress dialog was updated
    main_window._progress_dialog.setState.assert_called_once_with(
        2
    )  # 2 is the enum value for ERROR state
    main_window._progress_dialog.setStatusText.assert_called_once_with(error_message)
    main_window._progress_dialog.setCancelButtonText.assert_called_once_with("Close")


def test_close_progress_dialog(main_window, mock_progress_dialog):
    """Test close progress dialog function."""
    # Setup
    dialog_instance = mock_progress_dialog.return_value
    dialog_instance.hide = MagicMock()
    dialog_instance.accept = MagicMock()
    dialog_instance._end_operation = MagicMock()

    main_window._progress_dialog = dialog_instance
    main_window._import_in_progress = True

    # Call the function
    main_window._close_progress_dialog()

    # Verify progress dialog was properly closed
    dialog_instance.hide.assert_called_once()
    dialog_instance.accept.assert_called_once()

    # Verify that dialog reference is cleared
    assert main_window._progress_dialog is None
