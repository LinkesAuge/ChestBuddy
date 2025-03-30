"""
Tests for CorrectionView.

This module contains test cases for the CorrectionView class, which provides
a user interface for managing correction rules and applying corrections.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from chestbuddy.ui.views.correction_view import CorrectionView
from chestbuddy.ui.views.correction_rule_view import CorrectionRuleView


@pytest.fixture
def mock_data_model():
    """Create a mock ChestDataModel."""
    return MagicMock()


@pytest.fixture
def mock_correction_service():
    """Create a mock CorrectionService."""
    return MagicMock()


@pytest.fixture
def mock_data_view_controller():
    """Create a mock DataViewController."""
    controller = MagicMock()
    return controller


@pytest.fixture
def mock_correction_controller():
    """Create a mock CorrectionController."""
    controller = MagicMock()
    return controller


@pytest.fixture
def correction_view(qtbot, mock_data_model, mock_correction_service):
    """Create a CorrectionView instance for testing."""
    view = CorrectionView(mock_data_model, mock_correction_service)
    qtbot.addWidget(view)
    view.show()
    return view


class TestCorrectionView:
    """Test cases for the CorrectionView class."""

    def test_initialization(self, correction_view, mock_data_model, mock_correction_service):
        """Test that the view initializes correctly with all components."""
        # Check references are set correctly
        assert correction_view._data_model == mock_data_model
        assert correction_view._correction_service == mock_correction_service

        # Check initial state
        assert correction_view._controller is None
        assert correction_view._correction_controller is None
        assert correction_view._rule_view is None
        assert correction_view._rule_view_placeholder is not None

        # Check placeholder is visible
        placeholder_text = (
            correction_view._rule_view_placeholder.findChild(QVBoxLayout).itemAt(0).widget().text()
        )
        assert "Initializing correction rules view" in placeholder_text

    def test_set_controller(self, correction_view, mock_data_view_controller):
        """Test setting the data view controller."""
        correction_view.set_controller(mock_data_view_controller)

        # Check the controller is set
        assert correction_view._controller == mock_data_view_controller

        # Verify signals are connected (this is implementation-specific)
        mock_data_view_controller.correction_started.connect.assert_called()
        mock_data_view_controller.correction_completed.connect.assert_called()
        mock_data_view_controller.correction_error.connect.assert_called()
        mock_data_view_controller.operation_error.connect.assert_called()

    def test_set_correction_controller(self, correction_view, mock_correction_controller):
        """Test setting the correction controller creates the rule view."""
        # Initially, the rule view should be None and placeholder should exist
        assert correction_view._rule_view is None
        assert correction_view._rule_view_placeholder is not None

        # Set the correction controller
        correction_view.set_correction_controller(mock_correction_controller)

        # Check the controller is set and view is set in controller
        assert correction_view._correction_controller == mock_correction_controller
        mock_correction_controller.set_view.assert_called_once_with(correction_view)

        # Check placeholder is removed
        assert correction_view._rule_view_placeholder is None

        # Check rule view is created
        assert correction_view._rule_view is not None
        assert isinstance(correction_view._rule_view, CorrectionRuleView)

        # Check if the rule view is properly set up
        # Note: In Qt, parent() might not return the exact same object we passed as parent,
        # but it should be a QWidget, which is what we're checking here
        assert correction_view._rule_view.parent() is not None
        assert isinstance(correction_view._rule_view.parent(), QWidget)

    def test_update_view_content(self, correction_view):
        """Test that update_view_content updates the view properly."""
        # We'll use a spy to check if _show_status_message is called
        # instead of trying to mock _refresh_view_content
        correction_view._show_status_message = MagicMock()

        # Call update_view_content
        correction_view._update_view_content()

        # Verify _show_status_message was called at least twice
        # Once for "Updating correction rules..." and once for "Correction rules updated"
        assert correction_view._show_status_message.call_count >= 2
        assert (
            "Updating correction rules"
            in correction_view._show_status_message.call_args_list[0][0][0]
        )

    def test_rule_view_creation_with_debug_output(
        self, correction_view, mock_correction_controller
    ):
        """Test rule view creation with detailed debug output."""
        # Patch the logger to capture debug messages
        with patch("chestbuddy.ui.views.correction_view.logger") as mock_logger:
            # Set the correction controller
            correction_view.set_correction_controller(mock_correction_controller)

            # Check that appropriate debug messages were logged
            mock_logger.info.assert_called_with(
                "CorrectionView: Correction controller set and rule view created"
            )

            # Get the content layout
            content_layout = correction_view.get_content_layout()

            # Check that the rule view is in the layout
            rule_view_in_layout = False
            for i in range(content_layout.count()):
                if content_layout.itemAt(i).widget() == correction_view._rule_view:
                    rule_view_in_layout = True
                    break

            assert rule_view_in_layout, "Rule view should be in the content layout"
