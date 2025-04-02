# DataView Refactoring - File Structure Specification

## Overview

This document specifies the file organization strategy and directory structure for the refactored DataView component. A well-organized file structure is essential for maintainability, discoverability, and separation of concerns. The structure defined here follows Python best practices and aligns with the architectural principles outlined in the overview document.

## File Organization Strategy

The file organization follows these principles:

1. **Component-Based Organization**: Files are organized around components rather than layers.
2. **Logical Grouping**: Related files are grouped together in directories.
3. **Separation of Implementation and Interfaces**: Interface definitions are separate from implementations.
4. **Proximity of Tests**: Test files are placed close to the implementation files they test.
5. **Consistent Naming**: Clear and consistent naming conventions for files and directories.

## Main Directory Structure

The refactored DataView component will be organized under the following directory structure:

```
chestbuddy/
├── ui/
│   ├── data/                      # Main directory for DataView components
│   │   ├── __init__.py            # Package initialization
│   │   ├── models/                # Data models and adapters
│   │   ├── views/                 # View components
│   │   ├── delegates/             # Cell rendering and editing delegates
│   │   ├── actions/               # User actions and commands
│   │   ├── menus/                 # Menu components
│   │   ├── widgets/               # Supporting widgets
│   │   ├── adapters/              # Integration adapters
│   │   └── utils/                 # Utility functions and classes
│   ├── ... (other UI components)
├── ... (other application components)
└── tests/
    ├── ui/
    │   ├── data/                  # Tests for DataView components
    │   │   ├── __init__.py        # Test package initialization
    │   │   ├── models/            # Tests for data models
    │   │   ├── views/             # Tests for view components
    │   │   ├── delegates/         # Tests for delegates
    │   │   ├── actions/           # Tests for actions
    │   │   ├── menus/             # Tests for menus
    │   │   ├── widgets/           # Tests for widgets
    │   │   ├── adapters/          # Tests for adapters
    │   │   └── utils/             # Tests for utilities
    │   ├── ... (tests for other UI components)
    ├── ... (tests for other application components)
```

## Component-Specific Directories

### Models Directory

```
models/
├── __init__.py                    # Package initialization, exports public interfaces
├── data_view_model.py             # Core DataViewModel implementation
├── selection_model.py             # Selection state management
├── filter_model.py                # Data filtering functionality
├── sort_model.py                  # Data sorting functionality
├── column_model.py                # Column definition and management
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    ├── i_data_model.py            # Data model interface
    ├── i_selection_model.py       # Selection model interface
    └── i_filter_model.py          # Filter model interface
```

### Views Directory

```
views/
├── __init__.py                    # Package initialization, exports public interfaces
├── data_table_view.py             # Main table view component
├── data_header_view.py            # Column header view component
├── data_row_view.py               # Row view component
├── data_cell_view.py              # Cell view component
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    ├── i_data_view.py             # Data view interface
    └── i_header_view.py           # Header view interface
```

### Delegates Directory

```
delegates/
├── __init__.py                    # Package initialization, exports public interfaces
├── cell_display_delegate.py       # Delegate for cell display
├── cell_edit_delegate.py          # Delegate for cell editing
├── validation_indicator_delegate.py  # Delegate for validation status display
├── custom_delegates/              # Custom delegates for specific data types
│   ├── __init__.py                # Package initialization
│   ├── date_delegate.py           # Delegate for date fields
│   ├── numeric_delegate.py        # Delegate for numeric fields
│   └── text_delegate.py           # Delegate for text fields
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    └── i_cell_delegate.py         # Cell delegate interface
```

### Actions Directory

```
actions/
├── __init__.py                    # Package initialization, exports public interfaces
├── edit_actions.py                # Edit-related actions (copy, paste, etc.)
├── correction_actions.py          # Correction-related actions
├── validation_actions.py          # Validation-related actions
├── import_export_actions.py       # Import/export actions
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    └── i_action.py                # Action interface
```

### Menus Directory

```
menus/
├── __init__.py                    # Package initialization, exports public interfaces
├── data_context_menu.py           # Main context menu component
├── header_context_menu.py         # Header context menu component
├── menu_factory.py                # Factory for creating context menus
├── menu_items/                    # Menu item components
│   ├── __init__.py                # Package initialization
│   ├── edit_menu_items.py         # Edit-related menu items
│   ├── correction_menu_items.py   # Correction-related menu items
│   └── validation_menu_items.py   # Validation-related menu items
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    └── i_context_menu.py          # Context menu interface
```

### Widgets Directory

```
widgets/
├── __init__.py                    # Package initialization, exports public interfaces
├── data_toolbar.py                # Toolbar for data view
├── filter_panel.py                # Panel for filtering data
├── search_box.py                  # Search box component
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    └── i_data_widget.py           # Data widget interface
```

### Adapters Directory

```
adapters/
├── __init__.py                    # Package initialization, exports public interfaces
├── validation_adapter.py          # Adapter for validation service
├── correction_adapter.py          # Adapter for correction service
├── import_export_adapter.py       # Adapter for import/export functionality
├── table_state_adapter.py         # Adapter for table state management
└── interfaces/                    # Interface definitions
    ├── __init__.py                # Package initialization
    ├── i_service_adapter.py       # Service adapter interface
    └── i_state_adapter.py         # State adapter interface
```

### Utils Directory

```
utils/
├── __init__.py                    # Package initialization, exports public interfaces
├── cell_state_utils.py            # Utilities for cell state management
├── selection_utils.py             # Utilities for selection management
├── clipboard_utils.py             # Utilities for clipboard operations
├── validation_utils.py            # Utilities for validation operations
└── performance_utils.py           # Utilities for performance optimization
```

## Test Directory Structure

The test directory structure mirrors the implementation directory structure to facilitate easy navigation and association between tests and implementation:

```
tests/ui/data/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Common test fixtures and utilities
├── models/                        # Tests for data models
│   ├── __init__.py                # Test package initialization
│   ├── test_data_view_model.py    # Tests for DataViewModel
│   ├── test_selection_model.py    # Tests for SelectionModel
│   └── ... (tests for other models)
├── views/                         # Tests for view components
│   ├── __init__.py                # Test package initialization
│   ├── test_data_table_view.py    # Tests for DataTableView
│   └── ... (tests for other views)
├── ... (tests for other component directories)
├── integration/                   # Integration tests
│   ├── __init__.py                # Test package initialization
│   ├── test_validation_integration.py  # Tests for validation integration
│   └── ... (other integration tests)
└── performance/                   # Performance tests
    ├── __init__.py                # Test package initialization
    ├── test_large_dataset.py      # Tests with large datasets
    └── ... (other performance tests)
```

## File Naming Conventions

### Implementation Files

- **Class Files**: Named after the main class they contain, in snake_case (e.g., `data_view_model.py`).
- **Interface Files**: Prefixed with `i_` to indicate an interface (e.g., `i_data_model.py`).
- **Utility Files**: Named descriptively with a `_utils` suffix (e.g., `cell_state_utils.py`).

### Test Files

- **Test Files**: Prefixed with `test_` followed by the name of the file they test (e.g., `test_data_view_model.py`).
- **Test Fixture Files**: Named `conftest.py` for pytest fixtures.

### Other Files

- **Package Initialization**: Named `__init__.py`.
- **Type Definition Files**: Suffixed with `_types` (e.g., `validation_types.py`).

## Class Naming Conventions

- **Implementation Classes**: Named using PascalCase (e.g., `DataViewModel`).
- **Interface Classes**: Prefixed with `I` to indicate an interface (e.g., `IDataModel`).
- **Abstract Classes**: Prefixed with `Abstract` to indicate an abstract class (e.g., `AbstractDataView`).
- **Mixin Classes**: Suffixed with `Mixin` to indicate a mixin (e.g., `SelectionHandlingMixin`).

## Import Conventions

- **Import Organization**:
  1. Standard library imports
  2. Third-party library imports
  3. Application-specific imports, organized by package hierarchy

- **Import Aliases**: Use consistent aliases for commonly used imports:
  ```python
  import pandas as pd
  import numpy as np
  from PySide6 import QtCore, QtWidgets, QtGui
  ```

- **Relative Imports**: Use relative imports for intra-package references:
  ```python
  from .interfaces import IDataModel
  from ..utils import cell_state_utils
  ```

- **Absolute Imports**: Use absolute imports for cross-package references:
  ```python
  from chestbuddy.core.validation import ValidationService
  from chestbuddy.utils.common import logging_utils
  ```

## Module Structure

Each module should follow this general structure:

1. **Module Docstring**: Description of the module's purpose and contents.
2. **Imports**: Organized as described above.
3. **Constants**: Module-level constants.
4. **Type Definitions**: Type aliases and enums.
5. **Classes**: Class definitions.
6. **Functions**: Function definitions.
7. **Module-Level Code**: Any code that runs at module import time.

Example:

```python
"""
data_view_model.py

This module contains the DataViewModel class, which serves as an adapter between
the ChestDataModel and the DataTableView, providing data access, sorting, and filtering.
"""

# Standard library imports
import typing
from enum import Enum

# Third-party imports
import pandas as pd
from PySide6 import QtCore

# Application imports
from chestbuddy.core.models import ChestDataModel
from .interfaces import IDataModel

# Constants
DEFAULT_PAGE_SIZE = 100
MAX_VISIBLE_COLUMNS = 50

# Type definitions
ColumnIndex = typing.NewType('ColumnIndex', int)
RowIndex = typing.NewType('RowIndex', int)

# Classes
class SortOrder(Enum):
    """Enumeration for sort orders."""
    ASCENDING = 'asc'
    DESCENDING = 'desc'

class DataViewModel(QtCore.QAbstractTableModel, IDataModel):
    """
    Implementation of the DataViewModel, which adapts the ChestDataModel
    for display in a QTableView.
    """
    # Class implementation...

# Functions
def convert_column_index(model_index: ColumnIndex, view_index: ColumnIndex) -> ColumnIndex:
    """Convert between model and view column indices."""
    # Function implementation...
```

## Conclusion

This file structure specification provides a comprehensive guide for organizing the files in the DataView refactoring project. Following this structure will enhance maintainability, facilitate discovery, and ensure a clean separation of concerns throughout the codebase. The structure is designed to be scalable and adaptable as the project grows and evolves. 