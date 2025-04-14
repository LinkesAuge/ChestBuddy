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
    state_manager: Optional[Any]  # Use Any for now, or import TableStateManager
    correction_service: Optional[CorrectionService] = None  # Add optional service
    validation_service: Optional[ValidationService] = None  # Add optional validation service

    # Consider adding config_manager etc. as needed

    # Helper to get cell state (using Optional chaining in case model/state_manager is None)
    def get_cell_state(
        self, index: QModelIndex
    ) -> Optional[Any]:  # Return type depends on CellFullState
        """Helper method to safely get the state for a given index."""
        if self.state_manager and index.isValid():
            # Assuming state_manager has get_full_cell_state(row, col)
            # We need to map the potentially proxy model index to the source if necessary,
            # but actions typically operate on source model indices passed in context.
            # If model is proxy, map index first? Depends on how context is created.
            # For now, assume index passed IS the source index or state_manager handles proxy.
            # Let's assume state_manager takes row/col directly.
            try:
                # Import CellFullState if not already imported
                # from chestbuddy.core.table_state_manager import CellFullState
                return self.state_manager.get_full_cell_state(index.row(), index.column())
            except AttributeError:
                print("Warning: state_manager missing get_full_cell_state method")
                return None
            except Exception as e:
                print(f"Error getting cell state in ActionContext: {e}")
                return None
        return None
