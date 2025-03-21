# ChestBuddy

A comprehensive desktop application for Total Battle players and clan leaders to import, validate, correct, analyze, and visualize chest data.

## Overview

ChestBuddy combines the functionality of two existing tools (ChestParser and CorrectionTool) into a single, integrated application. It enables Total Battle players to:

- Import chest data from CSV files
- Validate data against known player names, chest types, and sources
- Correct common errors, including character encoding issues with German umlauts
- Analyze data with powerful filtering and grouping capabilities
- Visualize results with customizable charts
- Generate themed HTML reports with selected data and visualizations

## Features

- **Data Import/Export**: Support for CSV files with automatic encoding detection
- **Validation System**: Maintain validation lists for players, chest types, and sources
- **Correction System**: Apply string replacements based on correction rules
- **German Umlaut Handling**: Detection and repair of encoding issues for German characters
- **Analysis Capabilities**: Calculate statistics by player, chest type, and source
- **Visualization**: Multiple chart types with customization options
- **Report Generation**: Themed HTML reports with user-selected data and charts

## Development

### Prerequisites

- Python 3.12+
- UV package manager
- Git

### Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/ChestBuddy.git
   cd ChestBuddy
   ```

2. Set up virtual environment with UV
   ```
   uv venv
   ```

3. Install dependencies
   ```
   uv pip install -e .
   ```

4. Run the application
   ```
   python main.py
   ```

## Project Structure

```
ChestBuddy/
├── chestbuddy/         # Main package
├── data/               # Sample data and resources
├── docs/               # Documentation
├── memory-bank/        # Project memory
├── scripts/            # Utility scripts
├── tests/              # Test suite
├── .cursor/            # Cursor IDE settings
├── .gitignore          # Git ignore file
├── main.py             # Application entry point
├── pyproject.toml      # Project configuration
└── README.md           # Project readme
```

## License

[MIT License](LICENSE)
