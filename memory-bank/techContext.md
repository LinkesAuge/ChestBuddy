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
│   │   ├── services/   # Service classes
│   │   └── controllers/ # Controllers
│   ├── ui/             # User interface components
│   │   ├── views/      # View adapters and components
│   │   ├── widgets/    # Reusable UI widgets
│   │   └── resources/  # UI resources (icons, styles)
│   └── utils/          # Utility modules
│       └── background_processing.py  # Background processing utilities
├── data/               # Sample data and resources
├── docs/               # Documentation
├── memory-bank/        # Project memory
├── scripts/            # Utility scripts
├── tests/              # Test suite
│   ├── test_background_worker.py  # Background worker tests
│   ├── test_csv_background_tasks.py  # CSV background task tests
│   └── test_files/  # Test data files
├── .cursor/            # Cursor IDE settings
│   └── rules/          # Project rules
├── .gitignore          # Git ignore file
├── pyproject.toml      # Project configuration
├── README.md           # Project readme
└── .python-version     # Python version spec
```

## PySide6 Framework

ChestBuddy uses PySide6 (Qt for Python) as its GUI framework. Key components include:

### UI Components
- **QMainWindow**: Main application window structure
- **QWidget**: Base for all custom UI components
- **QVBoxLayout/QHBoxLayout**: Layout management for components
- **QStackedWidget**: Content view switching mechanism
- **QTableView**: Display of tabular data
- **QSplitter**: Resizable panel divisions
- **QProgressDialog**: Progress indication for long operations

### Event System
- **Signal/Slot**: Event-driven communication between components
- **QThread**: Background task execution

### Styling System
- **QSS (Qt Style Sheets)**: CSS-like styling for components
- **Custom Colors Class**: Centralized color definitions
- **Theme Variables**: Consistent styling across the application

Example QSS usage:
```python
def get_sidebar_style():
    return f"""
        QListWidget {{
            background-color: {Colors.PRIMARY_DARK};
            border: none;
            border-radius: 0px;
            outline: 0;
            padding: 5px;
        }}
        QListWidget::item {{
            color: {Colors.TEXT_LIGHT};
            border-radius: 4px;
            padding: 8px;
            margin: 2px 5px;
        }}
        QListWidget::item:selected {{
            background-color: {Colors.ACCENT};
            color: {Colors.TEXT_DARK};
        }}
    """
```

## Pandas Integration

Pandas is used extensively for data management and analysis:

### DataFrame Usage
- **Core Data Structure**: All chest data stored in DataFrame
- **Validation Status**: Separate DataFrame for validation results
- **Correction Status**: Separate DataFrame for correction tracking
- **Filtering**: Query and filtering operations
- **Aggregation**: Grouping and summarizing data
- **Import/Export**: Reading and writing CSV files

### Performance Considerations
- **Vectorized Operations**: Optimize performance with vectorized pandas operations
- **Chunked Reading**: Process large files in chunks
- **DataFrame Indexing**: Proper indexing for frequently filtered columns
- **Memory Management**: Copy vs view operations for data integrity

## Background Processing

ChestBuddy implements a robust background processing framework:

### Worker Pattern
- **BackgroundWorker**: Manages threads and task execution
- **BackgroundTask**: Base class for all asynchronous tasks
- **Signal-Based Communication**: Progress reporting and completion notification

### CSV Processing
- **MultiCSVLoadTask**: Load multiple CSV files with progress tracking
- **Chunked Processing**: Read large files in manageable chunks
- **Cancellation Support**: Allow user to cancel long-running operations

### Progress Reporting
- **ProgressDialog**: Custom dialog with visual feedback
- **ProgressBar**: State-based progress indicator (normal, success, error)
- **Throttled Updates**: Prevent UI flooding during frequent updates

## Testing Infrastructure

A comprehensive testing framework ensures reliability:

### Test Types
- **Unit Tests**: Testing individual components
- **Widget Tests**: Testing UI components with QtBot
- **Integration Tests**: Testing component interactions
- **End-to-End Tests**: Testing complete workflows

### Test Tools
- **pytest**: Main testing framework
- **pytestqt**: Testing Qt components and signals
- **fixtures**: Reusable test components and data

### Test Considerations
- **Async Testing**: Special handling for background operations
- **Signal Testing**: Testing signal emissions and connections
- **UI Testing**: Testing user interface behavior
- **Mocking**: Isolating components for targeted testing

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

### Future Considerations

#### Report Generation
- HTML reports with Total Battle theming
- Embedded data tables and SVG charts
- Summary statistics sections
- PDF export capability

#### PDF Generation Libraries (Under Evaluation)
- **WeasyPrint**: HTML to PDF conversion with CSS styling support
- **ReportLab**: Comprehensive PDF generation framework
- **PyFPDF**: Lightweight PDF generation library
- **Qt's QPdfWriter**: Native Qt-based PDF creation (via PySide6)

#### Advanced Features
- Advanced filtering and searching
- User-defined chart templates
- Enhanced keyboard navigation
- Data trend detection
