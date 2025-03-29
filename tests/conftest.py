"""
Test fixtures for the ChestBuddy application.

This module contains common fixtures used across different tests.
"""

import pytest
from typing import Any, Callable, List, Optional
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton

from tests.data import TestDataFactory
from tests.utils.helpers import temp_directory, temp_file, wait_until


@pytest.fixture(scope="session")
def sample_data_small():
    """Return a small dataset for testing."""
    return TestDataFactory.create_small_data()


@pytest.fixture(scope="session")
def sample_data_with_errors():
    """Return a dataset with errors for testing."""
    return TestDataFactory.create_small_data(with_errors=True)


@pytest.fixture(scope="session")
def sample_data_specific_errors():
    """Return a dataset with specific errors for testing."""
    return TestDataFactory.create_data_with_specific_errors({"player": 3, "chest": 2, "source": 2})


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with temp_directory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    content = """
    [General]
    DataPath=/path/to/data
    LogLevel=INFO
    
    [Display]
    Theme=default
    FontSize=12
    
    [Advanced]
    CacheSize=100
    DebugMode=false
    """
    with temp_file(content, suffix=".ini") as config_file:
        yield config_file


class EnhancedQtBot:
    """Enhanced QtBot with additional helper methods for UI testing."""

    def __init__(self, qtbot):
        """Initialize with a qtbot instance."""
        self.qtbot = qtbot

    def add_widget(self, widget):
        """Add a widget to the qtbot."""
        self.qtbot.addWidget(widget)
        return widget

    def click_button(self, button):
        """Click a button."""
        self.qtbot.mouseClick(button, Qt.LeftButton)

    def double_click(self, widget, pos=None):
        """Double-click a widget at the given position."""
        if pos is None:
            # Click center of widget
            pos = widget.rect().center()
        self.qtbot.mouseDClick(widget, Qt.LeftButton, pos=pos)

    def enter_text(self, widget, text):
        """Enter text into a widget."""
        widget.setFocus()
        self.qtbot.keyClicks(widget, text)

    def wait_for(self, condition_func, timeout=1000):
        """Wait for a condition to be met."""
        return wait_until(condition_func, timeout=timeout)

    def wait_for_signal(self, signal, timeout=1000):
        """Wait for a signal to be emitted."""
        with self.qtbot.waitSignal(signal, timeout=timeout):
            pass

    def wait_for_window(self, window_class, timeout=1000):
        """Wait for a window of a specific class to appear."""

        def check_window():
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, window_class) and widget.isVisible():
                    return True
            return False

        return self.wait_for(check_window, timeout=timeout)


@pytest.fixture
def enhanced_qtbot(qtbot):
    """Provide an enhanced qtbot fixture with additional helpers."""
    return EnhancedQtBot(qtbot)


@pytest.fixture
def main_window():
    """Create a QMainWindow for testing."""
    window = QMainWindow()
    window.setWindowTitle("Test Window")
    window.resize(800, 600)
    yield window
    window.close()
