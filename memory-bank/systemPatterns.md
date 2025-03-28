---
title: System Patterns - ChestBuddy Application
date: 2023-04-02
---

# System Patterns

*Last Updated: 2023-10-18*

## Core Architecture

ChestBuddy follows a layered architecture with clear separation of concerns:

### Layer Structure
1. **UI Layer**: PySide6-based user interface components
   - Views (Dashboard, Data, Reports, Settings)
   - Widgets (custom UI components)
   - **UI State Management System** (for managing UI blocking/unblocking)
2. **Application Layer**: Business logic and coordination
   - Services (DataService, ValidationService, etc.)
   - Controllers (coordinating between UI and data)
3. **Domain Layer**: Core business logic
   - Models (data structures and business rules)
   - Validators (data validation logic)
4. **Data Layer**: Data persistence and retrieval
   - Repositories (data access)
   - CSV handling and persistence

### Pattern: UI State Management System

We've implemented a centralized UI State Management system to handle UI blocking and unblocking during long-running operations. This replaces the previous ad-hoc approach with a systematic, reference-counted solution.

#### Components
1. **UIStateManager**: Singleton class that manages the UI state
   - Tracks blockable UI elements and element groups
   - Manages blocking operations with reference counting
   - Emits signals for UI state changes
   - Thread-safe implementation

2. **BlockableElementMixin**: Mixin for UI elements that can be blocked
   - Provides standard methods for blocking/unblocking
   - Tracks which operations are blocking an element
   - Allows custom block/unblock behavior

3. **OperationContext**: Context manager for UI blocking operations
   - Automatically blocks elements when entering context
   - Unblocks elements when exiting (even if exceptions occur)
   - Supports operation naming and status tracking

4. **UIOperations & UIElementGroups**: Enums for standardizing operations and element groups
   - Provides consistency in naming operations (IMPORT, EXPORT, etc.)
   - Standardizes element group definitions (MAIN_WINDOW, DATA_VIEW, etc.)

#### Key Design Principles
1. **Centralized Control**: Single source of truth for UI state
2. **Reference Counting**: Properly handles nested operations
3. **Thread Safety**: Mutex-protected for concurrent access
4. **Declarative API**: Simple and clear interface for blocking/unblocking
5. **Automatic Cleanup**: Context managers ensure proper unblocking

#### Usage Pattern
```python
# Block UI elements during an operation
with OperationContext(ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.MAIN_WINDOW]):
    # Perform long-running operation
    import_data()
    
    # UI elements are automatically unblocked when context exits
```

## Design Patterns

### Singleton Pattern
Used for global managers and services that should have only one instance:
- ConfigManager
- LogManager
- DataManager
- **UIStateManager**

### Observer Pattern
Implemented through Qt's signal/slot mechanism:
- UI components observe data model changes
- Progress updates from background workers
- **UI state changes from UIStateManager**

### Factory Pattern
Used for creating UI components and data structures:
- ViewFactory for creating view instances
- WidgetFactory for custom widgets
- DialogFactory for standard dialogs

### Strategy Pattern
Used for interchangeable algorithms:
- Validation strategies for different data types
- Import strategies for different file formats
- Export strategies for different output formats

### Command Pattern
Used for undoable operations:
- Data edits
- Validation rule changes
- Configuration changes

## Threading Model

### Background Processing
- BackgroundWorker class manages threading
- QThread for UI-independent operations
- Signals/slots for thread communication
- **Integration with UIStateManager for UI blocking during background operations**

### Thread Safety
- Mutex locks for shared resources
- Thread-local storage for thread-specific data
- Signals/slots for safe cross-thread communication
- **UIStateManager uses QMutex for thread-safe operation**

## State Management

### Application State
- ConfigManager for persistent settings
- DataManager for data loading state
- **UIStateManager for UI blocking state**

### UI State
- View-specific state management
- Coordinated through MainWindow
- **Centralized blocking/unblocking through UIStateManager**

## Component Communication

### Signal-based Communication
- Qt signals/slots between components
- Custom signals for application-specific events
- **UIStateManager signals for UI state changes**

### Service-based Communication
- Services as intermediaries between components
- Injectable services for dependency management

## Error Handling

### Exception Management
- Try/except blocks at appropriate boundaries
- Error logging and reporting
- User-friendly error messages
- **OperationContext ensures UI unblocking even when exceptions occur**

### Validation
- Input validation in UI layer
- Business rule validation in domain layer
- Data integrity validation in data layer

## Logging and Diagnostics

### Logging Levels
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Potential issues that don't affect operation
- ERROR: Errors that affect operation but allow recovery
- CRITICAL: Errors that prevent operation

### Log Categories
- UI events
- Data operations
- Background processing
- **UI state changes**

## Application Architecture

The ChestBuddy application follows a layered architecture pattern with these key layers:

### 1. Presentation Layer (UI)
- **MainWindow**: Central UI container that manages views and navigation
- **SidebarNavigation**: Provides navigation between different application views
- **ViewAdapters**: Bridge between views and the application layer
- **Components**: Reusable UI elements like buttons, toolbars, and widgets

### 2. Application Layer (Services)
- **DataManager**: Coordinates data loading, saving, and manipulation
- **ConfigManager**: Handles application configuration and settings
- **ValidationService**: Manages validation rules and processing
- **CorrectionService**: Applies corrections to identified data issues
- **DashboardService**: Provides dashboard statistics and chart data (planned)

### 3. Domain Layer (Core Logic)
- **Models**: Core data structures representing chest data
- **Rules**: Business logic for data validation and processing
- **Algorithms**: Analysis and processing algorithms
- **Events**: Domain events representing significant state changes

### 4. Infrastructure Layer (Data & System)
- **FileIO**: Handles file reading and writing operations
- **Database**: Manages persistent storage (SQLite)
- **Logging**: System-wide logging functionality
- **Configuration**: Application settings storage and retrieval

## UI Component Library

ChestBuddy implements a custom UI component library designed for consistency and reusability:

### ActionButton
- **Purpose**: Standardized button with consistent styling and behavior
- **Features**:
  - Icon support (leading or trailing)
  - Multiple styles (primary, secondary, danger)
  - Size variations (small, medium, large)
  - Disabled state styling
  - Customizable tooltips

### ActionToolbar
- **Purpose**: Container for organizing action buttons
- **Features**:
  - Horizontal or vertical orientation
  - Consistent spacing and alignment
  - Button grouping capabilities
  - Overflow handling for smaller screens
  - Style coordination with ActionButtons

### EmptyStateWidget
- **Purpose**: Visual feedback when content is unavailable
- **Features**:
  - Customizable title and message
  - Icon display
  - Action button for resolution
  - Consistent visual style with the application
  - Signal for action button clicks

### FilterBar
- **Purpose**: Interface for searching and filtering data
- **Features**:
  - Search field with clear button
  - Filter button with dropdown options
  - Placeholder text customization
  - Search term highlighting
  - Real-time filtering capability

### Dashboard Components (Phase 3)

#### StatCard
- **Purpose**: Display data metrics with visual indicators
- **Features**:
  - Icon support for visual context
  - Trend indicators (up/down arrows)
  - Click actions for navigation
  - Color customization based on value
  - Compact and expanded modes

#### ChartPreview
- **Purpose**: Display interactive chart previews with context
- **Features**:
  - Qt Charts integration for chart rendering
  - Title and subtitle display for context
  - Clickable interaction for detailed view
  - Compact mode for space-efficient display
  - Placeholder state when no chart is available
  - Icon support for additional context
  - Responsive layout adjustments

#### ActionCard
- **Purpose**: Interactive card for dashboard actions
- **Features**:
  - Title and description display
  - Icon support for visual context
  - Hover and click effects for better UX
  - Signal emission for action triggering
  - Callback support for direct function calls
  - Consistent styling with application theme
  - Located at: `chestbuddy/ui/widgets/action_card.py`

#### ChartCard
- **Purpose**: Display chart thumbnails with context
- **Features**:
  - Chart thumbnail with proper sizing and scaling
  - Title and description for context
  - Chart identifier for navigation
  - Signal emission for chart selection
  - Interactive hover and click states
  - Placeholder for missing thumbnails
  - Located at: `chestbuddy/ui/widgets/chart_card.py`

#### Enhanced RecentFilesList
- **Purpose**: Display recent files with metadata and actions
- **Features**:
  - File metadata display (size, date, row count)
  - Quick action buttons per file
  - File status indicators
  - Sorting and filtering capabilities
  - Empty state handling

#### WelcomeStateWidget
- **Purpose**: Provide first-time user experience
- **Features**:
  - Application branding and introduction
  - Getting started guidance
  - Quick start action buttons
  - Preference to disable in future sessions
  - Responsive layout for different screen sizes

## Navigation and State Management

### Sidebar Navigation System
- **Structure**: Hierarchical navigation with primary and secondary items
- **State Management**: Navigation items can be enabled/disabled based on application state
- **Visual Feedback**: Clear indication of current view and disabled items
- **Customization**: Configurable through the ConfigManager

### State-Dependent Navigation
- **Data Loading State**: Navigation sections requiring loaded data are disabled when no data is available
- **View Transitions**: Smooth transitions between views with state preservation
- **History Management**: Back/forward navigation capability
- **Persistent State**: View state is stored between sessions

### Empty State Handling
- **Data Required Views**: Views that require data display EmptyStateWidget when no data is loaded
- **Custom Messages**: Each view provides specific guidance when data is missing
- **Action Integration**: Empty state actions connect directly to data loading functionality
- **Consistent Experience**: Unified approach to no-data states across the application

### Dashboard States (Phase 3 Plan)
- **Welcome State**: First-time user experience with getting started information
- **Empty State**: No data loaded, prompting for data import
- **Data Loaded State**: Shows insights and statistics about loaded data
- **Error State**: Displays information about errors and recovery actions
- **State Transitions**: Handled by DashboardViewAdapter based on application state

## Design Principles

### Signal-Based Communication
- Components communicate through Qt signals and slots
- Changes in one component can trigger updates in others
- Clear separation of concerns with loose coupling
- Event-driven architecture for responsive UI

### Consistent Styling
- Unified color scheme defined in StyleConstants
- Common margins, paddings, and spacing values
- Typography system with defined text styles
- Shared icons and visual elements

### Property-Based Configuration
- UI components are configured through QProperties
- Dynamic updates when properties change
- Default values with override capabilities
- Type checking for properties

### Composition over Inheritance
- UI components built by composing smaller elements
- Limited inheritance depth to avoid complexity
- Clear interfaces between components
- Focused component responsibilities

### Test-Driven Development
- Comprehensive test suite for UI components
- Mock objects for testing complex interactions
- Automated UI testing for critical paths
- Performance testing for data-intensive operations

## Data Management

### Data Flow Patterns
- **Import → Validation → Correction → Analysis → Export** pipeline
- Clear boundaries between processing stages
- Progress tracking throughout the pipeline
- Error handling at each stage

### State Management
- Observable data models via Qt's Model/View framework
- Centralized DataManager for coordinating data operations
- Change notification via signals
- Undo/redo capability for data modifications

### Dashboard Data Service (Phase 3 Plan)
- **Statistics Calculation**: Compute metrics from data model
- **Chart Data Generation**: Prepare data for chart visualizations
- **User Activity Tracking**: Monitor frequently used actions
- **Dashboard Configuration**: Manage dashboard layout preferences
- **Data Change Monitoring**: Update dashboard on data changes

### Data Loading Process
1. File selection via standard dialog
2. Progress indication during loading
3. Initial validation of data structure
4. Population of data models
5. UI update with loaded data

### Data Processing
1. Validation rules application
2. Issue identification and categorization
3. Correction suggestions generation
4. Manual or automated corrections
5. Results visualization

### Data Export
1. Format selection (CSV, Excel, PDF)
2. Export configuration options
3. Progress indication during export
4. Success confirmation with file location
5. Error handling for export failures

## Testing Strategy

### Component Testing
- Individual UI components tested in isolation
- Property verification
- Signal emission testing
- Visual appearance verification
- Edge case handling

### Integration Testing
- Component interactions tested
- Data flow verification
- State transitions
- Error propagation

### End-to-End Testing
- Complete workflows tested
- File import/export
- Data processing pipeline
- Configuration persistence

## Extension and Plugin Architecture

### Plugin Interfaces
- **DataImportPlugin**: Custom data import formats
- **ValidationRulePlugin**: Custom validation rules
- **VisualizationPlugin**: Custom chart types
- **ExportFormatPlugin**: Custom export formats

### Future Architectural Considerations
- Multi-user support
- Cloud integration
- Mobile companion application
- Distributed processing for large datasets

## Dashboard Redesign Architecture (Phase 3 Plan)

### Component Relationships

```
┌───────────────────┐          ┌─────────────────────┐
│ DashboardAdapter  │◄────────►│  DashboardService   │
└───────┬───────────┘          └─────────┬───────────┘
        │                                 │
        │                                 │
        ▼                                 ▼
┌───────────────────┐          ┌─────────────────────┐
│   DashboardView   │◄────────►│   DataModel/Other   │
└───────┬───────────┘          │      Services       │
        │                      └─────────────────────┘
        │
        ├─────────────┬─────────────┬──────────────┐
        │             │             │              │
        ▼             ▼             ▼              ▼
┌───────────────┐ ┌─────────────┐ ┌────────────┐ ┌──────────────┐
│   StatCard    │ │ChartPreview │ │ ActionCard │ │RecentFilesList│
└───────────────┘ └─────────────┘ └────────────┘ └──────────────┘
```

### Key Architectural Patterns for Dashboard

1. **Adapter Pattern**:
   - DashboardViewAdapter mediates between MainWindow and DashboardView
   - Handles data state transitions and UI updates
   - Connects dashboard components to application services
   - Manages dashboard configuration

2. **Service Pattern**:
   - DashboardService provides data to dashboard components
   - Abstracts data retrieval and processing logic
   - Monitors data changes and updates dashboard
   - Handles dashboard-specific configuration

3. **Composite Pattern**:
   - Dashboard composed of multiple smaller components
   - Each component is self-contained with its own responsibility
   - Components communicate through well-defined interfaces
   - Layout manager handles component arrangement

4. **State Pattern**:
   - Dashboard handles multiple states (welcome, empty, data loaded)
   - State transitions are managed by the adapter
   - Each state has specific visual representation
   - Components respond to state changes

5. **Observer Pattern**:
   - Dashboard components observe data model changes
   - Components update when observed data changes
   - Loose coupling between data and visualization
   - Signal/slot mechanism for change notification

## Key Design Patterns

### 1. Model-View-Controller (MVC)

The application follows an MVC pattern:
- **Models**: Responsible for data structure and business logic
- **Views**: UI components for data display and user interaction
- **Controllers**: Coordinate between models and views

### 2. Service Layer

Services encapsulate specific functionality and are injected where needed:
- `CSVService`: Handles CSV file operations
- `ValidationService`: Validates data against rules
- `CorrectionService`: Applies corrections to data
- `ConfigService`: Manages application configuration
- `ChartService`: Generates data visualizations
- *Planned* `ReportService`: Will handle report generation

### 3. Dependency Injection

Dependencies are injected through constructors rather than created internally:
```python
def __init__(self, config_service: ConfigService, csv_service: CSVService):
    self._config_service = config_service
    self._csv_service = csv_service
```

### 4. Event-Driven Communication

Components communicate through Qt signals and slots:
```python
# Signal definition
data_loaded = Signal(pd.DataFrame)

# Connection
self._data_service.data_loaded.connect(self._on_data_loaded)

# Slot implementation
@Slot(pd.DataFrame)
def _on_data_loaded(self, df: pd.DataFrame) -> None:
    # Handle loaded data
```

### 5. Background Processing

Long-running operations are executed in background threads:
```python
# Running a task in background
self._worker.run_task(
    self._csv_service.load_csv, 
    file_path, 
    on_success=self._on_load_success,
    on_error=self._on_load_error
)
```

### 6. UI Component Composition

UI is built through composition of smaller components:
```python
# Main view composed of header and content
self._header = ViewHeader("Dashboard")
self._content = QWidget()
self._content_layout = QVBoxLayout(self._content)

# Add components to layout
self._content_layout.addWidget(self._chart_view)
self._content_layout.addWidget(self._stats_panel)
```

### 7. UI Widget Pattern

Custom widgets are created for reusable UI elements with consistent behavior and styling. Each widget follows patterns:

1. **Base Widget Class**: Define custom widget inheriting from Qt class with controlled API
2. **State Management**: Internal state tracking with signals for state changes
3. **Styling**: Use Colors and stylesheet constants for consistent appearance
4. **Custom Painting**: Override paintEvent for custom appearance when needed

Examples:
```python
# Signal definitions
valueChanged = Signal(int)
stateChanged = Signal(int)

# Property definition with getter/setter
@Property(int, value, setValue)
def progress(self):
    return self._value

# Custom painting
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    # Custom drawing code
```

Key UI widgets:
- `ProgressBar`: Custom progress bar with state-based styling (normal, success, error)
- `ProgressDialog`: Dialog wrapping ProgressBar with enhanced functionality
- `StatusBar`: Custom status bar with multiple information sections
- `ViewHeader`: Standardized header for application views
- `ActionButton`: Customizable button with consistent styling for actions
  - Supports text, icon, or both
  - Offers primary and secondary styling variants
  - Configurable for compact mode (icon only with tooltip)
  - Manages enabled/disabled state with appropriate visual feedback
  - Provides hover and pressed state styling
  - Emits clicked signal for action handling
  
- `ActionToolbar`: Container for organizing related ActionButtons
  - Supports horizontal or vertical orientation
  - Can group buttons with separators for logical organization
  - Manages button visibility and enabled states
  - Handles button addition, removal and retrieval
  - Allows spacing customization between buttons
  
- `EmptyStateWidget`: Configurable empty state display with call-to-action
  - Displays title, message, and optional action button
  - Supports custom icons for visual context
  - Provides centralized layout with proper spacing
  - Emits signals when action button is clicked
  - Visually consistent representation of empty states across the application
  
- `FilterBar`: Compact search and filtering interface
  - Combines search field with expandable advanced filters
  - Supports multiple filter categories with options
  - Emits signals for filter and search text changes
  - Collapsible design to maximize content space when not in use
  - Provides clear visual feedback on active filters

### 8. Adapter Pattern for Views

View adapters connect the UI components to the application logic:
```python
class DataViewAdapter:
    def __init__(self, data_view: DataView, data_model: DataModel):
        self._data_view = data_view
        self._data_model = data_model
        
        # Connect signals
        self._data_model.data_changed.connect(self._update_view)
```

### 9. Resource Management

Resources like icons and styles are centrally managed:
```python
# Resource loading
icon = self._resource_manager.get_icon("open_file")
```

### 10. Configuration Management

Application settings are managed through a dedicated service:
```python
# Getting configuration
auto_save = self._config.get_bool("Autosave", "enabled", default=True)

# Setting configuration
self._config.set_value("Autosave", "interval", 5)
```

## Error Handling Strategy

1. **Service Level**: Catch and log specific errors, translate to appropriate signals
2. **Controller Level**: Connect error signals to UI updates
3. **UI Level**: Display error messages to users, recover gracefully
4. **Background Tasks**: Catch and report errors without crashing the application

Example error handling flow:
```python
try:
    # Operation that might fail
    result = potentially_failing_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    self.operation_failed.emit(str(e))
    return False
```

## Progress Reporting Pattern

Progress reporting follows a standardized pattern:

1. **Signal Definition**: Services define progress signals
   ```python
   load_started = Signal()
   load_progress = Signal(str, int, int)  # file_path, current, total
   load_finished = Signal(str)  # message
   ```

2. **Progress Dialog**: UI shows a custom ProgressDialog when operations start
   ```python
   # Create progress dialog
   self._progress_dialog = ProgressDialog(
       "Loading data...", 
       "Cancel", 
       0, 
       100, 
       self
   )
   self._progress_dialog.canceled.connect(self._cancel_operation)
   ```

3. **Progress Updates**: Operations emit progress updates
   ```python
   # Emit progress
   self.load_progress.emit(file_path, current_row, total_rows)
   ```

4. **State Management**: ProgressBar displays different states
   ```python
   # Set state based on result
   if success:
       self._progress_dialog.setState(ProgressBar.State.SUCCESS)
   else:
       self._progress_dialog.setState(ProgressBar.State.ERROR)
   ```

5. **Completion Handling**: Services emit finished signal
   ```python
   # Operation completed
   self.load_finished.emit("Data loaded successfully")
   ```

## File Structure 

The application follows a modular file structure:

```
chestbuddy/
├── app.py                  # Application entry point
├── config.py               # Configuration management
├── core/                   # Core functionality
│   ├── models/             # Data models
│   └── services/           # Business logic services
├── ui/                     # User interface components
│   ├── widgets/            # Reusable UI widgets
│   │   ├── progress_bar.py # Custom progress bar
│   │   └── progress_dialog.py # Custom progress dialog
│   ├── views/              # Main application views
│   ├── adapters/           # View adapters
│   └── resources/          # UI resources (icons, styles)
└── utils/                  # Utility functions and classes
    └── background_processing.py  # Background task handling
```

## Integration Points

1. **Data Loading → Validation**: Loaded data is passed to validation service
2. **Validation → Correction**: Validation results guide correction process
3. **Data → Charts**: Chart service uses data model for visualization
4. **Charts → Reports**: Chart outputs will be embedded in reports
5. **Configuration → All Components**: Configuration service informs component behavior

## Architecture Overview

The Chest Buddy application follows a Model-View-Controller (MVC) architecture with clear separation of concerns:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│     Models     │◄────┤  Controllers   │◄────┤     Views      │
│  (Data Logic)  │     │ (App Logic)    │     │  (UI Elements) │
└───────┬────────┘     └────────────────┘     └────────────────┘
        │                                             ▲
        │                                             │
        ▼                                             │
┌────────────────┐                           ┌────────────────┐
│   Services     │                           │    Config      │
│  (Utilities)   │                           │   Management   │
└───────┬────────┘                           └────────────────┘
        │
        ▼
┌────────────────┐
│  Background    │
│   Processing   │
└────────────────┘
```

## Core Components

### 1. Data Model Layer
- **ChestDataModel**: Represents the core chest data structure
- **ValidationModel**: Manages validation lists and rules
- **CorrectionModel**: Manages correction rules and transformations

### 2. Controller Layer
- **ImportController**: Handles CSV import and initial processing
- **ValidationController**: Manages validation processes
- **CorrectionController**: Applies correction rules
- **AnalysisController**: Performs data analysis operations
- **ReportController**: Manages report generation

### 3. View Layer
- **MainWindow**: Primary application interface
- **DataTableView**: Displays and highlights data
- **ChartView**: Renders visualizations
- **ValidationView**: Interface for validation management
- **CorrectionView**: Interface for correction rules
- **ReportBuilderView**: Interface for report creation

### 4. Service Layer
- **CSVService**: Handles CSV file operations
- **CharsetService**: Manages character encoding detection and correction
- **AnalysisService**: Provides data analysis functions
- **ChartService**: Generates chart visualizations
- **ReportService**: Generates HTML reports
- **DataManager**: Handles high-level data operations including loading, saving, and column mapping

### 5. Background Processing Layer
- **BackgroundWorker**: Manages execution of tasks in separate threads
- **BackgroundTask**: Base class for defining asynchronous operations
- **CSVReadTask**: Specific implementation for CSV reading operations
- **MultiCSVLoadTask**: Handles loading of multiple CSV files with progress tracking

### 6. Configuration Layer
- **ConfigManager**: Manages application settings and user preferences
- **ValidationConfig**: Manages validation list configuration
- **CorrectionConfig**: Manages correction rule configuration

### 7. Testing Layer
- **Unit Tests**: Tests for individual components and functions
- **UI Component Tests**: Tests for UI components and interactions
- **Integration Tests**: Tests for cross-component workflows
- **Workflow Tests**: End-to-end tests for complete user scenarios
- **Performance Tests**: Tests for measuring performance metrics

## Key Design Patterns

### 1. Observer Pattern
Used for updating views when data models change:
- Data models emit signals when modified
- Views subscribe to relevant signals
- Ensures UI stays synchronized with data state

### 2. Strategy Pattern
Used for validation and correction operations:
- Common interface for different validation strategies
- Different correction approaches can be swapped
- Allows for flexible rule application

### 3. Factory Pattern
Used for creating visualization components:
- ChartFactory creates different chart types based on user selection
- ReportElementFactory creates different report elements

### 4. Singleton Pattern
Used for configuration and service instances:
- ConfigManager as a singleton
- Ensures consistent access to configuration

### 5. Command Pattern
Used for validation and correction operations:
- Each operation is encapsulated as a command
- Allows for undo/redo functionality
- Maintains operation history

### 6. Worker Pattern
Used for background processing:
- BackgroundWorker manages thread lifecycle
- Tasks implement a common interface (BackgroundTask)
- Signal-based communication between threads
- Ensures UI responsiveness during heavy operations

### 7. Fixture Pattern
Used for testing:
- Common test fixtures for reusable test setup
- Data fixtures for consistent test data
- Component fixtures for UI testing
- Ensures consistent test environments

## Test Architecture

The test architecture follows a layered approach to verify application functionality at multiple levels:

```
┌────────────────┐
│  Workflow      │
│    Tests       │ End-to-end user workflow tests
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Integration   │
│    Tests       │ Cross-component interaction tests
└───────┬────────┘
        │
        ▼
┌────────────────┐     ┌────────────────┐
│  UI Component  │     │  Background    │
│    Tests       │     │ Process Tests  │
└───────┬────────┘     └───────┬────────┘
        │                      │
        ▼                      ▼
┌────────────────┐     ┌────────────────┐
│  Unit Tests    │     │ Performance    │
│                │     │    Tests       │
└────────────────┘     └────────────────┘
```

## Data Flow

1. **Import Flow**:
   - CSV file → CSVService → ChestDataModel → DataTableView
   - Optional automatic validation and correction

2. **Background Import Flow**:
   - CSV file → CSVService → CSVReadTask → BackgroundWorker → ChestDataModel → DataTableView
   - Progress reporting during import
   - Non-blocking UI during processing

3. **Validation Flow**:
   - ChestDataModel → ValidationController → ValidationModel → ChestDataModel (updated)
   - UI feedback on validation errors

4. **Correction Flow**:
   - ChestDataModel → CorrectionController → CorrectionModel → ChestDataModel (corrected)
   - UI updates to show corrections

5. **Analysis Flow**:
   - ChestDataModel → AnalysisController → AnalysisService → ChartView
   - User-selected data dimensions determine visualization

6. **Report Flow**:
   - ChestDataModel + Charts → ReportController → ReportService → HTML Output
   - User-customized report elements

7. **Test Flow**:
   - Test Case → Test Fixtures → Component Under Test → Assertions → Test Results
   - Mock external dependencies where necessary
   - Use realistic data for integration and workflow tests

## Module Organization

```
chestbuddy/
├── core/
│   ├── models/
│   ├── controllers/
│   └── services/
├── ui/
│   ├── views/
│   ├── widgets/
│   └── resources/
├── utils/
│   ├── config/
│   ├── validation/
│   ├── correction/
│   └── background_processing.py
├── data/
│   ├── validators/
│   ├── correction_rules/
│   └── templates/
└── tests/
    ├── unit/
    ├── integration/
    ├── test_background_worker.py
    ├── test_csv_background_tasks.py
    ├── test_main_window.py (planned)
    ├── test_integration.py (planned)
    ├── test_workflows.py (planned)
    └── resources/
```

## Error Handling Strategy

- Comprehensive try-except blocks for all file operations
- Signal-based error reporting to the UI
- Status bar and dialog-based error notifications
- Logging of errors with sufficient context for debugging
- User-friendly error messages with suggested actions

## Testing Strategy

- Unit tests for individual components to ensure correct behavior
- UI component tests to verify proper UI initialization and interaction
- Integration tests to verify correct interaction between components
- Workflow tests to validate end-to-end user scenarios
- Performance tests to measure and ensure efficiency with large datasets
- Use of fixtures for consistent test setup and teardown
- QtBot for simulating user interactions with UI components
- Mocking external dependencies for isolation and reproducibility
- Test data generators for various test scenarios
- Cleanup mechanisms to ensure test isolation

## Background Processing Strategy

- Worker-based threading model for all long-running operations
- Clear separation between UI thread and worker threads
- Signal-based communication for progress updates and results
- Cancellation support for long-running operations
- Resource cleanup on task completion or cancellation
- Chunked processing for memory-intensive operations
- Improved thread management with graceful cleanup during application shutdown
- Two-level progress reporting for multi-file operations (overall progress and per-file progress)
- Consistent progress reporting on a 0-100 scale for all background tasks
- Callbacks for detailed progress reporting during complex operations

### Progress Dialog Architecture

The progress dialog system implements a comprehensive approach to providing feedback during long-running operations:

```mermaid
sequenceDiagram
    participant UI as MainWindow
    participant DM as DataManager
    participant BW as BackgroundWorker
    participant Task as MultiCSVLoadTask
    participant Dialog as ProgressDialog

    UI->>DM: load_csv_files(files)
    DM->>BW: start_task(MultiCSVLoadTask)
    BW->>Task: run()
    BW-->>DM: load_started
    DM-->>UI: load_started
    UI->>Dialog: show()
    
    loop For each file
        Task->>Task: process_file()
        Task-->>BW: progress_updated(file_index, file_count, file_progress)
        BW-->>DM: load_progress
        DM-->>UI: load_progress
        UI->>Dialog: update(overall_progress, file_info)
        
        UI->>DM: check_cancel
        DM->>BW: check_cancel
        BW->>Task: check_cancel
    end
    
    Task-->>BW: task_finished(result)
    BW-->>DM: load_finished
    DM-->>UI: load_finished
    UI->>Dialog: complete()
```

The progress reporting follows a consistent pattern:
1. Task initialization triggers load_started signal
2. Regular progress updates during processing with contextual information
3. Completion triggers load_finished signal with results
4. Cancellation can be checked and applied at any point in the process

### Multi-File Processing Pattern

For operations involving multiple files:

```mermaid
graph TD
    Start[Start Task] --> Init[Initialize Progress Tracking]
    Init --> FileLoop[Process Next File]
    FileLoop --> FileProgress[Update File Progress]
    FileProgress --> OverallProgress[Calculate & Update Overall Progress]
    OverallProgress --> Cancel{Check Cancel}
    Cancel -->|Yes| CleanupCancel[Cleanup Resources]
    Cancel -->|No| NextFile{More Files?}
    NextFile -->|Yes| FileLoop
    NextFile -->|No| CompleteProcess[Complete Processing]
    CompleteProcess --> EmitResult[Emit Final Result]
    EmitResult --> Cleanup[Cleanup Resources]
    CleanupCancel --> EmitCancelled[Emit Cancelled]
    EmitCancelled --> Cleanup
```

## Planned Report Generation Architecture

For the upcoming Report Generation phase, we're planning to implement the following architecture:

### 1. Report Service Components

```mermaid
classDiagram
    class ReportService {
        +generate_report(template, data, charts)
        +export_to_pdf(report)
        +list_templates()
        +preview_report(report)
    }
    
    class ReportTemplate {
        +String name
        +String description
        +Dict sections
        +apply(data, charts)
    }
    
    class PDFExporter {
        +export(report_html)
        -setup_page_settings()
        -embed_charts()
        -apply_styling()
    }
    
    class ReportElement {
        +String type
        +Dict properties
        +render()
    }
    
    ReportService --> ReportTemplate : uses
    ReportService --> PDFExporter : uses
    ReportTemplate --> ReportElement : contains
```

### 2. Report Generation Flow

```mermaid
graph TD
    UserRequest[User Request] --> SelectTemplate[Select Template]
    SelectTemplate --> ConfigureReport[Configure Report]
    ConfigureReport --> DataSelection[Select Data to Include]
    DataSelection --> ChartSelection[Select Charts to Include]
    ChartSelection --> GenerateReport[Generate Report]
    GenerateReport --> PreviewReport[Preview Report]
    PreviewReport --> Export{Export?}
    Export -->|Yes| ExportPDF[Export to PDF]
    Export -->|No| Return[Return to Editor]
```

### 3. Report View Architecture

```mermaid
classDiagram
    class ReportView {
        +init_ui()
        +setup_connections()
        +update_preview()
        +export_report()
    }
    
    class TemplateSelector {
        +List templates
        +selection_changed()
    }
    
    class ReportConfigPanel {
        +setup_options()
        +apply_config()
    }
    
    class DataSelectionPanel {
        +show_available_data()
        +get_selected_data()
    }
    
    class ChartSelectionPanel {
        +show_available_charts()
        +get_selected_charts()
    }
    
    class ReportPreview {
        +update_preview(html)
        +zoom_in()
        +zoom_out()
    }
    
    ReportView --> TemplateSelector : contains
    ReportView --> ReportConfigPanel : contains
    ReportView --> DataSelectionPanel : contains
    ReportView --> ChartSelectionPanel : contains
    ReportView --> ReportPreview : contains
```

This architecture will allow for flexible, customizable report generation with a focus on user experience and high-quality output. The components are designed to be modular and extensible, enabling easy addition of new report templates and export formats in the future.

## UI Architecture

The UI architecture of ChestBuddy follows a component-based design with clear separation of concerns and standardized patterns for consistency.

### UI Component Hierarchy

```mermaid
classDiagram
    class MainWindow {
        -SidebarNavigation _sidebar
        -QStackedWidget _content_stack
        -StatusBar _status_bar
        -Dict[str, BaseView] _views
        +_create_views()
        +_set_active_view(view_name)
    }
    
    class BaseView {
        -String _title
        -ViewHeader _header
        -QWidget _content
        -QVBoxLayout _content_layout
        +_setup_ui()
        +_connect_signals()
        +_add_action_buttons()
        +get_content_widget()
        +get_content_layout()
    }
    
    class ViewHeader {
        -String _title
        -QLabel _title_label
        -Dict _action_buttons
        +add_action_button(name, text, button_type)
        +get_action_button(name)
    }
    
    class SidebarNavigation {
        -List _sections
        -String _active_item
        +navigation_changed signal
        +set_active_item(item_name)
    }
    
    class DashboardView {
        -StatsCard _dataset_card
        -StatsCard _validation_card
        -StatsCard _correction_card
        -RecentFilesWidget _recent_files
        -QuickActionsWidget _quick_actions
        +action_triggered signal
        +file_selected signal
    }
    
    class AdapterView {
        -OriginalComponent _component
        +_setup_ui()
        +_connect_signals()
    }
    
    MainWindow *-- SidebarNavigation
    MainWindow *-- "many" BaseView
    BaseView <|-- DashboardView
    BaseView <|-- AdapterView
    BaseView *-- ViewHeader
    
    note for AdapterView "Abstract representation of all adapter views:\n- DataViewAdapter\n- ValidationViewAdapter\n- CorrectionViewAdapter\n- ChartViewAdapter"
```

### Key UI Patterns

#### 1. Adapter Pattern

For integrating existing UI components with the new UI structure, we use the adapter pattern:

```mermaid
graph TD
    BV[BaseView] --> Adapter[AdapterView]
    Adapter --> OC[Original Component]
    
    style BV fill:#1a3055,color:#fff
    style Adapter fill:#234a87,color:#fff
    style OC fill:#2e62b5,color:#fff
```

**Implementation Example:**
```python
class DataViewAdapter(BaseView):
    def __init__(self, data_model, parent=None):
        # Store references
        self._data_model = data_model
        
        # Create the original component
        self._data_view = DataView(data_model)
        
        # Initialize the base view
        super().__init__("Data View", parent)
        
    def _setup_ui(self):
        # First call the parent class's _setup_ui method
        super()._setup_ui()
        
        # Add the original component to the content widget
        self.get_content_layout().addWidget(self._data_view)
```

#### 2. Content View Pattern

For consistent UI components with standardized structure:

```mermaid
graph TD
    BV[BaseView] --> H[Header]
    BV --> C[Content]
    H --> T[Title]
    H --> A[Action Buttons]
    
    style BV fill:#1a3055,color:#fff
    style H fill:#234a87,color:#fff
    style C fill:#234a87,color:#fff
    style T fill:#2e62b5,color:#fff
    style A fill:#2e62b5,color:#fff
```

#### 3. Navigation Pattern

For consistent and organized application navigation:

```mermaid
graph LR
    MW[MainWindow] --> SN[SidebarNavigation]
    SN -- navigation_changed --> MW
    MW -- set_active_item --> SN
    MW -- setCurrentWidget --> CS[ContentStack]
    
    style MW fill:#1a3055,color:#fff
    style SN fill:#234a87,color:#fff
    style CS fill:#234a87,color:#fff
```

#### 4. Dashboard Pattern

```mermaid
graph TD
    DB[DashboardView] --> SC[Stats Cards]
    DB --> RF[Recent Files]
    DB --> QA[Quick Actions]
    DB --> CH[Charts]
    QA -- action_triggered --> MW[MainWindow]
    RF -- file_selected --> MW
    
    style DB fill:#1a3055,color:#fff
    style SC fill:#234a87,color:#fff
    style RF fill:#234a87,color:#fff
    style QA fill:#234a87,color:#fff
    style CH fill:#234a87,color:#fff
    style MW fill:#2e62b5,color:#fff
```

## UI Component Interactions

### Signal-Slot Mechanism

The UI components communicate primarily through the Qt Signal-Slot mechanism:

```mermaid
sequenceDiagram
    participant User
    participant SidebarNav
    participant MainWindow
    participant ContentViews
    
    User->>SidebarNav: Click navigation item
    SidebarNav->>MainWindow: navigation_changed signal
    MainWindow->>ContentViews: Switch active view
    ContentViews-->>User: Display view
```

### UI Update Flow

```mermaid
sequenceDiagram
    participant DM as DataModel
    participant MW as MainWindow
    participant SB as StatusBar
    participant DV as DataView
    
    DM->>DM: Data changes
    DM->>MW: data_changed signal
    MW->>SB: Update status
    MW->>DV: Reflect changes
    DV-->>User: Display updated data
```

## UI Visual Style

### Color Scheme

We've selected a professional dark blue theme with gold accents:

```
PRIMARY: #1a3055 (Dark Blue)
SECONDARY: #ffc107 (Gold)
ACCENT: #f8c760 (Light Gold)
BACKGROUND: #141e30 (Darker Blue)
TEXT_LIGHT: #ffffff (White)
TEXT_MUTED: #a0aec0 (Light Gray)
BORDER: #2d4a77 (Medium Blue)
```

### Visual Mockup


2. **Dashboard Sections**:
   - **Quick Actions**: Grid of ActionCards for common tasks
     ```python
     self._create_action_section("Quick Actions", [
         ActionCard("Import Data", "Load CSV files", Icons.IMPORT, "import"),
         ActionCard("Export", "Save as CSV or Excel", Icons.EXPORT, "export"),
         ActionCard("Analyze", "Run data analysis", Icons.CHART, "analyze"),
         ActionCard("Settings", "Configure application", Icons.SETTINGS, "settings")
     ])
     ```
   
   - **Recent Files**: List of recently opened files
     ```python
     self._create_recent_files_section("Recent Files", recent_files)
     ```
   
   - **Charts & Analytics**: Grid of ChartCards for analytics
     ```python
     self._create_charts_section("Charts & Analytics", [
         ChartCard("Revenue Trends", "Monthly revenue", "revenue", thumbnail1),
         ChartCard("Product Distribution", "By category", "products", thumbnail2)
     ])
     ```

3. **Empty States**:
   - Each section has its own empty state handling
   - Dashboard shows appropriate messaging when data isn't available
   - Action buttons guide users to load data or perform initial actions

## Navigation Pattern

The application uses a view adapter pattern for navigation:

1. **ViewAdapter Base Class**
   - **Implementation**: `chestbuddy/ui/views/view_adapter.py`
   - **Responsibilities**:
     - Get/set view title and icon
     - Handle data requirements
     - Manage view lifecycle
     - Support data availability state

2. **Specialized View Adapters**
   - **DashboardViewAdapter**: Main dashboard with card-based UI
   - **DataViewAdapter**: Tabular data display with filtering
   - **ValidationViewAdapter**: Data validation interfaces
   - **CorrectionViewAdapter**: Data correction workflows
   - **ChartViewAdapter**: Detailed chart visualization

3. **Navigation Flow**:
   - Dashboard is always accessible regardless of data state
   - Other views require data to be loaded
   - `MainWindow` manages navigation state
   - Navigation sidebar reflects data availability
   - Empty states guide users to appropriate actions

## Data Management

### Data Loading Pattern

1. **DataManager**
   - Central data handling service
   - Responsible for loading, processing, and providing data
   - Emits signals for data state changes

2. **MultiCSVLoadTask**
   - Handles loading multiple CSV files
   - Reports progress for each file
   - Manages memory efficiently for large datasets

3. **Data Access Pattern**
   - Views request data through DataManager
   - Data availability is checked before operations
   - Empty states shown when data is not available

## UI Component Patterns

1. **Consistent Signal Pattern**:
   - Components use Qt's signal-slot mechanism
   - Signals emit clear information about user actions
   - Components don't make assumptions about handling

2. **Style Consistency**:
   - Components use shared style variables
   - Common visual language across the application
   - Components adapt to application theme

3. **Component Hierarchy**:
   - Basic components (buttons, inputs)
   - Composite components (cards, toolbars)
   - View components (organized layouts)
   - Screen components (full views)

4. **State Management**:
   - Components handle their own internal state
   - Parent components manage child component state
   - Application state managed by service classes

## Application Patterns

ChestBuddy implements several key architectural and design patterns:

### 1. Model-View-Presenter (MVP)
The application follows an MVP architecture with:
- **Models**: Core data structures and business logic (ChestDataModel)
- **Views**: User interface components (MainWindow, various UI widgets)
- **Presenters**: Business logic that coordinates between models and views (DataManager, Services)

The MVP pattern provides separation of concerns and facilitates testing.

### 2. Observer Pattern
Implemented via Qt's signal-slot mechanism to provide loose coupling between components. Key examples:
- DataManager emits signals when data changes, which views observe
- FileService emits signals when file operations complete
- ProgressDialog emits signals when users interact with it

### 3. Factory Pattern
Used to create complex objects with standardized configuration:
- ViewFactory creates UI views with proper initialization
- DialogFactory creates standardized dialogs with consistent styling
- ServiceFactory provides access to application services

### 4. Adapter Pattern
Adapts between different interfaces, particularly for:
- TableModelAdapter converts DataFrame data to Qt table models
- ChartAdapter converts data structures to chart-compatible formats
- FileAdapter standardizes access to different file formats

### 5. Command Pattern
Encapsulates operations as objects to support:
- Undo/redo functionality
- Operation logging
- Batch processing

### 6. Singleton Pattern
Used for service access and shared resources:
- ConfigManager maintains a single configuration instance
- LogManager provides centralized logging
- DataStore serves as a single source of truth for application data

### 7. Strategy Pattern
Allows interchangeable algorithms:
- ValidationStrategy for different validation approaches
- CorrectionStrategy for applying corrections with different rules
- ExportStrategy for supporting different export formats

### 8. State Pattern
Manages application state transitions:
- ApplicationState tracks high-level application state
- ViewState manages view-specific state
- ImportState tracks the state of import operations

### 9. UI State Management Pattern
A systematic architectural pattern implemented to handle UI blocking/unblocking during operations:

#### Architecture Overview

The UI State Management System provides a centralized, thread-safe way to manage UI element states during operations. It addresses the fundamental issues with ad-hoc UI blocking approaches by creating a cohesive system with proper reference counting and automatic cleanup.

![UI State Management Architecture](https://mermaid.ink/img/pako:eNqFkl9PwjAUxb_KTZ-MIWSI8EBC5sM0PvjgixGSmrbdWrtlvRuDGPj2dh3IH_HBS5Oe3t85t-dWTFFJioAZy-yRY59GyZYxZaqQOGRMeXylcDcl3pE9DqbpLX1J3UymvgS50jz_AxiJb3qX0QzH79nqOcvu0nEYrJLFnE7HwXL-OEkvoL0UaZW_Z_Nk9T5P30jt1Yy_SWKMNwolCe9p1W1d-6yNcjKxB_EL9gfxO3-LntH9ILahzaBb_bK0gTDmtKb-IUuSCZSVACy4UbSE5kjVQgX_zXK4J7uDRucq4WZqe5jIr2_XWYbhXCrHYp0ZzPNGKcqtUMCMMFhCZLVujCTUlZbK7sFqj63Wm-V1p5nFwFHDEIGG7aCxnKgGcRXNSC-9VjaBFxXDqjJiDw25MsZzzVkh7W97RtqhbcpvZxcOfA?type=png)

#### Core Components

1. **UIStateManager**
   - Singleton class for central UI state management
   - Maps UI elements to their blocking operations
   - Maintains reference counts for nested operations
   - Provides thread-safe access with mutex locks
   - Emits signals when element states change

   ```python
   # Accessing the UI State Manager
   from chestbuddy.ui.state.manager import UIStateManager
   
   # Get the singleton instance
   manager = UIStateManager()
   
   # Check if an element is blocked
   is_blocked = manager.is_element_blocked(element_id)
   
   # Get operations blocking an element
   operations = manager.get_blocking_operations(element_id)
   ```

2. **BlockableElementMixin**
   - Mixin class that adds blocking capability to UI components
   - Handles registration with UIStateManager
   - Provides standard interface for blockable UI elements
   - Customizable block/unblock behavior via _apply_block and _apply_unblock
   - Automatically unregisters from manager when closed

   ```python
   from PySide6.QtWidgets import QWidget
   from chestbuddy.ui.state.blockable import BlockableElementMixin
   from chestbuddy.ui.state.enums import UIElementGroups
   
   class MyBlockableWidget(QWidget, BlockableElementMixin):
       def __init__(self, parent=None, element_id="my_widget"):
           QWidget.__init__(self, parent)
           BlockableElementMixin.__init__(
               self, 
               element_id=element_id,
               element_group=UIElementGroups.DATA_VIEW
           )
           
       def _apply_block(self):
           # Custom blocking behavior
           self.setEnabled(False)
           self.setStyleSheet("background-color: #f0f0f0;")
           
       def _apply_unblock(self):
           # Custom unblocking behavior
           self.setEnabled(True)
           self.setStyleSheet("")
           
       def closeEvent(self, event):
           # Ensure unregistration when widget is closed
           self.unregister_from_ui_state_manager()
           super().closeEvent(event)
   ```

3. **OperationContext**
   - Context manager for operations that block UI elements
   - Automatically handles blocking/unblocking, even with exceptions
   - Supports blocking individual elements or element groups
   - Uses reference counting for nested operations
   - Thread-safe implementation

   ```python
   from chestbuddy.ui.state.context import OperationContext
   from chestbuddy.ui.state.enums import UIOperations, UIElementGroups
   
   # Block specific elements
   with OperationContext(
       operation=UIOperations.DATA_IMPORT,
       element_ids=["data_view", "toolbar"]
   ):
       # Perform operation that should block these elements
       # Elements will be unblocked when exiting the context
       # Even if an exception occurs
       load_data_from_csv()
       
   # Block entire element groups
   with OperationContext(
       operation=UIOperations.DATA_VALIDATION,
       element_groups=[UIElementGroups.DATA_VIEW, UIElementGroups.NAVIGATION]
   ):
       # All elements in these groups will be blocked
       validate_data()
   ```

4. **Standardized Enumerations**
   - UIOperations: Standard operations that can block UI
   - UIElementGroups: Logical groupings of related elements

   ```python
   from chestbuddy.ui.state.enums import UIOperations, UIElementGroups
   
   # Available operations
   print(UIOperations.DATA_IMPORT)  # For data import operations
   print(UIOperations.DATA_EXPORT)  # For data export operations
   print(UIOperations.DATA_VALIDATION)  # For validation operations
   print(UIOperations.DATA_CORRECTION)  # For correction operations
   
   # Available element groups
   print(UIElementGroups.NAVIGATION)  # Navigation elements
   print(UIElementGroups.DATA_VIEW)  # Data view components
   print(UIElementGroups.TOOLBAR)  # Toolbar actions
   print(UIElementGroups.DIALOG)  # Dialog components
   print(UIElementGroups.VALIDATION)  # Validation UI components
   print(UIElementGroups.CORRECTION)  # Correction UI components
   ```

#### Reference Counting for Nested Operations

The system handles nested operations through reference counting:

1. When an operation starts and blocks an element, the reference count increases
2. When a nested operation also blocks the same element, the count increases again
3. When operations complete, the count decreases
4. Only when the count reaches zero is the element unblocked

```python
# Example of nested operations
with OperationContext(operation=UIOperations.DATA_IMPORT, 
                     element_groups=[UIElementGroups.DATA_VIEW]):
    # DATA_VIEW elements are blocked (count=1)
    
    # Some processing...
    
    with OperationContext(operation=UIOperations.DATA_VALIDATION, 
                         element_groups=[UIElementGroups.DATA_VIEW]):
        # DATA_VIEW elements still blocked (count=2)
        validate_data()
    
    # DATA_VIEW elements still blocked (count=1)
    finish_import()

# DATA_VIEW elements unblocked (count=0)
```

#### Thread Safety

The UI State Management System is designed to be thread-safe:

1. All state modifications use QMutex for thread safety
2. UI updates are always performed on the main thread using QMetaObject.invokeMethod
3. Signals and slots connect with Qt.QueuedConnection to ensure thread safety

```python
# Thread-safe operation from background thread
def run_in_background():
    # This can safely be called from any thread
    with OperationContext(operation=UIOperations.DATA_PROCESSING,
                         element_groups=[UIElementGroups.DATA_VIEW]):
        # Process data in background
        process_large_dataset()
        
# Start background thread
worker = BackgroundWorker(run_in_background)
worker.start()
```

#### Integration with BackgroundWorker

The system integrates with the BackgroundWorker class for background processing:

```python
from chestbuddy.core.background.worker import BackgroundWorker
from chestbuddy.core.background.task import BackgroundTask
from chestbuddy.ui.state.enums import UIOperations, UIElementGroups

class MyDataTask(BackgroundTask):
    def __init__(self, data):
        super().__init__()
        self.data = data
        
    def run(self):
        # Process data
        # Progress is automatically reported
        self.progress.emit(50)
        # Final result
        return processed_data

# The BackgroundWorker automatically creates an OperationContext
worker = BackgroundWorker(
    task=MyDataTask(data),
    operation=UIOperations.DATA_PROCESSING,
    element_groups=[UIElementGroups.DATA_VIEW]
)

# Connect signals
worker.finished.connect(on_task_completed)
worker.error.connect(on_task_error)

# Start the worker (UI elements will be blocked)
worker.start()
# UI elements will be automatically unblocked when worker finishes
```

#### Blockable UI Components

The system includes blockable versions of key UI components:

1. **BlockableDataView**: For data viewing and editing
2. **BlockableValidationTab**: For data validation operations
3. **BlockableCorrectionTab**: For data correction operations
4. **BlockableProgressDialog**: For operation progress display

These components register with the UI State Manager and automatically handle their own blocking/unblocking based on active operations.

#### Integration with Adapters

The blockable components are integrated through view adapters:

```python
# View adapters automatically use blockable components
class DataViewAdapter(BaseView):
    def __init__(self, data_model):
        # Create blockable component with unique ID
        self._data_view = BlockableDataView(
            parent=None,
            element_id=f"data_view_adapter_{id(self)}",
        )
        
        # Initialize base view
        super().__init__("Data View", parent)
        
    def _setup_ui(self):
        super()._setup_ui()
        # Add blockable component to layout
        self.get_content_layout().addWidget(self._data_view)
```

#### Best Practices

1. **Unique Element IDs**
   - Always use unique, descriptive IDs for UI elements
   - Consider using class name + instance ID format
   - Example: `f"data_view_{id(self)}"`

2. **Proper Element Groups**
   - Assign elements to appropriate groups for batch operations
   - Create new groups for specialized component types

3. **Minimal Operation Scope**
   - Keep operation contexts as narrow as possible
   - Only block elements that are directly affected by the operation

4. **Always Use Context Managers**
   - Never manually block/unblock elements
   - Always use OperationContext to ensure proper cleanup

5. **Custom Block/Unblock Behavior**
   - Override _apply_block and _apply_unblock for custom blocking behavior
   - Consider visual indicators beyond just disabling

6. **Thread Safety**
   - Always be aware of which thread is running your code
   - Use QMetaObject.invokeMethod for cross-thread UI updates

7. **Testing Blockable Components**
   - Mock UIStateManager in tests to isolate components
   - Verify registration happens correctly
   - Test that block/unblock methods are called appropriately

#### Implementation Examples

**Example 1: Creating a new blockable button**

```python
from PySide6.QtWidgets import QPushButton
from chestbuddy.ui.state.blockable import BlockableElementMixin
from chestbuddy.ui.state.enums import UIElementGroups

class BlockableButton(QPushButton, BlockableElementMixin):
    def __init__(self, text, parent=None, element_id=None):
        QPushButton.__init__(self, text, parent)
        BlockableElementMixin.__init__(
            self,
            element_id=element_id or f"button_{id(self)}",
            element_group=UIElementGroups.TOOLBAR
        )
        
    def _apply_block(self):
        self.setEnabled(False)
        self.setToolTip("This action is not available during the current operation")
        
    def _apply_unblock(self):
        self.setEnabled(True)
        self.setToolTip("")
```

**Example 2: Using operation context with multiple elements**

```python
def process_and_export_data():
    # Define which elements/groups to block
    elements_to_block = ["export_button", "format_dropdown"]
    groups_to_block = [UIElementGroups.DATA_VIEW]
    
    with OperationContext(
        operation=UIOperations.DATA_EXPORT,
        element_ids=elements_to_block,
        element_groups=groups_to_block
    ):
        # Prepare data
        prepare_data_for_export()
        
        # Export to file (nested operation)
        with OperationContext(
            operation=UIOperations.FILE_WRITE,
            element_ids=["cancel_button"]
        ):
            write_to_file()
            
        # Finalize export
        finalize_export()
```

This UI State Management pattern provides a robust, systematic approach to managing UI state during operations, eliminating the issues with ad-hoc UI blocking/unblocking and providing clear visibility into the UI state at all times.

``` 