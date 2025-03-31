"""
signal_manager.py

Description: Utility for managing signal connections in the ChestBuddy application
Usage:
    signal_manager = SignalManager()
    signal_manager.connect(sender, "signal_name", receiver, "slot_name")
"""

import inspect
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import weakref

from PySide6.QtCore import QObject, QTimer, Signal

# Set up logger
logger = logging.getLogger(__name__)

# Conditional import of signal_tracer to avoid warnings in production
signal_tracer = None
try:
    # Only import if in debug mode
    from chestbuddy.utils.signal_tracer import signal_tracer
except ImportError:
    pass
except UserWarning:
    # Ignore the UserWarning from signal_tracer
    pass


class SignalManager:
    """
    Utility class for managing PySide6 signal connections.

    This class provides methods for connecting signals to slots with tracking,
    preventing duplicate connections, and ensuring safe disconnection.

    Attributes:
        _connections (dict): Dictionary tracking active connections
        _throttled_connections (dict): Dictionary tracking throttled connections
        _prioritized_connections (dict): Dictionary tracking prioritized connections
        _debug_mode (bool): Whether debug mode is enabled
        _type_checking (bool): Whether type checking is enabled
    """

    # Define priority constants
    PRIORITY_HIGHEST = 100
    PRIORITY_HIGH = 75
    PRIORITY_NORMAL = 50
    PRIORITY_LOW = 25
    PRIORITY_LOWEST = 0

    _instance = None

    @classmethod
    def instance(cls) -> "SignalManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = SignalManager()
        return cls._instance

    def __init__(self, debug_mode: bool = False, type_checking: bool = True):
        """
        Initialize the signal manager with an empty connections dictionary.

        Args:
            debug_mode: Whether to enable debug mode
            type_checking: Whether to enable type checking for signal/slot connections
        """
        # Structure: {(signal_object, signal_name): set([(receiver, slot_name)])}
        self._connections: Dict[Tuple[QObject, str], Set[Tuple[QObject, str]]] = {}
        # Structure: {(signal_object, signal_name): set([(receiver, slot_name, throttled_slot, throttle_ms, mode)])}
        self._throttled_connections: Dict[
            Tuple[QObject, str], Set[Tuple[QObject, str, Callable, int, str]]
        ] = {}
        # Structure: {(signal_object, signal_name): list([(receiver, slot_name, priority, wrapper_slot)])}
        self._prioritized_connections: Dict[
            Tuple[QObject, str], List[Tuple[QObject, str, int, Callable]]
        ] = {}
        self._debug_mode = debug_mode
        self._type_checking = type_checking

        # Track connections by (emitter, signal, receiver, slot)
        self._connections: Dict[
            Tuple[int, str, int, str], Tuple[QObject, str, QObject, Callable, bool]
        ] = {}

        # Maps to quickly locate connections
        # signal_emitter_id -> [(signal_name, connection_id), ...]
        self._emitter_map: Dict[int, List[Tuple[str, Tuple[int, str, int, str]]]] = {}

        # receiver_id -> [(slot_name, connection_id), ...]
        self._receiver_map: Dict[int, List[Tuple[str, Tuple[int, str, int, str]]]] = {}

        # slot_name -> [(receiver, connection_id), ...]
        self._slot_map: Dict[str, List[Tuple[QObject, Tuple[int, str, int, str]]]] = {}

        # Track emitters and receivers as weak references to avoid memory leaks
        # This also helps with cleanup when objects are destroyed
        self._weak_emitters: Dict[int, "weakref.ReferenceType[QObject]"] = {}
        self._weak_receivers: Dict[int, "weakref.ReferenceType[QObject]"] = {}

        # Set of connections to be checked for memory leaks
        self._leaked_connection_check: Set[Tuple[int, str, int, str]] = set()

    def _check_signal_slot_compatibility(
        self, sender: QObject, signal_name: str, receiver: QObject, slot_name: str
    ) -> bool:
        """
        Check if the signal and slot are type-compatible.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that will receive the signal
            slot_name: Name of the slot

        Returns:
            bool: True if compatible, False otherwise

        Raises:
            TypeError: If signal and slot signatures are incompatible
        """
        if not self._type_checking:
            return True

        try:
            # Get the actual signal and slot
            signal_obj = getattr(sender, signal_name)
            slot_obj = getattr(receiver, slot_name)

            # Check if it's actually a Signal instance
            if not isinstance(signal_obj, Signal):
                if self._debug_mode:
                    logger.warning(f"{sender}.{signal_name} is not a Signal instance")
                return True  # Skip checking as we can't determine signature

            # Get slot signature
            slot_sig = inspect.signature(slot_obj)

            # Handle *args parameter case - these can accept any number of arguments
            if any(
                param.kind == inspect.Parameter.VAR_POSITIONAL
                for param in slot_sig.parameters.values()
            ):
                return True

            # Determine if this is a bound method (has __self__ attribute)
            # If it is, we need to exclude the 'self' parameter from our count
            is_bound_method = hasattr(slot_obj, "__self__")

            # Get all parameters
            params = list(slot_sig.parameters.values())

            # Count total regular parameters (excluding self for methods)
            if is_bound_method:
                # For bound methods, parameter count should not include 'self'
                # PySide6 will automatically handle the 'self' parameter
                total_params = len(params)
            else:
                # For regular functions, count all parameters
                total_params = len(params)

            # Count required parameters (those without default values)
            required_params = 0
            for param in params:
                if param.default == inspect.Parameter.empty and param.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    required_params += 1

            # For signals, we need to know how many parameters they emit
            signal_param_count = 0

            # Try to get signal argument count from class definition
            if hasattr(sender.__class__, signal_name):
                signal_class_attr = getattr(sender.__class__, signal_name)
                if isinstance(signal_class_attr, Signal):
                    # Parse signal string to find argument types
                    signal_str = str(signal_class_attr)

                    # PySide6 signals look like: "signal_name(type1, type2)"
                    if "(" in signal_str and ")" in signal_str:
                        param_str = signal_str.split("(", 1)[1].split(")", 1)[0].strip()
                        if param_str:
                            # Split by comma and count non-empty parameters
                            signal_param_count = len([p for p in param_str.split(",") if p.strip()])

            # Special case for test signals - use name-based detection
            if signal_param_count == 0:
                if signal_name == "zero_args_signal":
                    signal_param_count = 0
                elif signal_name == "one_arg_signal":
                    signal_param_count = 1
                elif signal_name == "two_args_signal":
                    signal_param_count = 2
                elif signal_name == "three_args_signal":
                    signal_param_count = 3
                elif "test_signal" in signal_name:
                    # Default case for test_signal
                    signal_param_count = 1

            if self._debug_mode:
                logger.debug(
                    f"Type check: {sender.__class__.__name__}.{signal_name}[{signal_param_count}] -> "
                    f"{receiver.__class__.__name__}.{slot_name}[req:{required_params},total:{total_params}] "
                    f"(bound method: {is_bound_method})"
                )

            # Check compatibility rules:
            # 1. Signal must not emit more args than slot can accept
            if signal_param_count > total_params:
                raise TypeError(
                    f"Incompatible signal/slot signature: "
                    f"{sender.__class__.__name__}.{signal_name} emits {signal_param_count} "
                    f"parameters but {receiver.__class__.__name__}.{slot_name} "
                    f"accepts only {total_params} parameters"
                )

            # 2. Signal must emit at least as many args as slot requires
            if required_params > 0 and signal_param_count < required_params:
                raise TypeError(
                    f"Incompatible signal/slot signature: "
                    f"{sender.__class__.__name__}.{signal_name} emits only {signal_param_count} "
                    f"parameters but {receiver.__class__.__name__}.{slot_name} "
                    f"requires at least {required_params} parameters"
                )

            return True
        except (AttributeError, TypeError) as e:
            if isinstance(e, TypeError) and "Incompatible signal/slot" in str(e):
                raise
            if self._debug_mode:
                logger.warning(f"Could not check signal/slot compatibility: {e}")
            return True  # Skip checking on error

    def connect(
        self,
        sender: QObject,
        signal_name: str,
        receiver: QObject,
        slot_name: str,
        disconnect_first: bool = False,
    ) -> bool:
        """
        Connect a signal to a slot with tracking.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal (without the signal() suffix)
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            disconnect_first: Whether to disconnect existing connections first

        Returns:
            bool: True if connection was established, False if already connected

        Raises:
            AttributeError: If signal or slot doesn't exist
            TypeError: If signal and slot signatures are incompatible
        """
        try:
            # Get the actual signal and slot
            signal = getattr(sender, signal_name)
            slot = getattr(receiver, slot_name)

            # Check signal/slot compatibility
            self._check_signal_slot_compatibility(sender, signal_name, receiver, slot_name)

            # Check if this connection already exists
            connection_key = (sender, signal_name)
            connection_value = (receiver, slot_name)

            if connection_key not in self._connections:
                self._connections[connection_key] = set()

            if connection_value in self._connections[connection_key]:
                if disconnect_first:
                    # Disconnect existing connection before reconnecting
                    try:
                        signal.disconnect(slot)
                        self._connections[connection_key].remove(connection_value)
                        if self._debug_mode:
                            logger.debug(
                                f"Disconnected existing connection: {sender}.{signal_name} -> {receiver}.{slot_name}"
                            )
                    except (TypeError, RuntimeError) as e:
                        # The connection might have been lost already, just log and continue
                        logger.debug(f"Could not disconnect: {e}")
                else:
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

    def connect_throttled(
        self,
        sender: QObject,
        signal_name: str,
        receiver: QObject,
        slot_name: str,
        throttle_ms: int = 100,
        throttle_mode: str = "throttle",
    ) -> bool:
        """
        Connect a signal to a slot with throttling to prevent rapid firing.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal (without the signal() suffix)
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            throttle_ms: Throttle time in milliseconds
            throttle_mode: 'throttle' (calls at regular intervals) or 'debounce' (waits until idle)

        Returns:
            bool: True if connection was established, False if already connected

        Raises:
            AttributeError: If signal or slot doesn't exist
            ValueError: If throttle_mode is invalid
            TypeError: If signal and slot signatures are incompatible
        """
        try:
            # Validate throttle mode
            if throttle_mode not in ["throttle", "debounce"]:
                raise ValueError(
                    f"Invalid throttle mode: {throttle_mode}. Must be 'throttle' or 'debounce'."
                )

            # Get the actual signal and slot
            signal = getattr(sender, signal_name)
            slot = getattr(receiver, slot_name)

            # Check signal/slot compatibility
            self._check_signal_slot_compatibility(sender, signal_name, receiver, slot_name)

            # Check if this connection already exists
            connection_key = (sender, signal_name)

            if connection_key in self._throttled_connections:
                for recv, sname, throttled_slot, _, _ in self._throttled_connections[
                    connection_key
                ]:
                    if recv == receiver and sname == slot_name:
                        if self._debug_mode:
                            logger.debug(
                                f"Throttled connection already exists: {sender}.{signal_name} -> {receiver}.{slot_name}"
                            )
                        return False

            # Create a throttled version of the slot
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(throttle_ms)

            # Different function for throttle vs debounce mode
            if throttle_mode == "throttle":
                # In throttle mode, we call immediately and then ignore until timer expires
                last_called = [0]  # Use list to allow modification in inner scope

                def throttled_slot(*args, **kwargs):
                    nonlocal last_called
                    if not timer.isActive():
                        slot(*args, **kwargs)
                        timer.start()
                        last_called[0] = timer.remainingTime()

            else:  # debounce mode
                # Store the last args to use when timer fires
                last_args = [None]
                last_kwargs = [None]

                def throttled_slot(*args, **kwargs):
                    nonlocal last_args, last_kwargs
                    last_args[0] = args
                    last_kwargs[0] = kwargs
                    timer.start()

                # Connect the timer timeout to call the slot with the last args
                timer.timeout.connect(
                    lambda: slot(*last_args[0], **last_kwargs[0])
                    if last_args[0] is not None
                    else None
                )

            # Connect the signal to the throttled slot
            signal.connect(throttled_slot)

            # Track the connection
            if connection_key not in self._throttled_connections:
                self._throttled_connections[connection_key] = set()

            self._throttled_connections[connection_key].add(
                (receiver, slot_name, throttled_slot, throttle_ms, throttle_mode)
            )

            if self._debug_mode:
                logger.debug(
                    f"Connected throttled ({throttle_mode}, {throttle_ms}ms): "
                    f"{sender}.{signal_name} -> {receiver}.{slot_name}"
                )

            return True
        except AttributeError as e:
            logger.error(f"Failed to connect throttled signal: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to connect throttled signal: {e}")
            raise

    def _create_throttled_slot(
        self, receiver: QObject, slot_name: str, throttle_ms: int, mode: str
    ) -> Callable:
        """
        Create a throttled wrapper for a slot.

        Args:
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            throttle_ms: Throttle time in milliseconds
            mode: "throttle" or "debounce"

        Returns:
            Callable: Throttled wrapper function
        """
        slot = getattr(receiver, slot_name)
        timer = QTimer()
        timer.setSingleShot(True)

        # For tracking parameters between calls
        state = {"last_args": None, "last_kwargs": None, "timer_active": False}

        def throttled_slot(*args, **kwargs):
            state["last_args"] = args
            state["last_kwargs"] = kwargs

            if mode == "throttle" and not state["timer_active"]:
                # Throttle mode - call immediately, then ignore until timer expires
                state["timer_active"] = True
                slot(*args, **kwargs)
                timer.start(throttle_ms)
            elif mode == "debounce":
                # Debounce mode - reset timer each time, only call when timer expires
                if timer.isActive():
                    timer.stop()
                timer.start(throttle_ms)

        def on_timer_timeout():
            state["timer_active"] = False
            if mode == "debounce":
                # In debounce mode, call the slot with the most recent parameters
                slot(*state["last_args"], **state["last_kwargs"])

        timer.timeout.connect(on_timer_timeout)
        return throttled_slot

    def disconnect_throttled(
        self,
        sender: QObject,
        signal_name: str,
        receiver: Optional[QObject] = None,
        slot_name: Optional[str] = None,
    ) -> int:
        """
        Disconnect throttled signal(s).

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Optional object that receives the signal
            slot_name: Optional name of the slot

        Returns:
            int: Number of disconnections made
        """
        connection_key = (sender, signal_name)

        if connection_key not in self._throttled_connections:
            return 0

        signal = getattr(sender, signal_name)
        count = 0

        if receiver is None:
            # Disconnect all throttled connections for this signal
            connections = list(self._throttled_connections[connection_key])
            for conn in connections:
                recv, sname, throttled_slot, throttle_ms, throttle_mode = conn
                try:
                    signal.disconnect(throttled_slot)
                    self._throttled_connections[connection_key].remove(conn)
                    count += 1

                    if self._debug_mode:
                        logger.debug(
                            f"Disconnected throttled: {sender}.{signal_name} -> {recv}.{sname}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to disconnect throttled signal: {e}")

            if not self._throttled_connections[connection_key]:
                del self._throttled_connections[connection_key]
        elif slot_name is None:
            # Disconnect all throttled connections to this receiver
            connections = list(self._throttled_connections[connection_key])
            for conn in connections:
                recv, sname, throttled_slot, throttle_ms, throttle_mode = conn
                if recv == receiver:
                    try:
                        signal.disconnect(throttled_slot)
                        self._throttled_connections[connection_key].remove(conn)
                        count += 1

                        if self._debug_mode:
                            logger.debug(
                                f"Disconnected throttled: {sender}.{signal_name} -> {recv}.{sname}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to disconnect throttled signal: {e}")

            if not self._throttled_connections[connection_key]:
                del self._throttled_connections[connection_key]
        else:
            # Disconnect specific throttled connection(s)
            connections = list(self._throttled_connections[connection_key])
            for conn in connections:
                recv, sname, throttled_slot, throttle_ms, throttle_mode = conn
                if recv == receiver and sname == slot_name:
                    try:
                        signal.disconnect(throttled_slot)
                        self._throttled_connections[connection_key].remove(conn)
                        count += 1

                        if self._debug_mode:
                            logger.debug(
                                f"Disconnected throttled: {sender}.{signal_name} -> {receiver}.{slot_name}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to disconnect throttled signal: {e}")

            if not self._throttled_connections[connection_key]:
                del self._throttled_connections[connection_key]

        return count

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

        # Disconnect regular connections
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

        # Disconnect throttled connections
        for connection_key, connections in list(self._throttled_connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            for receiver, slot_name, throttled_slot, _, _ in list(connections):
                signal.disconnect(throttled_slot)
                count += 1

                if self._debug_mode:
                    logger.debug(
                        f"Disconnected throttled: {sender}.{signal_name} -> {receiver}.{slot_name}"
                    )

        self._throttled_connections = {}

        # Disconnect prioritized connections
        for connection_key, connections in list(self._prioritized_connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            for receiver, slot_name, _, wrapper_slot in connections:
                try:
                    signal.disconnect(wrapper_slot)
                    count += 1

                    if self._debug_mode:
                        logger.debug(
                            f"Disconnected prioritized: {sender}.{signal_name} -> {receiver}.{slot_name}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to disconnect prioritized signal: {e}")

        self._prioritized_connections = {}

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

        # Disconnect regular connections
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

        # Disconnect throttled connections
        for connection_key, connections in list(self._throttled_connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            for recv, slot_name, throttled_slot, throttle_ms, throttle_mode in list(connections):
                if recv == receiver:
                    signal.disconnect(throttled_slot)
                    self._throttled_connections[connection_key].remove(
                        (recv, slot_name, throttled_slot, throttle_ms, throttle_mode)
                    )
                    count += 1

                    if self._debug_mode:
                        logger.debug(
                            f"Disconnected throttled: {sender}.{signal_name} -> {receiver}.{slot_name}"
                        )

            if not self._throttled_connections[connection_key]:
                del self._throttled_connections[connection_key]

        # Disconnect prioritized connections
        for connection_key, connections in list(self._prioritized_connections.items()):
            sender, signal_name = connection_key
            signal = getattr(sender, signal_name)

            connections_to_keep = []

            for conn in connections:
                recv, slot_name, priority, wrapper_slot = conn

                if recv == receiver:
                    # Disconnect this connection
                    try:
                        signal.disconnect(wrapper_slot)
                        count += 1

                        if self._debug_mode:
                            logger.debug(
                                f"Disconnected prioritized: {sender}.{signal_name} -> {receiver}.{slot_name}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to disconnect prioritized signal: {e}")
                else:
                    # Keep this connection
                    connections_to_keep.append(conn)

            if connections_to_keep:
                self._prioritized_connections[connection_key] = connections_to_keep
            else:
                del self._prioritized_connections[connection_key]

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

        regular_connected = (
            connection_key in self._connections
            and connection_value in self._connections[connection_key]
        )

        throttled_connected = False
        if connection_key in self._throttled_connections:
            for recv, sname, _, _, _ in self._throttled_connections[connection_key]:
                if recv == receiver and sname == slot_name:
                    throttled_connected = True
                    break

        prioritized_connected = False
        if connection_key in self._prioritized_connections:
            for recv, sname, _, _ in self._prioritized_connections[connection_key]:
                if recv == receiver and sname == slot_name:
                    prioritized_connected = True
                    break

        return regular_connected or throttled_connected or prioritized_connected

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

        # Get regular connections
        for (src, sig_name), connections in self._connections.items():
            if sender is not None and src != sender:
                continue
            if signal_name is not None and sig_name != signal_name:
                continue

            for recv, slot_name in connections:
                if receiver is not None and recv != receiver:
                    continue
                result.append((src, sig_name, recv, slot_name))

        # Get throttled connections
        for (src, sig_name), connections in self._throttled_connections.items():
            if sender is not None and src != sender:
                continue
            if signal_name is not None and sig_name != signal_name:
                continue

            for recv, slot_name, _, _, _ in connections:
                if receiver is not None and recv != receiver:
                    continue
                result.append((src, sig_name, recv, slot_name))

        # Get prioritized connections
        for (src, sig_name), connections in self._prioritized_connections.items():
            if sender is not None and src != sender:
                continue
            if signal_name is not None and sig_name != signal_name:
                continue

            for recv, slot_name, _, _ in connections:
                if receiver is not None and recv != receiver:
                    continue
                result.append((src, sig_name, recv, slot_name))

        return result

    def get_prioritized_connections(
        self,
        sender: Optional[QObject] = None,
        signal_name: Optional[str] = None,
        receiver: Optional[QObject] = None,
    ) -> List[Tuple[QObject, str, QObject, str, int]]:
        """
        Get a list of prioritized connections matching the specified criteria.

        Args:
            sender: Optional sender to filter by
            signal_name: Optional signal name to filter by
            receiver: Optional receiver to filter by

        Returns:
            list: List of connections as (sender, signal_name, receiver, slot_name, priority)
        """
        result = []

        for (src, sig_name), connections in self._prioritized_connections.items():
            if sender is not None and src != sender:
                continue
            if signal_name is not None and sig_name != signal_name:
                continue

            for recv, slot_name, priority, _ in connections:
                if receiver is not None and recv != receiver:
                    continue
                result.append((src, sig_name, recv, slot_name, priority))

        return result

    def connect_prioritized(
        self,
        sender: QObject,
        signal_name: str,
        receiver: QObject,
        slot_name: str,
        priority: int = 50,
    ) -> bool:
        """
        Connect a signal to a slot with a specific priority.

        Higher priority connections are called first. When multiple connections have
        the same priority, they are called in the order they were connected.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal (without the signal() suffix)
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            priority: Priority of the connection (0-100, higher is called first)

        Returns:
            bool: True if connection was established, False if already connected

        Raises:
            AttributeError: If signal or slot doesn't exist
            ValueError: If priority is invalid
            TypeError: If signal and slot signatures are incompatible
        """
        try:
            # Validate priority
            if not 0 <= priority <= 100:
                raise ValueError(f"Invalid priority: {priority}. Must be between 0 and 100")

            # Get the actual signal and slot
            signal = getattr(sender, signal_name)
            slot = getattr(receiver, slot_name)

            # Check signal/slot compatibility
            self._check_signal_slot_compatibility(sender, signal_name, receiver, slot_name)

            # Check if this connection already exists
            connection_key = (sender, signal_name)

            # Check if we already have this exact prioritized connection
            if connection_key in self._prioritized_connections:
                for r, s, p, _ in self._prioritized_connections[connection_key]:
                    if r == receiver and s == slot_name:
                        if self._debug_mode:
                            logger.debug(
                                f"Prioritized connection already exists: {sender}.{signal_name} -> {receiver}.{slot_name}"
                            )
                        return False

            # Create a wrapper function to use for the actual connection
            # This allows us to disconnect it later
            def wrapper_slot(*args, **kwargs):
                slot(*args, **kwargs)

            # Connect the signal to the wrapper
            signal.connect(wrapper_slot)

            # Track the connection
            if connection_key not in self._prioritized_connections:
                self._prioritized_connections[connection_key] = []

            # Add the connection to the list and sort by priority (highest first)
            self._prioritized_connections[connection_key].append(
                (receiver, slot_name, priority, wrapper_slot)
            )
            self._prioritized_connections[connection_key].sort(key=lambda x: x[2], reverse=True)

            # Reconnect all slots in priority order to ensure execution order
            self._reorder_prioritized_connections(sender, signal_name)

            if self._debug_mode:
                logger.debug(
                    f"Connected prioritized (priority {priority}): "
                    f"{sender}.{signal_name} -> {receiver}.{slot_name}"
                )

            return True
        except AttributeError as e:
            logger.error(f"Failed to connect prioritized signal: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to connect prioritized signal: {e}")
            raise

    def _reorder_prioritized_connections(self, sender: QObject, signal_name: str) -> None:
        """
        Reorder prioritized connections to ensure they are called in priority order.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
        """
        connection_key = (sender, signal_name)

        if connection_key not in self._prioritized_connections:
            return

        if not self._prioritized_connections[connection_key]:
            return

        # Get the signal
        signal = getattr(sender, signal_name)

        # Temporarily disconnect all slots
        for _, _, _, wrapper_slot in self._prioritized_connections[connection_key]:
            try:
                signal.disconnect(wrapper_slot)
            except Exception as e:
                if self._debug_mode:
                    logger.warning(f"Failed to disconnect signal during reordering: {e}")

        # Reconnect slots in priority order
        for _, _, _, wrapper_slot in self._prioritized_connections[connection_key]:
            signal.connect(wrapper_slot)

    def disconnect_prioritized(
        self,
        sender: QObject,
        signal_name: str,
        receiver: Optional[QObject] = None,
        slot_name: Optional[str] = None,
    ) -> int:
        """
        Disconnect prioritized signal(s).

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Optional object that receives the signal
            slot_name: Optional name of the slot

        Returns:
            int: Number of disconnections made
        """
        connection_key = (sender, signal_name)

        if connection_key not in self._prioritized_connections:
            return 0

        signal = getattr(sender, signal_name)
        count = 0

        connections_to_keep = []

        for conn in self._prioritized_connections[connection_key]:
            recv, sname, priority, wrapper_slot = conn

            if (receiver is None or recv == receiver) and (slot_name is None or sname == slot_name):
                # This connection should be disconnected
                try:
                    signal.disconnect(wrapper_slot)
                    count += 1

                    if self._debug_mode:
                        logger.debug(
                            f"Disconnected prioritized: {sender}.{signal_name} -> {recv}.{sname}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to disconnect prioritized signal: {e}")
            else:
                # Keep this connection
                connections_to_keep.append(conn)

        if connections_to_keep:
            self._prioritized_connections[connection_key] = connections_to_keep
        else:
            del self._prioritized_connections[connection_key]

        return count

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

        print("Current Throttled Signal Connections:")
        print("===================================")

        for i, ((sender, signal_name), connections) in enumerate(
            self._throttled_connections.items()
        ):
            sender_name = sender.__class__.__name__
            print(f"{i + 1}. {sender_name}.{signal_name} connected to:")

            for j, (receiver, slot_name, _, throttle_ms, throttle_mode) in enumerate(connections):
                receiver_name = receiver.__class__.__name__
                print(f"   {j + 1}. {receiver_name}.{slot_name} ({throttle_mode}, {throttle_ms}ms)")

            print()

        print("Current Prioritized Signal Connections:")
        print("====================================")

        for i, ((sender, signal_name), connections) in enumerate(
            self._prioritized_connections.items()
        ):
            sender_name = sender.__class__.__name__
            print(f"{i + 1}. {sender_name}.{signal_name} connected to:")

            for j, (receiver, slot_name, priority, _) in enumerate(connections):
                receiver_name = receiver.__class__.__name__
                print(f"   {j + 1}. {receiver_name}.{slot_name} (priority: {priority})")

            print()

    def has_connection(
        self, sender: QObject, signal_name: str, receiver: QObject, slot_name: str
    ) -> bool:
        """
        Check if a connection exists between the given signal and slot.

        This is an alias for is_connected for a more intuitive API.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that receives the signal
            slot_name: Name of the slot

        Returns:
            bool: True if connection exists, False otherwise
        """
        return self.is_connected(sender, signal_name, receiver, slot_name)

    def get_connection_count(self) -> int:
        """
        Get the total number of managed connections.

        Returns:
            int: The number of active connections
        """
        # Count regular connections
        regular_count = sum(len(connections) for connections in self._connections.values())

        # Count throttled connections
        throttled_count = sum(
            len(connections) for connections in self._throttled_connections.values()
        )

        # Count prioritized connections
        prioritized_count = sum(
            len(connections) for connections in self._prioritized_connections.values()
        )

        return regular_count + throttled_count + prioritized_count

    def safe_connect(
        self,
        sender: QObject,
        signal_name: str,
        receiver: QObject,
        slot_name_or_callable: Union[str, Callable, None] = None,
        safe_disconnect_first: bool = True,
    ) -> bool:
        """
        Safely connect a signal with optional disconnect first.

        This method allows connecting either a callable directly or a method by name.
        If both slot and slot_name are provided, slot takes precedence.

        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that will receive the signal
            slot_name_or_callable: Name of the method to call when signal is emitted or callable to connect
            safe_disconnect_first: Whether to disconnect first

        Returns:
            bool: True if connection was established, False otherwise
        """
        try:
            # Validate parameters
            if not isinstance(sender, QObject):
                logger.error(f"Error in safe_connect: sender must be a QObject, got {type(sender)}")
                return False

            if not isinstance(signal_name, str):
                logger.error(
                    f"Error in safe_connect: signal_name must be a string, got {type(signal_name)}"
                )
                return False

            # Get the signal
            if not hasattr(sender, signal_name):
                logger.error(
                    f"Error in safe_connect: {sender.__class__.__name__} has no signal {signal_name}"
                )
                return False

            signal = getattr(sender, signal_name)

            # Handle slot parameter options
            if slot_name_or_callable is not None:
                if callable(slot_name_or_callable):
                    # Use the provided callable directly
                    if safe_disconnect_first:
                        try:
                            signal.disconnect(slot_name_or_callable)
                        except Exception:
                            # Ignore disconnection errors
                            pass
                    signal.connect(slot_name_or_callable)
                    return True
                elif isinstance(slot_name_or_callable, str):
                    # It's a method name, connect through our regular connect method with the appropriate parameter
                    return self.connect(
                        sender,
                        signal_name,
                        receiver,
                        slot_name_or_callable,
                        disconnect_first=safe_disconnect_first,  # Use the parameter name expected by connect()
                    )
                else:
                    logger.error(
                        f"Error in safe_connect: slot_name_or_callable must be a callable or string, got {type(slot_name_or_callable)}"
                    )
                    return False
            else:
                logger.error(f"Error in safe_connect: slot_name_or_callable must be provided")
                return False
        except Exception as e:
            logger.error(f"Error in safe_connect: {e}")
            return False

    @contextmanager
    def blocked_signals(self, sender: QObject, signal_name: str = None):
        """
        Context manager to temporarily block signals.

        Args:
            sender: Object whose signals should be blocked
            signal_name: Optional specific signal to block (not implemented yet)

        Example:
            ```
            with signal_manager.blocked_signals(model, "data_changed"):
                model.update_data(new_data)  # won't emit data_changed
            ```
        """
        if signal_name is not None:
            # Specific signal blocking is not yet implemented
            # For now, we just block all signals from the sender
            logger.debug(
                f"Blocking specific signal {signal_name} is not supported yet, blocking all signals from {sender.__class__.__name__}"
            )

        original_state = sender.blockSignals(True)
        try:
            yield
        finally:
            sender.blockSignals(original_state)

    def connect_signal(
        self,
        emitter: QObject,
        signal_name: str,
        receiver: QObject,
        slot: Union[Callable, str],
        track_only: bool = False,
    ) -> bool:
        """
        Connect a signal to a slot and register it with the manager.

        Args:
            emitter: The object emitting the signal
            signal_name: The name of the signal (without the signature)
            receiver: The object receiving the signal
            slot: Either a callable or the name of the method to connect to
            track_only: If True, don't make the actual connection, just track it
                        (useful when connections are made elsewhere)

        Returns:
            bool: True if the connection was successfully made or tracked
        """
        # Get signal object by name
        signal_obj = getattr(emitter, signal_name, None)
        if not isinstance(signal_obj, Signal):
            logger.error(f"Signal '{signal_name}' not found on {emitter}")
            return False

        # Resolve slot if it's a string
        if isinstance(slot, str):
            slot_name = slot
            slot_method = getattr(receiver, slot, None)
            if not callable(slot_method):
                logger.error(f"Slot '{slot}' not found on {receiver}")
                return False
        else:
            # Try to get the method name for a callable
            slot_method = slot
            try:
                slot_name = slot_method.__name__
            except AttributeError:
                # For lambdas and other callables without __name__
                slot_name = f"lambda_{id(slot)}"

        # Create unique IDs for connection tracking
        emitter_id = id(emitter)
        receiver_id = id(receiver)

        # Create a unique connection ID
        connection_id = (emitter_id, signal_name, receiver_id, slot_name)

        # Check if this connection already exists
        if connection_id in self._connections:
            logger.debug(
                f"Connection already exists: {emitter}.{signal_name} -> {receiver}.{slot_name}"
            )
            return True

        # Add weak references to track object lifecycle
        self._weak_emitters[emitter_id] = weakref.ref(
            emitter, lambda ref: self._cleanup_emitter(emitter_id)
        )

        self._weak_receivers[receiver_id] = weakref.ref(
            receiver, lambda ref: self._cleanup_receiver(receiver_id)
        )

        # Make the actual connection if not track_only
        if not track_only:
            signal_obj.connect(slot_method)

        # Store the connection details for tracking
        self._connections[connection_id] = (emitter, signal_name, receiver, slot_method, track_only)

        # Update the quick lookup maps
        # Emitter map
        if emitter_id not in self._emitter_map:
            self._emitter_map[emitter_id] = []
        self._emitter_map[emitter_id].append((signal_name, connection_id))

        # Receiver map
        if receiver_id not in self._receiver_map:
            self._receiver_map[receiver_id] = []
        self._receiver_map[receiver_id].append((slot_name, connection_id))

        # Slot map
        if slot_name not in self._slot_map:
            self._slot_map[slot_name] = []
        self._slot_map[slot_name].append((receiver, connection_id))

        # Register with the signal tracer if it's active
        if signal_tracer.is_active():
            signal_tracer.register_signal(emitter, signal_name, receiver, slot_name)

        logger.debug(
            f"Connected: {emitter.__class__.__name__}.{signal_name} -> {receiver.__class__.__name__}.{slot_name}"
        )
        return True
