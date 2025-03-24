"""
test_ui_state_performance.py

Description: Performance tests for the UI State Management System,
focusing on large datasets and high-frequency operations.
"""

import sys
import time
from pathlib import Path
import random
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the mock main window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow, MockBackgroundWorker

# Import UI state components
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
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
def large_dataset(tmp_path):
    """Create a large test dataset."""
    # Create a dataframe with 100,000 rows and 20 columns
    rows = 100000
    columns = 20

    data = {}
    for i in range(columns):
        col_name = f"column_{i}"
        data[col_name] = [random.randint(0, 1000) for _ in range(rows)]

    df = pd.DataFrame(data)

    # Save to CSV
    file_path = tmp_path / "large_dataset.csv"
    df.to_csv(file_path, index=False)

    return file_path, df


@pytest.fixture
def mock_services():
    """Create standard mock services."""
    # Create mock data model
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=True)

    # Create mock CSV service
    csv_service = MagicMock()

    # Create mock data manager with background worker
    data_manager = MagicMock()
    data_manager._worker = MockBackgroundWorker()

    # Add necessary signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "data_manager": data_manager,
    }


@pytest.fixture
def performance_main_window(qtbot, mock_services):
    """Create a main window for performance testing."""
    main_window = MockMainWindow(services=mock_services)
    qtbot.addWidget(main_window)

    # Add a method to simulate high-frequency UI operations
    def run_high_frequency_operations(operation_count=100, element_count=10):
        """Run many operations in rapid succession."""
        start_time = time.time()

        # Create many UI elements to test with
        elements = []
        for i in range(element_count):
            element = QWidget()
            element = main_window.make_blockable(element, f"element_{i}")
            main_window.ui_state_manager.add_element_to_group(element, UIElementGroups.DATA_VIEW)
            elements.append(element)

        # Perform operations
        for i in range(operation_count):
            operation = UIOperations.PROCESSING
            with OperationContext(main_window.ui_state_manager, operation, elements):
                # Just pass - we're testing performance, not functionality
                pass

        end_time = time.time()
        return {
            "time_taken": end_time - start_time,
            "operations_per_second": operation_count / (end_time - start_time),
            "elements": elements,
        }

    # Add method to process large dataset
    def process_large_dataset(df):
        """Simulate processing a large dataset with UI state management."""
        start_time = time.time()

        # Get some UI elements
        data_view = main_window.get_view("data")
        validation_view = main_window.get_view("validation")
        elements = [data_view, validation_view, main_window]

        # Start a long operation
        with OperationContext(main_window.ui_state_manager, UIOperations.PROCESSING, elements):
            # Simulate data processing in chunks
            chunk_size = 10000
            num_chunks = len(df) // chunk_size + (1 if len(df) % chunk_size > 0 else 0)

            for i in range(num_chunks):
                # Process each chunk
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(df))
                chunk = df.iloc[start_idx:end_idx]

                # Simulate processing time proportional to chunk size
                time.sleep(0.01)  # Small sleep to simulate work

                # Update progress
                progress = int((i + 1) / num_chunks * 100)
                mock_services["data_manager"].load_progress.emit(
                    progress, f"Processing chunk {i + 1}/{num_chunks}"
                )

                # Process events to keep UI responsive
                QApplication.processEvents()

        end_time = time.time()
        return {
            "time_taken": end_time - start_time,
            "rows_per_second": len(df) / (end_time - start_time),
        }

    # Add method for rapid UI state changes
    def run_rapid_ui_state_changes(duration=1.0, elements=None):
        """Rapidly change UI state to test responsiveness."""
        if elements is None:
            # Use default elements
            elements = [
                main_window.get_view("data"),
                main_window.get_view("validation"),
                main_window,
            ]

        # Track metrics
        operations_performed = 0
        start_time = time.time()
        end_time = start_time + duration

        # Run until the duration expires
        while time.time() < end_time:
            # Choose a random operation
            operation = random.choice(
                [
                    UIOperations.IMPORT,
                    UIOperations.EXPORT,
                    UIOperations.PROCESSING,
                    UIOperations.VALIDATION,
                    UIOperations.CORRECTION,
                ]
            )

            # Choose a random subset of elements
            target_elements = random.sample(elements, k=random.randint(1, len(elements)))

            # Perform the operation
            main_window.ui_state_manager.start_operation(operation, elements=target_elements)

            # Simulate minimal work
            QApplication.processEvents()

            # End the operation
            main_window.ui_state_manager.end_operation(operation, elements=target_elements)

            # Count the operation
            operations_performed += 1

        # Calculate metrics
        actual_duration = time.time() - start_time
        return {
            "operations_performed": operations_performed,
            "actual_duration": actual_duration,
            "operations_per_second": operations_performed / actual_duration,
        }

    # Add the methods to the main window
    main_window.run_high_frequency_operations = run_high_frequency_operations
    main_window.process_large_dataset = process_large_dataset
    main_window.run_rapid_ui_state_changes = run_rapid_ui_state_changes

    return main_window


class TestPerformance:
    """Performance tests for the UI State Management System."""

    def test_high_frequency_operations(self, qtbot, app, performance_main_window):
        """
        Test performance with high-frequency operations.

        This test measures how quickly the UI State Manager can handle
        many operations in rapid succession.
        """
        # Get the main window
        main_window = performance_main_window
        main_window.show()

        # Run high-frequency operations test
        result = main_window.run_high_frequency_operations(operation_count=1000, element_count=20)

        # Print performance metrics
        print(f"\nHigh-frequency operations test:")
        print(f"Time taken: {result['time_taken']:.4f} seconds")
        print(f"Operations per second: {result['operations_per_second']:.2f}")

        # Verify performance is acceptable
        # These thresholds should be adjusted based on the expected performance
        assert result["operations_per_second"] > 100, "Performance below threshold"

        # Verify all elements are enabled after test
        for element in result["elements"]:
            assert element.isEnabled(), "Element should be enabled after operations"

        # Verify no active operations remain
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_large_dataset_processing(self, qtbot, app, performance_main_window, large_dataset):
        """
        Test UI state management performance with large dataset processing.

        This test simulates processing a large dataset while managing UI state,
        to ensure the UI remains responsive during heavy processing.
        """
        # Get the main window and dataset
        main_window = performance_main_window
        main_window.show()
        file_path, df = large_dataset

        # Run the large dataset processing test
        result = main_window.process_large_dataset(df)

        # Print performance metrics
        print(f"\nLarge dataset processing test:")
        print(f"Dataset size: {len(df)} rows")
        print(f"Time taken: {result['time_taken']:.4f} seconds")
        print(f"Rows processed per second: {result['rows_per_second']:.2f}")

        # Verify performance is acceptable
        # These thresholds should be adjusted based on the expected performance
        assert result["rows_per_second"] > 10000, "Processing performance below threshold"

        # Verify UI is responsive after processing
        assert main_window.isEnabled(), "MainWindow should be enabled after processing"
        assert main_window.get_view("data").isEnabled(), (
            "DataView should be enabled after processing"
        )

        # Verify no active operations remain
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_rapid_ui_state_changes(self, qtbot, app, performance_main_window):
        """
        Test UI responsiveness with rapid UI state changes.

        This test rapidly changes UI state to ensure the system
        can handle frequent state transitions without degrading performance.
        """
        # Get the main window
        main_window = performance_main_window
        main_window.show()

        # Create extra UI elements to test with
        elements = []
        for i in range(30):  # Create 30 elements
            element = QWidget()
            element = main_window.make_blockable(element, f"element_{i}")
            main_window.ui_state_manager.add_element_to_group(
                element, UIElementGroups.DATA_VIEW if i % 2 == 0 else UIElementGroups.IMPORT_EXPORT
            )
            elements.append(element)

        # Run rapid UI state changes test (2 seconds duration)
        result = main_window.run_rapid_ui_state_changes(duration=2.0, elements=elements)

        # Print performance metrics
        print(f"\nRapid UI state changes test:")
        print(f"Duration: {result['actual_duration']:.4f} seconds")
        print(f"Operations performed: {result['operations_performed']}")
        print(f"Operations per second: {result['operations_per_second']:.2f}")

        # Verify performance is acceptable
        assert result["operations_per_second"] > 500, "UI state change performance below threshold"

        # Verify UI is responsive after test
        assert main_window.isEnabled(), "MainWindow should be enabled after test"

        # Verify all elements are enabled after test
        for element in elements:
            assert element.isEnabled(), "Element should be enabled after test"

        # Verify no active operations remain
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"

    def test_memory_usage_stability(self, qtbot, app, performance_main_window):
        """
        Test memory usage stability with repeated operations.

        This test ensures that the UI State Manager doesn't leak memory
        over many operations.
        """
        # Skip test if psutil is not available
        pytest.importorskip("psutil")
        import psutil

        # Get the main window
        main_window = performance_main_window
        main_window.show()

        # Get current process
        process = psutil.Process()

        # Measure initial memory usage
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Run many operations
        for _ in range(5):  # Run 5 batches
            # Run 1000 operations per batch
            main_window.run_high_frequency_operations(operation_count=1000, element_count=10)

            # Force garbage collection
            import gc

            gc.collect()

        # Measure final memory usage
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory

        # Print memory metrics
        print(f"\nMemory usage test:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")

        # Allow for some memory increase, but not too much
        # This threshold should be adjusted based on expected behavior
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f} MB"

        # Verify no active operations remain
        assert len(main_window.ui_state_manager._operations) == 0, "No operations should be active"
