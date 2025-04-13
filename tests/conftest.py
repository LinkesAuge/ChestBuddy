"""
Test fixtures for the ChestBuddy application.

This module provides common test fixtures for all tests.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import pandas as pd
from typing import List, Optional, Callable, Any
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal, QEvent, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget

from tests.data.test_data_factory import TestDataFactory
from tests.utils.helpers import SignalSpy


@pytest.fixture
def sample_data_small():
    """Return a small sample dataset."""
    return TestDataFactory.create_small_data()


@pytest.fixture
def sample_data_with_errors():
    """Return a small sample dataset with errors."""
    return TestDataFactory.create_small_data(with_errors=True)


@pytest.fixture
def sample_data_specific_errors():
    """Return a dataset with specific error types."""
    return TestDataFactory.create_data_with_specific_errors()


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    fd, path = tempfile.mkstemp(suffix=".ini")
    yield Path(path)
    import os

    os.close(fd)
    os.unlink(path)


@pytest.fixture
def my_custom_qtbot_wrapper(qtbot):
    """
    Enhanced version of qtbot with additional helper methods.

    This fixture provides additional methods for UI testing beyond
    what the standard qtbot provides.
    """

    class EnhancedQtBot:
        def __init__(self, qtbot):
            self.qtbot = qtbot
            self.tracked_objects = []

        def add_widget(self, widget):
            """Add a widget to qtbot and track it for cleanup."""
            self.qtbot.addWidget(widget)
            self.tracked_objects.append(widget)
            return widget

        def click_button(self, button):
            """Click a button and wait for events to process."""
            self.qtbot.mouseClick(button, Qt.LeftButton)
            QApplication.processEvents()

        def add_spy(self, signal):
            """Create a signal spy and track it for cleanup."""
            spy = SignalSpy(signal)
            self.tracked_objects.append(spy)
            return spy

        def cleanup(self):
            """Clean up all tracked objects."""
            for obj in reversed(self.tracked_objects):
                if isinstance(obj, SignalSpy):
                    obj.disconnect()
                elif isinstance(obj, QObject) and not obj.parent():
                    if hasattr(obj, "deleteLater"):
                        obj.deleteLater()
            self.tracked_objects.clear()
            QApplication.processEvents()

    enhanced = EnhancedQtBot(qtbot)

    yield enhanced

    # Clean up after the test
    enhanced.cleanup()


@pytest.fixture
def signal_connections():
    """
    Fixture for tracking and cleaning up signal connections.

    This fixture helps ensure that signals are properly disconnected
    after tests to prevent signal leakage between tests.
    """
    connections = []

    def connect(signal, slot):
        """Connect a signal to a slot and track the connection."""
        connection = signal.connect(slot)
        connections.append((signal, connection))
        return connection

    yield connect

    # Clean up connections
    for signal, connection in connections:
        try:
            QObject.disconnect(connection)
        except RuntimeError:
            pass  # Already disconnected


@pytest.fixture
def main_window():
    """Create a QMainWindow for testing."""
    window = QMainWindow()
    window.resize(800, 600)
    window.setWindowTitle("Test Window")

    yield window

    # Clean up
    window.close()
    window.deleteLater()
    QApplication.processEvents()
