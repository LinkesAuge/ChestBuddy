"""
Test for MainWindow initialization with ChartTab.
"""

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QTabWidget

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.ui.main_window import MainWindow


@pytest.fixture
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def data_model():
    """Create a data model for testing."""
    return ChestDataModel()


@pytest.fixture
def csv_service(data_model):
    """Create a CSV service for testing."""
    return CSVService(data_model)


@pytest.fixture
def chart_service(data_model):
    """Create a chart service for testing."""
    return ChartService(data_model)


def test_main_window_with_chart_tab(qapp, data_model, csv_service, chart_service):
    """Test that MainWindow initializes correctly with a ChartTab when chart_service is provided."""
    print("Starting test_main_window_with_chart_tab")
    
    # Create mock services for validation and correction
    validation_service = MagicMock()
    correction_service = MagicMock()
    
    # Create the main window
    print("Creating main window")
    main_window = MainWindow(
        data_model,
        csv_service,
        validation_service,
        correction_service,
        chart_service
    )
    print("Main window created")
    
    # Find the tab widget
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break
    
    print(f"Tab widget found: {tab_widget is not None}")
    assert tab_widget is not None, "Tab widget not found in MainWindow"
    
    # Check if there's a tab labeled "Charts"
    chart_tab_index = -1
    for i in range(tab_widget.count()):
        print(f"Tab {i}: {tab_widget.tabText(i)}")
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break
    
    print(f"Chart tab index: {chart_tab_index}")
    assert chart_tab_index >= 0, "Chart tab not found in TabWidget"
    print("Test completed successfully")
