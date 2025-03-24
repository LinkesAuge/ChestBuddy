"""
test_main_window_ui_state.py

Description: Tests for the MainWindow integration with the UI State Management System
"""

import os
import sys
import logging
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.utils.ui_state import UIStateManager
from chestbuddy.utils.ui_state.context import OperationContext
from chestbuddy.utils.ui_state.elements import BlockableElementMixin
from chestbuddy.utils.ui_state.constants import UIElementGroups, UIOperations
from chestbuddy.ui.widgets.blockable_progress_dialog import BlockableProgressDialog


# Import the real MainWindow class at the end to avoid metaclass conflicts
from chestbuddy.ui.main_window import MainWindow


@pytest.fixture
def app():
    """Create a QApplication instance."""
    # Check if there's already a QApplication instance
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def mock_services():
    """Mock the services for MainWindow."""
    data_model = MagicMock(spec=ChestDataModel)
    data_model.is_empty = PropertyMock(return_value=True)

    csv_service = MagicMock(spec=CSVService)
    validation_service = MagicMock(spec=ValidationService)
    correction_service = MagicMock(spec=CorrectionService)
    chart_service = MagicMock(spec=ChartService)

    # Create a mock data_manager with the required signals
    data_manager = MagicMock()
    data_manager.load_started = Signal()
    data_manager.load_progress = Signal(int, int)
    data_manager.load_finished = Signal()
    data_manager.load_success = Signal(str)
    data_manager.load_error = Signal(str)

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "validation_service": validation_service,
        "correction_service": correction_service,
        "chart_service": chart_service,
        "data_manager": data_manager,
    }


@pytest.fixture
def main_window(qtbot, app, mock_services):
    """Create a MainWindow instance for testing."""
    window = MainWindow(
        mock_services["data_model"],
        mock_services["csv_service"],
        mock_services["validation_service"],
        mock_services["correction_service"],
        mock_services["chart_service"],
        mock_services["data_manager"],
    )

    qtbot.addWidget(window)
    window.show()
    qtbot.waitForWindowShown(window)

    yield window

    window.close()


class TestMainWindowUIState:
    """Test cases for the MainWindow integration with the UI State Management System."""

    def test_main_window_inherits_blockable_element_mixin(self, main_window):
        """Test that MainWindow inherits from BlockableElementMixin."""
        assert isinstance(main_window, QMainWindow)
        assert isinstance(main_window, BlockableElementMixin)

    def test_main_window_registers_with_ui_state_manager(self, main_window):
        """Test that MainWindow registers with the UIStateManager."""
        # Check that the MainWindow's BlockableElementMixin is properly initialized
        assert main_window._is_registered
        assert main_window._ui_state_manager is not None

        # Check that the MainWindow is registered with the correct group
        ui_state_manager = UIStateManager()
        assert ui_state_manager.is_element_in_group(main_window, UIElementGroups.MAIN_WINDOW)

    def test_apply_block_implementation(self, main_window):
        """Test the _apply_block implementation."""
        # Manually call _apply_block to test its implementation
        main_window._apply_block()

        # Check that the UI components are disabled
        assert not main_window._sidebar.isEnabled()
        assert not main_window._content_stack.isEnabled()
        assert not main_window.menuBar().isEnabled()

    def test_apply_unblock_implementation(self, main_window):
        """Test the _apply_unblock implementation."""
        # First block the UI
        main_window._apply_block()

        # Then unblock it
        main_window._apply_unblock()

        # Check that the UI components are enabled
        assert main_window._sidebar.isEnabled()
        assert main_window._content_stack.isEnabled()
        assert main_window.menuBar().isEnabled()

    def test_on_load_started_uses_blockable_progress_dialog(self, main_window, qtbot):
        """Test that _on_load_started uses BlockableProgressDialog."""
        # Mock the BlockableProgressDialog.show_with_blocking method
        with patch(
            "chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog.show_with_blocking"
        ) as mock_show:
            # Call _on_load_started
            main_window._on_load_started()

            # Check that a BlockableProgressDialog was created
            assert isinstance(main_window._progress_dialog, BlockableProgressDialog)

            # Check that show_with_blocking was called with the correct parameters
            mock_show.assert_called_once()
            args, kwargs = mock_show.call_args
            assert args[0] == UIOperations.IMPORT
            assert UIElementGroups.MAIN_WINDOW in kwargs.get("groups", [])
            assert UIElementGroups.DATA_VIEW in kwargs.get("groups", [])
            assert UIElementGroups.NAVIGATION in kwargs.get("groups", [])

            # Clean up
            main_window._progress_dialog.accept()

    def test_close_progress_dialog_cleans_up_operation(self, main_window, qtbot):
        """Test that _close_progress_dialog properly cleans up the operation."""
        # Set up a progress dialog
        main_window._on_load_started()

        # Mock the accept method to prevent actual dialog closing
        with patch.object(main_window._progress_dialog, "accept") as mock_accept:
            # Call _close_progress_dialog
            main_window._close_progress_dialog()

            # Check that accept was called
            mock_accept.assert_called_once()
            
            # Check that the progress dialog was set to None
            assert main_window._progress_dialog is None

    def test_ui_blocking_during_import(self, main_window, qtbot):
        """Test that the UI is properly blocked during import operations."""
        # Start an import operation
        main_window._on_load_started()

        # Check that the UI state manager shows the import operation as active
        ui_state_manager = UIStateManager()
        assert ui_state_manager.is_operation_active(UIOperations.IMPORT)

        # Check that main window components are disabled
        assert not main_window._sidebar.isEnabled()
        assert not main_window._content_stack.isEnabled()
        assert not main_window.menuBar().isEnabled()

        # Clean up
        main_window._close_progress_dialog()

        # Check that the UI state manager no longer shows the import operation as active
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)

        # Check that main window components are re-enabled
        assert main_window._sidebar.isEnabled()
        assert main_window._content_stack.isEnabled()
        assert main_window.menuBar().isEnabled()