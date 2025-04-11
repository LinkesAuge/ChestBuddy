"""
correction_adapter.py

Connects the CorrectionService to the TableStateManager for correction states.
"""

from PySide6.QtCore import QObject, Slot
import typing

# Placeholder imports - adjust based on actual locations
from chestbuddy.core.services import CorrectionService
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState, CellState
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Placeholder types for clarity
# CorrectionService = typing.NewType("CorrectionService", QObject)
# TableStateManager = typing.NewType("TableStateManager", QObject)
# CorrectionState = typing.NewType(
#     "CorrectionState", object
# )  # Type depends on what state manager needs


class CorrectionAdapter(QObject):
    """
    Listens for correction suggestions/results from CorrectionService and updates
    the TableStateManager accordingly.
    """

    def __init__(
        self,
        correction_service: CorrectionService,
        table_state_manager: TableStateManager,
        parent: QObject = None,
    ):
        """
        Initialize the CorrectionAdapter.

        Args:
            correction_service: The application's CorrectionService instance.
            table_state_manager: The application's TableStateManager instance.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._correction_service = correction_service
        self._table_state_manager = table_state_manager

        self._connect_signals()

    def _connect_signals(self):
        """Connect signals from the CorrectionService."""
        # Assuming CorrectionService has a 'correction_suggestions_available' signal
        # that emits correction info (e.g., a dict mapping (row, col) to suggestions)
        # Adjust signal name and signature as needed
        try:
            self._correction_service.correction_suggestions_available.connect(
                self._on_corrections_available
            )
            print("Successfully connected correction_suggestions_available signal.")  # Debug print
        except AttributeError:
            print(
                f"Error: CorrectionService object has no signal 'correction_suggestions_available'"
            )  # Debug print
        except Exception as e:
            print(f"Error connecting correction_suggestions_available signal: {e}")  # Debug print

    @Slot(object)
    def _on_corrections_available(self, correction_suggestions: dict):
        """
        Slot to handle the correction_suggestions_available signal from CorrectionService.

        Processes the suggestions (expected dict: {(row, col): [suggestion1, ...]}) and updates
        the TableStateManager, marking cells as CORRECTABLE and preserving existing validation info.

        Args:
            correction_suggestions: Dictionary mapping (row, col) tuples to lists of suggestions.
        """
        print(
            f"CorrectionAdapter received correction_suggestions_available: {type(correction_suggestions)}"
        )
        if not correction_suggestions or not isinstance(correction_suggestions, dict):
            print("No correction suggestions received or not a dict, skipping update.")
            return

        state_changes: typing.Dict[typing.Tuple[int, int], CellFullState] = {}

        for (row, col), suggestions in correction_suggestions.items():
            if not suggestions:
                continue  # Skip if suggestions list is empty

            key = (row, col)
            # Fetch existing state to merge, preserving validation info
            existing_state = (
                self._table_state_manager.get_full_cell_state(row, col) or CellFullState()
            )

            # Create update object: Mark as CORRECTABLE and store suggestions
            # Keep existing validation details
            change_state = CellFullState(
                validation_status=CellState.CORRECTABLE,
                error_details=existing_state.error_details,  # Preserve validation details
                correction_suggestions=suggestions,
            )
            state_changes[key] = change_state

        # Update TableStateManager using the update_states method
        try:
            if state_changes:
                self._table_state_manager.update_states(state_changes)
                print(
                    f"Sent {len(state_changes)} correction state updates to TableStateManager."
                )  # Debug
            else:
                print("No correction state changes detected.")  # Debug
        except AttributeError as e:
            print(f"Error: TableStateManager missing method or attribute: {e}")  # Debug
        except Exception as e:
            print(f"Error updating TableStateManager with correction state updates: {e}")  # Debug

    def disconnect_signals(self):
        """Disconnect signals to prevent issues during cleanup."""
        try:
            self._correction_service.correction_suggestions_available.disconnect(
                self._on_corrections_available
            )
            print(
                "Successfully disconnected correction_suggestions_available signal."
            )  # Debug print
        except RuntimeError:
            print(
                "Correction signal already disconnected or connection failed initially."
            )  # Debug print
        except AttributeError:
            print(
                f"Error disconnecting: CorrectionService object has no signal 'correction_suggestions_available'"
            )  # Debug print
        except Exception as e:
            print(
                f"Error disconnecting correction_suggestions_available signal: {e}"
            )  # Debug print
