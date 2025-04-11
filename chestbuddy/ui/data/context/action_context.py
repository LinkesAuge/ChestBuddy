"""
action_context.py

Defines the context passed to actions.
"""

import typing
from dataclasses import dataclass

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QWidget

# Import the actual DataViewModel class
from ..models.data_view_model import DataViewModel


@dataclass
class ActionContext:
    """Information needed to build context menus and execute actions."""

    clicked_index: QModelIndex
    selection: typing.List[QModelIndex]
    model: typing.Optional[DataViewModel]
    parent_widget: QWidget  # Needed for QMenu parent and potentially for action execution
    # Add other context if needed by actions (e.g., view object)
