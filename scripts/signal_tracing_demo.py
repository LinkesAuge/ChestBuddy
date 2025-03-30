#!/usr/bin/env python
"""
Demo script for the SignalTracer utility.

This script demonstrates how to use the SignalTracer to debug
and visualize signal flow in a PySide6 application.
"""

import sys
import time
import random
from pathlib import Path

# Add the project root to the Python path to import the application modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QCoreApplication
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QLabel, QWidget

# Import the SignalTracer utility
from chestbuddy.utils.signal_tracer import signal_tracer
from chestbuddy.utils.signal_manager import SignalManager, SignalPriority


class DataModel(QObject):
    """
    Simple data model that emits signals when the data changes.
    """

    data_changed = Signal(dict)
    data_loaded = Signal(str)
    data_saved = Signal(str)

    def __init__(self):
        super().__init__()
        self._data = {}

    def update_data(self, key, value):
        """Update a value in the data dictionary and emit a signal."""
        self._data[key] = value
        self.data_changed.emit(self._data.copy())

    def load_data(self, filename):
        """Simulate loading data from a file."""
        print(f"Loading data from {filename}...")
        # Simulate some loading time
        time.sleep(0.1)
        self._data = {
            "player": "TestPlayer",
            "score": random.randint(100, 1000),
            "level": random.randint(1, 50),
        }
        self.data_loaded.emit(filename)
        self.data_changed.emit(self._data.copy())

    def save_data(self, filename):
        """Simulate saving data to a file."""
        print(f"Saving data to {filename}...")
        # Simulate some saving time
        time.sleep(0.05)
        self.data_saved.emit(filename)


class DataController(QObject):
    """
    Controller that processes data operations and updates the UI.
    """

    update_ui = Signal(dict)
    status_changed = Signal(str)

    def __init__(self, data_model):
        super().__init__()
        self.data_model = data_model

        # Connect signals from the data model
        self.data_model.data_changed.connect(self.on_data_changed)
        self.data_model.data_loaded.connect(self.on_data_loaded)
        self.data_model.data_saved.connect(self.on_data_saved)

    @Slot(dict)
    def on_data_changed(self, data):
        """Handle data changes and update the UI."""
        print("Data changed:", data)
        self.update_ui.emit(data)

    @Slot(str)
    def on_data_loaded(self, filename):
        """Handle data loaded event."""
        print(f"Data loaded from {filename}")
        self.status_changed.emit(f"Data loaded from {filename}")

    @Slot(str)
    def on_data_saved(self, filename):
        """Handle data saved event."""
        print(f"Data saved to {filename}")
        self.status_changed.emit(f"Data saved to {filename}")

    def update_score(self, score):
        """Update player score in the data model."""
        self.data_model.update_data("score", score)

    def load_data(self):
        """Trigger data loading."""
        self.data_model.load_data("demo_data.json")

    def save_data(self):
        """Trigger data saving."""
        self.data_model.save_data("demo_data.json")


class MainView(QMainWindow):
    """
    Main window for the demo application.
    """

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.signal_manager = SignalManager()

        # Set up the UI
        self.setWindowTitle("SignalTracer Demo")
        self.setMinimumSize(600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Add data display label
        self.data_label = QLabel("No data yet")
        self.data_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f5f5f5;")
        layout.addWidget(self.data_label)

        # Add status label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        # Add buttons
        load_button = QPushButton("Load Data")
        save_button = QPushButton("Save Data")
        update_button = QPushButton("Update Score")
        trace_button = QPushButton("Toggle Tracing")
        report_button = QPushButton("Generate Report")

        # Connect buttons to actions
        load_button.clicked.connect(self.controller.load_data)
        save_button.clicked.connect(self.controller.save_data)
        update_button.clicked.connect(self.on_update_score)
        trace_button.clicked.connect(self.toggle_tracing)
        report_button.clicked.connect(self.generate_report)

        # Add buttons to layout
        layout.addWidget(load_button)
        layout.addWidget(save_button)
        layout.addWidget(update_button)
        layout.addWidget(trace_button)
        layout.addWidget(report_button)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Use SignalManager to connect controller signals
        self.signal_manager.connect(
            self.controller,
            "update_ui",
            self,
            "update_data_display",
            priority=SignalPriority.HIGH,  # Prioritize UI updates
        )

        # Use throttling for status updates to prevent flooding
        self.signal_manager.connect_throttled(
            self.controller,
            "status_changed",
            self,
            "update_status",
            throttle_ms=200,  # Throttle rapid status updates
        )

        # Register these signals with the tracer for detailed tracking
        signal_tracer.register_signal(self.controller, "update_ui", self, "update_data_display")
        signal_tracer.register_signal(self.controller, "status_changed", self, "update_status")

        # Set a slow threshold for the update_ui signal
        signal_tracer.set_slow_threshold("DataController.update_ui", 10.0)  # ms

    @Slot(dict)
    def update_data_display(self, data):
        """Update the data display with the current data."""
        # Simulate a slow handler occasionally
        if random.random() < 0.3:
            time.sleep(0.02)  # 20ms delay to trigger slow handler detection

        text = "\n".join([f"{key}: {value}" for key, value in data.items()])
        self.data_label.setText(text)

    @Slot(str)
    def update_status(self, status):
        """Update the status label."""
        self.status_label.setText(f"Status: {status}")

    def on_update_score(self):
        """Update the player score with a random value."""
        new_score = random.randint(100, 1000)
        self.controller.update_score(new_score)

    def toggle_tracing(self):
        """Toggle the signal tracing on or off."""
        if signal_tracer.is_active():
            signal_tracer.stop_tracing()
            self.status_label.setText("Status: Tracing stopped")
        else:
            signal_tracer.start_tracing()
            signal_tracer.clear()  # Clear previous traces
            self.status_label.setText("Status: Tracing started")

    def generate_report(self):
        """Generate and display a signal tracing report."""
        if not signal_tracer.is_active():
            self.status_label.setText("Status: No active tracing session")
            return

        report = signal_tracer.generate_report()
        print("\n" + "=" * 80)
        print(report)
        print("=" * 80 + "\n")
        self.status_label.setText("Status: Report generated (see console)")


def main():
    """Main entry point for the demo application."""
    app = QApplication(sys.argv)

    # Create the model and controller
    data_model = DataModel()
    controller = DataController(data_model)

    # Create and show the main window
    main_window = MainView(controller)
    main_window.show()

    # Set up a timer to generate some events automatically
    demo_timer = QTimer()

    def generate_event():
        """Generate a random event."""
        event_type = random.choice(["load", "save", "update"])
        if event_type == "load":
            controller.load_data()
        elif event_type == "save":
            controller.save_data()
        else:
            controller.update_score(random.randint(100, 1000))

    # Connect timer to event generation
    demo_timer.timeout.connect(generate_event)
    demo_timer.start(2000)  # Generate an event every 2 seconds

    print("Signal Tracing Demo started.")
    print("Click 'Toggle Tracing' to start/stop tracing, and 'Generate Report' to see the results.")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
