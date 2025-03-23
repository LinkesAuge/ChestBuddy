"""
UI State Management System Usage Examples.

This module provides examples of how to use the UI state management system
in different scenarios.
"""

import logging
import time
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QTableView,
    QProgressDialog,
)

from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    UIElementGroups,
    UIOperations,
    BlockableElementMixin,
)

# Set up logger
logger = logging.getLogger(__name__)


# Example 1: Basic usage with OperationContext
def example_basic_operation_context():
    """
    Basic example of using OperationContext to block UI elements.

    This example shows how to:
    1. Get the UIStateManager instance
    2. Register UI elements
    3. Use OperationContext to block UI elements during operations
    """
    # Get the singleton instance
    ui_state_manager = UIStateManager()

    # Create some UI elements
    main_window = QMainWindow()
    button = QPushButton("Click Me")
    table_view = QTableView()

    # Register elements with the manager
    ui_state_manager.register_element(button)
    ui_state_manager.register_element(table_view)

    # Register groups
    ui_state_manager.register_group(
        UIElementGroups.MAIN_WINDOW,
        elements=[main_window],
    )
    ui_state_manager.register_group(
        UIElementGroups.DATA_VIEW,
        elements=[table_view],
    )

    # Use OperationContext to block UI during an operation
    def import_data():
        # Block the main window during import
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.MAIN_WINDOW]
        ):
            logger.info("Importing data...")
            # Simulate long operation
            time.sleep(2)
            logger.info("Import complete!")

        # UI is automatically unblocked when the context exits

    # Connect button click to import function
    button.clicked.connect(import_data)


# Example 2: Custom blockable widget
class MyBlockableButton(QPushButton, BlockableElementMixin):
    """
    Example of a custom button that implements BlockableElementMixin.

    This shows how to create a UI element that can be blocked/unblocked
    with custom blocking behavior.
    """

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        """Initialize the button."""
        QPushButton.__init__(self, text, parent)
        BlockableElementMixin.__init__(self)

        # Styling for blocked state
        self._normal_style = self.styleSheet()
        self._blocked_style = "background-color: #f0f0f0; color: #a0a0a0;"

    def _apply_block(self) -> None:
        """
        Apply custom blocking behavior.

        Overrides the default implementation to apply custom styling.
        """
        # Save current enabled state
        self._original_enabled_state = self.isEnabled()

        # Apply blocked style
        self.setStyleSheet(self._blocked_style)

        # Disable the button
        self.setEnabled(False)

        logger.debug(f"Custom block applied to {self.text()}")

    def _apply_unblock(self) -> None:
        """
        Apply custom unblocking behavior.

        Overrides the default implementation to restore original styling.
        """
        # Restore original style
        self.setStyleSheet(self._normal_style)

        # Restore original enabled state
        self.setEnabled(self._original_enabled_state)

        logger.debug(f"Custom unblock applied to {self.text()}")


# Example 3: Integration with MainWindow
class ExampleMainWindow(QMainWindow):
    """
    Example of integrating UIStateManager with a MainWindow.

    This shows how to:
    1. Initialize UIStateManager in a main window
    2. Register elements and groups
    3. Use OperationContext for operations
    4. Connect to state change signals
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        # Set up UI
        self.setWindowTitle("UI State Manager Example")
        self.resize(800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Add standard button
        self.standard_button = QPushButton("Standard Button")
        layout.addWidget(self.standard_button)

        # Add blockable button
        self.blockable_button = MyBlockableButton("Blockable Button")
        layout.addWidget(self.blockable_button)

        # Add table view
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Initialize UI state manager
        self.ui_state_manager = UIStateManager()

        # Register elements and groups
        self._init_ui_state()

        # Connect signals
        self._connect_signals()

    def _init_ui_state(self) -> None:
        """Initialize UI state management."""
        # Register individual elements
        self.ui_state_manager.register_element(self.standard_button)
        self.ui_state_manager.register_element(self.blockable_button)
        self.ui_state_manager.register_element(self.table_view)

        # Register groups
        self.ui_state_manager.register_group(
            UIElementGroups.MAIN_WINDOW,
            elements=[self],
        )
        self.ui_state_manager.register_group(
            UIElementGroups.DATA_VIEW,
            elements=[self.table_view],
        )

        # Register the blockable button with itself
        self.blockable_button.register_with_manager(self.ui_state_manager)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        # Connect standard button to import function
        self.standard_button.clicked.connect(self.start_import)

        # Connect blockable button to export function
        self.blockable_button.clicked.connect(self.start_export)

        # Connect UI state signals
        self.ui_state_manager.signals.element_blocked.connect(self._on_element_blocked)
        self.ui_state_manager.signals.element_unblocked.connect(self._on_element_unblocked)
        self.ui_state_manager.signals.operation_started.connect(self._on_operation_started)
        self.ui_state_manager.signals.operation_ended.connect(self._on_operation_ended)

    def start_import(self) -> None:
        """Start an import operation."""
        # Use a QTimer to run the operation after button click is processed
        QTimer.singleShot(0, self._run_import)

    def _run_import(self) -> None:
        """Run the import operation."""
        try:
            with OperationContext(
                self.ui_state_manager,
                UIOperations.IMPORT,
                groups=[UIElementGroups.MAIN_WINDOW],
                operation_name="Data Import",
            ):
                # Show a progress dialog
                progress = QProgressDialog("Importing data...", "Cancel", 0, 100, self)
                progress.setWindowTitle("Import Progress")
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()

                # Simulate long operation with progress updates
                for i in range(101):
                    # Check for cancel
                    if progress.wasCanceled():
                        break

                    # Update progress
                    progress.setValue(i)

                    # Process events to keep UI responsive
                    QApplication.processEvents()

                    # Simulate work
                    time.sleep(0.05)

                # Close progress dialog
                progress.close()

                logger.info("Import complete!")
        except Exception as e:
            logger.error(f"Import failed: {e}")

    def start_export(self) -> None:
        """Start an export operation."""
        # Use a QTimer to run the operation after button click is processed
        QTimer.singleShot(0, self._run_export)

    def _run_export(self) -> None:
        """Run the export operation."""
        try:
            with OperationContext(
                self.ui_state_manager,
                UIOperations.EXPORT,
                groups=[UIElementGroups.DATA_VIEW],
                operation_name="Data Export",
            ):
                # Show a progress dialog
                progress = QProgressDialog("Exporting data...", "Cancel", 0, 100, self)
                progress.setWindowTitle("Export Progress")
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()

                # Simulate long operation with progress updates
                for i in range(101):
                    # Check for cancel
                    if progress.wasCanceled():
                        break

                    # Update progress
                    progress.setValue(i)

                    # Process events to keep UI responsive
                    QApplication.processEvents()

                    # Simulate work
                    time.sleep(0.03)

                # Close progress dialog
                progress.close()

                logger.info("Export complete!")
        except Exception as e:
            logger.error(f"Export failed: {e}")

    @Slot(object, object)
    def _on_element_blocked(self, element, operation) -> None:
        """
        Handle element blocked signal.

        Args:
            element: The element that was blocked.
            operation: The operation blocking the element.
        """
        # Only update for UI elements we care about
        if element == self.blockable_button or element == self.standard_button:
            logger.debug(f"Element {element} blocked by {operation}")
            self.status_label.setText(f"Blocked: {operation}")

    @Slot(object, object)
    def _on_element_unblocked(self, element, operation) -> None:
        """
        Handle element unblocked signal.

        Args:
            element: The element that was unblocked.
            operation: The operation that unblocked the element.
        """
        # Only update for UI elements we care about
        if element == self.blockable_button or element == self.standard_button:
            logger.debug(f"Element {element} unblocked from {operation}")
            self.status_label.setText("Ready")

    @Slot(object, object)
    def _on_operation_started(self, operation, affected_elements) -> None:
        """
        Handle operation started signal.

        Args:
            operation: The operation that started.
            affected_elements: The elements affected by the operation.
        """
        logger.debug(f"Operation {operation} started")

    @Slot(object, object)
    def _on_operation_ended(self, operation, affected_elements) -> None:
        """
        Handle operation ended signal.

        Args:
            operation: The operation that ended.
            affected_elements: The elements affected by the operation.
        """
        logger.debug(f"Operation {operation} ended")


# Example 4: Manual Operation Context
def example_manual_operation_context():
    """
    Example of using ManualOperationContext for more complex operations.

    This example shows how to:
    1. Create a manual operation context
    2. Start and end the operation manually
    3. Handle errors properly
    """
    from chestbuddy.utils.ui_state.context import ManualOperationContext

    # Get the singleton instance
    ui_state_manager = UIStateManager()

    # Create a manual operation context
    operation_context = ManualOperationContext(
        ui_state_manager,
        UIOperations.PROCESSING,
        groups=[UIElementGroups.DATA_VIEW],
        operation_name="Data Processing",
    )

    try:
        # Start the operation (block UI)
        operation_context.start()

        logger.info("Processing data...")
        # Simulate long operation
        time.sleep(2)
        logger.info("Processing complete!")
    finally:
        # End the operation (unblock UI), even if an error occurred
        operation_context.end()


if __name__ == "__main__":
    import sys

    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Create application
    app = QApplication(sys.argv)

    # Create main window
    window = ExampleMainWindow()
    window.show()

    # Run application
    sys.exit(app.exec_())
