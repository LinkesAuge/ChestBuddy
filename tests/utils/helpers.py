"""
Test helper utilities.

This module provides common testing utilities and helpers for all tests.
"""

from typing import Any, Callable, Iterator, List, Optional, Type, TypeVar, Union
from contextlib import contextmanager
from pathlib import Path
import os
import tempfile
import shutil

import pytest
from PySide6.QtCore import QObject, Signal, Qt, QTimer, QCoreApplication, QEvent
from PySide6.QtWidgets import QWidget, QApplication


T = TypeVar("T")


def get_test_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a test resource file.

    Args:
        relative_path (str): Relative path from the test resources directory

    Returns:
        Path: Absolute path to the resource file
    """
    base_dir = Path(__file__).parent.parent / "resources"
    return base_dir / relative_path


@contextmanager
def temp_directory() -> Iterator[Path]:
    """
    Create a temporary directory for tests.

    Yields:
        Path: Path to the temporary directory

    Example:
        with temp_directory() as tmp_dir:
            # Use temporary directory
            my_file = tmp_dir / "test.txt"
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@contextmanager
def temp_file(content: Optional[str] = None, suffix: str = ".txt") -> Iterator[Path]:
    """
    Create a temporary file for tests.

    Args:
        content (Optional[str]): Content to write to the file
        suffix (str): File suffix/extension

    Yields:
        Path: Path to the temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        if content is not None:
            with open(fd, "w") as f:
                f.write(content)
        yield Path(path)
    finally:
        os.close(fd)
        os.unlink(path)


def wait_until(condition_func: Callable[[], bool], timeout: int = 1000, interval: int = 50) -> bool:
    """
    Wait until a condition is met or timeout occurs.

    Args:
        condition_func (Callable[[], bool]): Function that returns True when condition is met
        timeout (int): Maximum time to wait in milliseconds
        interval (int): Check interval in milliseconds

    Returns:
        bool: True if condition was met, False if timeout occurred
    """
    remaining = timeout
    while remaining > 0:
        if condition_func():
            return True
        QCoreApplication.processEvents()
        QTimer.singleShot(interval, lambda: None)
        QCoreApplication.processEvents()
        remaining -= interval
    return False


def find_widget_by_type(parent: QWidget, widget_type: Type[T]) -> List[T]:
    """
    Find all child widgets of a specific type.

    Args:
        parent (QWidget): Parent widget to search in
        widget_type (Type[T]): Type of widget to find

    Returns:
        List[T]: List of found widgets of the specified type
    """
    return [widget for widget in parent.findChildren(QObject) if isinstance(widget, widget_type)]


def find_widget_by_text(
    parent: QWidget, text: str, widget_type: Optional[Type[T]] = None
) -> List[T]:
    """
    Find all child widgets containing specific text.

    Args:
        parent (QWidget): Parent widget to search in
        text (str): Text to search for
        widget_type (Optional[Type[T]]): Type of widget to find (if specified)

    Returns:
        List[T]: List of found widgets containing the specified text
    """
    widgets = (
        parent.findChildren(QObject) if widget_type is None else parent.findChildren(widget_type)
    )
    result = []

    for widget in widgets:
        if hasattr(widget, "text") and callable(widget.text):
            if text in widget.text():
                result.append(widget)
        elif hasattr(widget, "windowTitle") and callable(widget.windowTitle):
            if text in widget.windowTitle():
                result.append(widget)

    return result


class EventRecorder(QObject):
    """
    Records Qt events for testing event handling.

    Attributes:
        events (List[QEvent.Type]): List of recorded event types
    """

    def __init__(
        self, target: QObject, event_types: List[QEvent.Type], parent: Optional[QObject] = None
    ):
        """
        Initialize the event recorder.

        Args:
            target (QObject): Target object to monitor events for
            event_types (List[QEvent.Type]): Types of events to record
            parent (Optional[QObject]): Parent object
        """
        super().__init__(parent)
        self.target = target
        self.event_types = event_types
        self.events = []
        self.target.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter events from the target object.

        Args:
            obj (QObject): Object that sent the event
            event (QEvent): Event that was sent

        Returns:
            bool: True if event was filtered, False otherwise
        """
        if obj is self.target and event.type() in self.event_types:
            self.events.append(event.type())
        return super().eventFilter(obj, event)

    def clear(self) -> None:
        """Clear the event history."""
        self.events.clear()


class SignalSpy(QObject):
    """
    Spy on Qt signals for testing.

    Attributes:
        signal_name (str): Name of the signal
        emitted (List[List[Any]]): List of signal emissions with arguments
        count (int): Number of times the signal was emitted
    """

    def __init__(self, signal: Signal, parent: Optional[QObject] = None):
        """
        Initialize the signal spy.

        Args:
            signal (Signal): Signal to spy on
            parent (Optional[QObject]): Parent object
        """
        super().__init__(parent)
        self.signal_name = signal.signal
        self.emitted = []
        self.count = 0

        signal.connect(self._slot)

    def _slot(self, *args: Any) -> None:
        """
        Slot called when the signal is emitted.

        Args:
            *args: Signal arguments
        """
        self.emitted.append(list(args))
        self.count += 1

    def wait(self, timeout: int = 1000) -> bool:
        """
        Wait for the signal to be emitted.

        Args:
            timeout (int): Maximum time to wait in milliseconds

        Returns:
            bool: True if signal was emitted, False if timeout occurred
        """
        initial_count = self.count
        return wait_until(lambda: self.count > initial_count, timeout)

    def clear(self) -> None:
        """Clear the emission history."""
        self.emitted.clear()
        self.count = 0
