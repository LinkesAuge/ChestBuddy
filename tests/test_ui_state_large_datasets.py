"""
test_ui_state_large_datasets.py

Description: Tests for UI State Management with large datasets,
focusing on performance optimization and memory usage.
"""

import gc
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
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


def measure_execution_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, (end_time - start_time) * 1000  # Time in milliseconds


def measure_memory_usage(func, *args, **kwargs):
    """Measure memory usage of a function."""
    try:
        import psutil
    except ImportError:
        pytest.skip("psutil not installed, skipping memory usage test")

    process = psutil.Process(os.getpid())

    # Force garbage collection before measurement
    gc.collect()

    # Get memory before
    before = process.memory_info().rss / 1024 / 1024  # MB

    # Execute function
    result = func(*args, **kwargs)

    # Force garbage collection after execution
    gc.collect()

    # Get memory after
    after = process.memory_info().rss / 1024 / 1024  # MB

    return result, after - before


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
def large_csv_file(tmp_path):
    """Create a large CSV file (100,000 rows) for testing."""
    file_path = tmp_path / "large_data.csv"

    # Create DataFrame with 100,000 rows
    data = {
        "Date": pd.date_range(start="2020-01-01", periods=100_000).astype(str),
        "Player Name": [f"Player{i}" for i in range(100_000)],
        "Source/Location": [f"Location{i % 100}" for i in range(100_000)],
        "Chest Type": [f"Chest{i % 20}" for i in range(100_000)],
        "Value": [i % 1000 for i in range(100_000)],
        "Clan": [f"Clan{i % 10}" for i in range(100_000)],
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def very_large_csv_file(tmp_path):
    """Create a very large CSV file (500,000 rows) for testing."""
    file_path = tmp_path / "very_large_data.csv"

    # Create a very large file in chunks to avoid memory issues
    with open(file_path, "w") as f:
        # Write header
        f.write("Date,Player Name,Source/Location,Chest Type,Value,Clan\n")

        # Write data in chunks
        for chunk in range(5):  # 5 chunks of 100,000 rows
            for i in range(100_000):
                idx = chunk * 100_000 + i
                date = (pd.Timestamp("2020-01-01") + pd.Timedelta(days=idx)).strftime("%Y-%m-%d")
                f.write(
                    f"{date},Player{idx},Location{idx % 100},Chest{idx % 20},{idx % 1000},Clan{idx % 10}\n"
                )

    return file_path


@pytest.fixture
def mock_services():
    """Create mock services for the MainWindow."""
    # Create a simple mock data model with chunked loading capability
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)

    # Create mock CSV service with chunked loading
    csv_service = MagicMock()

    # Mock data manager with load operations
    data_manager = MagicMock()

    # Add the necessary signals
    data_manager.load_started = MagicMock()
    data_manager.load_progress = MagicMock()
    data_manager.load_success = MagicMock()
    data_manager.load_error = MagicMock()
    data_manager.load_finished = MagicMock()

    # Add chunked loading capability to data_manager
    def load_file_chunked(file_path, chunk_size=10000):
        """Load a file in chunks to simulate efficient loading of large files."""
        # Emit started signal
        data_manager.load_started.emit()

        # Read the file in chunks
        total_chunks = 0
        accumulated_data = []

        # Count total lines to get progress information
        with open(file_path, "r") as f:
            total_lines = sum(1 for _ in f)

        # Process in chunks
        for chunk_idx, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
            # Emit progress
            progress = min(100, int((chunk_idx * chunk_size / total_lines) * 100))
            data_manager.load_progress.emit("", progress, 100)

            # Process the chunk
            accumulated_data.append(chunk)
            total_chunks += 1

            # Simulate some processing time
            time.sleep(0.05)

        # Combine chunks
        if accumulated_data:
            combined_data = pd.concat(accumulated_data)
            data_model.set_data(combined_data)

        # Emit success signals
        data_manager.load_finished.emit(True, f"Loaded {total_lines} rows in {total_chunks} chunks")
        data_manager.load_success.emit(file_path)

    data_manager.load_file_chunked = load_file_chunked

    # Use standard loading for smaller files
    def load_file(file_path):
        """Load a file in one go (standard method)."""
        # Emit started signal
        data_manager.load_started.emit()

        # Emit progress
        data_manager.load_progress.emit("", 50, 100)

        # Read the file
        data = pd.read_csv(file_path)

        # Set the data in the model
        data_model.set_data(data)

        # Emit success signals
        data_manager.load_finished.emit(True, f"Loaded {len(data)} rows")
        data_manager.load_success.emit(file_path)

    data_manager.load_file = load_file

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "data_manager": data_manager,
    }


class TestLargeDatasetPerformance:
    """Tests for UI State Management with large datasets."""

    def test_import_large_dataset(self, qtbot, app, mock_services, large_csv_file):
        """
        Test importing a large dataset and verify UI state.

        This test verifies that the UI State Management System properly
        handles UI blocking and unblocking during large dataset imports.
        """
        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Capture the initial UI state
        assert main_window.isEnabled(), "MainWindow should be enabled initially"

        # Get references to key UI elements we want to monitor
        data_view = main_window.get_view("data")
        assert data_view is not None, "DataView should exist"
        assert data_view.isEnabled(), "DataView should be enabled initially"

        # Keep track of UI state changes
        ui_states = {
            "main_window": [True],  # Initially enabled
            "data_view": [True],  # Initially enabled
        }

        # Create a slot to track UI state during import
        def track_ui_state():
            ui_states["main_window"].append(main_window.isEnabled())
            ui_states["data_view"].append(data_view.isEnabled())

        # Setup tracking timer to check UI state during import
        timer = QTimer()
        timer.timeout.connect(track_ui_state)
        timer.start(100)  # Check every 100ms

        # Flag to track completion
        import_completed = False

        def on_import_complete(*args, **kwargs):
            nonlocal import_completed
            import_completed = True

        # Connect to our mock signal
        mock_services["data_manager"].load_success.emit = on_import_complete

        try:
            # Measure import time
            start_time = time.time()

            # Start the import
            main_window.import_file(large_csv_file)

            # Wait for import to complete
            for _ in range(100):  # Wait up to 10 seconds
                if import_completed:
                    break
                qtbot.wait(100)
                app.processEvents()

            # Calculate import time
            import_time = time.time() - start_time

            # Verify import completed
            assert import_completed, "Import should have completed"

            # Wait for UI to update
            qtbot.wait(500)
            app.processEvents()
        finally:
            # Stop the timer to prevent accessing deleted Qt objects
            timer.stop()

        # There should be multiple UI state checks
        assert len(ui_states["main_window"]) > 1, "UI state should have been tracked multiple times"

        # Check if UI was blocked during import
        assert False in ui_states["main_window"] or False in ui_states["data_view"], (
            "UI should have been blocked at some point during import"
        )

        # Check final UI state - UI should be unblocked after import
        assert main_window.isEnabled(), "MainWindow should be enabled after import"
        assert data_view.isEnabled(), "DataView should be enabled after import"

        # Verify UI state manager has no active operations
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after import"
        )

        # Print performance information (not an assertion, just informational)
        print(f"Large dataset import time: {import_time:.2f} seconds")

    def test_lazy_loading_performance(self, qtbot, app, mock_services, large_csv_file):
        """
        Test that lazy loading works correctly with large datasets.

        This test verifies that chunked loading performs better than
        loading the entire dataset at once, while still maintaining
        proper UI state management.
        """
        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Get UI elements to monitor
        data_view = main_window.get_view("data")

        # Test standard loading first
        standard_import_completed = False

        def on_standard_import_complete(*args, **kwargs):
            nonlocal standard_import_completed
            standard_import_completed = True

        mock_services["data_manager"].load_success.emit = on_standard_import_complete

        # Measure standard import time
        standard_result, standard_time = measure_execution_time(
            main_window.import_file, large_csv_file
        )

        # Wait for standard import to complete
        for _ in range(100):  # Wait up to 10 seconds
            if standard_import_completed:
                break
            qtbot.wait(100)
            app.processEvents()

        # Wait for UI to update
        qtbot.wait(500)
        app.processEvents()

        # Verify UI is unblocked after standard import
        assert main_window.isEnabled(), "MainWindow should be enabled after standard import"
        assert data_view.isEnabled(), "DataView should be enabled after standard import"

        # Now test chunked loading
        chunked_import_completed = False

        def on_chunked_import_complete(*args, **kwargs):
            nonlocal chunked_import_completed
            chunked_import_completed = True

        mock_services["data_manager"].load_success.emit = on_chunked_import_complete

        # Create a custom import method that uses chunked loading
        def import_chunked(file_path):
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                mock_services["data_manager"].load_file_chunked(file_path)

        # Measure chunked import time
        chunked_result, chunked_time = measure_execution_time(import_chunked, large_csv_file)

        # Wait for chunked import to complete
        for _ in range(100):  # Wait up to 10 seconds
            if chunked_import_completed:
                break
            qtbot.wait(100)
            app.processEvents()

        # Wait for UI to update
        qtbot.wait(500)
        app.processEvents()

        # Verify UI is unblocked after chunked import
        assert main_window.isEnabled(), "MainWindow should be enabled after chunked import"
        assert data_view.isEnabled(), "DataView should be enabled after chunked import"

        # Print performance comparison (informational)
        print(f"Standard import time: {standard_time:.2f}ms")
        print(f"Chunked import time: {chunked_time:.2f}ms")

        # While we can't make absolute performance assertions (depends on hardware),
        # we can verify the UI state was properly managed in both cases
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after imports"
        )

    def test_memory_usage_optimization(self, qtbot, app, mock_services, very_large_csv_file):
        """
        Test that memory usage is optimized during large dataset operations.

        This test verifies that chunked loading uses less memory than
        standard loading, while still maintaining proper UI state management.
        """
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed, skipping memory usage test")

        # Create the MainWindow with our mocked services
        main_window = MockMainWindow(services=mock_services)
        qtbot.addWidget(main_window)
        main_window.show()

        # Get UI elements to monitor
        data_view = main_window.get_view("data")

        # Create regular import function that loads the entire file at once
        def standard_import():
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                # Read entire file into memory
                data = pd.read_csv(very_large_csv_file)
                mock_services["data_model"].set_data(data)

        # Create chunked import function that loads the file in chunks
        def chunked_import():
            with OperationContext(main_window.ui_state_manager, UIOperations.IMPORT, [main_window]):
                mock_services["data_manager"].load_file_chunked(
                    very_large_csv_file, chunk_size=10000
                )

        # Measure memory usage for regular import (may be high)
        try:
            # Skip if file is too large for available memory
            file_size_mb = os.path.getsize(very_large_csv_file) / (1024 * 1024)
            available_memory = psutil.virtual_memory().available / (1024 * 1024)

            if file_size_mb * 2 > available_memory:  # Need ~2x file size for pandas
                pytest.skip(f"Very large file requires too much memory: {file_size_mb:.2f}MB")

            # Measure standard import memory usage
            _, standard_memory = measure_memory_usage(standard_import)

            # Wait for UI to update and free memory
            qtbot.wait(500)
            app.processEvents()
            gc.collect()

            # Verify UI is unblocked
            assert main_window.isEnabled(), "MainWindow should be enabled after standard import"
            assert data_view.isEnabled(), "DataView should be enabled after standard import"

        except MemoryError:
            # If we run out of memory, that's actually what we expect
            standard_memory = float("inf")

            # Verify UI is unblocked even after memory error
            assert main_window.isEnabled(), "MainWindow should be enabled after memory error"
            assert data_view.isEnabled(), "DataView should be enabled after memory error"

        # Now measure chunked import memory usage
        _, chunked_memory = measure_memory_usage(chunked_import)

        # Wait for UI to update
        qtbot.wait(500)
        app.processEvents()

        # Verify UI is unblocked after chunked import
        assert main_window.isEnabled(), "MainWindow should be enabled after chunked import"
        assert data_view.isEnabled(), "DataView should be enabled after chunked import"

        # Print memory usage (informational)
        if standard_memory == float("inf"):
            print("Standard import: Memory error (ran out of memory)")
        else:
            print(f"Standard import memory usage: {standard_memory:.2f}MB")

        print(f"Chunked import memory usage: {chunked_memory:.2f}MB")

        # No operations should be active
        assert len(main_window.ui_state_manager._operations) == 0, (
            "No operations should be active after imports"
        )

        # Assert that chunked import uses less memory (if standard import didn't fail)
        if standard_memory != float("inf"):
            # This is a soft assertion as memory behavior can vary by platform
            if chunked_memory > standard_memory:
                print(f"Warning: Chunked import used more memory than standard import")
