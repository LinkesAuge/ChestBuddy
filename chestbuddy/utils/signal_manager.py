"""
signal_manager.py

Description: Utility for managing signal connections in the ChestBuddy application
Usage:
    signal_manager = SignalManager()
    signal_manager.connect(sender, "signal_name", receiver, "slot_name")
"""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from PySide6.QtCore import QObject

# Set up logger
logger = logging.getLogger(__name__)


class SignalManager:
    """
    Utility class for managing PySide6 signal connections.

    This class provides methods for connecting signals to slots with tracking,
    preventing duplicate connections, and ensuring safe disconnection.

    Attributes:
        _connections (dict): Dictionary tracking active connections
        _debug_mode (bool): Whether debug mode is enabled
    """

    def __init__(self, debug_mode: bool = False):
        """
        Initialize the signal manager with an empty connections dictionary.

        Args:
            debug_mode: Whether to enable debug mode
        """
        # Structure: {(signal_object, signal_name): set([(receiver, slot_name)])}
        self._connections: Dict[Tuple[QObject, str], Set[Tuple[QObject, str]]] = {}
        self._debug_mode = debug_mode

    def connect(self, sender: QObject, signal_name: str, receiver: QObject, slot_name: str) -> bool:
        """
        Connect a signal to a slot with tracking.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal (without the signal() suffix)
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted

        Returns:
            bool: True if connection was established, False if already connected

        Raises:
            AttributeError: If signal or slot doesn't exist
        """
        try:
            # Get the actual signal and slot
            signal = getattr(sender, signal_name)
            slot = getattr(receiver, slot_name)

            # Check if this connection already exists
            connection_key = (sender, signal_name)
            connection_value = (receiver, slot_name)

            if connection_key not in self._connections:
                self._connections[connection_key] = set()

            if connection_value in self._connections[connection_key]:
                if self._debug_mode:
                    logger.debug(
                        f"Connection already exists: {sender}.{signal_name} -> {receiver}.{slot_name}"
                    )
                return False

            # Make the connection
            signal.connect(slot)
            self._connections[connection_key].add(connection_value)

            if self._debug_mode:
                logger.debug(f"Connected: {sender}.{signal_name} -> {receiver}.{slot_name}")

            return True
        except AttributeError as e:
            logger.error(f"Failed to connect signal: {e}")
            raise

    def disconnect(
        self,
        sender: QObject,
        signal_name: str,
        receiver: Optional[QObject] = None,
        slot_name: Optional[str] = None,
    ) -> int:
        """
        Disconnect signal(s) with tracking.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Optional object that receives the signal
            slot_name: Optional name of the slot

        Returns:
            int: Number of disconnections made

        Raises:
            AttributeError: If signal or slot doesn't exist
        """
        connection_key = (sender, signal_name)

        if connection_key not in self._connections:
            return 0

        signal = getattr(sender, signal_name)
        count = 0

        if receiver is None:
            # Disconnect all connections for this signal
            connections = list(self._connections[connection_key])
            for recv, sname in connections:
                slot = getattr(recv, sname)
                signal.disconnect(slot)
                self._connections[connection_key].remove((recv, sname))
                count += 1

                if self._debug_mode:
                    logger.debug(f"Disconnected: {sender}.{signal_name} -> {recv}.{sname}")

            if not self._connections[connection_key]:
                del self._connections[connection_key]
        elif slot_name is None:
            # Disconnect all connections to this receiver
            connections = list(self._connections[connection_key])
            for recv, sname in connections:
                if recv == receiver:
                    slot = getattr(recv, sname)
                    signal.disconnect(slot)
                    self._connections[connection_key].remove((recv, sname))
                    count += 1

                    if self._debug_mode:
                        logger.debug(f"Disconnected: {sender}.{signal_name} -> {recv}.{sname}")

            if not self._connections[connection_key]:
                del self._connections[connection_key]
        else:
            # Disconnect specific connection
            connection_value = (receiver, slot_name)
            if connection_value in self._connections[connection_key]:
                slot = getattr(receiver, slot_name)
                signal.disconnect(slot)
                self._connections[connection_key].remove(connection_value)
                count += 1

                if self._debug_mode:
                    logger.debug(f"Disconnected: {sender}.{signal_name} -> {receiver}.{slot_name}")

                if not self._connections[connection_key]:
                    del self._connections[connection_key]

        return count

    def disconnect_all(self) -> int:
        """
        Disconnect all tracked connections.

        Returns:
            int: Number of disconnections made
        """
        count = 0
        for connection_key, connections in list(self._connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            for receiver, slot_name in list(connections):
                slot = getattr(receiver, slot_name)
                signal.disconnect(slot)
                count += 1

                if self._debug_mode:
                    logger.debug(f"Disconnected: {sender}.{signal_name} -> {receiver}.{slot_name}")

        self._connections = {}
        return count

    def disconnect_receiver(self, receiver: QObject) -> int:
        """
        Disconnect all signals connected to the given receiver.

        Args:
            receiver: Object receiving signals to disconnect

        Returns:
            int: Number of disconnections made
        """
        count = 0
        for connection_key, connections in list(self._connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            for recv, slot_name in list(connections):
                if recv == receiver:
                    slot = getattr(recv, slot_name)
                    signal.disconnect(slot)
                    self._connections[connection_key].remove((recv, slot_name))
                    count += 1

                    if self._debug_mode:
                        logger.debug(
                            f"Disconnected: {sender}.{signal_name} -> {receiver}.{slot_name}"
                        )

            if not self._connections[connection_key]:
                del self._connections[connection_key]

        return count

    def is_connected(
        self, sender: QObject, signal_name: str, receiver: QObject, slot_name: str
    ) -> bool:
        """
        Check if a specific signal-slot connection exists.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that receives the signal
            slot_name: Name of the slot

        Returns:
            bool: True if connected, False otherwise
        """
        connection_key = (sender, signal_name)
        connection_value = (receiver, slot_name)

        return (
            connection_key in self._connections
            and connection_value in self._connections[connection_key]
        )

    def get_connections(
        self,
        sender: Optional[QObject] = None,
        signal_name: Optional[str] = None,
        receiver: Optional[QObject] = None,
    ) -> List[Tuple[QObject, str, QObject, str]]:
        """
        Get a list of connections matching the specified criteria.

        Args:
            sender: Optional sender to filter by
            signal_name: Optional signal name to filter by
            receiver: Optional receiver to filter by

        Returns:
            list: List of connections as (sender, signal_name, receiver, slot_name)
        """
        result = []

        for (src, sig_name), connections in self._connections.items():
            if sender is not None and src != sender:
                continue
            if signal_name is not None and sig_name != signal_name:
                continue

            for recv, slot_name in connections:
                if receiver is not None and recv != receiver:
                    continue
                result.append((src, sig_name, recv, slot_name))

        return result

    @contextmanager
    def blocked_signals(self, sender: QObject, signal_name: Optional[str] = None):
        """
        Context manager to temporarily block signals.

        Args:
            sender: Object whose signals should be blocked
            signal_name: Optional specific signal to block

        Example:
            ```
            with signal_manager.blocked_signals(model, "data_changed"):
                model.update_data(new_data)  # won't emit data_changed
            ```
        """
        original_state = sender.blockSignals(True)
        try:
            yield
        finally:
            sender.blockSignals(original_state)

    def safe_connect(
        self,
        sender: QObject,
        signal_name: str,
        receiver: QObject,
        slot_name: str,
        safe_disconnect_first: bool = False,
    ) -> bool:
        """
        Safely connect a signal with optional disconnect first.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            safe_disconnect_first: Whether to disconnect first

        Returns:
            bool: True if connection was established
        """
        try:
            if safe_disconnect_first:
                self.disconnect(sender, signal_name, receiver, slot_name)

            return self.connect(sender, signal_name, receiver, slot_name)
        except Exception as e:
            logger.error(f"Error in safe_connect: {e}")
            return False

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Enable or disable debug mode.

        Args:
            enabled: Whether debug mode should be enabled
        """
        self._debug_mode = enabled

    def print_connections(self) -> None:
        """Print all tracked connections (useful for debugging)."""
        print("Current Signal Connections:")
        print("==========================")

        for i, ((sender, signal_name), connections) in enumerate(self._connections.items()):
            sender_name = sender.__class__.__name__
            print(f"{i + 1}. {sender_name}.{signal_name} connected to:")

            for j, (receiver, slot_name) in enumerate(connections):
                receiver_name = receiver.__class__.__name__
                print(f"   {j + 1}. {receiver_name}.{slot_name}")

            print()
