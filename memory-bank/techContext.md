# Technical Context: ChestBuddy

## DataView Refactoring Technical Details

### Overview
The DataView refactoring project is a comprehensive overhaul of the core data display component of the ChestBuddy application. This section details the technical aspects of this refactoring effort.

**Note on Migration (Updated: 2024-08-08):** The project is actively migrating away from an older implementation (`ui/data_view.py` relying on `QStandardItemModel`) towards the refactored structure (`ui/data/` using `QAbstractTableModel`). A `DataViewAdapter` currently bridges these, but its complexity and the dual structure are recognized risks. The goal is full consolidation onto the new architecture.

### Technology Stack
The refactored DataView uses these key technologies:

- **PySide6/Qt6**: Core UI framework for all visual components
- **pandas**: Data manipulation backend
- **pytest/pytest-qt**: Testing framework for all components
- **Qt Delegates**: Custom cell rendering mechanism
- **Qt Model/View Architecture**: Core paradigm for data display

### Project Structure
The refactored DataView follows this directory structure:

```
chestbuddy/
├── ui/
│   ├── data/                       # Refactored DataView-specific components
│   │   ├── models/                 # Data models (DataViewModel, FilterModel)
│   │   ├── views/                  # View components (DataTableView, HeaderView)
│   │   ├── delegates/              # Cell rendering delegates
│   │   ├── adapters/               # Integration adapters (ValidationAdapter, CorrectionAdapter)
│   │   ├── menus/                  # Context menus
│   │   ├── widgets/                # Supporting UI widgets
│   │   └── ...
│   ├── data_view.py            # <<< OLD Implementation (to be deprecated)
│   ├── views/
│   │   ├── data_view_adapter.py  # <<< Adapter wrapping OLD view (to be deprecated)
│   │   └── ...
...
```

### Key Components
*(Descriptions focus on the refactored components in `ui/data/`)*

#### Models

- **DataViewModel** (`data_view_model.py`): 
  - Core view model adapting ChestDataModel for display.
  - Implements `QAbstractTableModel` for efficiency.
  - Handles data access, modification signals (`dataChanged`), sorting.
  - Integrates with `TableStateManager` to provide state roles to delegates.

- **FilterModel** (`filter_model.py`):
  - Implements `QSortFilterProxyModel` for standard filtering/sorting.

#### Views

- **DataTableView** (`data_table_view.py`):
  - Main table view component extending `QTableView`.
  - Connects with delegates for cell rendering.

#### Delegates

- **ValidationDelegate**, **CorrectionDelegate**, etc.:
  - Visualize state based on data roles provided by `DataViewModel`.

#### Adapters

- **ValidationAdapter**, **CorrectionAdapter**:
  - Connect Services (`ValidationService`, `CorrectionService`) to `TableStateManager`.

### Technical Implementation Details

#### Data Flow (Intended Refactored Flow)
1.  **Data Source** (`ChestDataModel`) → **DataViewModel** → **FilterModel** → **DataTableView**
2.  **Service** (`ValidationService`) → **Adapter** (`ValidationAdapter`) → **StateManager** (`TableStateManager`) → **DataViewModel** (`dataChanged` signal) → **Delegate** (`ValidationDelegate` painting based on role)
3.  (Similar flow for Correction)
4.  **User Interaction** → **View** (`DataTableView` emitting higher-level signals) → **Controller** → **Service**

#### Qt Model Roles
Custom data roles are defined for specialized data access:

```python
# Data roles for accessing specific data types
ValidationRole = Qt.UserRole + 1  # Role for validation status
CorrectionRole = Qt.UserRole + 2  # Role for correction information
OriginalValueRole = Qt.UserRole + 3  # Role for original unformatted value
FormattedValueRole = Qt.UserRole + 4  # Role for formatted display value
MetadataRole = Qt.UserRole + 5  # Role for cell metadata
```

#### Validation Status Visualization
Validation status is visualized using color coding and icons:

| Status | Background Color | Icon | Description |
|--------|------------------|------|-------------|
| VALID | White (#ffffff) | None | Valid cell |
| INVALID | Light Red (#ffb6b6) | ✗ | Invalid cell |
| CORRECTABLE | Light Yellow (#fff3b6) | ▼ | Cell with correction available |
| WARNING | Light Orange (#ffe4b6) | ! | Cell with warning |
| INFO | Light Blue (#b6e4ff) | ℹ | Cell with information |

#### Performance Optimizations
Several techniques are used to optimize performance:

1. **Lazy Loading**: Only load visible data
2. **Viewport Rendering**: Optimize rendering for visible area
3. **Cached State**: Cache validation and correction states
4. **Background Processing**: Process validation in background threads
5. **Chunked Updates**: Update UI in chunks to maintain responsiveness
- **Chunked Updates Note (Updated: 2024-08-08):** Code review suggested using `QTimer.singleShot(0, ...)` instead of `QApplication.processEvents()` for chunked processing to better manage the event loop. This should be considered if optimizing the old view or implementing chunking in the new one.

### Testing Strategy
The DataView refactoring includes a comprehensive testing strategy:

#### Unit Tests
- Test each component in isolation
- Mock dependencies for true unit testing
- Test edge cases and error handling

#### Integration Tests
- Test interactions between components
- Verify data flow and state management
- Test signal-slot connections

#### UI Tests
- Test rendering and visualization
- Test user interactions (clicks, context menus)
- Test keyboard navigation

#### Performance Tests
- Test with large datasets (10,000+ rows)
- Measure rendering performance
- Test memory usage and efficiency

### Integration with Existing Codebase
The refactored DataView will integrate with the existing ChestBuddy codebase through:

1. **Clear API**: Well-defined interfaces for interaction
2. **Adapter Pattern**: Adapters for service integration
3. **Backwards Compatibility**: Maintaining existing connection points
4. **Gradual Migration**: Replacing components incrementally

## Final Technical Stack

The ChestBuddy application is built using the following technologies:

### Core Technologies
- **Python 3.9+**: Primary development language
- **PySide6 (Qt 6)**: GUI framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical operations supporting pandas
- **matplotlib**: Charting and data visualization
- **openpyxl**: Excel file reading/writing
- **lxml**: XML parsing for data import/export
- **pytest**: Testing framework
- **pytestqt**: Qt-specific testing utilities
- **UV**: Package management and virtual environment

### Application Architecture
- **Model-View-Controller (MVC)**: Core architectural pattern
- **Service Layer**: Business logic encapsulation
- **Controllers Layer**: Coordination between UI and services
- **Adapter Pattern**: UI component wrapping
- **Signal-Slot System**: Event-based communication
- **Observer Pattern**: Data change notification
- **Command Pattern**: For undoable operations
- **Strategy Pattern**: For validation and correction strategies

### Data Management
- **DataFrameStore**: Central data storage mechanism
- **ValidationService**: Rules-based data validation
- **CorrectionService**: Automatic and manual data correction
- **ImportExportService**: Data import/export functionality
- **ChartService**: Data visualization generation

### UI Components
- **Qt Widgets**: For UI components 
- **QTableView**: Main data display
- **Custom Delegates**: For specialized cell rendering
- **QSplitter**: For resizable layouts
- **QStackedWidget**: For view switching
- **QWebEngineView**: For advanced visualization (optional)
- **Style Sheets**: For UI appearance customization

### Custom Utilities
- **SignalManager**: Signal connection tracking and management
- **UpdateManager**: UI update scheduling and optimization
- **ConfigManager**: Application configuration management
- **BackgroundWorker**: Asynchronous task processing
- **ValidationStatusDelegate**: Custom rendering of validation status
- **ServiceLocator**: Service access utility

## Development Tools and Environment

- **Visual Studio Code**: Primary IDE
- **Git**: Version control system
- **GitHub**: Code repository hosting
- **GitHub Actions**: CI/CD for automated testing
- **Ruff**: Code linting and formatting
- **pytest**: Test running and reporting
- **UV**: Package management and dependency resolution
- **pyenv**: Python version management

## Refactoring Progress Update (2024-08-06)
- Implemented `DataViewModel` with core logic for data access, roles, and sorting.
- Implemented `ValidationAdapter` and `CorrectionAdapter` to connect services to the `TableStateManager`.
- Completed unit tests for `DataViewModel`, `ValidationAdapter`, and `CorrectionAdapter`.
- Established basic integration tests for state propagation between adapters, state manager, view model, and delegates.
- These components form the foundation for visualizing validation and correction states in the refactored DataView.

## Project Structure

The project follows a clear, modular structure with these key directories:

- `chestbuddy/`: Main package
  - `core/`: Core application logic
    - `controllers/`: Controller components for UI and data coordination
    - `models/`: Data models and abstractions
    - `services/`: Business logic services
    - `enums/`: Enumeration types
  - `ui/`: User interface components
    - `views/`: UI view components
    - `widgets/`: Custom widgets
    - `dialogs/`: Dialog windows
    - `resources/`: UI resources (icons, styles)
  - `utils/`: Utility functions and helpers
- `tests/`: Test suite
  - `unit/`: Unit tests
  - `integration/`: Integration tests
  - `ui/`: UI component tests
  - `fixtures/`: Test fixtures and data
- `scripts/`: Utility scripts
- `docs/`: Documentation
- `memory-bank/`: Project memory files

## Key Technical Decisions

1. **Controller-Based Architecture**: Implemented a clean controller-based architecture with proper separation of concerns, with controllers as the mediators between the UI and the data/services.

2. **Signal Management**: Developed a robust signal management system with the SignalManager utility for tracking, connecting, and disconnecting signals, improving debugging and reducing memory leaks.

3. **UI Update Interface**: Created an optimized UI update system with the UpdateManager utility, allowing components to register for updates based on specific data changes rather than reacting to all changes.

4. **Background Processing**: Implemented the BackgroundWorker system for handling long-running operations in separate threads, keeping the UI responsive.

5. **Validation System**: Designed a flexible validation system using a rules-based approach with different validation levels and strategies.

6. **View Adapter Pattern**: Adopted the adapter pattern for UI components, allowing for cleaner integration and easier testing.

7. **Service-Oriented Design**: Encapsulated business logic in dedicated services with clear responsibilities.

8. **Configuration Management**: Created a centralized configuration system for managing application settings.

9. **Error Handling**: Implemented a comprehensive error handling system with proper error reporting and user feedback.

10. **Testing Approach**: Adopted a comprehensive testing strategy with unit, integration, and end-to-end tests.

11. **Chunked Processing (Updated: 2024-08-08):** While the old view uses `processEvents`, the recommended approach for future/refactored chunking is `QTimer.singleShot`.

## Technical Implementation Challenges and Solutions

### Challenge 1: Signal Connection Management
- **Problem**: Tracking and managing signal connections between components was complex and error-prone.
- **Solution**: Created the SignalManager utility for centralized signal connection management, with support for connection tracking, disconnection, and debugging.

### Challenge 2: UI Update Optimization
- **Problem**: Inefficient UI updates causing performance issues with larger datasets.
- **Solution**: Implemented the UpdateManager with support for data dependency tracking and optimized update scheduling.

### Challenge 3: Background Processing
- **Problem**: Long-running operations blocking the UI thread.
- **Solution**: Developed the BackgroundWorker system for asynchronous processing with proper progress reporting.

### Challenge 4: Data Validation Complexity
- **Problem**: Complex validation requirements with different validation levels and strategies.
- **Solution**: Created a flexible validation system with support for different validation strategies and configurable validation levels.

### Challenge 5: UI Component Integration
- **Problem**: Integrating Qt components with custom business logic.
- **Solution**: Adopted the adapter pattern for UI components, providing a clean interface for controller interaction.

## System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, Linux with Qt support
- **Python Version**: 3.9 or higher
- **Minimum RAM**: 4GB (8GB recommended for larger datasets)
- **Disk Space**: 200MB for application, additional space for data
- **Display**: 1280x720 minimum resolution
- **Dependencies**: All Python dependencies are managed through UV

## Final Technical Architecture

The ChestBuddy application follows a layered architecture:

1. **Presentation Layer**: UI components and adapters
   - Main application window and views
   - Input validation and user feedback
   - Progress reporting and status updates

2. **Controller Layer**: Mediators between UI and business logic
   - DataViewController for data operations
   - UIStateController for UI state management
   - FileOperationsController for file operations
   - ViewStateController for view state management
   - ErrorHandlingController for error handling

3. **Service Layer**: Business logic encapsulation
   - ValidationService for data validation
   - CorrectionService for data correction
   - ImportExportService for data import/export
   - ChartService for data visualization

4. **Data Layer**: Data storage and access
   - DataFrameStore for central data storage
   - ConfigManager for configuration management
   - FileService for file operations

5. **Utility Layer**: Supporting utilities
   - SignalManager for signal management
   - UpdateManager for UI update optimization
   - BackgroundWorker for asynchronous processing
   - ServiceLocator for service access

This layered approach provides a clean separation of concerns and facilitates maintainability, testability, and extensibility.

## Testing Framework

### Testing Tools
- **pytest**: Main testing framework
- **pytest-qt**: Plugin for testing Qt applications
- **pytest-cov**: Plugin for measuring code coverage

### Test Categories
- **Unit Tests**: Test individual components in isolation
  - Located in `tests/unit/`
  - Mock dependencies for true isolation

- **Integration Tests**: Test how components work together
  - Located in `tests/integration/`
  - Test real interactions between components
  - Focus on service integration, like `ValidationService` with `ConfigManager`

- **UI Tests**: 
  - Most UI tests require QtBot and can't run in headless CI environments
  - Use `pytest.mark.skipif` to conditionally skip these tests

### Test Runner Scripts
- `scripts/run_all_tests.py`: Run all tests with filtering options
  ```python
  python scripts/run_all_tests.py [--all|--unit|--integration] [--coverage] [--verbose] [--module MODULE]
  ```
  
- `scripts/run_integration_tests.py`: Run only integration tests
  ```python
  python scripts/run_integration_tests.py
  ```
  
- `scripts/run_validation_integration_tests.py`: Run ValidationService integration tests
  ```python
  python scripts/run_validation_integration_tests.py
  ```

## Configuration System

The application uses a `ConfigManager` class for managing application settings:

### Key Features
- **Singleton Pattern**: Ensures consistent access to configuration throughout the app
- **Default Configuration**: Provides sensible defaults for all settings
- **Type Conversion**: Methods for getting typed values (`get_bool`, `get_int`, etc.)
- **List Support**: Handles list values through JSON serialization
- **Error Handling**: Gracefully handles corrupted config files
- **Auto-save**: Automatically saves after changes
- **Migration Support**: Can update configuration from older versions

### Recent Enhancements
- Improved boolean value handling in `get_bool()` method
- Added configuration version migration support
- Added permission error handling in `save()` method
- Added `has_option()` method to check for option existence
- Added `load()` method to reload configuration from disk

### Configuration Sections
- **General**: Theme, language, version
- **Files**: Recent files, import/export directories
- **Validation**: Validation preferences, paths to validation lists
- **Correction**: Auto-correction settings, path to correction rules
- **UI**: Window size, table pagination

## Technologies Used

### Core Technologies

- **Python 3.9+** - Core programming language
- **PySide6** - Qt bindings for Python (UI framework)
- **UV** - Package management and virtual environment
- **pytest** - Testing framework

### UI Framework

- **PySide6 (Qt)** - Primary UI framework
  - QTableView - Used for data display
  - QWidgets - Core UI components
  - Qt Signals/Slots - Event handling mechanism
  - QSS - Styling the UI components

### Development Tools

- **Ruff** - Python linter
- **pytest** - Test framework
- **pytest-qt** - Qt testing utilities
- **pytest-cov** - Test coverage
- **mypy** - Static type checking

## Design Patterns

### MVC Pattern

The application follows a Model-View-Controller architecture:

- **Models**: DataModel, ValidationModel, CorrectionModel
- **Views**: Various UI components
- **Controllers**: Bridge between models and views

### Service Pattern

Business logic is encapsulated in service classes:

- **DataService** - Data operations
- **ValidationService** - Validation logic
- **CorrectionService** - Correction logic
- **ChartService** - Chart generation

### Observer Pattern (Qt Signals/Slots)

Qt's signal/slot mechanism is used throughout the application for event handling and communication between components:

- **Signals** - Notify about events
- **Slots** - React to events
- **Connections** - Link signals to slots

### Recursive Processing Pattern

A recursive processing pattern is used in the enhanced correction system to repeatedly apply corrections until no more changes occur:

```python
def apply_corrections_recursive():
    total_corrections = 0
    corrections = initial_correction_pass()
    total_corrections += corrections
    
    while corrections > 0:
        corrections = subsequent_correction_pass()
        total_corrections += corrections
    
    return total_corrections
```

### Status State Machine

The validation and correction system uses a state machine pattern to track entry status:

- **VALID** → Data is valid
- **INVALID** → Data is invalid
- **CORRECTABLE** → Data is invalid but can be corrected
- **CORRECTED** → Data was invalid but has been corrected

### Configuration Management

Application settings are managed centrally through a configuration manager:

```python
config_manager = ConfigManager()
value = config_manager.get_value("section/key", default_value)
config_manager.set_value("section/key", new_value)
```

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **UI Tests**: Test UI components and interactions
- **Test-Driven Development**: Write tests before implementing features

## Data Flow Architecture

The application uses a layered data flow architecture:

1. **User Interface** - User interaction layer
2. **Controllers** - Coordination layer
3. **Services** - Business logic layer
4. **Data Model** - Data storage layer
5. **Persistence** - File I/O layer

## Asynchronous Processing

Long-running operations are executed asynchronously to keep the UI responsive:

- **QThreadPool** - Thread pool for background tasks
- **QRunnable** - Runnable tasks for background processing
- **Signals** - Communicate results back to the UI thread
