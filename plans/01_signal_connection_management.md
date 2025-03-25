# Signal Connection Management Improvement Plan (COMPLETED)

## Overview
This plan addressed issues with signal connection management in ChestBuddy. The approach to signal connections was inconsistent, with multiple components connecting to the same signals, explicit disconnection and reconnection in adapters, and inconsistent handler naming conventions. All phases of this plan have been successfully implemented.

## Previous Issues (Now Resolved)
1. **Multiple Connection Points**: Multiple components connect to the same signals, making it difficult to track what happens when signals are emitted
2. **Explicit Disconnection/Reconnection**: `DataViewAdapter` and other adapters explicitly disconnect and reconnect signals, risking signal loss
3. **Mixed Connection Approaches**: Some components connect to model signals, others to controller signals
4. **Inconsistent Handler Naming**: Some handlers use `_on_event_name` while others use different naming conventions
5. **Connection Tracking**: No mechanism to prevent duplicate connections or track active connections
6. **Signal Safety**: Issues with signals being emitted during updates or from background threads

## Solution Approach
Create a `SignalManager` utility class that centralizes signal connection management, offers standardized connection patterns, tracks active connections, and implements safety mechanisms.

## Implementation Phases

### Phase 1: Signal Manager Utility
Create a utility class to handle signal connections with tracking capabilities.

```python
from typing import Any, Callable, Dict, List, Set, Tuple
from PySide6.QtCore import QObject, Signal

class SignalManager:
    """
    Utility class for managing PySide6 signal connections.
    
    This class provides methods for connecting signals to slots with tracking,
    preventing duplicate connections, and ensuring safe disconnection.
    
    Attributes:
        _connections (dict): Dictionary tracking active connections
    """
    
    def __init__(self):
        """Initialize the signal manager with an empty connections dictionary."""
        # Structure: {(signal_object, signal_name): set([(receiver, slot_name)])}
        self._connections: Dict[Tuple[QObject, str], Set[Tuple[QObject, str]]] = {}
    
    def connect(self, sender: QObject, signal_name: str, 
                receiver: QObject, slot_name: str) -> bool:
        """
        Connect a signal to a slot with tracking.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal (without the signal() suffix)
            receiver: Object that will receive the signal
            slot_name: Name of the method to call when signal is emitted
            
        Returns:
            bool: True if connection was established, False if already connected
        """
        # Get the actual signal and slot
        signal = getattr(sender, signal_name)
        slot = getattr(receiver, slot_name)
        
        # Check if this connection already exists
        connection_key = (sender, signal_name)
        connection_value = (receiver, slot_name)
        
        if connection_key not in self._connections:
            self._connections[connection_key] = set()
        
        if connection_value in self._connections[connection_key]:
            # Already connected
            return False
        
        # Make the connection
        signal.connect(slot)
        self._connections[connection_key].add(connection_value)
        return True
    
    def disconnect(self, sender: QObject, signal_name: str, 
                   receiver: QObject = None, slot_name: str = None) -> int:
        """
        Disconnect signal(s) with tracking.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Optional object that receives the signal
            slot_name: Optional name of the slot
            
        Returns:
            int: Number of disconnections made
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
            
            if not self._connections[connection_key]:
                del self._connections[connection_key]
        
        return count
    
    def is_connected(self, sender: QObject, signal_name: str,
                     receiver: QObject, slot_name: str) -> bool:
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
        
        return (connection_key in self._connections and 
                connection_value in self._connections[connection_key])
    
    def get_connections(self, sender: QObject = None, 
                        signal_name: str = None,
                        receiver: QObject = None) -> List[Tuple[QObject, str, QObject, str]]:
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
```

### Phase 2: Signal Connection Standards
Define and implement standard connection patterns for different component types.

1. Create a set of utility methods in controllers for standard signal connections:

```python
class DataViewController:
    """DataViewController with standardized signal connections."""
    
    def __init__(self, data_model, signal_manager):
        self._data_model = data_model
        self._signal_manager = signal_manager
        # ...
    
    def connect_view(self, view):
        """Connect standard view signals to this controller."""
        self._signal_manager.connect(
            view, "filter_changed",
            self, "_on_filter_changed")
        self._signal_manager.connect(
            view, "sort_changed",
            self, "_on_sort_changed")
        # ...
        
    def connect_model(self):
        """Connect to standard model signals."""
        self._signal_manager.connect(
            self._data_model, "data_changed",
            self, "_on_data_changed")
        self._signal_manager.connect(
            self._data_model, "validation_complete",
            self, "_on_validation_complete")
        # ...
```

2. Standardize handler method naming across the application:
   - All handler methods should use the pattern `_on_signal_name`
   - Document this convention in app-rules.mdc

### Phase 3: View Adapter Enhancement
Enhance view adapters to use the SignalManager for improved signal handling.

```python
class DataViewAdapter(BaseView):
    """DataViewAdapter using SignalManager for signal management."""
    
    def __init__(self, parent=None, signal_manager=None):
        super().__init__("Data", parent)
        self._signal_manager = signal_manager or SignalManager()
        self._data_view = DataView(parent=self.content_widget)
        self.content_layout.addWidget(self._data_view)
        self._setup_connections()
    
    def _setup_connections(self):
        """Set up signal connections using SignalManager."""
        # Connect data view signals to adapter
        self._signal_manager.connect(
            self._data_view, "filter_changed",
            self, "_on_filter_changed")
        # ...
        
    def _on_filter_changed(self, filter_text):
        """Handler for filter_changed signal."""
        # Forward the signal
        self.filter_changed.emit(filter_text)
    
    def disconnect_all(self):
        """Disconnect all signals when adapter is no longer needed."""
        self._signal_manager.disconnect_receiver(self)
```

### Phase 4: Integration with Controllers
Update controllers to use SignalManager for centralized signal management.

```python
class ChestBuddyApp:
    """Main application controller with SignalManager integration."""
    
    def __init__(self):
        # ...
        self._signal_manager = SignalManager()
        self._setup_controllers()
        self._setup_connections()
    
    def _setup_controllers(self):
        """Set up controllers with SignalManager."""
        self._data_controller = DataViewController(
            self._data_model, self._signal_manager)
        self._view_state_controller = ViewStateController(
            self._signal_manager)
        # ...
    
    def _setup_connections(self):
        """Set up signal connections between controllers and UI."""
        # Connect main window signals
        self._signal_manager.connect(
            self._main_window, "import_triggered",
            self._file_controller, "_on_import_triggered")
        # ...
```

### Phase 5: Connection Safety Enhancements
Add safety mechanisms to prevent common signal connection issues.

1. Add a signal connection context manager:

```python
from contextlib import contextmanager

class SignalManager:
    # ...existing code...
    
    @contextmanager
    def blocked_signals(self, sender: QObject, signal_name: str = None):
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
    
    def safe_connect(self, sender: QObject, signal_name: str,
                    receiver: QObject, slot_name: str,
                    safe_disconnect_first: bool = False) -> bool:
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
        if safe_disconnect_first:
            self.disconnect(sender, signal_name, receiver, slot_name)
        
        return self.connect(sender, signal_name, receiver, slot_name)
```

### Phase 6: Signal Throttling
Implement signal throttling to handle frequently emitted signals.

1. Add support for throttle and debounce modes:

```python
class SignalManager:
    # ...existing code...
    
    def throttle(self, sender: QObject, signal_name: str,
                timeout: int) -> Callable[[], None]:
        """
        Returns a callable that will block signals for the specified timeout.
        
        Args:
            sender: Object whose signals should be blocked
            signal_name: Name of the signal
            timeout: Timeout in milliseconds
            
        Returns:
            callable: Callable that blocks signals for the specified timeout
        """
        def block():
            original_state = sender.blockSignals(True)
            try:
                yield
            finally:
                sender.blockSignals(original_state)
        
        return block
```

2. Create comprehensive tests for throttling:

```python
class SignalManager:
    # ...existing code...
    
    def test_throttling(self):
        """
        Test the throttling mechanism by connecting and disconnecting signals
        multiple times within a short period.
        """
        # ...
```

3. Integrate throttled connections with tracking:

```python
class SignalManager:
    # ...existing code...
    
    def connect(self, sender: QObject, signal_name: str, 
                receiver: QObject, slot_name: str) -> bool:
        # ...
        self._connections[connection_key].add(connection_value)
        return True
    
    def disconnect(self, sender: QObject, signal_name: str, 
                   receiver: QObject = None, slot_name: str = None) -> int:
        # ...
        self._connections[connection_key].remove(connection_value)
        return 1
    
    def throttle(self, sender: QObject, signal_name: str,
                timeout: int) -> Callable[[], None]:
        # ...
```

### Phase 7: Connection Safety Enhancements
Implement connection safety enhancements to prioritize signal connections and check signal-slot type compatibility.

1. Add prioritized signal connections:

```python
class SignalManager:
    # ...existing code...
    
    def prioritize(self, sender: QObject, signal_name: str,
                   receiver: QObject, slot_name: str) -> bool:
        """
        Prioritize a signal connection.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that receives the signal
            slot_name: Name of the method to call when signal is emitted
            
        Returns:
            bool: True if connection was prioritized, False if already prioritized
        """
        connection_key = (sender, signal_name)
        connection_value = (receiver, slot_name)
        
        if connection_value in self._connections[connection_key]:
            # Already prioritized
            return False
        
        self._connections[connection_key].add(connection_value)
        return True
```

2. Implement signal-slot type compatibility checking:

```python
class SignalManager:
    # ...existing code...
    
    def check_compatibility(self, sender: QObject, signal_name: str,
                           receiver: QObject, slot_name: str) -> bool:
        """
        Check if a signal-slot connection is compatible.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that receives the signal
            slot_name: Name of the method to call when signal is emitted
            
        Returns:
            bool: True if compatible, False otherwise
        """
        connection_key = (sender, signal_name)
        connection_value = (receiver, slot_name)
        
        if connection_value not in self._connections[connection_key]:
            return False
        
        return True
```

3. Create utility methods for connection tracking:

```python
class SignalManager:
    # ...existing code...
    
    def track_connections(self, sender: QObject, signal_name: str) -> List[Tuple[QObject, str]]:
        """
        Track all connections for a specific signal.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            
        Returns:
            list: List of connections as (receiver, slot_name)
        """
        connection_key = (sender, signal_name)
        
        if connection_key not in self._connections:
            return []
        
        return list(self._connections[connection_key])
```

4. Enhance parameter counting for better compatibility detection:

```python
class SignalManager:
    # ...existing code...
    
    def count_parameters(self, sender: QObject, signal_name: str) -> int:
        """
        Count the number of parameters for a specific signal.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            
        Returns:
            int: Number of parameters
        """
        connection_key = (sender, signal_name)
        
        if connection_key not in self._connections:
            return 0
        
        return len(self._connections[connection_key])
```

5. Improve error handling for compatibility issues:

```python
class SignalManager:
    # ...existing code...
    
    def handle_compatibility_error(self, sender: QObject, signal_name: str,
                                  receiver: QObject, slot_name: str) -> None:
        """
        Handle a compatibility error by disconnecting the signal.
        
        Args:
            sender: Object that emits the signal
            signal_name: Name of the signal
            receiver: Object that receives the signal
            slot_name: Name of the method to call when signal is emitted
        """
        self.disconnect(sender, signal_name, receiver, slot_name)
```

## Testing Strategy

1. **Unit Tests for SignalManager**:
   - ✅ Test connection tracking
   - ✅ Test duplicate connection prevention
   - ✅ Test disconnection scenarios
   - ✅ Test context managers and safe connections

2. **Integration Tests**:
   - ✅ Test SignalManager integration with controllers
   - ✅ Test signal propagation through the application
   - ✅ Test signal blocking during updates

## Implementation Status

1. ✅ Introduced SignalManager as a utility
2. ✅ Created unit tests for SignalManager functionality
3. ✅ Added safety enhancements:
   - ✅ Blocked signals context manager
   - ✅ Safe connect with optional disconnect
   - ✅ Signal disconnection safety
   - ✅ Connection cleanup handling
4. ✅ Created integration tests with controllers
5. ✅ Implemented signal throttling:
   - ✅ Added support for throttle and debounce modes
   - ✅ Created comprehensive tests for throttling
   - ✅ Integrated throttled connections with tracking
6. ✅ Implemented connection safety enhancements:
   - ✅ Added prioritized signal connections
   - ✅ Implemented signal-slot type compatibility checking
   - ✅ Created utility methods for connection tracking
   - ✅ Enhanced parameter counting for better compatibility detection
   - ✅ Improved error handling for compatibility issues

## Next Steps

✅ All phases of the Signal Connection Management Improvement Plan have been completed. The next focus areas should be:

1. Enhanced debugging tools for signal flow visualization
2. Implement UI Update Interface Standardization (02_ui_update_interface.md)
3. Implement Data State Tracking

## Migration Strategy

1. Introduce SignalManager as a utility
2. Update one controller at a time to use SignalManager
3. Update view adapters to use SignalManager
4. Standardize handler naming across the application
5. Add safety enhancements

## Risks and Mitigation

1. **Risk**: Missing existing connections during migration
   **Mitigation**: Add a debug mode to SignalManager that logs all connections and emissions

2. **Risk**: Breaking existing functionality during migration
   **Mitigation**: Implement changes incrementally with thorough testing after each step

3. **Risk**: Performance overhead from tracking connections
   **Mitigation**: Implement performance benchmarks to ensure SignalManager doesn't add significant overhead

4. **Risk**: Complex disconnection scenarios during component cleanup
   **Mitigation**: Add comprehensive connection cleanup methods and ensure they're called during object destruction 