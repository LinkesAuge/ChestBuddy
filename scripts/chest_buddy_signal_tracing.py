#!/usr/bin/env python
"""
ChestBuddy Signal Tracing Demonstration

This script demonstrates how to use the SignalTracer to debug
signal flow in the actual ChestBuddy application context.
"""

import sys
import time
import logging
from pathlib import Path

# Add the project root to the Python path to import the application modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal, Slot
import pandas as pd

# Import key ChestBuddy components
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.controllers import (
    FileOperationsController,
    DataViewController,
    ViewStateController,
    UIStateController,
)
from chestbuddy.utils.signal_tracer import signal_tracer
from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.services import CSVService

# Configure logging for the demo
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo")


class MockDataManager(QObject):
    """Mock DataManager for the demonstration."""

    load_started = Signal()
    load_progress = Signal(str, int, int)
    load_finished = Signal(str)
    load_error = Signal(str)
    save_success = Signal(str)
    save_error = Signal(str)


class MockValidationService(QObject):
    """Mock validation service for the demonstration."""

    validation_started = Signal()
    validation_complete = Signal(dict)
    validation_error = Signal(str)

    def validate_data(self, data):
        """Perform mock validation on data."""
        self.validation_started.emit()
        # Simulate validation processing
        time.sleep(0.05)
        # Return mock validation results
        results = {"valid": True, "errors": 0, "warnings": 0}
        self.validation_complete.emit(results)
        return results


class ExtendedDataViewController(DataViewController):
    """Extended DataViewController with file handling for demo purposes."""

    data_validated = Signal(dict)  # Add the signal explicitly

    def __init__(self, data_model, signal_manager=None):
        """Initialize with data model."""
        super().__init__(data_model, signal_manager)
        # Add validation service for demonstration
        self._validation_service = MockValidationService()

    @Slot(str)
    def on_file_opened(self, file_path: str):
        """Handle file opened signal for demonstration purposes."""
        logger.info(f"DataViewController: Handling file opened: {file_path}")
        # In a real implementation, this would process the file data
        # and update the data model

    def validate_data(self):
        """Validate the current data."""
        logger.info("DataViewController: Validating data...")
        try:
            # Call validation service
            results = self._validation_service.validate_data(self._data_model.data)
            # Emit the validated signal
            self.data_validated.emit(results)
            return results
        except Exception as e:
            logger.error(f"Error in validate_data: {e}")
            self.operation_error.emit(f"Error validating data: {str(e)}")
            return None


class ExtendedViewStateController(ViewStateController):
    """Extended ViewStateController with validation handling for demo purposes."""

    def __init__(self, data_model, signal_manager=None):
        """Initialize with data model."""
        super().__init__(data_model, signal_manager)
        # Add view registry for demonstration
        self._registered_views = {
            "Dashboard": True,
            "Data": True,
            "Validation": True,
            "Charts": True,
        }

    @Slot(dict)
    def on_data_validated(self, validation_results: dict):
        """Handle data validation results for demonstration purposes."""
        logger.info(f"ViewStateController: Handling data validation results: {validation_results}")
        # In a real implementation, this would update UI based on validation results

    def set_active_view(self, view_name: str):
        """Set the active view."""
        # Override to handle demo views
        view_name = view_name.capitalize()  # Ensure consistent naming
        logger.info(f"ViewStateController: Setting active view to {view_name}")

        if view_name in self._registered_views:
            # Simulate view activation
            self.view_changed.emit(view_name)
            logger.info(f"View changed to {view_name}")
        else:
            logger.warning(f"View '{view_name}' not found in registered views")


class MinimalApp(QObject):
    """Minimal application for demonstration purposes."""

    def __init__(self):
        """Initialize the minimal application components."""
        super().__init__()
        try:
            # Create minimal components needed for demonstration
            self.signal_manager = SignalManager(debug_mode=True)

            self.config_manager = ConfigManager("chestbuddy_demo")

            # Create model and services
            self.data_model = ChestDataModel()
            self.csv_service = CSVService()
            self.data_manager = MockDataManager()

            # Create controllers
            self.file_controller = FileOperationsController(
                self.data_manager, self.config_manager, self.signal_manager
            )

            # Create extended DataViewController with file handling for demo
            self.data_controller = ExtendedDataViewController(self.data_model, self.signal_manager)

            # Create extended ViewStateController with data validation handling for demo
            self.view_state_controller = ExtendedViewStateController(
                self.data_model, self.signal_manager
            )

            self.ui_state_controller = UIStateController(self.signal_manager)

            # Connect controllers - the data model is already set in the DataViewController constructor
            self.view_state_controller.set_data_view_controller(self.data_controller)

            # Register signals that would normally be automatically connected
            self._connect_signals()

            logger.info("Minimal application instance created successfully")
        except Exception as e:
            logger.error(f"Error initializing minimal application: {e}")
            raise

    def _connect_signals(self):
        """Connect key signals between components."""
        try:
            # Connect file controller signals to data controller - use file_opened signal
            self.signal_manager.connect(
                self.file_controller, "file_opened", self.data_controller, "on_file_opened"
            )

            # Connect data model signals to controllers
            self.signal_manager.connect(
                self.data_model, "data_changed", self.data_controller, "_on_data_changed"
            )

            # Connect data validation signals - use on_data_validated instead of _on_data_validated
            self.signal_manager.connect(
                self.data_controller,
                "data_validated",
                self.view_state_controller,
                "on_data_validated",
            )

            logger.info(
                f"Connected {self.signal_manager.get_connection_count()} signals between components"
            )
        except Exception as e:
            logger.error(f"Error connecting signals: {e}")
            raise

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up application...")
        # Disconnect signals and release resources
        if hasattr(self, "signal_manager"):
            self.signal_manager.disconnect_all()


def simulate_signal_traces(minimal_app):
    """Simulate signal traces for demonstration purposes using the test methods."""
    logger.info("Simulating signal traces for demonstration...")

    # Get references to key components
    data_model = minimal_app.data_model
    file_controller = minimal_app.file_controller
    data_controller = minimal_app.data_controller
    view_state_controller = minimal_app.view_state_controller

    # Simulate file_opened signal trace
    file_open_id = signal_tracer._test_record_emission(
        file_controller,
        "file_opened",
        data_controller,
        "on_file_opened",
        args=("sample_data.csv",),
        duration_ms=5.2,
    )

    # Simulate data_changed signal trace
    data_changed_id = signal_tracer._test_record_emission(
        data_model,
        "data_changed",
        data_controller,
        "_on_data_changed",
        args=(None,),
        duration_ms=45.7,
    )

    # Simulate validation_complete signal trace
    validation_service = data_controller._validation_service
    validation_complete_id = signal_tracer._test_record_emission(
        validation_service,
        "validation_complete",
        data_controller,
        "_on_validation_complete",
        args=({"valid": True, "errors": 0},),
        duration_ms=12.3,
        parent_id=data_changed_id,  # Make this a child of data_changed
    )

    # Simulate data_validated signal trace
    data_validated_id = signal_tracer._test_record_emission(
        data_controller,
        "data_validated",
        view_state_controller,
        "on_data_validated",
        args=({"valid": True, "errors": 0},),
        duration_ms=8.5,
        parent_id=validation_complete_id,  # Make this a child of validation_complete
    )

    # Simulate view_changed signal trace
    view_changed_id = signal_tracer._test_record_emission(
        view_state_controller, "view_changed", None, None, args=("Data",), duration_ms=3.2
    )

    # Simulate a slow handler
    slow_handler_id = signal_tracer._test_record_emission(
        data_model,
        "data_changed",
        data_controller,
        "_on_data_changed",
        args=(None,),
        duration_ms=120.5,  # This is slow
    )

    logger.info("Simulated signal traces created")
    return True


def main():
    """Main entry point for the SignalTracer demonstration."""
    logger.info("\n=== ChestBuddy Signal Tracing Demonstration ===\n")

    # Create application
    app = QApplication(sys.argv)

    try:
        # Create a minimal application instance
        logger.info("Creating minimal application instance for demonstration...")
        minimal_app = MinimalApp()

        # Get the model and controllers
        data_model = minimal_app.data_model
        file_controller = minimal_app.file_controller
        data_controller = minimal_app.data_controller
        view_state_controller = minimal_app.view_state_controller
        ui_state_controller = minimal_app.ui_state_controller

        # Get the global SignalManager instance
        signal_manager = SignalManager.instance()
        logger.info(f"SignalManager has {signal_manager.get_connection_count()} connections")

        # Set up the SignalTracer
        logger.info("\nSetting up SignalTracer...")

        # Register key signals to track
        logger.info("Registering key signals for detailed tracking...")
        signal_tracer.register_signal(
            data_model, "data_changed", data_controller, "_on_data_changed"
        )
        # Use on_data_validated instead of _on_data_validated
        signal_tracer.register_signal(
            data_controller, "data_validated", view_state_controller, "on_data_validated"
        )
        # Update to use file_opened signal with the correct handler
        signal_tracer.register_signal(
            file_controller, "file_opened", data_controller, "on_file_opened"
        )

        # Set slow threshold for specific signals
        signal_tracer.set_slow_threshold("ChestDataModel.data_changed", 20.0)  # ms
        signal_tracer.set_default_slow_threshold(50.0)  # ms for other signals

        # Start tracing
        logger.info("Starting signal tracing...")
        signal_tracer.start_tracing()
        signal_tracer.clear()  # Clear any previous traces

        # Simulate application interactions
        logger.info("\nSimulating application interactions...")

        # 1. Load sample data
        logger.info("1. Simulating data loading...")
        # Create a small sample dataset as a DataFrame instead of a dictionary
        sample_data = pd.DataFrame(
            {
                "DATE": ["2025-03-01", "2025-03-02", "2025-03-03"],
                "PLAYER": ["Player1", "Player2", "Player3"],
                "SOURCE": ["Location1", "Location2", "Location3"],
                "CHEST": ["Gold", "Silver", "Bronze"],
                "SCORE": [100, 150, 200],
                "CLAN": ["Clan1", "Clan2", "Clan3"],
            }
        )

        # Simulate file loading using file_opened signal
        file_controller.file_opened.emit("sample_data.csv")
        logger.info("  - Emitted file_opened signal")
        time.sleep(0.1)  # Brief pause for the signal to propagate

        # 2. Update data model
        logger.info("2. Updating data model...")
        data_model.update_data(sample_data)
        logger.info("  - Emitted data_changed signal")
        time.sleep(0.1)

        # 3. Validate data
        logger.info("3. Validating data...")
        data_controller.validate_data()
        logger.info("  - Called validate_data method")
        time.sleep(0.1)

        # 4. Change view state
        logger.info("4. Changing view state...")
        view_state_controller.set_active_view("Data")
        logger.info("  - Called set_active_view method")
        time.sleep(0.1)

        # 5. Update UI state
        logger.info("5. Updating UI state...")
        ui_state_controller.update_status_message("Data loaded and validated")
        logger.info("  - Called update_status_message method")
        time.sleep(0.1)

        # 6. Update data again to trigger another round of signals
        logger.info("6. Updating data again...")
        # Add a row to the sample data - create a new row as a DataFrame
        new_row = pd.DataFrame(
            {
                "DATE": ["2025-03-04"],
                "PLAYER": ["Player4"],
                "SOURCE": ["Location4"],
                "CHEST": ["Platinum"],
                "SCORE": [250],
                "CLAN": ["Clan4"],
            }
        )

        # Append the new row to the sample data
        updated_data = pd.concat([sample_data, new_row], ignore_index=True)

        data_model.update_data(updated_data)
        logger.info("  - Emitted data_changed signal again")
        time.sleep(0.1)

        # Add simulated signal traces for the demonstration
        simulate_signal_traces(minimal_app)

        # Stop tracing
        logger.info("\nStopping signal tracing...")
        signal_tracer.stop_tracing()

        # Generate and display report
        logger.info("\nGenerating signal tracing report...\n")
        report = signal_tracer.generate_report()
        logger.info(report)

        # Show benefits of the signal tracing
        logger.info("\n=== Benefits of Signal Tracing ===")
        logger.info("1. Visibility into signal flow between components")
        logger.info("2. Detection of slow signal handlers for performance optimization")
        logger.info("3. Identification of missing connections and disconnections")
        logger.info("4. Simplified debugging of complex signal chains")
        logger.info("5. Statistical insights for app optimization")

        # Report on slow handlers
        slow_handlers = signal_tracer.find_slow_handlers()
        logger.info(f"\nFound {len(slow_handlers)} potentially slow signal handlers")
        for handler, duration in slow_handlers:
            logger.info(f"  - {handler}: {duration:.2f}ms")

        # Clean up resources
        minimal_app.cleanup()
        logger.info("\n=== Demonstration Complete ===")

    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
