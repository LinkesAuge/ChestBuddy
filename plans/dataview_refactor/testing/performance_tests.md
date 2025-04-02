# DataView Refactoring - Performance Testing Strategy

## Overview

This document outlines the performance testing strategy for the DataView refactoring project. Performance testing is critical for ensuring that the refactored DataView component can efficiently handle large datasets while maintaining a responsive user interface. This strategy focuses on measuring, benchmarking, and optimizing performance across various aspects of the DataView.

## Performance Testing Approach

The performance testing strategy follows these principles:

1. **Establish Baselines**: Measure current performance to establish baseline metrics.
2. **Regular Benchmarking**: Continually test performance throughout development.
3. **Realistic Data Sets**: Test with real-world data volumes and complexity.
4. **User-Centric Metrics**: Focus on metrics that directly impact user experience.
5. **Identify Bottlenecks**: Use profiling to identify optimization opportunities.

## Critical Performance Metrics

### 1. Load Time Metrics

- **Initial Load Time**: Time to load and display data when view is first created
- **Data Update Time**: Time to refresh view when underlying data changes
- **Column Add/Remove Time**: Time to update view when columns are added/removed
- **Filter Application Time**: Time to apply filters to large datasets

### 2. Interaction Metrics

- **Scroll Responsiveness**: Time to render during scrolling operations
- **Selection Response Time**: Time to highlight selected cells/rows
- **Context Menu Display Time**: Time to display context menu on right-click
- **Sort Operation Time**: Time to sort data by column

### 3. Rendering Metrics

- **Cell Rendering Time**: Time to render individual cells
- **Validation Highlight Time**: Time to apply validation highlighting
- **Correction Indicator Time**: Time to display correction indicators
- **Total Frame Rate**: Frames per second during various operations

### 4. Memory Usage Metrics

- **Memory Consumption**: RAM usage with various dataset sizes
- **Memory Growth Pattern**: How memory usage scales with data size
- **Peak Memory Usage**: Maximum memory consumption during operations
- **Memory Leaks**: Detection of memory not properly released

## Performance Test Environments

### Test Data Sizes

Performance tests will be conducted with datasets of various sizes:

- **Small**: 100-1,000 rows (baseline)
- **Medium**: 10,000-50,000 rows (typical use case)
- **Large**: 100,000+ rows (stress testing)

### System Configurations

Tests will be run on multiple system configurations:

- **Development Environment**: High-performance development machines
- **Minimum Spec Environment**: Hardware meeting minimum requirements
- **Target Environment**: Hardware matching typical user environments

## Performance Test Implementation

### Test Fixtures and Utilities

```python
# performance_test_fixtures.py

import pytest
import time
import pandas as pd
import numpy as np
import psutil
import os
from functools import wraps
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from chestbuddy.ui.data.views import DataTableView
from chestbuddy.ui.data.models import DataViewModel
from chestbuddy.core.models import ChestDataModel

# Benchmark decorator
def benchmark(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"Function: {func.__name__}")
        print(f"Execution time: {execution_time:.4f} seconds")
        print(f"Memory change: {memory_used:.2f} MB")
        
        return result, execution_time, memory_used
    return wrapper

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def generate_test_data():
    """Generate test data of specified size."""
    def _generate(rows, columns=5):
        """Generate pandas DataFrame with specified dimensions."""
        data = {}
        for i in range(columns):
            col_name = f"Column_{i}"
            if i == 0:
                # String column (e.g., Player names)
                data[col_name] = [f"Player_{j}" for j in range(rows)]
            elif i == 1:
                # Categorical column (e.g., Chest types)
                categories = ["Gold", "Silver", "Bronze", "Diamond", "Platinum"]
                data[col_name] = [categories[j % len(categories)] for j in range(rows)]
            elif i == 2:
                # Numeric column (e.g., Scores)
                data[col_name] = np.random.randint(1, 1000, rows)
            elif i == 3:
                # Date column
                data[col_name] = [f"2023-{(j % 12) + 1:02d}-{(j % 28) + 1:02d}" for j in range(rows)]
            else:
                # Boolean column
                data[col_name] = [j % 2 == 0 for j in range(rows)]
        
        return pd.DataFrame(data)
    
    return _generate

@pytest.fixture
def data_view_with_data(qapp, generate_test_data):
    """Create a DataTableView with test data of specified size."""
    def _create_view(rows, columns=5):
        # Generate test data
        test_data = generate_test_data(rows, columns)
        
        # Create data model and view model
        data_model = ChestDataModel()
        data_model.update_data(test_data)
        view_model = DataViewModel(data_model)
        
        # Create view
        view = DataTableView()
        view.setModel(view_model)
        view.resize(800, 600)
        
        return view, test_data
    
    return _create_view

@pytest.fixture
def frame_counter(qtbot):
    """Count frames rendered in a time period."""
    class FrameCounter:
        def __init__(self, widget):
            self.widget = widget
            self.count = 0
            self.running = False
            
            # Create a function to count repaints
            def count_paint():
                if self.running:
                    self.count += 1
            
            # Connect to repaint events
            self.widget.repaint = count_paint
        
        def start(self):
            """Start counting frames."""
            self.count = 0
            self.running = True
            
        def stop(self):
            """Stop counting frames."""
            self.running = False
            return self.count
            
        def measure_fps(self, seconds=1.0):
            """Measure frames per second."""
            self.start()
            qtbot.wait(int(seconds * 1000))
            frames = self.stop()
            return frames / seconds
    
    return FrameCounter

@pytest.fixture
def profile_memory():
    """Track memory usage over time."""
    class MemoryProfiler:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.snapshots = []
            
        def take_snapshot(self, label=""):
            """Take a memory snapshot."""
            memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.snapshots.append((label, memory, time.time()))
            return memory
            
        def get_report(self):
            """Get a memory usage report."""
            if not self.snapshots:
                return "No snapshots taken"
                
            report = ["Memory Usage Report:"]
            base_time = self.snapshots[0][2]
            base_memory = self.snapshots[0][1]
            
            for label, memory, timestamp in self.snapshots:
                time_delta = timestamp - base_time
                memory_delta = memory - base_memory
                report.append(f"{label}: {memory:.2f} MB (Δ{memory_delta:+.2f} MB) at {time_delta:.2f}s")
                
            return "\n".join(report)
    
    return MemoryProfiler
```

### Load Time Performance Tests

```python
# test_load_performance.py

import pytest
import time
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt

class TestLoadPerformance:
    """Tests for data loading and update performance."""
    
    def test_initial_load_time(self, data_view_with_data, benchmark):
        """Test time to create and load DataView with various data sizes."""
        # Test with different dataset sizes
        sizes = [100, 1000, 10000, 50000, 100000]
        results = []
        
        for size in sizes:
            @benchmark
            def load_data():
                view, data = data_view_with_data(size)
                return view
                
            result, time_taken, memory_used = load_data()
            results.append((size, time_taken, memory_used))
        
        # Log results
        for size, load_time, memory_used in results:
            print(f"Size: {size} rows - Load Time: {load_time:.4f}s - Memory: {memory_used:.2f} MB")
        
        # Check that load times scale reasonably (not exponentially)
        # For example, 10x data should take less than 20x time
        small_load = results[0][1]  # Time for smallest dataset
        large_load = results[-1][1]  # Time for largest dataset
        size_ratio = sizes[-1] / sizes[0]
        time_ratio = large_load / small_load
        
        assert time_ratio < size_ratio * 2, f"Load time scaling is poor: {time_ratio:.2f}x time for {size_ratio:.2f}x data"
    
    def test_data_update_time(self, data_view_with_data, qtbot, benchmark):
        """Test time to update DataView when data changes."""
        # Create view with initial data
        view, initial_data = data_view_with_data(10000)
        
        # Wait for initial load
        qtbot.wait(100)
        
        # Test update time with various data sizes
        sizes = [100, 1000, 10000, 50000, 100000]
        results = []
        
        for size in sizes:
            # Create new data
            new_data = pd.DataFrame({
                'Column_0': [f"Player_{i}" for i in range(size)],
                'Column_1': ["Gold", "Silver", "Bronze"] * (size // 3 + 1),
                'Column_2': np.random.randint(1, 1000, size),
                'Column_3': [f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(size)],
                'Column_4': [i % 2 == 0 for i in range(size)]
            })
            
            # Benchmark update
            @benchmark
            def update_data():
                view.model().sourceModel().update_data(new_data)
                qtbot.wait(10)  # Small wait for events to process
                
            result, time_taken, memory_used = update_data()
            results.append((size, time_taken, memory_used))
        
        # Log results
        for size, update_time, memory_used in results:
            print(f"Size: {size} rows - Update Time: {update_time:.4f}s - Memory: {memory_used:.2f} MB")
        
        # Check that update times for large datasets meet performance targets
        # Maximum acceptable update time (adjust based on requirements)
        max_acceptable_time = 2.0  # seconds
        assert results[-1][1] < max_acceptable_time, f"Update time for large dataset too slow: {results[-1][1]:.4f}s"
```

### Interaction Performance Tests

```python
# test_interaction_performance.py

import pytest
import time
import numpy as np
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest

class TestInteractionPerformance:
    """Tests for user interaction performance."""
    
    def test_scrolling_performance(self, data_view_with_data, qtbot, frame_counter):
        """Test scrolling performance with large datasets."""
        # Create view with large dataset
        view, data = data_view_with_data(100000)
        qtbot.wait(200)  # Wait for initial load
        
        # Show view to enable rendering
        view.show()
        qtbot.wait(100)
        
        # Create frame counter
        counter = frame_counter(view)
        
        # Measure baseline FPS (no scrolling)
        baseline_fps = counter.measure_fps(0.5)
        
        # Measure FPS during scrolling
        counter.start()
        
        # Simulate scrolling through the data
        scrollbar = view.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # Scroll in steps
        steps = 10
        for i in range(0, steps + 1):
            # Set scroll position
            position = (max_value * i) // steps
            scrollbar.setValue(position)
            qtbot.wait(50)  # Wait for rendering
        
        # Calculate scrolling FPS
        scrolling_time = steps * 0.05  # 50ms per step
        frame_count = counter.stop()
        scrolling_fps = frame_count / scrolling_time
        
        # Log results
        print(f"Baseline FPS: {baseline_fps:.2f}")
        print(f"Scrolling FPS: {scrolling_fps:.2f}")
        
        # Check scrolling performance
        min_acceptable_fps = 15  # Minimum acceptable frames per second
        assert scrolling_fps >= min_acceptable_fps, f"Scrolling FPS too low: {scrolling_fps:.2f}"
    
    def test_selection_performance(self, data_view_with_data, qtbot, benchmark):
        """Test selection performance with large datasets."""
        # Create view with large dataset
        view, data = data_view_with_data(50000)
        view.show()
        qtbot.wait(200)  # Wait for initial load
        
        # Test single selection
        @benchmark
        def single_selection():
            # Select a single cell in the middle of the dataset
            middle_row = 25000
            index = view.model().index(middle_row, 0)
            view.setCurrentIndex(index)
            qtbot.wait(10)  # Small wait for events
            
        result, single_time, single_memory = single_selection()
        
        # Test range selection
        @benchmark
        def range_selection():
            # Clear selection
            view.clearSelection()
            
            # Select a range of cells
            start_row = 10000
            end_row = 11000  # 1000 rows
            
            # Select starting point
            start_index = view.model().index(start_row, 0)
            view.setCurrentIndex(start_index)
            
            # Press shift and extend selection
            view.selectionModel().select(
                view.model().index(end_row, 3),
                Qt.ItemSelectionModel.SelectCurrent | Qt.ItemSelectionModel.Rows
            )
            qtbot.wait(50)  # Wait for selection to complete
            
        result, range_time, range_memory = range_selection()
        
        # Log results
        print(f"Single cell selection time: {single_time:.4f}s")
        print(f"Range selection time (1000 rows): {range_time:.4f}s")
        
        # Check performance
        max_single_time = 0.1  # 100ms
        max_range_time = 0.5  # 500ms
        
        assert single_time < max_single_time, f"Single selection too slow: {single_time:.4f}s"
        assert range_time < max_range_time, f"Range selection too slow: {range_time:.4f}s"
```

### Rendering Performance Tests

```python
# test_rendering_performance.py

import pytest
import time
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt
from chestbuddy.core.enums.validation_enums import ValidationStatus

class TestRenderingPerformance:
    """Tests for rendering performance."""
    
    def test_validation_highlight_performance(self, data_view_with_data, qtbot, benchmark):
        """Test performance of validation highlighting."""
        # Create view with medium dataset
        view, data = data_view_with_data(20000)
        view.show()
        qtbot.wait(200)  # Wait for initial load
        
        # Create validation states
        # In a real application, this would come from ValidationService
        # Here we're creating a test validation dataframe
        
        # Create validation data with varying percentages of invalid cells
        percentages = [0, 1, 5, 10, 25, 50]
        results = []
        
        for percentage in percentages:
            # Number of invalid cells
            invalid_count = int(20000 * (percentage / 100))
            
            # Create validation DataFrame
            validation_data = {}
            for col in range(5):
                col_name = f"Column_{col}_status"
                
                # Default all to VALID
                statuses = [ValidationStatus.VALID] * 20000
                
                # Set some cells to INVALID randomly
                if invalid_count > 0:
                    invalid_indices = np.random.choice(20000, invalid_count, replace=False)
                    for idx in invalid_indices:
                        statuses[idx] = ValidationStatus.INVALID
                
                validation_data[col_name] = statuses
            
            validation_df = pd.DataFrame(validation_data)
            
            # Benchmark applying validation highlighting
            @benchmark
            def apply_validation():
                # Get table state manager
                table_state_manager = view.model().table_state_manager
                
                # Apply validation states
                # This depends on the actual implementation
                # In this example, we're assuming a direct update method
                table_state_manager.update_cell_states_from_validation(validation_df)
                
                # Wait for UI to update
                qtbot.wait(100)
            
            result, time_taken, memory_used = apply_validation()
            results.append((percentage, time_taken, memory_used))
        
        # Log results
        for percentage, highlight_time, memory_used in results:
            print(f"{percentage}% invalid - Time: {highlight_time:.4f}s - Memory: {memory_used:.2f} MB")
            
        # Check performance scaling
        # Time should scale reasonably with percentage of invalid cells
        # A simple check: 50% invalid should take less than 10x time of 5% invalid
        time_ratio = results[-1][1] / results[2][1]  # 50% vs 5%
        assert time_ratio < 10, f"Poor scaling for validation highlighting: {time_ratio:.2f}x slower for 10x more invalid cells"
    
    def test_cell_rendering_performance(self, data_view_with_data, qtbot, frame_counter):
        """Test cell rendering performance."""
        # Create views with different numbers of visible columns
        column_counts = [5, 10, 15, 20]
        fps_results = []
        
        for columns in column_counts:
            # Create view with data
            view, data = data_view_with_data(10000, columns)
            view.resize(800, 600)
            view.show()
            qtbot.wait(200)  # Wait for initial load
            
            # Create frame counter
            counter = frame_counter(view)
            
            # Measure FPS during scrolling
            fps = counter.measure_fps(1.0)
            fps_results.append((columns, fps))
            
            # Clean up
            view.hide()
            qtbot.wait(50)
        
        # Log results
        for columns, fps in fps_results:
            print(f"Columns: {columns} - FPS: {fps:.2f}")
            
        # Check performance
        min_acceptable_fps = 20  # Minimum acceptable FPS
        assert fps_results[-1][1] >= min_acceptable_fps, f"Rendering too slow with many columns: {fps_results[-1][1]:.2f} FPS"
```

### Memory Usage Tests

```python
# test_memory_usage.py

import pytest
import time
import gc
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt

class TestMemoryUsage:
    """Tests for memory usage and leaks."""
    
    def test_memory_scaling(self, data_view_with_data, profile_memory):
        """Test how memory usage scales with dataset size."""
        # Create memory profiler
        profiler = profile_memory()
        
        # Baseline memory
        profiler.take_snapshot("Baseline")
        
        # Test with different dataset sizes
        sizes = [1000, 10000, 50000, 100000, 200000]
        views = []
        
        for size in sizes:
            # Force garbage collection before each measurement
            gc.collect()
            
            # Create view with data
            view, data = data_view_with_data(size)
            profiler.take_snapshot(f"After loading {size} rows")
            
            # Keep reference to prevent garbage collection
            views.append(view)
        
        # Get memory report
        report = profiler.get_report()
        print(report)
        
        # Check memory scaling is reasonable
        # Extract memory values
        memory_values = [snapshot[1] for snapshot in profiler.snapshots[1:]]
        
        # Check that memory doesn't scale super-linearly
        # A simple check: doubling the data should less than triple the memory
        # This may need adjustment based on actual implementation
        assert memory_values[3] < memory_values[1] * 3, "Memory usage scales poorly with data size"
    
    def test_memory_leaks(self, data_view_with_data, profile_memory, qtbot):
        """Test for memory leaks during operations."""
        # Create memory profiler
        profiler = profile_memory()
        
        # Create view with medium dataset
        view, data = data_view_with_data(20000)
        view.show()
        qtbot.wait(200)  # Wait for initial load
        
        # Baseline memory
        profiler.take_snapshot("Initial view created")
        
        # Perform a series of operations that might cause leaks
        # 1. Multiple data updates
        for i in range(5):
            # Create new data with same size
            new_data = pd.DataFrame({
                'Column_0': [f"Player_{j}" for j in range(20000)],
                'Column_1': ["Gold", "Silver", "Bronze"] * (20000 // 3 + 1),
                'Column_2': np.random.randint(1, 1000, 20000),
                'Column_3': [f"2023-{(j % 12) + 1:02d}-{(j % 28) + 1:02d}" for j in range(20000)],
                'Column_4': [j % 2 == 0 for j in range(20000)]
            })
            
            view.model().sourceModel().update_data(new_data)
            qtbot.wait(100)
            
            # Force garbage collection
            gc.collect()
            profiler.take_snapshot(f"After data update {i+1}")
        
        # 2. Selections and scrolling
        for i in range(5):
            # Select different rows
            row = i * 1000
            view.setCurrentIndex(view.model().index(row, 0))
            
            # Scroll to position
            view.scrollTo(view.model().index(row + 500, 0))
            qtbot.wait(50)
            
            # Force garbage collection
            gc.collect()
            profiler.take_snapshot(f"After selection/scroll {i+1}")
        
        # 3. Clean up
        view.hide()
        view.deleteLater()
        qtbot.wait(100)
        gc.collect()
        profiler.take_snapshot("After view cleanup")
        
        # Get memory report
        report = profiler.get_report()
        print(report)
        
        # Check for memory leaks
        # The final memory should be close to initial memory
        initial_memory = profiler.snapshots[0][1]
        final_memory = profiler.snapshots[-1][1]
        
        # Allow some overhead (adjust based on expected behavior)
        max_allowed_leak = 10  # MB
        assert final_memory - initial_memory < max_allowed_leak, f"Memory leak detected: {final_memory - initial_memory:.2f} MB"
```

## Optimization Strategies

Based on performance testing results, the following optimization strategies will be implemented:

### Data Management Optimizations

1. **Lazy Loading**: Load only visible data, deferring loading of off-screen data
2. **Data Virtualization**: Maintain only visible rows in memory
3. **Chunked Updates**: Process large updates in smaller chunks
4. **Caching**: Cache calculated values and rendered cells

### Rendering Optimizations

1. **Custom Delegates**: Optimize cell rendering with custom delegates
2. **Viewport Clipping**: Only render cells within the visible viewport
3. **Reduced Repaints**: Minimize unnecessary repaints
4. **Deferred Validation**: Apply validation visuals only for visible cells

### Interaction Optimizations

1. **Throttled Updates**: Limit update frequency during scrolling
2. **Asynchronous Processing**: Move heavy operations off the UI thread
3. **Selective Updates**: Update only changed cells rather than the entire view
4. **Event Batching**: Batch UI update events to reduce overhead

## Performance Monitoring and Reporting

### Continuous Performance Testing

Performance tests will be integrated into the development workflow:

1. **Manual Benchmarking**: Run performance tests when making significant changes
2. **Automated Testing**: Include key performance tests in CI/CD pipeline
3. **Performance Regression Testing**: Compare against baseline metrics

### Performance Reports

Performance test results will be documented in reports including:

1. **Performance Metrics**: Raw performance data
2. **Trend Analysis**: Performance changes over time
3. **Bottleneck Identification**: Areas needing optimization
4. **Optimization Recommendations**: Suggested improvements

## Conclusion

This performance testing strategy provides a comprehensive approach to ensuring the refactored DataView component meets performance requirements. By establishing baseline metrics, continuously testing throughout development, and implementing targeted optimizations, we can deliver a DataView that handles large datasets efficiently while maintaining a responsive user interface.

The strategy focuses on the most critical performance aspects from a user perspective, ensuring that performance optimizations directly improve the user experience. Regular benchmarking and performance monitoring will help identify and address performance issues early in the development process. 