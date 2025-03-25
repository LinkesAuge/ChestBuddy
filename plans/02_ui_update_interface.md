# UI Update Interface Standardization Plan

## Overview
This plan addresses issues with inconsistent UI update patterns in ChestBuddy. Currently, each view implements its own update method without standardization, controllers must check for multiple method names, and there is redundant debouncing logic across components.

## Current Issues
1. **Inconsistent Update Methods**: Each view implements its own method (`_update_view`, `populate_table`, etc.) without standardization
2. **Method Name Checking**: Controllers need to check for multiple method names in components
3. **Redundant Debouncing**: Multiple components implement similar debouncing logic for updates
4. **No Common Interface**: Views lack a common interface for updates, making controller logic more complex
5. **State Tracking Duplication**: Components individually track whether they need updates
6. **Update Triggering**: Unclear when and how updates should be triggered

## Solution Approach
Create an `IUpdatable` interface with standardized methods for UI updates, centralize debouncing logic, and implement consistent update patterns across all view components.

## Implementation Phases

### Phase 1: Define the IUpdatable Interface
Create an interface class that defines the standard update methods.

```python
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from PySide6.QtCore import QObject

@runtime_checkable
class IUpdatable(Protocol):
    """
    Protocol defining the standard interface for updatable UI components.
    
    This protocol defines methods that all updatable UI components should implement
    to ensure consistent update patterns across the application.
    """
    
    def refresh(self) -> None:
        """
        Refresh the component's display with current data.
        
        This method should update the component's visual representation with
        the latest data, without changing the component's state.
        """
        ...
    
    def update(self, data: Optional[Any] = None) -> None:
        """
        Update the component with new data.
        
        This method should update both the component's internal state and
        visual representation with the provided data.
        
        Args:
            data: Optional new data to update the component with
        """
        ...
    
    def populate(self, data: Optional[Any] = None) -> None:
        """
        Completely populate the component with the provided data.
        
        This method should fully populate the component from scratch,
        replacing any existing content.
        
        Args:
            data: Optional data to populate the component with
        """
        ...
    
    def needs_update(self) -> bool:
        """
        Check if the component needs an update.
        
        Returns:
            bool: True if the component needs to be updated, False otherwise
        """
        ...
    
    def reset(self) -> None:
        """
        Reset the component to its initial state.
        
        This method should clear all data and return the component to its
        default state.
        """
        ...
```

Create a base class implementing this interface for views to extend:

```python
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, Signal

class UpdatableComponent(QObject):
    """
    Base class for updatable UI components implementing the IUpdatable interface.
    
    This class provides default implementations of the IUpdatable methods and
    standardized update tracking.
    
    Attributes:
        update_requested (Signal): Signal emitted when an update is requested
        _update_state (dict): Dictionary tracking update state
    """
    
    update_requested = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the updatable component."""
        super().__init__(parent)
        self._update_state: Dict[str, Any] = {
            "last_update_time": 0,
            "needs_update": True,
            "update_pending": False,
            "data_hash": None
        }
    
    def refresh(self) -> None:
        """
        Refresh the component's display with current data.
        
        Default implementation marks the component as needing an update
        and emits the update_requested signal.
        """
        self._update_state["needs_update"] = True
        self.update_requested.emit()
    
    def update(self, data: Optional[Any] = None) -> None:
        """
        Update the component with new data.
        
        Default implementation updates internal state and calls _do_update.
        
        Args:
            data: Optional new data to update the component with
        """
        self._update_state["needs_update"] = True
        self._do_update(data)
    
    def populate(self, data: Optional[Any] = None) -> None:
        """
        Completely populate the component with the provided data.
        
        Default implementation updates internal state and calls _do_populate.
        
        Args:
            data: Optional data to populate the component with
        """
        self._update_state["needs_update"] = True
        self._do_populate(data)
    
    def needs_update(self) -> bool:
        """
        Check if the component needs an update.
        
        Returns:
            bool: True if the component needs to be updated, False otherwise
        """
        return self._update_state["needs_update"]
    
    def reset(self) -> None:
        """
        Reset the component to its initial state.
        
        Default implementation updates internal state and calls _do_reset.
        """
        self._update_state["needs_update"] = True
        self._do_reset()
    
    def _do_update(self, data: Optional[Any] = None) -> None:
        """
        Implement component-specific update logic.
        
        This method should be overridden by subclasses to implement
        component-specific update logic.
        
        Args:
            data: Optional new data to update the component with
        """
        pass
    
    def _do_populate(self, data: Optional[Any] = None) -> None:
        """
        Implement component-specific populate logic.
        
        This method should be overridden by subclasses to implement
        component-specific populate logic.
        
        Args:
            data: Optional data to populate the component with
        """
        pass
    
    def _do_reset(self) -> None:
        """
        Implement component-specific reset logic.
        
        This method should be overridden by subclasses to implement
        component-specific reset logic.
        """
        pass
```

### Phase 2: Create an UpdateManager Utility
Create a utility class to centralize debouncing and update scheduling.

```python
import time
from typing import Callable, Dict, Optional, Set
from PySide6.QtCore import QObject, QTimer, Signal

class UpdateManager(QObject):
    """
    Utility class for managing UI component updates.
    
    This class provides methods for scheduling updates with debouncing,
    batching updates, and tracking update dependencies.
    
    Attributes:
        update_scheduled (Signal): Signal emitted when an update is scheduled
        update_completed (Signal): Signal emitted when all updates are completed
    """
    
    update_scheduled = Signal(object)  # Component that needs update
    update_completed = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the update manager."""
        super().__init__(parent)
        self._update_timers: Dict[IUpdatable, QTimer] = {}
        self._pending_updates: Set[IUpdatable] = set()
        self._debounce_intervals: Dict[IUpdatable, int] = {}
        self._update_dependencies: Dict[IUpdatable, Set[IUpdatable]] = {}
        self._global_timer = QTimer(self)
        self._global_timer.setSingleShot(True)
        self._global_timer.timeout.connect(self._process_pending_updates)
    
    def schedule_update(self, component: IUpdatable, 
                        debounce_ms: int = 100) -> None:
        """
        Schedule an update for a component with debouncing.
        
        Args:
            component: The component to update
            debounce_ms: Debounce interval in milliseconds
        """
        self._debounce_intervals[component] = debounce_ms
        self._pending_updates.add(component)
        
        # Start or restart the global timer
        self._global_timer.start(50)  # Process updates every 50ms
    
    def immediate_update(self, component: IUpdatable) -> None:
        """
        Update a component immediately without debouncing.
        
        Args:
            component: The component to update
        """
        if component in self._pending_updates:
            self._pending_updates.remove(component)
        
        if hasattr(component, 'update') and callable(component.update):
            component.update()
    
    def add_dependency(self, component: IUpdatable, 
                       dependency: IUpdatable) -> None:
        """
        Add an update dependency between components.
        
        When 'dependency' is updated, 'component' will also be updated.
        
        Args:
            component: The component that depends on another
            dependency: The component that triggers an update
        """
        if dependency not in self._update_dependencies:
            self._update_dependencies[dependency] = set()
        
        self._update_dependencies[dependency].add(component)
    
    def remove_dependency(self, component: IUpdatable, 
                          dependency: IUpdatable) -> None:
        """
        Remove an update dependency between components.
        
        Args:
            component: The component that depends on another
            dependency: The component to remove dependency from
        """
        if dependency in self._update_dependencies:
            if component in self._update_dependencies[dependency]:
                self._update_dependencies[dependency].remove(component)
            
            if not self._update_dependencies[dependency]:
                del self._update_dependencies[dependency]
    
    def _process_pending_updates(self) -> None:
        """Process all pending updates."""
        current_time = time.time() * 1000  # Current time in ms
        
        # Create a copy of pending updates to avoid modification during iteration
        components_to_update = list(self._pending_updates)
        
        for component in components_to_update:
            last_update = component._update_state.get("last_update_time", 0)
            debounce_interval = self._debounce_intervals.get(component, 100)
            
            if current_time - last_update >= debounce_interval:
                self._pending_updates.remove(component)
                
                # Update the component
                if hasattr(component, 'update') and callable(component.update):
                    component.update()
                    component._update_state["last_update_time"] = current_time
                    
                    # Update dependencies
                    if component in self._update_dependencies:
                        for dep_component in self._update_dependencies[component]:
                            self.schedule_update(dep_component)
        
        # Continue processing if there are still pending updates
        if self._pending_updates:
            self._global_timer.start(50)
        else:
            self.update_completed.emit()
```

### Phase 3: Update View Adapters
Update all view adapters to implement the `IUpdatable` interface.

```python
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

class DataViewAdapter(UpdatableComponent, BaseView):
    """
    Adapter for DataView implementing the IUpdatable interface.
    
    This adapter wraps the original DataView component and provides
    standardized update methods.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the data view adapter."""
        UpdatableComponent.__init__(self)
        BaseView.__init__(self, "Data", parent)
        self._data_view = DataView(parent=self.content_widget)
        self.content_layout.addWidget(self._data_view)
        self._setup_connections()
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self._data_view.filter_changed.connect(self._on_filter_changed)
        # Other connections...
    
    def _do_update(self, data: Optional[Any] = None) -> None:
        """
        Update the data view with current data.
        
        Args:
            data: Optional data to update the view with
        """
        if hasattr(self._data_view, '_update_view'):
            self._data_view._update_view()
        self._update_state["needs_update"] = False
    
    def _do_populate(self, data: Optional[Any] = None) -> None:
        """
        Populate the data view with data.
        
        Args:
            data: Optional data to populate the view with
        """
        if hasattr(self._data_view, 'populate_table'):
            self._data_view.populate_table(data)
        self._update_state["needs_update"] = False
    
    def _do_reset(self) -> None:
        """Reset the data view to its initial state."""
        if hasattr(self._data_view, 'clear'):
            self._data_view.clear()
        self._update_state["needs_update"] = True
    
    def needs_update(self) -> bool:
        """
        Check if the view needs an update.
        
        Returns:
            bool: True if the view needs to be updated, False otherwise
        """
        # Implement custom logic to determine if update is needed
        # e.g., by comparing current data dimensions with previous
        if not hasattr(self, '_data_dimensions'):
            self._data_dimensions = (0, 0)
        
        # Get current data dimensions from the model
        data_model = self._get_data_model()
        if data_model is not None:
            current_dimensions = (
                len(data_model.get_data()),
                len(data_model.get_data().columns) if not data_model.get_data().empty else 0
            )
            
            if current_dimensions != self._data_dimensions:
                self._data_dimensions = current_dimensions
                return True
        
        return self._update_state["needs_update"]
    
    def _get_data_model(self) -> Optional[Any]:
        """Get the data model for this view."""
        # Implementation depends on how the app provides access to models
        # This is just a placeholder
        app = QApplication.instance()
        if hasattr(app, 'data_model'):
            return app.data_model
        return None
```

### Phase 4: Update Controllers
Update controllers to use the standardized update interface.

```python
from typing import Dict, List, Optional, Set
from PySide6.QtCore import QObject, Signal

class DataViewController(QObject):
    """
    Controller for data views using the standardized update interface.
    
    This controller manages data operations and coordinates updates
    to data views.
    """
    
    data_updated = Signal()
    
    def __init__(self, data_model, update_manager: UpdateManager):
        """
        Initialize the data view controller.
        
        Args:
            data_model: The data model to control
            update_manager: The update manager for scheduling UI updates
        """
        super().__init__()
        self._data_model = data_model
        self._update_manager = update_manager
        self._views: Set[IUpdatable] = set()
        self._setup_connections()
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self._data_model.data_changed.connect(self._on_data_changed)
        # Other connections...
    
    def register_view(self, view: IUpdatable) -> None:
        """
        Register a view with this controller.
        
        Args:
            view: The view to register
        """
        self._views.add(view)
    
    def unregister_view(self, view: IUpdatable) -> None:
        """
        Unregister a view from this controller.
        
        Args:
            view: The view to unregister
        """
        if view in self._views:
            self._views.remove(view)
    
    def _on_data_changed(self) -> None:
        """Handle data changed event."""
        # Schedule updates for all registered views
        for view in self._views:
            if view.needs_update():
                self._update_manager.schedule_update(view)
        
        self.data_updated.emit()
    
    def update_all_views(self) -> None:
        """Force update of all registered views."""
        for view in self._views:
            self._update_manager.immediate_update(view)
    
    def apply_filter(self, filter_text: str) -> None:
        """
        Apply a filter to the data model.
        
        Args:
            filter_text: The filter text to apply
        """
        # Apply filter to data model
        self._data_model.apply_filter(filter_text)
        
        # Data model should emit data_changed, which will trigger view updates
```

### Phase 5: Update MainWindow
Update MainWindow to use UpdateManager for view updates.

```python
from PySide6.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    """Main application window using standardized update interface."""
    
    def __init__(self, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        self._update_manager = UpdateManager(self)
        self._setup_ui()
        self._setup_controllers()
        self._setup_connections()
    
    def _setup_controllers(self) -> None:
        """Set up controllers with UpdateManager."""
        self._data_controller = DataViewController(
            self._data_model, self._update_manager)
        # Other controllers...
    
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self._update_manager.update_completed.connect(
            self._on_updates_completed)
        # Other connections...
    
    def _on_updates_completed(self) -> None:
        """Handle completion of all pending updates."""
        # Update status or perform other actions when all updates are done
        self.statusBar().showMessage("All updates completed")
    
    def refresh_ui(self) -> None:
        """Refresh the entire UI."""
        # For views that implement IUpdatable
        for view_id, view in self._views.items():
            if isinstance(view, IUpdatable) and view.needs_update():
                self._update_manager.schedule_update(view)
```

## Testing Strategy

1. **Unit Tests for IUpdatable Interface**:
   - Test UpdatableComponent base implementation
   - Test update tracking logic
   - Test needs_update detection

2. **Unit Tests for UpdateManager**:
   - Test debouncing functionality
   - Test dependency tracking
   - Test update scheduling and execution

3. **Integration Tests**:
   - Test view adapter implementations
   - Test controller integration with UpdateManager
   - Test end-to-end update flow

## Migration Strategy

1. Create IUpdatable interface and UpdatableComponent base class
2. Implement UpdateManager for centralized update handling
3. Update one view adapter at a time to implement IUpdatable
4. Update controllers to use standardized methods
5. Update MainWindow to use UpdateManager

## Risks and Mitigation

1. **Risk**: Breaking existing update flows during migration
   **Mitigation**: Implement changes incrementally and maintain backwards compatibility during transition

2. **Risk**: Performance degradation from centralized update management
   **Mitigation**: Implement and test performance benchmarks, optimize debouncing parameters

3. **Risk**: Update dependencies creating circular update loops
   **Mitigation**: Add cycle detection in UpdateManager to break infinite update loops

4. **Risk**: Overwhelming the UI thread with batched updates
   **Mitigation**: Implement prioritization and chunking for large update batches

## Success Criteria

1. All view components implement the IUpdatable interface
2. Controllers use standard update methods without checking for multiple method names
3. Debouncing logic is centralized in UpdateManager
4. Update dependencies are properly tracked and managed
5. Performance is maintained or improved for update operations 