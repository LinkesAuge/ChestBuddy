# Technical Context: ChestBuddy

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

11. **Chunked Processing**: Implemented a chunked processing approach for UI-intensive operations to maintain responsiveness. This technique breaks large operations (like table population) into smaller chunks of work (200 rows at a time) and yields control back to the Qt event loop between processing chunks using QTimer.singleShot(). This prevents UI freezing during heavy operations while providing opportunities for progress feedback.

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
