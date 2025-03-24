"""
test_blockable_integration.py

Description: Integration tests for blockable UI components with the UI State Management System
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import pandas as pd
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import the UI state management components
from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    UIOperations,
    UIElementGroups,
)
from chestbuddy.utils.ui_state.manager import SingletonMeta

# Import the blockable components
from chestbuddy.ui.views.blockable import (
    BlockableDataView,
    BlockableValidationTab,
    BlockableCorrectionTab,
)

# Import adapters
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.views.correction_view_adapter import CorrectionViewAdapter


@pytest.fixture
def ui_state_manager():
    """Create a UIStateManager instance for testing."""
    # Reset the UIStateManager singleton instance
    if UIStateManager in SingletonMeta._instances:
        del SingletonMeta._instances[UIStateManager]

    # Create a new instance
    manager = UIStateManager()
    yield manager

    # Reset after test
    if UIStateManager in SingletonMeta._instances:
        del SingletonMeta._instances[UIStateManager]


@pytest.fixture
def mock_data_model():
    """Create a mock data model for testing."""
    mock = MagicMock()
    mock.data_changed = MagicMock()
    mock.validation_changed = MagicMock()

    # Add some mock data
    mock.get_dataframe.return_value = pd.DataFrame(
        {"ItemID": ["1", "2", "3"], "Value": [10, 20, 30]}
    )

    return mock


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service for testing."""
    mock = MagicMock()
    mock.validation_changed = MagicMock()
    mock.validate_data = MagicMock()
    return mock


@pytest.fixture
def mock_correction_service():
    """Create a mock correction service for testing."""
    mock = MagicMock()
    mock.correction_applied = MagicMock()
    mock.apply_correction = MagicMock()
    return mock


class TestBlockableIntegration:
    """Integration tests for blockable UI components."""

    def test_adapters_create_blockable_components(
        self,
        qtbot,
        ui_state_manager,
        mock_data_model,
        mock_validation_service,
        mock_correction_service,
    ):
        """Test that the view adapters create blockable components."""
        # Create the adapters
        data_view_adapter = DataViewAdapter(mock_data_model)
        validation_view_adapter = ValidationViewAdapter(mock_data_model, mock_validation_service)
        correction_view_adapter = CorrectionViewAdapter(mock_data_model, mock_correction_service)

        # Add widgets to qtbot for proper cleanup
        qtbot.addWidget(data_view_adapter)
        qtbot.addWidget(validation_view_adapter)
        qtbot.addWidget(correction_view_adapter)

        # Verify that the adapters created blockable components
        assert isinstance(data_view_adapter._data_view, BlockableDataView)
        assert isinstance(validation_view_adapter._validation_tab, BlockableValidationTab)
        assert isinstance(correction_view_adapter._correction_tab, BlockableCorrectionTab)

    def test_blockable_components_register_with_manager(
        self,
        qtbot,
        ui_state_manager,
        mock_data_model,
        mock_validation_service,
        mock_correction_service,
    ):
        """Test that blockable components register with the UI state manager."""
        # Create the blockable components directly
        data_view = BlockableDataView()
        validation_tab = BlockableValidationTab(mock_data_model, mock_validation_service)
        correction_tab = BlockableCorrectionTab(mock_data_model, mock_correction_service)

        # Add widgets to qtbot for proper cleanup
        qtbot.addWidget(data_view)
        qtbot.addWidget(validation_tab)
        qtbot.addWidget(correction_tab)

        # Verify that the components are registered with the UI state manager
        assert data_view._is_registered
        assert validation_tab._is_registered
        assert correction_tab._is_registered

        # Verify that they're registered with the correct groups
        assert any(
            elem is data_view
            for elem in ui_state_manager._group_registry.get(UIElementGroups.DATA_VIEW, set())
        )
        assert any(
            elem is validation_tab
            for elem in ui_state_manager._group_registry.get(UIElementGroups.VALIDATION, set())
        )
        assert any(
            elem is correction_tab
            for elem in ui_state_manager._group_registry.get(UIElementGroups.CORRECTION, set())
        )

    def test_operation_context_blocks_components(
        self,
        qtbot,
        ui_state_manager,
        mock_data_model,
        mock_validation_service,
        mock_correction_service,
    ):
        """Test that OperationContext correctly blocks and unblocks components."""
        # Create the blockable components
        data_view = BlockableDataView()
        validation_tab = BlockableValidationTab(mock_data_model, mock_validation_service)
        correction_tab = BlockableCorrectionTab(mock_data_model, mock_correction_service)

        # Add widgets to qtbot for proper cleanup
        qtbot.addWidget(data_view)
        qtbot.addWidget(validation_tab)
        qtbot.addWidget(correction_tab)

        # Verify that components start enabled
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()
        assert correction_tab.isEnabled()

        # Create an operation context for IMPORT that blocks data view
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]
        ):
            # Verify that data_view is blocked but others are not
            assert not data_view.isEnabled()
            assert validation_tab.isEnabled()
            assert correction_tab.isEnabled()

        # Verify all components are enabled again
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()
        assert correction_tab.isEnabled()

        # Create an operation context for VALIDATION that blocks validation tab
        with OperationContext(
            ui_state_manager, UIOperations.VALIDATION, groups=[UIElementGroups.VALIDATION]
        ):
            # Verify that validation_tab is blocked but others are not
            assert data_view.isEnabled()
            assert not validation_tab.isEnabled()
            assert correction_tab.isEnabled()

        # Verify all components are enabled again
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()
        assert correction_tab.isEnabled()

        # Create an operation context for CORRECTION that blocks correction tab
        with OperationContext(
            ui_state_manager, UIOperations.CORRECTION, groups=[UIElementGroups.CORRECTION]
        ):
            # Verify that correction_tab is blocked but others are not
            assert data_view.isEnabled()
            assert validation_tab.isEnabled()
            assert not correction_tab.isEnabled()

        # Verify all components are enabled again
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()
        assert correction_tab.isEnabled()

    def test_nested_operations(
        self,
        qtbot,
        ui_state_manager,
        mock_data_model,
        mock_validation_service,
        mock_correction_service,
    ):
        """Test that nested operations work correctly with reference counting."""
        # Create the blockable components
        data_view = BlockableDataView()
        validation_tab = BlockableValidationTab(mock_data_model, mock_validation_service)

        # Add widgets to qtbot for proper cleanup
        qtbot.addWidget(data_view)
        qtbot.addWidget(validation_tab)

        # Verify that components start enabled
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()

        # Create nested operation contexts
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]
        ):
            # First level - data_view blocked
            assert not data_view.isEnabled()

            with OperationContext(
                ui_state_manager, UIOperations.VALIDATION, groups=[UIElementGroups.VALIDATION]
            ):
                # Second level - data_view still blocked, validation_tab now blocked
                assert not data_view.isEnabled()
                assert not validation_tab.isEnabled()

                # Add another IMPORT operation that blocks data_view
                with OperationContext(
                    ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]
                ):
                    # Third level - data_view still blocked (now by 2 operations), validation_tab still blocked
                    assert not data_view.isEnabled()
                    assert not validation_tab.isEnabled()

                # After inner IMPORT - data_view still blocked by outer IMPORT, validation_tab still blocked
                assert not data_view.isEnabled()
                assert not validation_tab.isEnabled()

            # After VALIDATION - data_view still blocked by outer IMPORT, validation_tab unblocked
            assert not data_view.isEnabled()
            assert validation_tab.isEnabled()

        # After all operations - both should be unblocked
        assert data_view.isEnabled()
        assert validation_tab.isEnabled()

    def test_exception_handling(
        self,
        qtbot,
        ui_state_manager,
        mock_data_model,
        mock_validation_service,
        mock_correction_service,
    ):
        """Test that exception in operation context doesn't leave components blocked."""
        # Create the blockable components
        data_view = BlockableDataView()

        # Add widget to qtbot for proper cleanup
        qtbot.addWidget(data_view)

        # Verify that component starts enabled
        assert data_view.isEnabled()

        # Create operation context with an exception
        try:
            with OperationContext(
                ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]
            ):
                # Component should be blocked within the context
                assert not data_view.isEnabled()

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            # Exception caught, but component should be unblocked
            pass

        # Verify component is unblocked despite the exception
        assert data_view.isEnabled()
