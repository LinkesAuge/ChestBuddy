"""
UI State Signals.

This module defines the signals used by the UI state management system
to notify about UI state changes.
"""

from typing import Any, Dict, Set, Tuple

from PySide6.QtCore import QObject, Signal


class UIStateSignals(QObject):
    """
    Signals for the UI state management system.

    These signals are emitted when UI state changes occur, allowing
    components to react to changes in the UI state.
    """

    # Signal emitted when an element or group becomes blocked
    # Parameters: element_id, operation
    element_blocked = Signal(object, object)

    # Signal emitted when an element or group becomes unblocked
    # Parameters: element_id, operation
    element_unblocked = Signal(object, object)

    # Signal emitted when a blocking operation starts
    # Parameters: operation, affected_elements
    operation_started = Signal(object, object)

    # Signal emitted when a blocking operation ends
    # Parameters: operation, affected_elements
    operation_ended = Signal(object, object)

    # Signal emitted when the blocking state of an element changes
    # Parameters: element_id, is_blocked, blocking_operations
    blocking_state_changed = Signal(object, bool, object)

    # Signal emitted for logging or debugging purposes
    # Parameters: message, details
    state_debug = Signal(str, dict)
