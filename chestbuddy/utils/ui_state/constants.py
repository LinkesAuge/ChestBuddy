"""
UI State Constants.

This module defines constants used by the UI state management system,
including standard UI element groups and operations.
"""

from enum import Enum, auto


class UIElementGroups(Enum):
    """
    Standard groups of UI elements that can be blocked/unblocked together.

    These groups provide a convenient way to target multiple UI elements
    with a single operation.
    """

    # The entire main window
    MAIN_WINDOW = auto()

    # Data-related views and elements
    DATA_VIEW = auto()

    # Validation-related views and elements
    VALIDATION = auto()

    # Correction-related views and elements
    CORRECTION = auto()

    # Dashboard components
    DASHBOARD = auto()

    # Navigation elements (sidebar, tabs, etc.)
    NAVIGATION = auto()

    # Menu bar and associated actions
    MENU_BAR = auto()

    # Toolbar items
    TOOLBAR = auto()

    # Status bar
    STATUS_BAR = auto()

    # Dialog-specific elements
    DIALOG = auto()


class UIOperations(Enum):
    """
    Standard operations that might block UI elements.

    These operations provide a consistent way to identify what is
    blocking a UI element.
    """

    # Data import operations
    IMPORT = auto()

    # Data export operations
    EXPORT = auto()

    # General data processing operations
    PROCESSING = auto()

    # Data validation operations
    VALIDATION = auto()

    # Data correction operations
    CORRECTION = auto()

    # Chart generation and rendering
    CHART = auto()

    # Report generation
    REPORT = auto()

    # Background tasks
    BACKGROUND_TASK = auto()

    # Manual blocking (used when code explicitly blocks UI)
    MANUAL = auto()
