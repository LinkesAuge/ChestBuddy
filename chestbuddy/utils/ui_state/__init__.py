"""
UI State Management System.

This module provides a centralized way to manage UI state, especially
for blocking and unblocking UI elements during long-running operations.

Core Components:
    - UIStateManager: Singleton class for managing UI state.
    - OperationContext: Context manager for UI blocking operations.
    - BlockableElementMixin: Mixin for UI elements that can be blocked.
    - UIOperations: Enum of standard UI operations.
    - UIElementGroups: Enum of standard UI element groups.
    - UIStateSignals: Signals for UI state changes.
"""

from chestbuddy.utils.ui_state.constants import UIOperations, UIElementGroups
from chestbuddy.utils.ui_state.context import OperationContext, ManualOperationContext
from chestbuddy.utils.ui_state.elements import BlockableElementMixin, BlockableWidgetGroup
from chestbuddy.utils.ui_state.manager import UIStateManager
from chestbuddy.utils.ui_state.signals import UIStateSignals

__all__ = [
    "UIStateManager",
    "OperationContext",
    "ManualOperationContext",
    "BlockableElementMixin",
    "BlockableWidgetGroup",
    "UIOperations",
    "UIElementGroups",
    "UIStateSignals",
]
