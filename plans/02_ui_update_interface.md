# UI Update Interface Standardization Plan

**Status**: In Progress (Phase 2)

## Problem

Current UI update patterns are inconsistent across the application:
- Some views poll for data changes
- Some rely on signal connections
- Some use direct method calls
- Some have custom refresh methods with different names

This leads to:
1. Difficult to maintain code
2. Potential performance issues
3. Inconsistent user experience
4. Hard to test update logic

## Solution Approach

Standardize UI updates using an interface-based approach:

1. Define the `IUpdatable` interface for all UI components
2. Create a utility class for managing updates
3. Implement a dependency system for coordinated updates
4. Standardize update triggers across the application

## Implementation Plan

### Phase 1: Interface Definition ✅ COMPLETED
- ✅ Define the `IUpdatable` interface with methods:
  - `need_update()`: Check if component needs updating
  - `update_component()`: Update the component's view
  - `populate_component()`: Initial setup for data binding
  - `reset_component()`: Reset to initial state
- ✅ Create `UpdatableComponent` base class implementing `IUpdatable`
- ✅ Create test mock classes for `IUpdatable` components
- ✅ Setup test frameworks for verifying updatable components

### Phase 2: UpdateManager Utility ✅ COMPLETED
- ✅ Create `UpdateManager` class to centralize update scheduling
- ✅ Implement methods for:
  - ✅ Scheduling individual component updates
  - ✅ Handling batch updates
  - ✅ Managing update timing (debouncing)
- ✅ Create test framework for UpdateManager
- ✅ Fix test compatibility issues:
  - ✅ Implement QWidget-based MockUpdatableWidget
  - ✅ Make test mocks properly implement IUpdatable protocol
  - ✅ Fix test assertions to match actual UpdateManager behavior
- ✅ Implement ServiceLocator pattern for accessing UpdateManager:
  - ✅ Create ServiceLocator utility class
  - ✅ Integrate UpdateManager with ServiceLocator
  - ✅ Create helper function for getting UpdateManager
  - ✅ Add proper cleanup during application shutdown
  - ✅ Fix QTimer cleanup issues in UpdateManager
  - ✅ Add comprehensive tests for ServiceLocator
- ✅ Transition existing components to use UpdateManager through ServiceLocator

### Phase 3: View Integration 🔄 IN PROGRESS (40% Complete)
- ✅ Define `UpdatableView` base class for QWidget-based views
- ✅ Fix signal implementation in UpdatableView (signals as class attributes)
- ✅ Create comprehensive tests for UpdatableView
- ✅ Integrate DataViewAdapter with the update system
- ✅ Create comprehensive tests for DataViewAdapter's integration with UpdateManager
- ⏳ Update the remaining view components to implement `IUpdatable`:
  - ⏳ `ValidationViewAdapter`
  - ⏳ `CorrectionViewAdapter`
  - ⏳ `ChartViewAdapter`
  - ⏳ `SidebarNavigationView`
  - ⏳ `Dashboard`
- ⏳ Integrate UpdateManager into the main application
- ⏳ Update controllers to use UpdateManager for triggering UI updates

### Phase 4: Data State Tracking 📅 PLANNED
- Extend DataManager to track changes in data state
- Create a mechanism for auto-triggering updates based on state
- Define dependencies between components for cascading updates
- Optimize update frequency for performance

## Design Details

### IUpdatable Interface

```python
class IUpdatable(Protocol):
    """Protocol defining the interface for updatable UI components."""
    
    def need_update(self) -> bool:
        """Check if the component needs to be updated."""
        ...
        
    def update_component(self) -> None:
        """Update the component with current data."""
        ...
        
    def populate_component(self) -> None:
        """Populate the component with initial data."""
        ...
        
    def reset_component(self) -> None:
        """Reset the component to its initial state."""
        ...
```

### UpdateManager Utility

```python
class UpdateManager:
    """Centralized manager for UI component updates."""
    
    def __init__(self, debounce_ms: int = 50):
        """Initialize with optional debounce time."""
        self._pending_updates = set()
        self._dependencies = defaultdict(set)
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_updates)
        self._debounce_ms = debounce_ms
        
    def schedule_update(self, component: IUpdatable) -> None:
        """Schedule a component for update."""
        self._pending_updates.add(component)
        self._schedule_processing()
        
    def register_dependency(self, component: IUpdatable, 
                           depends_on: IUpdatable) -> None:
        """Register a dependency between components."""
        self._dependencies[depends_on].add(component)
```

### ServiceLocator Utility

```python
class ServiceLocator:
    """
    Service locator pattern implementation for accessing application-wide services.
    """
    
    # Class-level storage for services
    _services: Dict[str, Any] = {}
    _factories: Dict[str, callable] = {}
    
    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Register a service instance with the given name."""
        cls._services[name] = service
        
    @classmethod
    def get(cls, name: str) -> Any:
        """Get a service by name."""
        # Check if service is already instantiated
        if name in cls._services:
            return cls._services[name]
            
        # Check if we have a factory for this service
        if name in cls._factories:
            service = cls._factories[name]()
            cls._services[name] = service
            return service
            
        # Service not found
        raise KeyError(f"Service '{name}' not registered")
```

### Helper Function

```python
def get_update_manager() -> UpdateManager:
    """
    Get the application-wide UpdateManager instance.
    
    Returns:
        UpdateManager: The application's UpdateManager instance
        
    Raises:
        KeyError: If the UpdateManager has not been registered
    """
    return ServiceLocator.get_typed("update_manager", UpdateManager)
```

## Test Design

### Test Cases

1. **Basic Update Scheduling**
   - Schedule a single component update
   - Verify update is processed after debounce
   - Test multiple update requests are debounced

2. **Dependency Management**
   - Test dependent components are updated
   - Test dependency cycles are handled
   - Test priority-based updates

3. **Component Integration**
   - Test with real view components
   - Verify update chains in complex scenarios
   - Measure performance characteristics

4. **ServiceLocator Integration**
   - Test registering and retrieving UpdateManager
   - Test factory functions for lazy initialization
   - Test type-safe access to services
   - Test integration with application lifecycle

## Progress

### Updates (March 27, 2025)

1. **Completed**
   - Implemented UpdatableView base class for QWidget-based views
   - Fixed signal handling in UpdatableView (signals as class attributes)
   - Created comprehensive test suite for UpdatableView
   - Integrated DataViewAdapter with the update system
   - Created thorough tests for DataViewAdapter's integration with UpdateManager
   - Completed Phase 2 (UpdateManager Utility) with ServiceLocator integration
   - Fixed numerous signal handling issues in the UI update system

2. **In Progress**
   - Updating remaining view components to implement IUpdatable interface
   - Integrating UpdateManager into main application workflow
   - Ensuring proper connection between controllers and updatable views

3. **Next Steps**
   - Complete view component updates for ValidationViewAdapter and CorrectionViewAdapter
   - Update controllers to use UpdateManager for triggering UI updates
   - Implement data state tracking for optimized updates
   - Create visual debugging tools for update flow visualization 