# Chest Buddy - Chest Tracker Correction Tool

A tool for validating and correcting chest tracker data in Total Battle.

## Features

- Data import and export in CSV format
- Data validation with multiple rules
- Data correction with various strategies
- User-friendly interface

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ChestBuddy.git
   cd ChestBuddy
   ```

2. Install using uv:
   ```
   uv pip install -e .
   ```

## Usage

Run the application:

```
python -m chestbuddy.main
```

Or using the setuptools entry point:

```
chestbuddy
```

## Data Format

The application expects CSV files with the following columns:
- Date
- Player Name
- Source/Location
- Chest Type
- Value
- Clan

## Development

To run tests:

```
pytest
```

## License

MIT License
