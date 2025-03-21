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
├── data/               # Sample data and resources
├── docs/               # Documentation
├── memory-bank/        # Project memory
├── scripts/            # Utility scripts
├── tests/              # Test suite
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

### UI Responsiveness
- Separate threads for data processing
- Batch updates to UI elements
- Pagination for large datasets

### Memory Management
- Efficient data structures for large datasets
- Cleanup of temporary files and resources
- Memory usage monitoring

## Testing Strategy

### Unit Testing
- Component-level tests for models and services
- Mock objects for external dependencies
- Coverage for core logic and edge cases

### Integration Testing
- End-to-end workflow testing
- File import/export verification
- UI interaction testing

### Test Data
- Sample CSV files with various encodings
- Edge case datasets
- Corrupted data samples for error handling 