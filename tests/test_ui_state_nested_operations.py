"""
test_ui_state_nested_operations.py

Description: Tests for the UI State Management System with nested operations,
focusing on reference counting and proper operation stacking/unstacking.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the mock main window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow

# Import the UI state management components
from chestbuddy.utils.ui_state import (
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
)


@pytest.fixture
def app():
    """Create a QApplication for UI testing."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def test_csv_file(tmp_path):
    """Create a test CSV file with sample data."""
    file_path = tmp_path / "test_data.csv"
    with open(file_path, "w") as f:
        # Write header
        f.write("id,name,value\n")
        # Write some data
        f.write("1,Item 1,100\n")
        f.write("2,Item 2,200\n")
        f.write("3,Item 3,300\n")
    return file_path


@pytest.fixture
def mock_services():
    """Create standard mock services."""
    # Create a simple mock data model
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)

    # Create mock CSV service
    csv_service = MagicMock()

    # Create mock data manager
    data_manager = MagicMock()

    # Add the necessary signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    # Add validation service
    validation_service = MagicMock()
    validation_service.validate_data = MagicMock()
    validation_service.validation_complete = MagicMock()

    # Add correction service
    correction_service = MagicMock()
    correction_service.apply_correction = MagicMock()
    correction_service.correction_complete = MagicMock()

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "data_manager": data_manager,
        "validation_service": validation_service,
        "correction_service": correction_service,
    }


@pytest.fixture
def nested_operation_main_window(qtbot, mock_services):
    """Create a main window capable of nested operations for testing."""
    # Create the mock main window
    main_window = MockMainWindow(services=mock_services)
    qtbot.addWidget(main_window)

    # Add methods for nested operations
    def start_validation_during_import(file_path):
        """Start a validation operation nested inside an import operation."""
        # Start import operation
        with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
            # Emit started signal
            main_window.import_started.emit()

            # Start nested validation operation
            with OperationContext(
                main_window.ui_state_manager,
                UIOperations.VALIDATION,
                [main_window.get_view("data")],
            ):
                # Simulate validation
                if "validation_service" in mock_services:
                    mock_services["validation_service"].validate_data()

                # Wait to simulate work
                qtbot.wait(100)

            # Complete import operation
            if "data_manager" in mock_services:
                # Simulate data loading
                mock_services["data_manager"].load_finished.emit(True, "Import completed")
                mock_services["data_manager"].load_success.emit(file_path)
            else:
                main_window._on_load_finished(True, "Import completed")

    # Add method to main window
    main_window.start_validation_during_import = start_validation_during_import

    # Add method for multiple nested operations of the same type
    def start_multiple_nested_imports(file_path, nesting_depth=3):
        """Start multiple nested operations of the same type (IMPORT)."""

        # Create the outermost context
        def nested_import(depth):
            if depth <= 0:
                return

            # Start an import operation
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                # Emit started signal
                main_window.import_started.emit()

                # Recursively nest more operations
                if depth > 1:
                    nested_import(depth - 1)

                # Complete this level of import
                main_window._on_load_finished(True, f"Level {depth} import completed")

        # Start the nested imports
        nested_import(nesting_depth)

    # Add method to main window
    main_window.start_multiple_nested_imports = start_multiple_nested_imports

    # Add method for operations with different elements
    def start_operations_with_different_elements():
        """Start operations that block different UI elements."""
        # Start a main window operation
        with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
            # This should block main_window
            assert not main_window.isEnabled(), "MainWindow should be blocked"

            # Start a data view operation
            data_view = main_window.get_view("data")
            with OperationContext(
                main_window.ui_state_manager, UIOperations.VALIDATION, [data_view]
            ):
                # This should block data_view
                assert not data_view.isEnabled(), "DataView should be blocked"

                # Start a chart view operation
                chart_view = main_window.get_view("chart")
                with OperationContext(
                    main_window.ui_state_manager, UIOperations.EXPORT, [chart_view]
                ):
                    # This should block chart_view
                    assert not chart_view.isEnabled(), "ChartView should be blocked"

                    # Wait to simulate work
                    qtbot.wait(100)

                # After innermost operation, chart_view should be unblocked
                # but data_view and main_window should still be blocked
                assert chart_view.isEnabled(), "ChartView should be unblocked"
                assert not data_view.isEnabled(), "DataView should still be blocked"
                assert not main_window.isEnabled(), "MainWindow should still be blocked"

            # After middle operation, data_view should be unblocked
            # but main_window should still be blocked
            assert data_view.isEnabled(), "DataView should be unblocked"
            assert not main_window.isEnabled(), "MainWindow should still be blocked"

        # After outermost operation, all elements should be unblocked
        assert main_window.isEnabled(), "MainWindow should be unblocked"
        assert data_view.isEnabled(), "DataView should be unblocked"
        assert chart_view.isEnabled(), "ChartView should be unblocked"

    # Add method to main window
    main_window.start_operations_with_different_elements = start_operations_with_different_elements

    return main_window


class TestNestedOperations:
    """Tests for nested operations in the UI State Management System."""

    def test_nested_import_operations(
        self, qtbot, app, nested_operation_main_window, test_csv_file
    ):
        """
        Test nested operations - validation within import.

        This test verifies that nested operations work correctly, with each
        operation properly stacking and unstacking.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Capture initial state
        assert main_window.isEnabled(), "MainWindow should be enabled initially"
        assert data_view.isEnabled(), "DataView should be enabled initially"

        # Keep track of active operations
        operation_counts = []

        # Setup tracking timer to monitor operation counts during the test
        def track_operations():
            operation_counts.append(len(main_window.ui_state_manager._operations))

        timer = QTimer()
        timer.timeout.connect(track_operations)
        timer.start(50)  # Check every 50ms

        try:
            # Start nested operations
            main_window.start_validation_during_import(test_csv_file)

            # Wait for operations to complete
            qtbot.wait(500)
            app.processEvents()
        finally:
            timer.stop()

        # Verify operations were properly tracked
        assert max(operation_counts, default=0) > 1, "Should have had multiple active operations"
        assert operation_counts[-1] == 0, "No operations should be active at the end"

        # Verify UI state after nested operations
        assert main_window.isEnabled(), "MainWindow should be enabled after operations"
        assert data_view.isEnabled(), "DataView should be enabled after operations"

    def test_operation_reference_counting(self, qtbot, app, nested_operation_main_window):
        """
        Test reference counting in nested operations.

        This test verifies that reference counting works correctly for nested
        operations, with UI elements remaining blocked until all operations
        affecting them are complete.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Start a sequence of nested operations manually
        # First level: IMPORT
        with OperationContext(
            main_window.ui_state_manager, UIOperations.IMPORT, [main_window, data_view]
        ):
            # Verify elements are blocked
            assert not main_window.isEnabled(), "MainWindow should be blocked at first level"
            assert not data_view.isEnabled(), "DataView should be blocked at first level"

            # Check operation count
            assert len(main_window.ui_state_manager._operations) == 1, (
                "Should have one active operation"
            )

            # Second level: Same operation type (IMPORT)
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                # Elements should still be blocked
                assert not main_window.isEnabled(), "MainWindow should be blocked at second level"
                assert not data_view.isEnabled(), "DataView should be blocked at second level"

                # Check operation count - still one operation but with increased reference count
                assert len(main_window.ui_state_manager._operations) == 1, (
                    "Should still have one active operation"
                )

                # Third level: Different operation type (VALIDATION)
                with OperationContext(
                    main_window.ui_state_manager, UIOperations.VALIDATION, [data_view]
                ):
                    # Elements should still be blocked
                    assert not main_window.isEnabled(), (
                        "MainWindow should be blocked at third level"
                    )
                    assert not data_view.isEnabled(), "DataView should be blocked at third level"

                    # Check operation count - should be 2 since it's a different operation type
                    assert len(main_window.ui_state_manager._operations) == 2, (
                        "Should have two active operations"
                    )

        # After all operations complete, all elements should be unblocked
        assert main_window.isEnabled(), "MainWindow should be enabled after all operations"
        assert data_view.isEnabled(), "DataView should be enabled after all operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after all operations"
        )

    def test_multiple_nested_operations_same_type(
        self, qtbot, app, nested_operation_main_window, test_csv_file
    ):
        """
        Test multiple nested operations of the same type.

        This test verifies that multiple nested operations of the same type
        work correctly with reference counting.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Capture initial state
        assert main_window.isEnabled(), "MainWindow should be enabled initially"

        # Track the maximum nesting depth
        max_operation_count = 0

        # Setup tracking to monitor operation counts
        def track_operations():
            nonlocal max_operation_count
            current_count = len(main_window.ui_state_manager._operations)
            max_operation_count = max(max_operation_count, current_count)

        timer = QTimer()
        timer.timeout.connect(track_operations)
        timer.start(50)  # Check every 50ms

        try:
            # Start multiple nested operations
            main_window.start_multiple_nested_imports(test_csv_file, nesting_depth=3)

            # Wait for operations to complete
            qtbot.wait(500)
            app.processEvents()
        finally:
            timer.stop()

        # Only 1 operation type should be active even with 3 levels of nesting
        assert max_operation_count == 1, "Should have one operation type with 3 levels of nesting"

        # Verify UI state after operations
        assert main_window.isEnabled(), "MainWindow should be enabled after operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after operations"
        )

    def test_different_elements_in_operations(self, qtbot, app, nested_operation_main_window):
        """
        Test operations with different UI elements.

        This test verifies that operations can block and unblock different
        UI elements independently.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")
        chart_view = main_window.get_view("chart")

        # Capture initial state
        assert main_window.isEnabled(), "MainWindow should be enabled initially"
        assert data_view.isEnabled(), "DataView should be enabled initially"
        assert chart_view.isEnabled(), "ChartView should be enabled initially"

        # Run operations with different elements
        main_window.start_operations_with_different_elements()

        # Wait for operations to complete
        qtbot.wait(500)
        app.processEvents()

        # Verify UI state after operations
        assert main_window.isEnabled(), "MainWindow should be enabled after operations"
        assert data_view.isEnabled(), "DataView should be enabled after operations"
        assert chart_view.isEnabled(), "ChartView should be enabled after operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after operations"
        )

    def test_operation_groups(self, qtbot, app, nested_operation_main_window):
        """
        Test operations with element groups.

        This test verifies that operations can block and unblock elements
        based on their group membership.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")

        # Verify initial element group memberships
        assert main_window.ui_state_manager.is_element_in_group(
            main_window, UIElementGroups.MAIN_WINDOW
        ), "MainWindow should be in MAIN_WINDOW group"

        # Block elements by group
        with OperationContext(
            main_window.ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.MAIN_WINDOW]
        ):
            # MainWindow should be blocked
            assert not main_window.isEnabled(), "MainWindow should be blocked by group operation"

            # Now also block DATA_VIEW group
            with OperationContext(
                main_window.ui_state_manager,
                UIOperations.VALIDATION,
                groups=[UIElementGroups.DATA_VIEW],
            ):
                # DataView should be blocked
                data_view_is_blocked = False
                for view in main_window.views.values():
                    if view.get_name() == "data" and not view.is_enabled():
                        data_view_is_blocked = True
                assert data_view_is_blocked, "DataView should be blocked by group operation"

        # All elements should be unblocked
        assert main_window.isEnabled(), "MainWindow should be enabled after group operations"
        assert data_view.isEnabled(), "DataView should be enabled after group operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after operations"
        )

    def test_mixed_element_and_group_operations(self, qtbot, app, nested_operation_main_window):
        """
        Test operations with both specific elements and groups.

        This test verifies that operations can block and unblock both
        specific elements and element groups.
        """
        # Get the main window
        main_window = nested_operation_main_window
        main_window.show()

        # Get UI elements to track
        data_view = main_window.get_view("data")
        chart_view = main_window.get_view("chart")

        # Block specific element and group
        with OperationContext(
            main_window.ui_state_manager,
            UIOperations.IMPORT,
            elements=[main_window],
            groups=[UIElementGroups.DATA_VIEW],
        ):
            # MainWindow should be blocked as a specific element
            assert not main_window.isEnabled(), "MainWindow should be blocked as specific element"

            # DataView should be blocked as part of a group
            assert not data_view.isEnabled(), "DataView should be blocked as part of group"

            # ChartView should not be blocked (not specified and not in the group)
            assert chart_view.isEnabled(), "ChartView should not be blocked"

        # All elements should be unblocked
        assert main_window.isEnabled(), "MainWindow should be enabled after operations"
        assert data_view.isEnabled(), "DataView should be enabled after operations"
        assert chart_view.isEnabled(), "ChartView should be enabled after operations"

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after operations"
        )
