"""
debugging.py

Description: Debugging tools for the ChestBuddy application
Usage:
    Import specific debugging tools to diagnose issues with the application
"""

import logging
import time
import threading
import sys
import traceback
from typing import Any, Dict, List, Optional, Callable, Tuple
from pathlib import Path
import json
import datetime
from contextlib import contextmanager

from PySide6.QtCore import Qt, QObject, QEvent, QTimer, Signal, QEventLoop
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGridLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QScrollArea,
)

logger = logging.getLogger(__name__)

# ===========================================
# Enhanced Logging Formatter
# ===========================================


class DiagnosticLogFormatter(logging.Formatter):
    """Enhanced formatter with timestamps, thread info, and call stack depth."""

    def format(self, record):
        # Add thread ID
        record.threadName = f"{record.threadName}[{threading.get_ident()}]"

        # Add millisecond precision to timestamp
        record.msecs = int(record.relativeCreated % 1000)

        # Add stack info if not already present
        if not record.exc_info and not record.stack_info:
            # Get current frame and depth
            f = sys._getframe(6)  # Skip this frame + logging frames
            depth = 0
            while f:
                depth += 1
                f = f.f_back
            record.stackdepth = depth

            # Add the depth to the message
            original_msg = record.msg
            record.msg = f"[Depth:{depth}] {original_msg}"

        return super().format(record)


def setup_diagnostic_logging():
    """Set up enhanced logging for debugging."""
    # Create a handler that writes to both stderr and a file
    file_handler = logging.FileHandler(
        Path("debug_logs")
        / f"chestbuddy_debug_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    console_handler = logging.StreamHandler()

    # Create and set formatter
    formatter = DiagnosticLogFormatter(
        "%(asctime)s.%(msecs)03d %(threadName)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info("Diagnostic logging setup complete")


# ===========================================
# State Tracking and Comparison
# ===========================================


class StateSnapshot:
    """Captures and stores application state at a specific point in time."""

    def __init__(self, name: str = None):
        """
        Initialize a state snapshot.

        Args:
            name: An optional name for this snapshot
        """
        self.timestamp = time.time()
        self.name = name or f"Snapshot_{self.timestamp}"
        self.data = {}

    def capture_widget_state(self, widget: QWidget, prefix: str = "") -> None:
        """
        Capture the state of a widget and its children.

        Args:
            widget: The widget to capture state from
            prefix: Prefix for the state keys
        """
        if not widget:
            return

        # Capture basic widget properties
        key = f"{prefix}_{widget.objectName() or widget.__class__.__name__}"
        self.data[f"{key}.visible"] = widget.isVisible()
        self.data[f"{key}.enabled"] = widget.isEnabled()
        self.data[f"{key}.geometry"] = str(widget.geometry())
        self.data[f"{key}.class"] = widget.__class__.__name__

        # Capture focus state
        self.data[f"{key}.hasFocus"] = widget.hasFocus()

        # Capture additional properties for specific widget types
        if hasattr(widget, "text") and callable(widget.text):
            self.data[f"{key}.text"] = widget.text()

        if hasattr(widget, "isChecked") and callable(widget.isChecked):
            self.data[f"{key}.checked"] = widget.isChecked()

        if hasattr(widget, "windowModality") and callable(widget.windowModality):
            self.data[f"{key}.modality"] = str(widget.windowModality())

        # Recursively capture state of child widgets
        for child in widget.findChildren(QWidget):
            if child.parent() == widget:  # Only direct children
                self.capture_widget_state(child, f"{key}")

    def capture_application_state(self) -> None:
        """Capture the state of the entire application."""
        app = QApplication.instance()
        if not app:
            logger.warning("No QApplication instance found")
            return

        # Capture global application state
        self.data["app.modalLevel"] = app.modalLevel()
        self.data["app.hasPendingEvents"] = app.hasPendingEvents()

        # Capture active window and focus widget
        active_window = app.activeWindow()
        focus_widget = app.focusWidget()

        self.data["app.activeWindow"] = active_window.objectName() if active_window else "None"
        self.data["app.focusWidget"] = focus_widget.objectName() if focus_widget else "None"

        # Capture top-level widgets
        for widget in app.topLevelWidgets():
            self.capture_widget_state(widget)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the snapshot to a dictionary.

        Returns:
            Dictionary representation of the snapshot
        """
        return {"name": self.name, "timestamp": self.timestamp, "data": self.data}

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """
        Save the snapshot to a file.

        Args:
            path: Path to save the file to. If None, a default path is used.
        """
        if path is None:
            path = Path("debug_logs") / f"state_{self.name}_{int(self.timestamp)}.json"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"State snapshot saved to {path}")


def compare_snapshots(
    snapshot1: StateSnapshot, snapshot2: StateSnapshot
) -> Dict[str, Tuple[Any, Any]]:
    """
    Compare two state snapshots and return the differences.

    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot

    Returns:
        Dictionary of differences with key and (value1, value2) tuple
    """
    diffs = {}

    # Find keys in both snapshots
    all_keys = set(snapshot1.data.keys()) | set(snapshot2.data.keys())

    for key in all_keys:
        val1 = snapshot1.data.get(key, "<not present>")
        val2 = snapshot2.data.get(key, "<not present>")

        if val1 != val2:
            diffs[key] = (val1, val2)

    return diffs


def print_snapshot_diff(snapshot1: StateSnapshot, snapshot2: StateSnapshot) -> None:
    """
    Print the differences between two snapshots.

    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot
    """
    diffs = compare_snapshots(snapshot1, snapshot2)

    if not diffs:
        logger.info(f"No differences found between {snapshot1.name} and {snapshot2.name}")
        return

    logger.info(f"Found {len(diffs)} differences between {snapshot1.name} and {snapshot2.name}:")

    for key, (val1, val2) in diffs.items():
        logger.info(f"  {key}: {val1} -> {val2}")


# ===========================================
# Event Tracing
# ===========================================


class EventTracer(QObject):
    """Traces and logs Qt events for debugging."""

    def __init__(self, parent=None):
        """Initialize the event tracer."""
        super().__init__(parent)
        self.enabled = False
        self.event_counts = {}
        self.focus_events = []
        self.start_time = None

    def start_tracing(self) -> None:
        """Start tracing events."""
        self.enabled = True
        self.event_counts = {}
        self.focus_events = []
        self.start_time = time.time()
        QApplication.instance().installEventFilter(self)
        logger.info("Event tracing started")

    def stop_tracing(self) -> None:
        """Stop tracing events."""
        if not self.enabled:
            return

        self.enabled = False
        QApplication.instance().removeEventFilter(self)

        # Log event statistics
        logger.info("Event tracing stopped")
        logger.info("Event counts:")
        for event_type, count in sorted(
            self.event_counts.items(), key=lambda x: x[1], reverse=True
        ):
            logger.info(f"  {self._event_type_name(event_type)}: {count}")

        logger.info("Focus events sequence:")
        for timestamp, widget, gained in self.focus_events:
            action = "gained" if gained else "lost"
            logger.info(f"  {timestamp:.3f}s: {widget} {action} focus")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter Qt events.

        Args:
            obj: Object receiving the event
            event: The event

        Returns:
            Whether to filter out the event
        """
        if not self.enabled:
            return False

        event_type = event.type()

        # Count event types
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # Track focus events
        if event_type == QEvent.FocusIn:
            elapsed = time.time() - self.start_time
            self.focus_events.append((elapsed, obj.objectName() or obj.__class__.__name__, True))

        elif event_type == QEvent.FocusOut:
            elapsed = time.time() - self.start_time
            self.focus_events.append((elapsed, obj.objectName() or obj.__class__.__name__, False))

        # Log interesting event types
        event_type_name = self._event_type_name(event_type)

        # Only log certain interesting events with full details
        interesting_events = [
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.WindowBlocked,
            QEvent.WindowUnblocked,
            QEvent.ApplicationStateChange,
            QEvent.StatusTip,
            QEvent.Close,
            QEvent.Show,
            QEvent.Hide,
            QEvent.FocusIn,
            QEvent.FocusOut,
            QEvent.WindowActivate,
            QEvent.WindowDeactivate,
        ]

        if event_type in interesting_events:
            obj_name = obj.objectName() or obj.__class__.__name__
            logger.debug(f"[EVENT] {obj_name} received {event_type_name}")

        # Don't filter the event, just observe it
        return False

    def _event_type_name(self, event_type: QEvent.Type) -> str:
        """
        Get the name of an event type.

        Args:
            event_type: The event type

        Returns:
            Name of the event type
        """
        # Map event types to names
        event_types = {
            QEvent.None_: "None",
            QEvent.MouseButtonPress: "MouseButtonPress",
            QEvent.MouseButtonRelease: "MouseButtonRelease",
            QEvent.MouseButtonDblClick: "MouseButtonDblClick",
            QEvent.MouseMove: "MouseMove",
            QEvent.KeyPress: "KeyPress",
            QEvent.KeyRelease: "KeyRelease",
            QEvent.FocusIn: "FocusIn",
            QEvent.FocusOut: "FocusOut",
            QEvent.Enter: "Enter",
            QEvent.Leave: "Leave",
            QEvent.Paint: "Paint",
            QEvent.Move: "Move",
            QEvent.Resize: "Resize",
            QEvent.Show: "Show",
            QEvent.Hide: "Hide",
            QEvent.Close: "Close",
            QEvent.Quit: "Quit",
            QEvent.WindowActivate: "WindowActivate",
            QEvent.WindowDeactivate: "WindowDeactivate",
            QEvent.ShowToParent: "ShowToParent",
            QEvent.HideToParent: "HideToParent",
            QEvent.WinIdChange: "WinIdChange",
            QEvent.WindowTitleChange: "WindowTitleChange",
            QEvent.WindowIconChange: "WindowIconChange",
            QEvent.ApplicationWindowIconChange: "ApplicationWindowIconChange",
            QEvent.ApplicationFontChange: "ApplicationFontChange",
            QEvent.ApplicationLayoutDirectionChange: "ApplicationLayoutDirectionChange",
            QEvent.ApplicationPaletteChange: "ApplicationPaletteChange",
            QEvent.PaletteChange: "PaletteChange",
            QEvent.ApplicationStateChange: "ApplicationStateChange",
            QEvent.WindowStateChange: "WindowStateChange",
            QEvent.WindowBlocked: "WindowBlocked",
            QEvent.WindowUnblocked: "WindowUnblocked",
            QEvent.StatusTip: "StatusTip",
            QEvent.UpdateRequest: "UpdateRequest",
            QEvent.LanguageChange: "LanguageChange",
            QEvent.StyleChange: "StyleChange",
        }

        return event_types.get(event_type, f"Unknown({int(event_type)})")


# ===========================================
# UI Debugger Dialog
# ===========================================


class WidgetInfoItem(QTreeWidgetItem):
    """TreeWidgetItem to display widget information."""

    def __init__(self, parent, widget: QWidget):
        """
        Initialize with a widget.

        Args:
            parent: Parent tree item
            widget: The widget to display info for
        """
        super().__init__(parent)
        self.widget = widget
        self.setText(0, widget.objectName() or widget.__class__.__name__)
        self.setText(1, widget.__class__.__name__)
        self.setText(2, "Yes" if widget.isVisible() else "No")
        self.setText(3, "Yes" if widget.isEnabled() else "No")

        # Add additional properties
        if hasattr(widget, "windowModality") and callable(widget.windowModality):
            modality = widget.windowModality()
            modality_str = {
                Qt.NonModal: "NonModal",
                Qt.WindowModal: "WindowModal",
                Qt.ApplicationModal: "ApplicationModal",
            }.get(modality, str(modality))
            self.setText(4, modality_str)
        else:
            self.setText(4, "N/A")

        # Add children
        for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            WidgetInfoItem(self, child)


class DebuggerDialog(QDialog):
    """Dialog for debugging UI issues."""

    def __init__(self, parent=None):
        """Initialize the debugger dialog."""
        super().__init__(parent)
        self.setWindowTitle("UI Debugger")
        self.resize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)

        self._setup_ui()
        self._connect_signals()

        # Initialize event tracer
        self.event_tracer = EventTracer(self)

        # Set up refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_widget_tree)
        self.refresh_timer.start(1000)  # Refresh every second

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Widget hierarchy tab
        self.widget_tab = QWidget()
        self.tabs.addTab(self.widget_tab, "Widget Hierarchy")

        widget_layout = QVBoxLayout(self.widget_tab)

        # Controls
        controls_layout = QHBoxLayout()
        widget_layout.addLayout(controls_layout)

        self.refresh_button = QPushButton("Refresh")
        controls_layout.addWidget(self.refresh_button)

        self.auto_refresh_check = QCheckBox("Auto-Refresh")
        self.auto_refresh_check.setChecked(True)
        controls_layout.addWidget(self.auto_refresh_check)

        self.trace_events_check = QCheckBox("Trace Events")
        controls_layout.addWidget(self.trace_events_check)

        controls_layout.addStretch()

        # Widget tree
        self.widget_tree = QTreeWidget()
        self.widget_tree.setHeaderLabels(["Name", "Type", "Visible", "Enabled", "Modality"])
        self.widget_tree.setColumnWidth(0, 200)
        self.widget_tree.setColumnWidth(1, 150)
        self.widget_tree.setColumnWidth(2, 70)
        self.widget_tree.setColumnWidth(3, 70)
        widget_layout.addWidget(self.widget_tree)

        # Events tab
        self.events_tab = QWidget()
        self.tabs.addTab(self.events_tab, "Events")

        events_layout = QVBoxLayout(self.events_tab)

        # Event controls
        event_controls = QHBoxLayout()
        events_layout.addLayout(event_controls)

        self.start_trace_button = QPushButton("Start Tracing")
        event_controls.addWidget(self.start_trace_button)

        self.stop_trace_button = QPushButton("Stop Tracing")
        self.stop_trace_button.setEnabled(False)
        event_controls.addWidget(self.stop_trace_button)

        event_controls.addStretch()

        # Event log
        self.event_log = QLabel("Event tracing not active. Press 'Start Tracing' to begin.")
        self.event_log.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.event_log.setWordWrap(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.event_log)
        events_layout.addWidget(scroll_area)

        # Actions tab
        self.actions_tab = QWidget()
        self.tabs.addTab(self.actions_tab, "Actions")

        actions_layout = QVBoxLayout(self.actions_tab)

        # Emergency unblock button
        self.unblock_button = QPushButton("Emergency UI Unblock")
        self.unblock_button.setStyleSheet(
            "background-color: #dc3545; color: white; font-weight: bold; padding: 10px;"
        )
        actions_layout.addWidget(self.unblock_button)

        # Capture state button
        self.capture_state_button = QPushButton("Capture Application State")
        actions_layout.addWidget(self.capture_state_button)

        # Process events button
        self.process_events_button = QPushButton("Force Process Events")
        actions_layout.addWidget(self.process_events_button)

        # Enable all widgets button
        self.enable_all_button = QPushButton("Enable All Widgets")
        actions_layout.addWidget(self.enable_all_button)

        actions_layout.addStretch()

        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Button box
        button_box = QHBoxLayout()
        layout.addLayout(button_box)

        self.close_button = QPushButton("Close")
        button_box.addStretch()
        button_box.addWidget(self.close_button)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.refresh_button.clicked.connect(self._refresh_widget_tree)
        self.auto_refresh_check.toggled.connect(self._toggle_auto_refresh)
        self.trace_events_check.toggled.connect(self._toggle_event_tracing)
        self.close_button.clicked.connect(self.accept)

        self.start_trace_button.clicked.connect(self._start_event_tracing)
        self.stop_trace_button.clicked.connect(self._stop_event_tracing)

        self.unblock_button.clicked.connect(self._emergency_unblock)
        self.capture_state_button.clicked.connect(self._capture_application_state)
        self.process_events_button.clicked.connect(self._force_process_events)
        self.enable_all_button.clicked.connect(self._enable_all_widgets)

    def _refresh_widget_tree(self):
        """Refresh the widget tree."""
        if not self.isVisible() or self.tabs.currentWidget() != self.widget_tab:
            return

        self.widget_tree.clear()

        app = QApplication.instance()
        if not app:
            return

        # Add top-level widgets
        for widget in app.topLevelWidgets():
            WidgetInfoItem(self.widget_tree, widget)

        self.status_label.setText(f"Refreshed at {datetime.datetime.now().strftime('%H:%M:%S')}")

    def _toggle_auto_refresh(self, checked):
        """Toggle auto-refresh timer."""
        if checked:
            self.refresh_timer.start(1000)
        else:
            self.refresh_timer.stop()

    def _toggle_event_tracing(self, checked):
        """Toggle event tracing."""
        if checked:
            self._start_event_tracing()
        else:
            self._stop_event_tracing()

    def _start_event_tracing(self):
        """Start event tracing."""
        self.event_tracer.start_tracing()
        self.start_trace_button.setEnabled(False)
        self.stop_trace_button.setEnabled(True)
        self.trace_events_check.setChecked(True)
        self.event_log.setText("Event tracing active...")
        self.status_label.setText("Event tracing started")

    def _stop_event_tracing(self):
        """Stop event tracing."""
        self.event_tracer.stop_tracing()
        self.start_trace_button.setEnabled(True)
        self.stop_trace_button.setEnabled(False)
        self.trace_events_check.setChecked(False)

        # Update event log with counts
        counts_text = "Event Counts:\n"
        for event_type, count in sorted(
            self.event_tracer.event_counts.items(), key=lambda x: x[1], reverse=True
        ):
            counts_text += f"{self.event_tracer._event_type_name(event_type)}: {count}\n"

        self.event_log.setText(counts_text)
        self.status_label.setText("Event tracing stopped")

    def _emergency_unblock(self):
        """Emergency UI unblock - try to force enable the UI."""
        app = QApplication.instance()
        if not app:
            self.status_label.setText("No QApplication instance found")
            return

        logger.info("[EMERGENCY_UNBLOCK] Performing emergency UI unblock")

        # Process pending events
        app.processEvents()

        # Force unblock all top-level windows
        for widget in app.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isModal():
                logger.info(
                    f"[EMERGENCY_UNBLOCK] Forcing modal dialog to non-modal: {widget.objectName() or widget.__class__.__name__}"
                )
                widget.setWindowModality(Qt.NonModal)

                # Try to accept any open dialogs
                if widget.isVisible():
                    logger.info(
                        f"[EMERGENCY_UNBLOCK] Accepting visible dialog: {widget.objectName() or widget.__class__.__name__}"
                    )
                    widget.accept()

        # Process events again
        app.processEvents()

        # Force enable main window
        main_window = None
        for widget in app.topLevelWidgets():
            if widget.objectName() == "MainWindow":
                main_window = widget
                break

        if main_window:
            logger.info("[EMERGENCY_UNBLOCK] Enabling main window and all children")
            main_window.setEnabled(True)

            # Enable all widgets
            for widget in main_window.findChildren(QWidget):
                widget.setEnabled(True)

        # Process events once more
        app.processEvents()

        self.status_label.setText("Emergency unblock completed")
        logger.info("[EMERGENCY_UNBLOCK] Emergency unblock completed")

    def _capture_application_state(self):
        """Capture and save the current application state."""
        snapshot = StateSnapshot("manual_capture")
        snapshot.capture_application_state()
        snapshot.save_to_file()

        self.status_label.setText(
            f"Application state captured at {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

    def _force_process_events(self):
        """Force process all pending events."""
        logger.info("[FORCE_PROCESS] Forcing event processing")

        # Create a temporary event loop and process events
        loop = QEventLoop()
        loop.processEvents(QEventLoop.AllEvents)

        # Process application events too
        QApplication.instance().processEvents()

        self.status_label.setText(
            f"Events processed at {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        logger.info("[FORCE_PROCESS] Event processing completed")

    def _enable_all_widgets(self):
        """Force enable all widgets in the application."""
        app = QApplication.instance()
        if not app:
            self.status_label.setText("No QApplication instance found")
            return

        logger.info("[ENABLE_ALL] Enabling all widgets")

        widgets_enabled = 0

        for widget in app.topLevelWidgets():
            # Enable the top-level widget
            if not widget.isEnabled():
                logger.info(
                    f"[ENABLE_ALL] Enabling top-level widget: {widget.objectName() or widget.__class__.__name__}"
                )
                widget.setEnabled(True)
                widgets_enabled += 1

            # Enable all child widgets
            for child in widget.findChildren(QWidget):
                if not child.isEnabled():
                    logger.info(
                        f"[ENABLE_ALL] Enabling child widget: {child.objectName() or child.__class__.__name__}"
                    )
                    child.setEnabled(True)
                    widgets_enabled += 1

        # Process events after enabling widgets
        QApplication.instance().processEvents()

        self.status_label.setText(
            f"Enabled {widgets_enabled} widgets at {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        logger.info(f"[ENABLE_ALL] Enabled {widgets_enabled} widgets")


# ===========================================
# Debug Hotkey Handler
# ===========================================


class DebugHotkeyHandler(QObject):
    """Handles global debug hotkeys."""

    def __init__(self, parent=None):
        """Initialize the hotkey handler."""
        super().__init__(parent)
        self._debugger_dialog = None

        # Install application-wide event filter
        QApplication.instance().installEventFilter(self)

        logger.info("Debug hotkey handler initialized (F12 for debug dialog)")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter events to catch hotkeys.

        Args:
            obj: Object receiving the event
            event: The event

        Returns:
            Whether to filter out the event
        """
        if event.type() == QEvent.KeyPress:
            key_event = event

            # F12 key for debug dialog
            if key_event.key() == Qt.Key_F12:
                self._show_debug_dialog()
                return True

        # Don't filter the event, just observe it
        return False

    def _show_debug_dialog(self):
        """Show the debugger dialog."""
        if not self._debugger_dialog:
            self._debugger_dialog = DebuggerDialog()

        if self._debugger_dialog.isVisible():
            self._debugger_dialog.raise_()
            self._debugger_dialog.activateWindow()
        else:
            self._debugger_dialog.show()


# ===========================================
# Performance Timing
# ===========================================


@contextmanager
def measure_time(operation_name: str, log_level: int = logging.DEBUG) -> None:
    """
    Context manager to measure and log the execution time of a block of code.

    Args:
        operation_name: Name of the operation being timed
        log_level: Logging level to use
    """
    start_time = time.time()
    logger.log(log_level, f"[TIMING] Starting {operation_name}")

    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.log(log_level, f"[TIMING] {operation_name} completed in {duration:.4f} seconds")


# ===========================================
# Debug Hooks
# ===========================================


def install_debug_hooks(app=None) -> None:
    """
    Install debugging hooks into the application.

    Args:
        app: QApplication instance, or None to use QApplication.instance()
    """
    if app is None:
        app = QApplication.instance()

    if app is None:
        logger.error("No QApplication instance found")
        return

    # Set up enhanced logging
    setup_diagnostic_logging()

    # Install hotkey handler
    debug_hotkey_handler = DebugHotkeyHandler(app)

    # Initialize first state snapshot
    initial_snapshot = StateSnapshot("initial_state")
    initial_snapshot.capture_application_state()
    initial_snapshot.save_to_file()

    logger.info("Debug hooks installed successfully")

    return debug_hotkey_handler


# ===========================================
# Command Line Debug Interface
# ===========================================


def initialize_cli_debug() -> None:
    """Initialize command-line debug interface."""
    import code
    import threading

    def debug_console():
        """Run a debug console in a separate thread."""
        variables = {
            "QApplication": QApplication,
            "app": QApplication.instance(),
            "measure_time": measure_time,
            "StateSnapshot": StateSnapshot,
            "compare_snapshots": compare_snapshots,
            "print_snapshot_diff": print_snapshot_diff,
            "EventTracer": EventTracer,
            "DebuggerDialog": DebuggerDialog,
        }

        code.interact(
            banner="ChestBuddy Debug Console\n"
            "Type 'app' to access the QApplication instance.\n"
            "Available utilities: measure_time, StateSnapshot, compare_snapshots, "
            "print_snapshot_diff, EventTracer, DebuggerDialog",
            local=variables,
        )

    # Start console in a separate thread
    console_thread = threading.Thread(target=debug_console, daemon=True)
    console_thread.start()

    logger.info("Debug console thread started")
