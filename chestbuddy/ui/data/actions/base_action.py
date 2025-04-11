"""
base_action.py

Defines the abstract base class for context-aware actions.
"""

import typing
from abc import ABC, abstractmethod

from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QWidget

# Import real ActionContext
from ..context.action_context import ActionContext

# Assuming ContextMenuInfo will be renamed/moved
# from ..menus.context_menu_factory import ContextMenuInfo as ActionContext
# ActionContext = typing.NewType("ActionContext", object)  # Placeholder


class AbstractContextAction(ABC):
    """
    Abstract base class for actions that operate within a specific context
    (e.g., DataTableView context menu).
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the action (e.g., 'copy', 'view_error')."""
        pass

    @property
    @abstractmethod
    def text(self) -> str:
        """Text to display for the action (e.g., in a menu)."""
        pass

    @property
    def icon(self) -> typing.Optional[QIcon]:
        """Optional icon for the action."""
        return None

    @property
    def shortcut(self) -> typing.Optional[QKeySequence]:
        """Optional keyboard shortcut."""
        return None

    @property
    def tooltip(self) -> str:
        """Tooltip text for the action."""
        return self.text  # Default to action text

    @abstractmethod
    def is_applicable(self, context: ActionContext) -> bool:
        """
        Determines if this action should be considered/visible in the given context.
        (e.g., 'Apply Correction' is only applicable if a cell is correctable).
        """
        pass

    @abstractmethod
    def is_enabled(self, context: ActionContext) -> bool:
        """
        Determines if this action should be enabled (clickable) in the given context.
        Assumes is_applicable is already true.
        (e.g., 'Paste' is only enabled if clipboard has text).
        """
        pass

    @abstractmethod
    def execute(self, context: ActionContext) -> None:
        """
        Performs the action.
        """
        pass
