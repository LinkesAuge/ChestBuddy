# DataView Refactoring - Project Structure

## Overview

This document outlines the project structure for the DataView refactoring, including folder organization, file layout, and code organization. A well-organized structure is crucial for maintainability, readability, and ensuring clear separation of concerns.

## Folder Structure

The refactored DataView will follow a clear and logical folder structure within the ChestBuddy application. Below is the proposed organization:

```
chestbuddy/
├── ui/
│   ├── data/                       # DataView-specific components
│   │   ├── models/                 # Data models
│   │   │   ├── __init__.py
│   │   │   ├── data_view_model.py  # Main ViewModel for DataView
│   │   │   └── filter_model.py     # Filter proxy model
│   │   ├── views/                  # View components
│   │   │   ├── __init__.py
│   │   │   ├── data_table_view.py  # Main DataView component
│   │   │   └── header_view.py      # Custom header view
│   │   ├── delegates/              # Cell rendering delegates
│   │   │   ├── __init__.py
│   │   │   ├── cell_delegate.py    # Base cell delegate
│   │   │   ├── validation_delegate.py  # Validation visualization delegate
│   │   │   └── correction_delegate.py  # Correction visualization delegate
│   │   ├── adapters/               # Adapter components
│   │   │   ├── __init__.py
│   │   │   ├── validation_adapter.py   # Validation system adapter
│   │   │   └── correction_adapter.py   # Correction system adapter
│   │   ├── menus/                  # Context menus
│   │   │   ├── __init__.py
│   │   │   ├── context_menu.py     # Main context menu
│   │   │   └── correction_menu.py  # Correction-specific menu items
│   │   ├── widgets/                # Supporting UI widgets
│   │   │   ├── __init__.py
│   │   │   ├── filter_widget.py    # Data filtering widget
│   │   │   └── toolbar_widget.py   # DataView toolbar
│   │   ├── __init__.py
│   │   └── data_view.py            # Composite view combining components
│   └── ...
├── core/
│   ├── models/                     # Core data models
│   │   ├── __init__.py
│   │   └── chest_data_model.py     # Existing data model
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── validation_service.py   # Validation service
│   │   └── correction_service.py   # Correction service
│   ├── managers/                   # State managers
│   │   ├── __init__.py
│   │   └── table_state_manager.py  # Table cell state manager
│   ├── enums/                      # Enumerations
│   │   ├── __init__.py
│   │   └── validation_enums.py     # Validation status enums
│   └── ...
└── ...
```

## Key Components

### Models

The models folder contains classes that manage data representation and state:

- **DataViewModel** (`data_view_model.py`): Adapts the core ChestDataModel for display in the UI
- **FilterModel** (`filter_model.py`): Provides sorting and filtering capabilities

### Views

The views folder contains UI components that display data:

- **DataTableView** (`data_table_view.py`): Main table view component
- **HeaderView** (`header_view.py`): Customized header for advanced column operations

### Delegates

The delegates folder contains classes responsible for rendering cells:

- **CellDelegate** (`cell_delegate.py`): Base rendering delegate
- **ValidationDelegate** (`validation_delegate.py`): Delegate for validation visualization
- **CorrectionDelegate** (`correction_delegate.py`): Delegate for displaying correction options

### Adapters

The adapters folder contains classes that connect the core services to the UI:

- **ValidationAdapter** (`validation_adapter.py`): Adapts validation service output for UI
- **CorrectionAdapter** (`correction_adapter.py`): Adapts correction service for UI integration

### Menus

The menus folder contains context menu implementations:

- **ContextMenu** (`context_menu.py`): Main right-click context menu
- **CorrectionMenu** (`correction_menu.py`): Specialized menu for correction operations

### Widgets

The widgets folder contains supporting UI components:

- **FilterWidget** (`filter_widget.py`): UI for filtering data
- **ToolbarWidget** (`toolbar_widget.py`): Toolbar with common actions

## File Structure and Organization

### Component Organization

Each component will follow a consistent organization pattern:

```python
"""
Module docstring explaining purpose and usage
"""

from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtWidgets import QTableView

from .some_dependency import SomeDependency
# Additional imports...

class ComponentName:
    """
    Class docstring with detailed description,
    attributes, and usage examples
    """
    
    # SIGNALS
    # All signals defined at the top
    component_changed = Signal(object)
    
    def __init__(self, parent=None):
        """
        Constructor with clear parameter documentation
        """
        super().__init__(parent)
        
        # INTERNAL STATE
        self._private_attributes = None
        
        # SETUP
        self._setup_ui()
        self._connect_signals()
    
    # PUBLIC API
    def public_method(self):
        """
        Public method documentation
        """
        pass
    
    # PROPERTIES
    @property
    def some_property(self):
        """Getter for property"""
        return self._some_property
    
    @some_property.setter
    def some_property(self, value):
        """Setter for property"""
        self._some_property = value
    
    # SLOTS
    @Slot(object)
    def on_some_event(self, data):
        """
        Event handler documentation
        """
        pass
    
    # PRIVATE METHODS
    def _setup_ui(self):
        """Set up UI components"""
        pass
    
    def _connect_signals(self):
        """Connect signals and slots"""
        pass
```

### Component Interfaces

Each component will have a well-defined public interface:

1. **Public Methods**: Clearly documented methods for external use
2. **Properties**: Python properties for attribute access
3. **Signals**: Qt signals for event notification
4. **Slots**: Qt slots for event handling

Private methods and attributes will be prefixed with underscore (`_`).

## Implementation Guidelines

### Coding Standards

All code will follow these standards:

1. **PEP 8**: Follow Python style guide
2. **Type Hints**: Use type annotations for parameters and return values
3. **Docstrings**: Include comprehensive docstrings in Google style
4. **Comments**: Add explanatory comments for complex logic

### Dependency Management

Components will follow these dependency principles:

1. **Dependency Injection**: Pass dependencies in constructor
2. **Minimal Coupling**: Minimize dependencies between components
3. **Interface-based**: Depend on interfaces rather than implementations
4. **Service Locator**: Use service locator pattern for system-wide dependencies

### Component Interactions

Components will interact through these mechanisms:

1. **Signal/Slot**: Use Qt's signal/slot mechanism for loose coupling
2. **Event Propagation**: Propagate events up the widget hierarchy
3. **Adapter Pattern**: Use adapters to connect dissimilar interfaces
4. **Observer Pattern**: Implement observer pattern for state changes

## Example Component Implementation

Here's an example implementation of the DataTableView component:

```python
"""
DataTableView

A specialized table view for displaying chest data with validation
and correction visualizations.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QTableView

from ..delegates.cell_delegate import CellDelegate
from ..models.data_view_model import DataViewModel


class DataTableView(QTableView):
    """
    DataTableView displays chest data with validation and correction
    visualizations.
    
    It provides specialized rendering for different validation
    states and offers context menu integration for operations
    on the data.
    
    Attributes:
        selection_changed (Signal): Emitted when the selection changes
    """
    
    # SIGNALS
    selection_changed = Signal(list)  # List of selected indices
    
    def __init__(self, parent=None):
        """
        Initialize the DataTableView.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # SETUP
        self._setup_ui()
        self._connect_signals()
        
        # INTERNAL STATE
        self._last_selection = []
    
    # PUBLIC API
    def set_validation_visible(self, visible: bool) -> None:
        """
        Show or hide validation visualizations.
        
        Args:
            visible: Whether validation should be visible
        """
        # Implementation...
        pass
    
    # SLOTS
    @Slot()
    def on_selection_changed(self) -> None:
        """
        Handle changes in the current selection.
        Emits selection_changed signal with new selection.
        """
        current_selection = self.selectionModel().selectedIndexes()
        if current_selection != self._last_selection:
            self._last_selection = current_selection
            self.selection_changed.emit(current_selection)
    
    # OVERRIDES
    def contextMenuEvent(self, event):
        """
        Show context menu on right-click.
        
        Args:
            event: Context menu event
        """
        # Implementation...
        pass
    
    # PRIVATE METHODS
    def _setup_ui(self) -> None:
        """Set up UI components and style."""
        # Set selection behavior
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.ExtendedSelection)
        
        # Set default delegate
        self.setItemDelegate(CellDelegate(self))
        
        # Configure appearance
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        
        # Allow context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
    
    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect selection change
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Connect context menu
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position) -> None:
        """
        Show the context menu at the specified position.
        
        Args:
            position: Position where to show the menu
        """
        # Implementation...
        pass
```

## Integration with Existing Code

The refactored DataView will integrate with the existing ChestBuddy application through these strategies:

1. **Backwards Compatibility**: Maintain same public API where possible
2. **Gradual Transition**: Replace components incrementally
3. **Adapter Pattern**: Use adapters to integrate with existing systems
4. **Feature Parity**: Ensure all existing features are supported

## Conclusion

This project structure provides a clear organization for the DataView refactoring. By following this structure, we ensure:

1. **Clear Separation of Concerns**: Each component has a specific responsibility
2. **Maintainability**: Code is organized and follows consistent patterns
3. **Extensibility**: New features can be added without changing existing code
4. **Readability**: Developers can quickly understand the system organization

The structure will be reviewed and refined as implementation progresses, with any changes documented in this file. 