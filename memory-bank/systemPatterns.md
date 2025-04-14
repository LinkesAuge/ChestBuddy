---
title: System Patterns - ChestBuddy Application
date: 2024-08-05
---

# System Patterns - ChestBuddy Application

## DataView Refactoring Architecture

**(Updated: 2024-08-08 - Added notes based on code review)**

The DataView refactoring implements several key architectural patterns to create a more robust, maintainable, and feature-rich component. This section outlines the specific patterns being applied in this refactoring effort.

**Note on Migration:** The project is currently migrating from an older `ui/data_view.py` implementation to the new structure described below (`ui/data/`). A `DataViewAdapter` is temporarily used to bridge the gap. The goal is to fully consolidate onto the new architecture.

### Core Architectural Principles

The refactored DataView follows these architectural principles:

1. **Separation of Concerns**: Clear boundaries between data management, presentation, and business logic.
2. **Composability**: Components that can be composed to build more complex functionality.
3. **Testability**: Design that facilitates comprehensive testing.
4. **Single Responsibility**: Each component has one primary responsibility.
5. **Open/Closed**: Components open for extension but closed for modification.

### Component Architecture

The refactored DataView (`ui/data/`) is structured around these key component types:

#### Data Layer Components
- **DataViewModel**: Adapts the ChestDataModel for display in the UI (Inherits `QAbstractTableModel`)
- **FilterModel**: Provides sorting and filtering capabilities (Inherits `QSortFilterProxyModel`)
- **SelectionModel**: Manages selection state and operations (Often standard Qt implementation)

#### Presentation Layer Components
- **DataTableView**: Core table view component (Inherits `QTableView`)
- **DataHeaderView**: Custom header for advanced column operations (Inherits `QHeaderView`)
- **CellDelegate**: Base rendering delegate for cells (Inherits `QStyledItemDelegate`)

#### Specialized Delegates
- **ValidationDelegate**: Specialized rendering for validation status
- **CorrectionDelegate**: Specialized rendering for correction options
- **DateDelegate**, **NumericDelegate**, etc.: Type-specific rendering

#### Context Menu Components
- **ContextMenu**: Main context menu framework
- **MenuFactory**: Creates context-specific menu items
- **ActionProviders**: Supply actions based on selection context

#### Integration Adapters
- **ValidationAdapter**: Connects `ValidationService` to `TableStateManager`
- **CorrectionAdapter**: Connects `CorrectionService` to `TableStateManager`

#### State Management
- **TableStateManager**: Central manager for visual cell states (validation, correction). Crucial for ensuring consistent state visualization.

### Key Design Patterns in DataView Refactoring

#### 1. Composite Pattern
The DataView uses the Composite pattern to build complex UI structures from simpler components:

```python
class DataView:
    """Main composite view combining all DataView components."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create toolbar
        self._toolbar = ToolbarWidget(self)
        layout.addWidget(self._toolbar)
        
        # Create filter widget
        self._filter_widget = FilterWidget(self)
        layout.addWidget(self._filter_widget)
        
        # Create main table view
        self._table_view = DataTableView(self)
        layout.addWidget(self._table_view)
        
        # Set up model
        self._model = DataViewModel(self)
        self._filter_model = FilterModel(self)
        self._filter_model.setSourceModel(self._model)
        self._table_view.setModel(self._filter_model)
```

#### 2. Delegate Pattern
The DataView uses the Delegate pattern extensively for customized cell rendering and interaction. Delegates (`ValidationDelegate`, `CorrectionDelegate`) are responsible for visualizing cell state managed by `TableStateManager`.

**State Flow Note:** The *intended and correct* flow is for delegates to read state information (validation, correction) from the `DataViewModel` (via custom roles populated from `TableStateManager`) during the `paint` method. Direct manipulation of item properties (like background color) *within the view* for state visualization should be avoided to maintain consistency through the `TableStateManager`.

```python
class CellDelegate(QtWidgets.QStyledItemDelegate):
    """Base delegate for all cell rendering."""
    
    def paint(self, painter, option, index):
        """Paint the cell with custom styling."""
        # Default implementation
        super().paint(painter, option, index)
        
    def createEditor(self, parent, option, index):
        """Create custom editor for cell."""
        return super().createEditor(parent, option, index)
        
class ValidationDelegate(CellDelegate):
    """Specialized delegate for validation status visualization."""
    
    def paint(self, painter, option, index):
        """Paint the cell with validation status indicators."""
        # Get validation status from the model (populated by TableStateManager)
        status = index.data(DataViewModel.ValidationStateRole)
        
        # Apply background color based on status
        if status == ValidationStatus.INVALID:
            painter.fillRect(option.rect, self.INVALID_COLOR)
        elif status == ValidationStatus.CORRECTABLE:
            painter.fillRect(option.rect, self.CORRECTABLE_COLOR)
            
        # Draw basic cell content
        super().paint(painter, option, index)
        
        # Draw status indicator icon if needed
        if status != ValidationStatus.VALID:
            self._draw_status_icon(painter, option, status)
```

#### 3. Adapter Pattern
The DataView uses the Adapter pattern to connect core services (`ValidationService`, `CorrectionService`) with the `TableStateManager`. Adapters (`ValidationAdapter`, `CorrectionAdapter`) transform service results into state updates for the manager.

- **Responsibility:** Listen for service signals (e.g., `validation_complete`), receive data (often DataFrames), map service-specific statuses (e.g., `ValidationStatus`) to UI cell states (`CellState`), create a dictionary of `(row, col): CellFullState` updates, and call `TableStateManager.update_states()`.
- **`ValidationAdapter` Example:**
    - Connects to `ValidationService.validation_complete` signal.
    - Receives the `status_df` (DataFrame).
    - Iterates through `status_df` and the `TableStateManager.headers_map`.
    - Maps `ValidationStatus` enum values from `status_df` to `CellState` enum values.
    - Constructs `CellFullState` objects for changed cells.
    - Calls `TableStateManager.update_states()` with the constructed dictionary.

```python
# Example: ValidationAdapter._on_validation_complete
def _on_validation_complete(self, validation_results: pd.DataFrame) -> None:
    status_df = validation_results
    self._headers_map = self._table_state_manager.headers_map # Get current header map
    new_states = {}
    for row_idx in status_df.index:
        for base_col_name, col_idx in self._headers_map.items():
            status_col = f"{base_col_name}_status"
            message_col = f"{base_col_name}_message"
            if status_col in status_df.columns:
                status_value = status_df.at[row_idx, status_col]
                message_value = status_df.at[row_idx, message_col]

                # Map ValidationStatus -> CellState
                cell_state_status = self._map_validation_status_to_cell_state(status_value)
                error_details = str(message_value) if pd.notna(message_value) else ""

                # Get current state for comparison
                current_full_state = self._table_state_manager.get_full_cell_state(row_idx, col_idx)
                if current_full_state is None:
                    current_full_state = CellFullState()

                # Determine if update is needed and build partial update dict
                needs_update, partial_update = self._determine_update(current_full_state, cell_state_status, error_details)

                if needs_update:
                    # Merge changes and store
                    merged_state_dict = dataclasses.asdict(current_full_state)
                    merged_state_dict.update(partial_update)
                    # Preserve existing correction suggestions
                    if "correction_suggestions" not in partial_update:
                         merged_state_dict.setdefault("correction_suggestions", current_full_state.correction_suggestions or [])
                    new_states[(row_idx, col_idx)] = CellFullState(**merged_state_dict)

    if new_states:
        self._table_state_manager.update_states(new_states)
```

#### 4. Factory Pattern
The DataView uses the Factory pattern for creating context-specific menu items:

```python
class ContextMenuFactory:
    """Factory for creating context-specific menu items."""
    REGISTERED_ACTION_CLASSES = [CopyAction, PasteAction, ...]

    @staticmethod
    def create_context_menu(info: ActionContext) -> typing.Tuple[QMenu, typing.Dict[str, QAction]]:
        """Create a context menu based on selection and cell state."""
        menu = QMenu(info.parent_widget)
        created_qactions = {}
        action_instances = [ActionClass() for ActionClass in ContextMenuFactory.REGISTERED_ACTION_CLASSES]

        # Add actions based on applicability and enabled state
        for action_instance in action_instances:
            if action_instance.is_applicable(info):
                qaction = QAction(action_instance.icon, action_instance.text, menu)
                qaction.setEnabled(action_instance.is_enabled(info))
                qaction.triggered.connect(lambda checked=False, bound_action=action_instance: bound_action.execute(info))
                menu.addAction(qaction)
                created_qactions[action_instance.id] = qaction
        
        # Add separators and cell-type specific placeholders
        # ... logic to add separators and placeholders ...
        
        return menu, created_qactions

class ActionContext:
    """Dataclass holding context for menu creation/action execution."""
    clicked_index: QModelIndex
    selection: typing.List[QModelIndex]
    model: DataViewModel
    parent_widget: QWidget
    state_manager: TableStateManager
    clipboard_text: str # Added for paste action

class AbstractContextAction:
    """Base class for all context menu actions."""
    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def text(self) -> str:
        raise NotImplementedError

    # ... other properties like icon, shortcut, tooltip ...

    def is_applicable(self, context: ActionContext) -> bool:
        """Is this action generally relevant given the context?"""
        return True

    def is_enabled(self, context: ActionContext) -> bool:
        """Is this action currently allowed given the context?"""
        return True

    def execute(self, context: ActionContext) -> None:
        """Perform the action."""
        raise NotImplementedError
```
This pattern uses a factory (`ContextMenuFactory`) to instantiate registered action classes (`AbstractContextAction` subclasses) and build a `QMenu`. Each action determines its own applicability and enabled state based on the provided `ActionContext`, allowing for flexible and context-aware menus.

#### 5. Strategy Pattern
The DataView uses the Strategy pattern for different rendering strategies:

```python
class CellRenderingStrategy:
    """Base strategy for cell rendering."""
    
    def render(self, painter, option, index):
        """Render the cell."""
        raise NotImplementedError("Subclasses must implement this method")
        
class ValidationRenderingStrategy(CellRenderingStrategy):
    """Strategy for rendering validation status."""
    
    def render(self, painter, option, index):
        """Render validation status."""
        # Implementation...
        
class CorrectionRenderingStrategy(CellRenderingStrategy):
    """Strategy for rendering correction options."""
    
    def render(self, painter, option, index):
        """Render correction options."""
        # Implementation...
```

#### 6. Observer Pattern (Signal/Slot)
The DataView uses Qt's signal-slot mechanism. 
- `TableStateManager` emits signals (e.g., `cell_states_changed`) when state updates.
- `DataViewModel` connects to these signals and emits `dataChanged` for the relevant cells/roles to notify the view.
- Views/Controllers connect to model/service signals.

**Decoupling Note:** For actions triggered by UI elements (like delegates or context menus), prefer emitting higher-level signals from the main view component (`DataTableView` or its direct adapter) rather than connecting delegate/menu signals directly in external components like `MainWindow`. This improves component reusability.

```python
# Example in DataViewModel
class DataViewModel(QtCore.QAbstractTableModel):
    # ...
    def connect_state_manager(self, state_manager):
        state_manager.cell_states_changed.connect(self._on_state_manager_state_changed)
        
    @Slot(set)
    def _on_state_manager_state_changed(self, changed_indices: set):
        # Determine minimal bounding box or individual indices
        # Emit dataChanged for affected indices and relevant roles
        # (e.g., Qt.BackgroundRole, Qt.ToolTipRole, ValidationStateRole)
        # Avoid full model reset if possible
        pass 

# Example in DataTableView (Conceptual)
class DataTableView(QTableView):
    correction_action_triggered = Signal(object, object) # e.g., index, correction_data
    
    def _setup_delegates(self):
        # ... create correction_delegate ...
        # Connect internal delegate signal to emit a higher-level view signal
        correction_delegate.correction_selected.connect(self._handle_delegate_correction)
        
    def _handle_delegate_correction(self, index, correction_data):
        # Emit the view-level signal
        self.correction_action_triggered.emit(index, correction_data)
```

### Component Interactions (Refined State Flow)

The intended state flow for validation/correction visualization is:
1. **Service**: Performs validation/correction check (`ValidationService`, `CorrectionService`), emits results (often a DataFrame) via a signal (e.g., `validation_complete`).
2. **Adapter**: Listens for the service signal (`ValidationAdapter`, `CorrectionAdapter`), receives the results DataFrame, maps service-specific statuses/data to `CellState` and `CellFullState` components.
3. **StateManager**: Adapter calls `TableStateManager.update_states()` with a dictionary of `(row, col): CellFullState` updates. The `TableStateManager` merges these changes with existing states and emits `state_changed` with the set of affected cell coordinates.
4. **ViewModel**: `DataViewModel` listens for `TableStateManager.state_changed`, determines the minimal bounding box or individual indices affected, and emits `dataChanged` for those indices and the relevant custom data roles (e.g., `ValidationStateRole`, `CorrectionStateRole`, `Qt.ToolTipRole`).
5. **View/Delegate**: `DataTableView` receives `dataChanged`. During repaint, `ValidationDelegate`/`CorrectionDelegate` reads the updated state roles from the `DataViewModel` via the `index` and paints the cell background, icons, or tooltips accordingly.

This ensures the `TableStateManager` is the single source of truth for visual cell state, promoting consistency.

## Final Architecture Overview

The ChestBuddy application now implements a comprehensive set of design patterns and architectural principles, creating a robust, maintainable, and extensible codebase. This document outlines the key patterns used throughout the application, with particular emphasis on their implementation in the completed validation system integration.

**Update**: The core `DataViewModel` and Adapters (`ValidationAdapter`, `CorrectionAdapter`) for the DataView refactor are now implemented and tested. They successfully integrate with the `TableStateManager` to manage and propagate cell state information, forming the backbone of the refactored data display and validation/correction visualization.

## Core Architectural Pattern: Model-View-Controller (MVC)

The application follows a strict MVC architecture with clear separation of concerns:

1. **Model Layer**:
   - `ChestDataModel`: Central data store using pandas DataFrames
   - `ValidationListModel`: Manages validation lists for different data types
   - Domain-specific data structures and state tracking

2. **View Layer**:
   - `MainWindow`: Main application window
   - Specialized view adapters (DataViewAdapter, ValidationViewAdapter, etc.)
   - UI components with minimal business logic

3. **Controller Layer**:
   - `DataViewController`: Handles data operations and view updates
   - `UIStateController`: Manages UI state across the application
   - `FileOperationsController`: Handles file operations
   - `ViewStateController`: Manages active view state
   - `ErrorHandlingController`: Centralizes error handling
   - `ProgressController`: Manages progress reporting

### Validation System MVC Implementation

The validation system integration follows the MVC pattern:
- **Model**: ValidationListModel for validation lists, ValidationService for business logic
- **View**: ValidationViewAdapter and ValidationStatusDelegate for visualization
- **Controller**: UIStateController and DataViewController for coordination

## Key Design Patterns

### 1. Observer Pattern

**Implementation**: Signal-Slot mechanism from Qt/PySide6, enhanced with our custom `SignalManager`

**Key Components**:
- Signal declarations in model and controller classes
- Connect methods in observers
- Signal emissions on state changes

**Validation System Example**:
```python
# In UIStateController
validation_state_changed = Signal(dict)

# In DataViewController
def _connect_to_ui_state_controller(self):
    self._ui_state_controller.validation_state_changed.connect(
        self._on_validation_state_changed
    )

# Signal emission
self.validation_state_changed.emit(self._validation_state.copy())
```

### 2. Service Layer Pattern

**Implementation**: Dedicated service classes for business logic

**Key Services**:
- `ValidationService`: Handles data validation logic
- `CorrectionService`: Manages data correction strategies
- `ImportExportService`: Handles file operations
- `ChartService`: Creates and manages data visualizations
- `ConfigurationService`: Manages application configuration

**Validation Example**:
```python
class ValidationService:
    def validate_data(self, dataframe, rules=None):
        # Validation logic
        return validation_results
        
    def add_to_validation_list(self, list_type, value):
        # Add entry to validation list
        return success
```

### 3. Strategy Pattern

**Implementation**: Pluggable strategies for different operations

**Examples**:
- Validation strategies for different data types
- Correction strategies for different error types
- Import/export strategies for different file formats

**Validation Strategy Example**:
```python
class ExactMatchValidator(BaseValidator):
    def validate(self, value, valid_values):
        return value in valid_values

class FuzzyMatchValidator(BaseValidator):
    def validate(self, value, valid_values):
        # Fuzzy matching logic
        return match_found
```

### 4. Adapter Pattern

**Implementation**: View adapters to wrap complex UI components

**Key Adapters**:
- `DataViewAdapter`: Wraps data table view
- `ValidationViewAdapter`: Wraps validation UI components
- `ChartViewAdapter`: Wraps chart visualization
- `CorrectionViewAdapter`: Wraps correction UI

**Validation Adapter Example**:
```python
class ValidationViewAdapter(BaseView):
    def __init__(self, validation_service, parent=None):
        super().__init__(parent)
        self._validation_tab = ValidationTabView(validation_service)
        self.content_layout.addWidget(self._validation_tab)
        self._connect_signals()
```

### 5. Command Pattern

**Implementation**: Encapsulated operations for validation and correction actions

**Examples**:
- Correction commands for undo/redo support
- Validation commands for applying validation rules
- Import/export commands for file operations

**Validation Command Example**:
```python
class AddToValidationListCommand:
    def __init__(self, service, list_type, value):
        self.service = service
        self.list_type = list_type
        self.value = value
        
    def execute(self):
        return self.service.add_to_validation_list(self.list_type, self.value)
```

### 6. Factory Pattern

**Implementation**: Factories for creating complex objects

**Examples**:
- `ValidationRuleFactory`: Creates validation rules
- `CorrectionStrategyFactory`: Creates correction strategies
- `ChartFactory`: Creates chart visualizations

**Validation Factory Example**:
```python
class ValidationRuleFactory:
    @staticmethod
    def create_rule(rule_type, parameters):
        if rule_type == "exact_match":
            return ExactMatchValidator(parameters)
        elif rule_type == "fuzzy_match":
            return FuzzyMatchValidator(parameters)
```

### 7. Singleton Pattern

**Implementation**: Singleton services and utilities

**Examples**:
- `ConfigManager`: Application configuration
- `SignalManager`: Signal connection tracking
- `ServiceLocator`: Access to application services
- `UpdateManager`: UI update scheduling

**ServiceLocator Example**:
```python
class ServiceLocator:
    _services = {}
    
    @classmethod
    def register(cls, name, service):
        cls._services[name] = service
        
    @classmethod
    def get(cls, name):
        return cls._services.get(name)
```

### 8. State Pattern

**Implementation**: State tracking for UI and data components

**Examples**:
- `UIStateController`: Tracks UI state
- `ViewStateController`: Tracks active view
- `DataState`: Tracks data model state changes

**UI State Example**:
```python
class UIStateController(BaseController):
    def __init__(self):
        self._action_states = {}
        self._validation_state = {
            "has_issues": False,
            "issue_count": 0,
            "categories": {},
        }
    
    def update_validation_state(self, **validation_info):
        # Update state and notify observers
```

### 9. Bridge Pattern

**Implementation**: Separation of abstraction and implementation

**Examples**:
- Abstract validators with concrete implementations
- Abstract file parsers with format-specific implementations
- View interfaces with concrete adapter implementations

**ValidationService Bridge Example**:
```python
class ValidationService:
    def __init__(self):
        self._validators = {
            "player_name": ExactMatchValidator(),
            "chest_type": FuzzyMatchValidator(),
        }
    
    def validate_field(self, field_type, value):
        validator = self._validators.get(field_type)
        if validator:
            return validator.validate(value, self._get_valid_values(field_type))
```

### 10. Proxy Pattern

**Implementation**: Control access to objects

**Examples**:
- Lazy-loading proxies for expensive resources
- Access control proxies for sensitive operations
- Remote proxies for external services

**ValidationListProxy Example**:
```python
class ValidationListProxy:
    def __init__(self, list_type):
        self._list_type = list_type
        self._list = None
    
    def get_list(self):
        if self._list is None:
            # Load list only when needed
            self._list = self._load_list(self._list_type)
        return self._list
```

### 11. Chunked Processing Pattern

**Implementation**: Breaking large operations into smaller chunks processed sequentially

**Examples**:
- Table population in DataView for large datasets
- Validation processing for large datasets
- File loading operations with progress reporting

**Benefits**:
- Maintains UI responsiveness during heavy operations
- Provides opportunity for progress feedback
- Prevents blocking the main UI thread
- Reduces perceived processing time for users

**DataView Chunked Population Example**:
```python
def populate_table(self) -> None:
    """Populate the table with data from the data model.
    
    Uses a chunked approach to prevent UI freezing with large datasets.
    Each chunk processes a limited number of rows (200) and then yields
    back to the event loop before continuing.
    """
    if not self._data_model or self._data_model.is_empty():
        return

    # Reset population state
    self._rows_to_process = len(self._data_model)
    self._current_row_index = 0
    self._population_in_progress = True
    
    # Clear existing table and prepare model
    self._table_model.clear()
    self._setup_horizontal_headers()
    
    # Start the chunked population process
    self._populate_chunk()

def _populate_chunk(self) -> None:
    """Process a chunk of rows (200 max) and schedule the next chunk."""
    if not self._population_in_progress:
        return
        
    chunk_size = 200  # Process 200 rows at a time
    end_row = min(self._current_row_index + chunk_size, self._rows_to_process)
    
    # Process this chunk
    for row_idx in range(self._current_row_index, end_row):
        # Add row to the table model
        # ... row processing code ...
    
    # Update progress
    self._current_row_index = end_row
    progress = (self._current_row_index / self._rows_to_process) * 100
    
    # If more rows to process, schedule next chunk
    if self._current_row_index < self._rows_to_process:
        QTimer.singleShot(0, self._populate_chunk)
    else:
        # Finalize population
        self._population_in_progress = False
        self._finalize_population()
```

This pattern is essential for operations that would otherwise block the UI thread for an extended period. By breaking the work into manageable chunks and yielding control back to the event loop between chunks (via `QTimer.singleShot(0, ...)`), the UI remains responsive and can update progress indicators, respond to user input, and provide a better overall user experience.

For the ChestBuddy application, this pattern is used in:
1. Table population when displaying large datasets
2. Data validation processing for extensive rule checks
3. CSV import operations with multiple files
4. Chart generation with complex datasets

The implementation uses Qt's timer system (specifically `QTimer.singleShot()`) to schedule each chunk of work while ensuring the UI event loop can process pending events between chunks.

### 11. State Management Pattern: TableStateManager

**Implementation**: Centralized state management for table data

**Key Components**:
1. **TableStateManager**:
   - Manages cell states (`_cell_states`: `Dict[Tuple[int, int], CellFullState]`) and validation history.
   - Handles batch processing operations.
   - Tracks corrections and errors.
   - Provides correction summaries.
   - **`update_states(changes)` Method:** Merges incoming `CellFullState` updates with existing states, only storing/emitting changes. Uses `dataclasses.asdict` for robust merging.
   - **`headers_map` Property:** Provides a public property `headers_map: Dict[str, int]` mapping column names to indices, created/updated via `_create_headers_map` / `update_headers_map`.
   - **`get_full_cell_state(row, col)` Method:** Returns the complete `CellFullState` object for a cell, or `None` if no specific state is stored (implying default `NORMAL` state).
   - Emits `state_changed(set)` signal with coordinates of affected cells.

2. **Progress Reporting**:
   - Non-blocking batch operations.
   - Progress visualization.
   - Correction logging.
   - Error aggregation.

**Example Implementation**:
```python
class TableStateManager:
    def __init__(self):
        self._states = {}  # (row, col) -> CellState
        self._correction_log = []
        self._error_log = []
        self._batch_size = 100
        
    def process_validation(self, data, progress_callback):
        """Process validation in batches with progress reporting"""
        
    def process_correction(self, data, progress_callback):
        """Process corrections in batches with logging"""
        
    def get_correction_summary(self):
        """Get summary of applied corrections"""
```

**Integration with MVC**:
- **Model**: Stores cell states and correction history
- **View**: Updates UI based on state changes
- **Controller**: Coordinates state updates and UI refresh

**Key Features**:
1. Batch Processing:
   - Fixed batch size of 100 rows
   - Non-blocking operations
   - Progress reporting

2. State Tracking:
   - Cell-level state management
   - Validation history
   - Correction logging

3. Error Handling:
   - Error aggregation
   - Critical error detection
   - Comprehensive logging

4. Progress Visualization:
   - Overall progress tracking
   - Correction details display
   - Error summary presentation

## Utility Patterns

### 1. SignalManager

**Purpose**: Centralized management of signal connections

**Key Features**:
- Connection tracking
- Safe connection and disconnection
- Debugging support
- Type checking for signals

**Implementation Example**:
```python
class SignalManager:
    def connect(self, sender, signal_name, receiver, slot_name):
        # Create and track connection
        getattr(sender, signal_name).connect(getattr(receiver, slot_name))
        self._connections.append((sender, signal_name, receiver, slot_name))
```

### 2. UpdateManager

**Purpose**: Optimized UI updates

**Key Features**:
- Update scheduling
- Data dependency tracking
- Batch updates
- Update prioritization

**Implementation Example**:
```python
class UpdateManager:
    def schedule_update(self, component, data_state=None):
        # Schedule component for update based on data state
        self._update_queue.append((component, data_state))
        self._process_updates()
```

### 3. ServiceLocator

**Purpose**: Access to application services

**Key Features**:
- Service registration
- Service lookup
- Dependency management

**Implementation Example**:
```python
# Register service
ServiceLocator.register("validation_service", validation_service)

# Lookup service
validation_service = ServiceLocator.get("validation_service")
```

## Integration Patterns

### 1. Controller Integration

The controllers are integrated through:
- Clear responsibilities
- Explicit dependencies
- Signal-based communication

**Example**: UIStateController and DataViewController Integration
```python
# In app.py
self._ui_state_controller = UIStateController(self._signal_manager)
self._data_view_controller = DataViewController(
    self._data_model,
    self._signal_manager,
    ui_state_controller=self._ui_state_controller
)

# In DataViewController
def _connect_to_ui_state_controller(self):
    if self._ui_state_controller:
        # Connect to UI state controller signals
```

### 2. View-Controller Integration

Views and controllers are integrated through:
- Controller references in views
- Signal connections
- Update notifications

**Example**: Validation View-Controller Integration
```python
# In MainWindow
self._validation_view = ValidationViewAdapter(self._validation_service)
self._data_view_controller.connect_to_view(self._validation_view)

# In DataViewController
def connect_to_view(self, view):
    # Connect to view signals and set up event handling
```

### 3. Model-Service Integration

Models and services are integrated through:
- Service operations on models
- Model notifications to services
- Clear data access patterns

**Example**: ValidationService and DataModel Integration
```python
# In ValidationService
def validate_data(self, dataframe):
    # Validate dataframe and return results
    
# In DataViewController
def validate_data(self):
    results = self._validation_service.validate_data(self._data_model.data)
    self.validation_completed.emit(results)
```

## Completed Validation System Integration

The validation system integration represents the final piece of the ChestBuddy application architecture. It demonstrates the seamless integration of all the design patterns discussed above:

1. **MVC Pattern**: Clear separation between validation data (model), UI representation (view), and coordination logic (controller).

2. **Observer Pattern**: Signal-based communication between validation components, with UIStateController observing validation results.

3. **Service Layer**: ValidationService encapsulating all validation logic.

4. **Adapter Pattern**: ValidationViewAdapter providing a standardized interface to validation UI components.

5. **Command Pattern**: Validation operations encapsulated as commands.

6. **State Pattern**: Validation state tracking in UIStateController.

7. **Controller Integration**: UIStateController and DataViewController coordinating validation workflows.

8. **Testing Infrastructure**: Comprehensive unit, integration, and end-to-end tests for validation functionality.

This integration demonstrates the power and flexibility of the architecture we've established, showing how all components work together to create a cohesive, maintainable system.

## Signal-Slot Patterns

### Data Validation Signal Flow

The ChestBuddy application uses a robust signal-slot mechanism for propagating validation results from the data model to the UI components. This pattern ensures loose coupling between components while maintaining a clear data flow.

#### Validation Signal Chain

1. **ChestDataModel → ValidationService → UI Components**:
   ```
   ValidationService.validate_data()
     ↓
   ValidationService._update_validation_status()
     ↓
   ChestDataModel.set_validation_status()
     ↓ [emit validation_changed signal]
   ValidationTabView._on_validation_changed()
     ↓ [emit validation_changed signal]
   ValidationViewAdapter and other UI components
   ```

2. **Signal Definition Best Practices**:
   - Define signals with explicit parameter types: `Signal(object)` for DataFrames
   - Document signal parameters in comments and method signatures
   - Use type hints for signal handler parameters: `def _on_validation_changed(self, status_df: pd.DataFrame)`

3. **Connection Safety Patterns**:
   - Disconnect signals before reconnecting to prevent duplicate connections
   - Use try/except to handle disconnection of signals that might not be connected
   - Log connection and disconnection events for debugging
   - Add fallback mechanisms for service dependencies (ServiceLocator pattern)

4. **Signal Handling Patterns**:
   - Create dedicated methods for signal handling with clear naming (_on_X)
   - Keep signal handlers focused on a single responsibility
   - Maintain consistent parameter semantics across the connection chain
   - Emit signals with appropriate parameters, even if empty (DataFrame() instead of no params)

#### Example Signal Flow Code

1. **Signal Definition in ChestDataModel**:
   ```python
   # Define the signal with object parameter
   validation_changed = Signal(object)  # Will emit the validation status DataFrame
   
   def set_validation_status(self, status_df: pd.DataFrame) -> None:
       """Set the validation status DataFrame."""
       self._validation_status = status_df.copy()
       # Emit signal with the updated status DataFrame
       self.validation_changed.emit(self._validation_status)
   ```

2. **Signal Connection in ValidationService**:
   ```python
   def _update_validation_status(self, validation_results: Dict) -> None:
       """Update validation status in the data model."""
       # Process validation results
       status_df = self._create_status_dataframe()
       # ...process results...
       
       # Update the model, which will emit validation_changed
       self._data_model.set_validation_status(status_df)
   ```

3. **Signal Handling in ValidationTabView**:
   ```python
   def _connect_signals(self) -> None:
       """Connect signals and slots."""
       # Connect signals from validation service
       if hasattr(self._validation_service, "validation_changed"):
           # Disconnect existing connections first to prevent duplicates
           try:
               self._validation_service.validation_changed.disconnect(self._on_validation_changed)
               logger.debug("Disconnected existing validation_changed signal.")
           except (TypeError, RuntimeError):
               logger.debug("No existing validation_changed signal to disconnect.")

           # Connect the signal
           self._validation_service.validation_changed.connect(self._on_validation_changed)
           logger.debug("Connected validation_changed signal to _on_validation_changed.")
       else:
           logger.warning("ValidationService has no validation_changed signal.")
   
   def _on_validation_changed(self, status_df: pd.DataFrame) -> None:
       """Handle validation changes."""
       logger.info(f"Received validation_changed signal with status shape: {status_df.shape}")
       self._set_status_message("Validation status updated.")
       # Emit our own signal if needed by parent components
       self.validation_changed.emit(status_df)
   ```

The validation signal pattern allows for flexible component configuration while maintaining a consistent flow of validation data through the application. This approach ensures that validation results are properly displayed in the UI regardless of which component initiates the validation process.

## 13. Correction System Architecture Pattern

The refactored correction system follows a comprehensive architecture that integrates with existing patterns while introducing specialized components for rule-based corrections.

### Core Architecture

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Model Layer  │◄────►│ Service Layer │◄────►│ Controller    │
│               │      │               │      │ Layer         │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        │                      │                      │
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ CorrectionRule│      │CorrectionServi│      │CorrectionContr│
│ Model         │◄────►│ce             │◄────►│oller          │
└───────────────┘      └───────────────┘      └───────┬───────┘
                                                      │
                                                      │
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │  View Layer   │
                                              │               │
                                              └───────┬───────┘
                                                      │
                                                      │
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │CorrectionView │
                                              │               │
                                              └───────────────┘
```

### Pattern Implementation Details

#### 1. Model Layer
- **CorrectionRule**: Simple data class representing a correction rule mapping
- **CorrectionRuleManager**: Manages persistence and CRUD operations for rules
- **Rule storage**: CSV-based with clear structured format
- **Specialized Model Capabilities**:
  - Rule ordering and prioritization
  - Category-based organization
  - Status tracking (enabled/disabled)

#### 2. Service Layer
- **CorrectionService**: Core business logic for applying corrections
- **Two-pass correction algorithm**:
  - First pass: Apply general rules
  - Second pass: Apply category-specific rules
- **Integration with ValidationService** for identifying invalid cells
- **Background processing** support for performance

#### 3. Controller Layer
- **CorrectionController**: Mediates between views and service layer
- **Orchestrates UI operations**:
  - Rule management (add, edit, delete, reorder)
  - Rule application with progress tracking
  - Configuration management
- **Error handling and recovery**
- **Event propagation** using signal/slot mechanism

#### 4. View Layer
- **CorrectionView**: User interface for rule management
- **CorrectionRuleTable**: Table with sorting and filtering
- **BatchCorrectionDialog**: UI for creating multiple rules
- **ProgressDialog**: Feedback during correction operations
- **UI-only responsibilities** with business logic in controller/service

### Integration with Existing Patterns

The correction system leverages several of our established patterns:

#### 1. Observer Pattern
```python
# Signal declarations in CorrectionController
class CorrectionController(BaseController):
    # Signals
    correction_started = Signal(str)  # Strategy name
    correction_completed = Signal(str, int)  # Strategy name, affected rows
    correction_error = Signal(str)  # Error message
    operation_error = Signal(str)  # General error message
    
    # Signal emissions
    def apply_corrections(self):
        self.correction_started.emit("Applying corrections")
        # ... correction logic ...
        self.correction_completed.emit("Corrections applied", affected_count)
```

#### 2. Service Pattern
```python
class CorrectionService:
    def __init__(self, rule_manager, data_model):
        self._rule_manager = rule_manager
        self._data_model = data_model
        
    def apply_corrections(self, only_invalid=False):
        """Apply corrections to the data model"""
        # Core business logic
```

#### 3. Adapter Pattern
```python
class CorrectionViewAdapter(BaseView):
    """Adapter to integrate correction functionality with the main UI"""
    def __init__(self, correction_controller):
        super().__init__("Correction")
        self._controller = correction_controller
        self._setup_ui()
        self._connect_signals()
```

#### 4. Command Pattern
```python
class ApplyCorrectionRuleCommand:
    """Command for applying a single correction rule"""
    def __init__(self, service, rule, data_model):
        self.service = service
        self.rule = rule
        self.data_model = data_model
        
    def execute(self):
        return self.service.apply_single_rule(self.rule)
```

#### 5. Worker Pattern
```python
class CorrectionWorker(QObject):
    """Worker for handling corrections in a background thread"""
    progress = Signal(int, int)  # current, total
    result = Signal(dict)  # correction results
    finished = Signal()  # work complete
    
    def run(self):
        """Execute correction processing in background"""
        # Background processing logic
```

### Key Design Decisions

1. **Strict separation between UI and business logic**:
   - UI components never directly manipulate data
   - Controllers mediate all interactions
   - Services contain all business logic

2. **Two-level prioritization for rules**:
   - Category-level: general vs. specific categories
   - Order within category: position in the list

3. **Background processing with progress reporting**:
   - Worker objects for non-blocking operations
   - Progress signals for UI feedback
   - Cancellation support

4. **Visual feedback integration**:
   - Non-invasive integration with existing highlighting system
   - Color-coded cell states for different correction situations

5. **Rule storage**:
   - CSV-based persistence for simplicity and compatibility
   - Regular backups during operations
   - Import/export support

This architecture provides a clean, maintainable system for managing correction rules and applying them to data, while maintaining strict separation of concerns and leveraging existing architectural patterns.

## Correction System Architecture

The correction system is designed to automatically fix invalid data entries based on predefined correction rules. The system is being enhanced with the following improvements:

1. **Recursive Correction** - Apply corrections repeatedly until no more matches
2. **Selection-Based Correction** - Apply corrections to selected data only
3. **Correctable Status Detection** - Identify which invalid entries can be fixed
4. **Auto-Correction Options** - Control when corrections are applied automatically

### Key Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  DataController │     │  CorrectionCtrl │     │  ValidationCtrl │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   DataService   │     │ CorrectionService│     │ValidationService│
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────►◄──────┴───────────────►◄──────┘
                             DataModel
```

### Data Flow

1. **Validation Process**:
   - DataController loads data
   - ValidationController validates data
   - Invalid entries are marked
   - CorrectionController identifies correctable entries

2. **Correction Process**:
   - CorrectionController initiates correction
   - CorrectionService applies rules to data
   - If recursive, process repeats until no more corrections
   - ValidationController re-validates data
   - DataView updates to show corrected data

### Validation Status Workflow

```
┌─────────┐     ┌─────────┐     ┌─────────────┐     ┌────────────┐
│  VALID  │     │ INVALID │────►│ CORRECTABLE │────►│  CORRECTED │
└─────────┘     └─────────┘     └─────────────┘     └────────────┘
                      ▲                                   │
                      └───────────────────────────────────┘
```

## View System Architecture

ChestBuddy uses a view-based architecture with the following key components:

1. **MainWindow** - The main application window that hosts all views
2. **ViewStateController** - Manages view navigation and history
3. **View Components** - Individual UI components for different functions

### View Hierarchy

```
MainWindow
├── SidebarView
├── ContentArea
│   ├── DashboardView
│   ├── DataView
│   ├── ValidationView
│   ├── CorrectionView
│   └── ChartView
└── StatusBar
```

## Controller Architecture

Controllers manage application logic and coordinate between the UI and services:

1. **DataController** - Manages data operations
2. **ValidationController** - Manages data validation
3. **CorrectionController** - Manages data correction
4. **FileOperationsController** - Manages file operations
5. **ChartController** - Manages chart generation
6. **ViewStateController** - Manages navigation between views

## Service Architecture

Services implement business logic and interact with the data model:

1. **DataService** - Core data operations
2. **ValidationService** - Data validation logic
3. **CorrectionService** - Data correction logic
4. **ChartService** - Chart generation logic
5. **ImportExportService** - Import/export functionality

## Data Model

The data model is a structure that holds the application data and provides methods for data access and manipulation:

1. **DataModel** - The main model that holds all data
2. **ValidationModel** - Stores validation rules and results
3. **CorrectionModel** - Stores correction rules

## Configuration Management

The application uses a centralized configuration system:

1. **ConfigManager** - Manages application settings
2. **Default Settings** - Provides default configuration values
3. **User Settings** - Stored in config.ini 