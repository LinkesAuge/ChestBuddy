"""
test_mock_main_window.py

Description: Implementation of a mock MainWindow for testing UI state management.
This mock simulates the behavior of a real MainWindow, including views, services,
and signal connections.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import UI state management components
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
)


class MockBackgroundWorker(QObject):
    """Mock background worker for testing."""

    started = Signal()
    progress = Signal(int, str)
    completed = Signal(bool, str)
    cancelled = Signal()
    success = Signal(object)
    error = Signal(str)


class MockMainWindow(QMainWindow):
    """Mock implementation of the MainWindow for testing."""

    # Define signals
    import_started = Signal()
    import_completed = Signal(bool, str)
    import_success = Signal(str)
    import_error = Signal(str)
    export_started = Signal()
    export_completed = Signal(bool, str)

    def __init__(self, services=None, parent=None):
        super().__init__(parent)

        # Create UI State Manager
        self.ui_state_manager = UIStateManager()

        # Set up services
        self.services = services or {}

        # Set up views
        self._views = {}
        self._setup_views()

        # Register with UI state manager
        self.register_with_manager(self.ui_state_manager)

        # Set up connections
        self._setup_connections()

    def _setup_views(self):
        """Set up views for testing."""
        # Create mock views
        view_names = ["data", "validation", "correction", "settings", "dashboard"]

        for view_name in view_names:
            # Create a simple QWidget
            view = QWidget(self)

            # Make it blockable
            view = self.make_blockable(view, view_name)

            # Register with UI state manager
            view.register_with_manager(self.ui_state_manager)

            # Add to groups based on view name
            if view_name == "data":
                self.ui_state_manager.add_element_to_group(view, UIElementGroups.DATA_VIEW)
            elif view_name == "validation":
                self.ui_state_manager.add_element_to_group(view, UIElementGroups.VALIDATION)
            elif view_name == "correction":
                self.ui_state_manager.add_element_to_group(view, UIElementGroups.CORRECTION)
            elif view_name == "settings":
                # Use DIALOG group instead of non-existent SETTINGS
                self.ui_state_manager.add_element_to_group(view, UIElementGroups.DIALOG)
            elif view_name == "dashboard":
                self.ui_state_manager.add_element_to_group(view, UIElementGroups.DASHBOARD)

            # Store the view
            self._views[view_name] = view

    def _setup_connections(self):
        """Set up signal connections."""
        # Connect import signals
        self.import_started.connect(self._on_import_started)
        self.import_completed.connect(self._on_import_completed)
        self.import_success.connect(self._on_import_success)
        self.import_error.connect(self._on_import_error)

        # Connect export signals
        self.export_started.connect(self._on_export_started)
        self.export_completed.connect(self._on_export_completed)

        # Connect data manager signals if available
        if "data_manager" in self.services:
            data_manager = self.services["data_manager"]

            # Check if signals exist before connecting
            if hasattr(data_manager, "load_started"):
                data_manager.load_started.connect(self._on_load_started)

            if hasattr(data_manager, "load_progress"):
                data_manager.load_progress.connect(self._on_load_progress)

            if hasattr(data_manager, "load_finished"):
                data_manager.load_finished.connect(self._on_load_finished)

            if hasattr(data_manager, "load_success"):
                data_manager.load_success.connect(self._on_load_success)

            if hasattr(data_manager, "load_error"):
                data_manager.load_error.connect(self._on_load_error)

    def make_blockable(self, widget, name):
        """Convert a widget to a blockable element."""
        # Create a new class that inherits from the widget's class and BlockableElementMixin
        blockable_class = type(
            f"Blockable{widget.__class__.__name__}",
            (widget.__class__, BlockableElementMixin),
            {"__init__": lambda self, *args, **kwargs: self._init(*args, **kwargs)},
        )

        # Define _init method for the new class
        def _init(self, *args, **kwargs):
            # Call parent class constructors
            super(self.__class__, self).__init__(*args)
            BlockableElementMixin.__init__(self)
            self.setObjectName(name)

        # Add _init to the class
        blockable_class._init = _init

        # Create an instance of the new class
        blockable_widget = blockable_class(widget.parent())

        # Copy properties from the original widget
        blockable_widget.setGeometry(widget.geometry())
        blockable_widget.setVisible(widget.isVisible())
        blockable_widget.setEnabled(widget.isEnabled())

        # Delete the original widget
        widget.deleteLater()

        return blockable_widget

    def register_with_manager(self, manager):
        """Register this window with the UI state manager."""
        # Create our own implementation of BlockableElementMixin for MainWindow
        # since we can't directly inherit from it
        self._is_blocked = False
        self._block_operations = {}

        # Register with the manager
        manager.register_element(self)

        # Add to main window group
        manager.add_element_to_group(self, UIElementGroups.MAIN_WINDOW)

    def is_blocked(self):
        """Return whether this element is blocked."""
        return self._is_blocked

    def block(self, operation):
        """Block this element for the given operation."""
        if operation not in self._block_operations:
            self._block_operations[operation] = 0

        self._block_operations[operation] += 1

        if not self._is_blocked:
            self._is_blocked = True
            self._apply_block()

    def unblock(self, operation):
        """Unblock this element for the given operation."""
        if operation in self._block_operations:
            self._block_operations[operation] -= 1

            if self._block_operations[operation] <= 0:
                del self._block_operations[operation]

        if len(self._block_operations) == 0 and self._is_blocked:
            self._is_blocked = False
            self._apply_unblock()

    def _apply_block(self):
        """Apply blocking to this element."""
        self.setEnabled(False)

    def _apply_unblock(self):
        """Apply unblocking to this element."""
        self.setEnabled(True)

    def get_view(self, name):
        """Get a view by name."""
        return self._views.get(name)

    def get_views(self):
        """Get all views."""
        return self._views

    def import_file(self, file_path):
        """Import a file."""
        # Use an operation context to manage UI state
        with OperationContext(self.ui_state_manager, UIOperations.IMPORT, [self]):
            # Emit started signal
            self.import_started.emit()

            # Check if data manager is available
            if "data_manager" in self.services:
                # Use data manager to load file
                self.services["data_manager"].load_file(file_path)
            else:
                # Simulate loading
                self.import_completed.emit(True, f"Imported {file_path}")
                self.import_success.emit(str(file_path))

    def export_file(self, file_path):
        """Export to a file."""
        # Use an operation context to manage UI state
        with OperationContext(self.ui_state_manager, UIOperations.EXPORT, [self]):
            # Emit started signal
            self.export_started.emit()

            # Simulate export
            # ... export logic would go here ...

            # Emit completed signal
            self.export_completed.emit(True, f"Exported to {file_path}")

    def _on_import_started(self):
        """Handle import started."""
        print("Import started")

    def _on_import_completed(self, success, message):
        """Handle import completed."""
        print(f"Import completed: {success}, {message}")

    def _on_import_success(self, file_path):
        """Handle import success."""
        print(f"Import success: {file_path}")

    def _on_import_error(self, error):
        """Handle import error."""
        print(f"Import error: {error}")

    def _on_export_started(self):
        """Handle export started."""
        print("Export started")

    def _on_export_completed(self, success, message):
        """Handle export completed."""
        print(f"Export completed: {success}, {message}")

    def _on_load_started(self):
        """Handle load started signal from data manager."""
        print("Load started")

    def _on_load_progress(self, progress, message):
        """Handle load progress signal from data manager."""
        print(f"Load progress: {progress}%, {message}")

    def _on_load_finished(self, success, message):
        """Handle load finished signal from data manager."""
        print(f"Load finished: {success}, {message}")

        # Emit our own signals
        self.import_completed.emit(success, message)

    def _on_load_success(self, file_path):
        """Handle load success signal from data manager."""
        print(f"Load success: {file_path}")

        # Emit our own signal
        self.import_success.emit(file_path)

    def _on_load_error(self, error):
        """Handle load error signal from data manager."""
        print(f"Load error: {error}")

        # Emit our own signal
        self.import_error.emit(error)


# Add test functions for direct testing of the mock
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
def mock_services():
    """Create standard mock services."""
    # Create a simple mock data model
    data_model = MagicMock()
    data_model.set_data = MagicMock()
    data_model.is_data_loaded = MagicMock(return_value=False)

    # Create mock CSV service
    csv_service = MagicMock()

    # Create mock data manager with background worker
    data_manager = MagicMock()
    data_manager._worker = MockBackgroundWorker()

    # Add the necessary signals
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
def mock_main_window(qtbot, mock_services):
    """Create a mock main window."""
    main_window = MockMainWindow(services=mock_services)
    qtbot.addWidget(main_window)
    return main_window


class TestMockMainWindow:
    """Tests for the MockMainWindow class."""

    def test_initialization(self, mock_main_window):
        """Test that the mock main window initializes correctly."""
        # Check that views were created
        assert mock_main_window.get_view("data") is not None
        assert mock_main_window.get_view("validation") is not None
        assert mock_main_window.get_view("correction") is not None
        assert mock_main_window.get_view("settings") is not None
        assert mock_main_window.get_view("dashboard") is not None

        # Check that UI state manager was created
        assert mock_main_window.ui_state_manager is not None

        # Check that the main window is registered with the UI state manager
        assert mock_main_window in mock_main_window.ui_state_manager._elements

    def test_view_groups(self, mock_main_window):
        """Test that views are added to the correct groups."""
        # Get UI state manager
        manager = mock_main_window.ui_state_manager

        # Check main window group
        assert mock_main_window in manager._element_groups[UIElementGroups.MAIN_WINDOW]

        # Check data view group
        assert (
            mock_main_window.get_view("data") in manager._element_groups[UIElementGroups.DATA_VIEW]
        )

        # Check validation group
        assert (
            mock_main_window.get_view("validation")
            in manager._element_groups[UIElementGroups.VALIDATION]
        )

        # Check correction group
        assert (
            mock_main_window.get_view("correction")
            in manager._element_groups[UIElementGroups.CORRECTION]
        )

        # Check settings group
        assert (
            mock_main_window.get_view("settings") in manager._element_groups[UIElementGroups.DIALOG]
        )

        # Check dashboard group
        assert (
            mock_main_window.get_view("dashboard")
            in manager._element_groups[UIElementGroups.DASHBOARD]
        )

    def test_blocking_unblocking(self, mock_main_window):
        """Test that the main window can be blocked and unblocked."""
        # Initially enabled
        assert mock_main_window.isEnabled()

        # Block
        mock_main_window.block(UIOperations.IMPORT)
        assert not mock_main_window.isEnabled()

        # Unblock
        mock_main_window.unblock(UIOperations.IMPORT)
        assert mock_main_window.isEnabled()

    def test_operation_context(self, mock_main_window):
        """Test the operation context with the mock main window."""
        # Get UI state manager
        manager = mock_main_window.ui_state_manager

        # Get data view
        data_view = mock_main_window.get_view("data")

        # Initially enabled
        assert mock_main_window.isEnabled()
        assert data_view.isEnabled()

        # Start an operation
        with OperationContext(manager, UIOperations.IMPORT, [mock_main_window, data_view]):
            # Should be disabled during operation
            assert not mock_main_window.isEnabled()
            assert not data_view.isEnabled()

        # Should be enabled after operation
        assert mock_main_window.isEnabled()
        assert data_view.isEnabled()

        # Make sure no operations are still active
        assert len(manager._operations) == 0
