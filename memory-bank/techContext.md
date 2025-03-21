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

## Performance Optimization

### Data Loading
- Efficient CSV parsing with Pandas
- Background thread for loading large files
- Progress indication for long operations
- Chunked reading for memory efficiency

### Background Processing
- Worker-based threading model using QThread
- Task abstraction with BackgroundTask base class
- Signal-based progress reporting mechanism
- Proper error handling and cancellation support
- Thread-safe UI updates

### UI Responsiveness
- Separate threads for data processing
- Background workers for long-running operations
- Signal/slot mechanism for thread communication
- Batch updates to UI elements
- Pagination for large datasets

### Memory Management
- Chunked data processing for large files
- Efficient data structures for large datasets
- Cleanup of temporary files and resources
- Worker cleanup after task completion
- Memory usage monitoring

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
- Reference files for validation verification
- Various file formats and structures
- International character sets in test data
- Malformed data for robustness testing

### Test Infrastructure
- Fixtures for common test setup and teardown
- Helper functions for repetitive testing operations
- Custom assertions for common verification patterns
- Resource cleanup utilities
- Thread-safe test helpers
- Test data generators
- Mock factory for external dependencies

### Planned Test Files
- test_main_window.py: Tests for the main application window
- test_integration.py: Tests for cross-component interactions
- test_workflows.py: End-to-end workflow tests
- test_performance.py: Performance and memory usage tests
- Enhancements to existing test files for more comprehensive coverage 