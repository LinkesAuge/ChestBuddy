"""
test_updatable.py

Description: Tests for the IUpdatable interface and UpdatableComponent base class.
"""

import time
import pytest
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from chestbuddy.ui.interfaces import IUpdatable, UpdatableComponent


# Mock class for testing
class MockUpdatableComponent(UpdatableComponent):
    """Mock implementation of UpdatableComponent for testing."""

    updated = Signal(object)
    reset_called = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.update_count = 0
        self.refresh_count = 0
        self.populate_count = 0
        self.reset_count = 0
        self.last_data = None

    def _do_update(self, data: Optional[Any] = None) -> None:
        self.update_count += 1
        self.last_data = data
        self.updated.emit(data)

    def _do_refresh(self) -> None:
        self.refresh_count += 1
        super()._do_refresh()

    def _do_populate(self, data: Optional[Any] = None) -> None:
        self.populate_count += 1
        self.last_data = data
        super()._do_populate(data)

    def _do_reset(self) -> None:
        self.reset_count += 1
        self.last_data = None
        self.reset_called.emit()


# QWidget-based mock class for testing
class MockUpdatableWidget(QWidget):
    """
    Mock implementation of IUpdatable as a QWidget for testing.
    This class implements the IUpdatable interface directly for use in tests
    where a QWidget-based updatable component is required.
    """

    update_requested = Signal()
    update_completed = Signal()
    updated = Signal(object)
    reset_called = Signal()

    def __init__(self, name: str, parent: Optional[QWidget] = None):
        """Initialize the mock widget.

        Args:
            name: Identifier for the component
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.name = name
        self.update_count = 0
        self.refresh_count = 0
        self.populate_count = 0
        self.reset_count = 0
        self.last_data = None
        self._update_state = {
            "last_update_time": 0.0,
            "needs_update": True,
            "update_pending": False,
            "data_hash": None,
            "initial_population": False,
        }

    def refresh(self) -> None:
        """Refresh the component state."""
        self.refresh_count += 1
        self._update_state["needs_update"] = True
        self.update_requested.emit()
        self._update_state["last_update_time"] = time.time()
        self.update_completed.emit()

    def update(self, data: Optional[Any] = None) -> None:
        """Update the component with the given parameters.

        Args:
            data: Optional parameters for the update
        """
        self.update_count += 1
        self.last_data = data
        self._update_state["needs_update"] = False
        self._update_state["last_update_time"] = time.time()
        self.updated.emit(data)
        self.update_completed.emit()

    def populate(self, data: Optional[Any] = None) -> None:
        """Populate the component with data."""
        self.populate_count += 1
        self.last_data = data
        self._update_state["initial_population"] = True
        self._update_state["needs_update"] = False
        self._update_state["last_update_time"] = time.time()
        self.update_completed.emit()

    def needs_update(self) -> bool:
        """Check if the component needs an update.

        Returns:
            True if an update is needed, False otherwise
        """
        return self._update_state["needs_update"]

    def is_populated(self) -> bool:
        """Check if the component has been populated.

        Returns:
            True if the component has been populated, False otherwise
        """
        return self._update_state["initial_population"]

    def reset(self) -> None:
        """Reset the component state."""
        self.reset_count += 1
        self.last_data = None
        self._update_state["initial_population"] = False
        self._update_state["needs_update"] = True
        self._update_state["data_hash"] = None
        self.reset_called.emit()

    def last_update_time(self) -> float:
        """Get the timestamp of the last update.

        Returns:
            float: Timestamp of the last update
        """
        return self._update_state["last_update_time"]


class TestIUpdatable:
    """Tests for the IUpdatable protocol."""

    def test_protocol_compliance(self):
        """Test that a class implementing all IUpdatable methods is recognized."""
        component = MockUpdatableComponent()
        assert isinstance(component, IUpdatable)

    def test_protocol_non_compliance(self):
        """Test that a class not implementing IUpdatable methods is not recognized."""

        class NonUpdatable(QObject):
            pass

        component = NonUpdatable()
        assert not isinstance(component, IUpdatable)

    def test_partial_protocol_compliance(self):
        """Test that a class implementing only some IUpdatable methods is not recognized."""

        class PartialUpdatable(QObject):
            def update(self, data=None):
                pass

            def refresh(self):
                pass

        component = PartialUpdatable()
        assert not isinstance(component, IUpdatable)

    def test_widget_compliance(self):
        """Test that a QWidget implementing IUpdatable methods is recognized."""
        widget = MockUpdatableWidget("test_widget")
        assert isinstance(widget, IUpdatable)
        assert isinstance(widget, QWidget)


class TestUpdatableComponent:
    """Tests for the UpdatableComponent base class."""

    def test_initial_state(self):
        """Test the initial state of a component."""
        component = MockUpdatableComponent()
        assert component.needs_update() is True
        assert component.is_populated() is False
        assert component.last_update_time() == 0.0

    def test_update(self):
        """Test the update method."""
        component = MockUpdatableComponent()
        test_data = {"test": "data"}

        # Initial update
        component.update(test_data)
        assert component.update_count == 1
        assert component.last_data == test_data
        assert component.needs_update() is False
        assert component.last_update_time() > 0.0

        # Second update with same data should not call _do_update
        component._update_state["needs_update"] = False  # Reset needs_update flag
        component.update(test_data)
        assert component.update_count == 1  # Should not increase

        # Update with different data
        component.update({"test": "different"})
        assert component.update_count == 2
        assert component.last_data == {"test": "different"}

    def test_refresh(self):
        """Test the refresh method."""
        component = MockUpdatableComponent()
        component.refresh()
        assert component.refresh_count == 1
        assert component.update_count == 1  # Default implementation calls _do_update
        assert component.last_update_time() > 0.0

    def test_populate(self):
        """Test the populate method."""
        component = MockUpdatableComponent()
        test_data = {"test": "data"}

        component.populate(test_data)
        assert component.populate_count == 1
        assert component.update_count == 1  # Default implementation calls _do_update
        assert component.last_data == test_data
        assert component.is_populated() is True
        assert component.needs_update() is False
        assert component.last_update_time() > 0.0

    def test_reset(self):
        """Test the reset method."""
        component = MockUpdatableComponent()
        component.populate({"test": "data"})
        assert component.is_populated() is True

        component.reset()
        assert component.reset_count == 1
        assert component.is_populated() is False
        assert component.last_data is None

    def test_update_hash(self):
        """Test that update hash prevents unnecessary updates."""
        component = MockUpdatableComponent()

        # Initial update
        component.update({"test": "data"})
        assert component.update_count == 1

        # Store the original hash
        original_hash = component._update_state["data_hash"]
        assert original_hash is not None

        # Set needs_update to False
        component._update_state["needs_update"] = False

        # Update with same data (should use hash comparison)
        component.update({"test": "data"})
        assert component.update_count == 1  # Should not increase

        # Update with different data
        component.update({"test": "different"})
        assert component.update_count == 2  # Should increase
        assert component._update_state["data_hash"] != original_hash

    def test_update_with_dataframe_like_object(self):
        """Test updating with an object that has a to_dict method (like pandas DataFrame)."""
        component = MockUpdatableComponent()

        class DataFrameLike:
            def __init__(self, data):
                self.data = data

            def to_dict(self):
                return self.data

        df1 = DataFrameLike({"col1": [1, 2, 3]})
        df2 = DataFrameLike({"col1": [1, 2, 3]})  # Same data
        df3 = DataFrameLike({"col1": [4, 5, 6]})  # Different data

        # Initial update
        component.update(df1)
        assert component.update_count == 1

        # Set needs_update to False
        component._update_state["needs_update"] = False

        # Update with same data (should use hash comparison)
        component.update(df2)
        assert component.update_count == 1  # Should not increase

        # Update with different data
        component.update(df3)
        assert component.update_count == 2  # Should increase

    def test_signals(self):
        """Test that signals are emitted correctly."""
        component = MockUpdatableComponent()

        # Set up signal tracking
        update_requested_called = False
        update_completed_called = False

        def on_update_requested():
            nonlocal update_requested_called
            update_requested_called = True

        def on_update_completed():
            nonlocal update_completed_called
            update_completed_called = True

        component.update_requested.connect(on_update_requested)
        component.update_completed.connect(on_update_completed)

        # Perform update
        component.update({"test": "data"})

        # Check signals
        assert update_requested_called is True
        assert update_completed_called is True

    def test_hash_calculation_errors(self):
        """Test handling of errors in hash calculation."""
        component = MockUpdatableComponent()

        # Create an object that raises an exception in str()
        class ErrorObject:
            def __str__(self):
                raise ValueError("Test error")

        # Should not raise an exception
        component.update(ErrorObject())
        assert component.update_count == 1

    def test_update_exceptions(self):
        """Test handling of exceptions in _do_update."""

        class ErrorComponent(UpdatableComponent):
            def _do_update(self, data=None):
                raise ValueError("Test error")

        component = ErrorComponent()

        # Should propagate the exception
        with pytest.raises(ValueError):
            component.update({"test": "data"})

        # Should reset the update_pending flag
        assert component._update_state["update_pending"] is False

    def test_is_populated_after_update(self):
        """Test that is_populated remains False after update without populate."""
        component = MockUpdatableComponent()
        component.update({"test": "data"})
        assert component.is_populated() is False

        component.populate({"test": "data"})
        assert component.is_populated() is True
