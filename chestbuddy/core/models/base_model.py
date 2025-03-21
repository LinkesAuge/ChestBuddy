"""
BaseModel module.

This module provides the BaseModel class that other models can inherit from.
"""

from PySide6.QtCore import QObject, Signal


class BaseModel(QObject):
    """
    Base class for all models in the application.

    Provides common functionality and signals that are used by multiple model classes.
    Follows the Observer pattern by inheriting from QObject and using signals.

    Attributes:
        model_changed (Signal): Signal emitted when the model data changes.
    """

    # Define signals
    model_changed = Signal()

    def __init__(self) -> None:
        """Initialize the BaseModel."""
        super().__init__()

    def initialize(self) -> None:
        """
        Initialize the model with default values.

        This method should be overridden by subclasses to initialize
        model-specific data structures.
        """
        pass

    def clear(self) -> None:
        """
        Clear all data in the model.

        This method should be overridden by subclasses to clear
        model-specific data structures.
        """
        pass

    def save(self) -> bool:
        """
        Save the model data.

        This method should be overridden by subclasses to save
        model-specific data.

        Returns:
            True if the data was saved successfully, False otherwise.
        """
        return True

    def load(self) -> bool:
        """
        Load the model data.

        This method should be overridden by subclasses to load
        model-specific data.

        Returns:
            True if the data was loaded successfully, False otherwise.
        """
        return True

    def _notify_change(self) -> None:
        """Emit the model_changed signal to notify observers of changes."""
        self.model_changed.emit()
