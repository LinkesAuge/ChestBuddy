"""
action_context.py

Defines the context passed to actions.
"""

import typing
from dataclasses import dataclass
from typing import List, Optional, Any

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QWidget

# Import the actual DataViewModel class
from ..models.data_view_model import DataViewModel

# Forward declare CorrectionService type hint
CorrectionService = Any  # Replace Any with actual type when available
# Forward declare ValidationService type hint
ValidationService = Any  # Replace Any with actual type when available


@dataclass(frozen=True)
class ActionContext:
    """Holds information about the context in which an action is invoked."""

    clicked_index: QModelIndex
    selection: List[QModelIndex]
    model: Optional["DataViewModel"]  # Use string literal for forward reference
    parent_widget: Optional[QWidget]
    correction_service: Optional[CorrectionService] = None  # Add optional service
    validation_service: Optional[ValidationService] = None  # Add optional validation service

    # Consider adding config_manager etc. as needed
