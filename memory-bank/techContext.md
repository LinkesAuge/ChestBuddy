# Technical Context

## Technology Stack

### Core Technologies
- **Python 3.12+**: Base programming language
- **PySide6**: GUI framework (Qt for Python)
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Visualization library
- **Jinja2**: HTML template engine for reports

### Dependency Management
- **UV**: Modern Python package installer and resolver

### Text Processing
- **ftfy**: Fixes text encoding issues
- **charset-normalizer**: Charset detection
- **unidecode**: Unicode character conversion

### Development Tools
- **pytest**: Testing framework
- **Ruff**: Python linter and formatter
- **pytestqt**: Qt testing plugin for pytest

## Development Environment

### Setup Requirements
- Python 3.12 or newer
- UV package manager
- Git for version control
- Virtual environment (managed by UV)

### Project Structure
```
ChestBuddy/
├── chestbuddy/         # Main package
│   ├── core/           # Core business logic
│   │   ├── models/     # Data models
│   │   └── services/   # Service classes
│   ├── ui/             # User interface components
│   │   ├── views/      # Main application views
│   │   ├── widgets/    # Reusable UI components
│   │   └── resources/  # UI resources (icons, styles)
│   ├── data/           # Data handling
│   └── utils/          # Utility modules
│       └── background_processing.py  # Background processing utilities
├── data/               # Sample data and resources
├── docs/               # Documentation
├── memory-bank/        # Project memory
├── scripts/            # Utility scripts
├── tests/              # Test suite
│   ├── test_background_worker.py  # Background worker tests
│   ├── test_csv_background_tasks.py  # CSV background task tests
│   ├── test_integration.py  # Integration tests (planned)
│   ├── test_main_window.py  # MainWindow tests (planned)
│   ├── test_workflows.py  # End-to-end workflow tests (planned)
│   └── test_files/  # Test data files
├── .cursor/            # Cursor IDE settings
│   └── rules/          # Project rules
├── .gitignore          # Git ignore file
├── main.py             # Application entry point
├── pyproject.toml      # Project configuration
├── README.md           # Project readme
└── .python-version     # Python version spec
```

### Key Libraries Usage

#### PySide6
- Used for the entire UI layer
- Provides QTableView for data display
- Enables chart rendering with QtCharts
- Handles dialog windows and user interactions
- Implements signal-slot mechanism for event handling
- QThread for background processing

#### Pandas
- Core data structure for chest data (DataFrame)
- Handles CSV import/export
- Provides filtering, grouping, and aggregation
- Assists with data validation and transformation

#### Matplotlib
- Generates visualization charts
- Renders charts as embedded SVGs in reports
- Creates PNG/JPG exports of visualization

#### Jinja2
- Templates for HTML report generation
- Dynamic content rendering in reports
- Theme application to reports

#### pytestqt
- Enables testing of Qt components in pytest
- Provides QtBot for GUI interaction simulation
- Handles signal waiting and verification in tests

## Technical Requirements

### Performance Requirements
- Handle CSV files with 10,000+ rows efficiently
- Responsive UI during data processing
- Efficient chart generation
- Memory-optimized for large datasets

### Compatibility
- Windows 10/11 (primary target)
- macOS support (secondary target)
- Linux support (potential future target)

### Security Considerations
- Local file operations only
- No external data transmission
- Secure file handling

## Implementation Considerations

### Character Encoding
- Special handling for German umlauts (ä, ö, ü, ß)
- Automatic detection of file encoding
- Normalization of Unicode characters
- Conversion between different encoding formats

### CSV Format Support
```
Date,Player Name,Source/Location,Chest Type,Value,Clan
2023-03-11,Feldjäger,Level 25 Crypt,Fire Chest,275,MY_CLAN
```

### Validation System
- Maintain lists for valid player names, chest types, and sources
- Visual highlight of validation errors in data table
- Toggles for automatic validation on import
- Error reporting with suggested corrections

### Correction System
- String replacement based on correction rules
- Fuzzy matching with configurable strictness
- Correction history tracking
- Rule management interface

### Report Generation
- HTML reports with Total Battle theming
- Embedded data tables and SVG charts
- Summary statistics sections
- User-customizable report elements
- PDF export capability using a dedicated library (planned)

### PDF Generation Libraries (Under Evaluation)
- **WeasyPrint**: HTML to PDF conversion with CSS styling support
- **ReportLab**: Comprehensive PDF generation framework
- **PyFPDF**: Lightweight PDF generation library
- **Qt's QPdfWriter**: Native Qt-based PDF creation (via PySide6)
- Final selection will be based on chart embedding capability, styling options, and integration with existing code

## Performance Optimization

### Data Loading
- Efficient CSV parsing with Pandas
- Background thread for loading large files
- Progress indication for long operations
- Chunked reading for memory efficiency
- Multi-file loading with consolidated progress reporting
- Two-level progress tracking (overall and per-file)

### Background Processing
- Worker-based threading model using QThread
- Task abstraction with BackgroundTask base class
- Signal-based progress reporting mechanism
- Proper error handling and cancellation support
- Thread-safe UI updates
- Improved thread cleanup with error handling
- Graceful thread termination during application shutdown
- Support for hierarchical progress reporting (task → subtask)
- Callback mechanism for detailed operation status updates

### UI Responsiveness
- Separate threads for data processing
- Background workers for long-running operations
- Signal/slot mechanism for thread communication
- Batch updates to UI elements
- Pagination for large datasets
- Enhanced progress dialog with detailed status information
- Consistent progress reporting scale (0-100) across all operations
- Cancellation support with proper cleanup

### Memory Management
- Chunked data processing for large files
- Efficient data structures for large datasets
- Cleanup of temporary files and resources
- Worker cleanup after task completion
- Memory usage monitoring
- Improved reference handling during thread termination
- Prevention of memory leaks during error conditions

## Testing Strategy

### Testing Approach
- Use pytest as the primary testing framework
- Use pytestqt for testing Qt components
- Create fixtures for common test setups
- Implement test utilities for repetitive operations
- Minimize mocking to test actual component behavior
- Organize tests by component type and workflow
- Prioritize test isolation and reproducibility
- Implement proper resource cleanup in all tests
- Include performance metrics in relevant tests

### Unit Testing
- Component-level tests for models and services
- Mock objects for external dependencies
- Coverage for core logic and edge cases
- Validate behavior of individual classes and methods
- Test error handling and edge cases
- Focus on individual component correctness

### UI Component Testing
- Test initialization and state management of UI components
- Simulate user interactions with QtBot
- Test signal emission and handling
- Test data display and visualization logic
- Verify UI state transitions and responsiveness
- Test component lifecycle (creation, update, destruction)
- Test component interaction with models and services
- Validate UI updates in response to data changes

### Integration Testing
- Test interactions between components
- Verify data flow across system boundaries
- Test different import → process → export flows
- Test configuration impact on component behavior
- Validate cross-component signal handling
- Test service coordination across multiple components
- Verify state consistency between components

### End-to-End Workflow Testing
- Simulate full user workflows
- Test critical user journeys from start to finish
- Validate error handling and recovery
- Test with realistic datasets and scenarios
- Measure performance metrics for complete workflows
- Verify UI responsiveness during long operations
- Test cancellation of operations mid-workflow
- Validate final state after workflow completion

### Background Processing Testing
- QtBot for simulating signal interactions
- Dedicated tests for background workers
- Verification of thread safety
- Task cancellation testing
- Progress reporting verification
- Resource cleanup validation
- Test execution in separate threads
- Validate thread ID differences
- Test signal handling between threads
- Verify proper cleanup on task completion
- Test error handling and reporting from background tasks

### Performance Testing
- Test with varying data sizes (small, medium, large)
- Measure processing time for key operations
- Verify memory usage with large datasets
- Include benchmarks for critical operations
- Test chunked processing efficiency
- Validate memory usage during large file operations
- Test UI responsiveness during heavy processing
- Compare performance with and without optimizations

### Test Data
- Sample CSV files with various encodings
- Edge case datasets for validation testing
- Corrupted data samples for error handling
- Large datasets for performance testing

## Logging System

### Log Configuration
- Log level is configurable (default: DEBUG)
- Log rotation enabled (5 files of 1MB each)
- Both file and console logging available
- Log format includes timestamp, level, and module name
- Detailed exception reporting with traceback
- Log handlers for both application and Qt warnings

### Log File Organization
- All logs are stored in chestbuddy/logs/
- The logs directory is automatically created if it doesn't exist
- The log path is determined relative to the app.py file location, ensuring consistency regardless of where the application is launched from 

## Progress Dialog System

### Dialog Features
- Consistent modal dialog for all long-running operations
- Clear title indicating the current operation
- Progress bar with percentage display (0-100%)
- Detailed status message showing:
  - Current file being processed (x of y)
  - File name and path
  - Current operation details (rows processed, etc.)
- Cancel button for operation termination
- Minimum width to ensure readability of paths and messages
- Proper cleanup on cancellation or completion

### Progress Reporting Protocol
- Operations report progress on a consistent 0-100 scale
- Multi-step operations provide hierarchical progress:
  - Overall operation progress (e.g., files 2/10)
  - Current step progress (e.g., rows 150/500)
- Each progress update includes:
  - Numeric progress value (0-100)
  - Contextual information (current file, operation details)
  - Optional status message override

### Implementation
- MainWindow manages the ProgressDialog instance
- DataManager coordinates between UI and background workers
- BackgroundWorker manages the thread and signal connections
- Tasks emit progress signals with detailed information
- Signal chain: Task → BackgroundWorker → DataManager → MainWindow → ProgressDialog

### Progress State Tracking
- MainWindow maintains a _loading_state dictionary with:
  - Total number of files being processed
  - Current file index and path
  - List of processed files
  - Current operation details
- This state ensures consistent progress reporting across loading phases
- Provides context for progress dialog messages
- Enables proper handling of cancellation and cleanup

## Report Generation System (Planned)

### Report Templates
- HTML-based templates using Jinja2
- Configurable sections and layouts
- Ability to include or exclude specific data sections
- Support for embedded charts and visualizations
- Custom styling options

### Report Elements
- **DataTable**: Tabular representation of data
- **Chart**: Embedded visualization
- **Summary**: Statistical summary of data
- **Header**: Report identification and metadata
- **Footer**: Notes and additional information
- **Custom**: User-defined content sections

### PDF Generation
- HTML to PDF conversion
- Support for embedded SVG charts
- Page sizing and layout options
- Header and footer on each page
- Proper handling of page breaks
- Bookmarks for navigation
- Metadata support (title, author, keywords)

### Report Generation Workflow
1. User selects report template
2. User configures included data and charts
3. User customizes report layout and styling
4. System generates HTML report preview
5. User can make adjustments
6. System exports final report (HTML or PDF)

### Implementation Considerations
- Support for large datasets in reports
- Memory optimization during report generation
- Progress reporting during report creation
- PDF library selection based on feature requirements
- Chart embedding approach that maintains quality
- Support for interactive elements in HTML reports
