"""
correction_adapter.py

Connects the CorrectionService to the TableStateManager for correction states.
"""

from PySide6.QtCore import QObject, Slot
import typing

# Placeholder imports - adjust based on actual locations
from chestbuddy.core.services import CorrectionService
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState
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

    @Slot(object)  # Adjust type hint based on actual signal payload (e.g., dict)
    def _on_corrections_available(self, correction_suggestions):
        """
        Slot to handle the correction_suggestions_available signal from CorrectionService.

        Processes the suggestions and updates the TableStateManager to mark cells correctable.

        Args:
            correction_suggestions: The correction suggestions (dict mapping (r,c) to list expected).
        """
        print(
            f"CorrectionAdapter received correction_suggestions_available: {type(correction_suggestions)}"
        )  # Debug print
        if not correction_suggestions or not isinstance(correction_suggestions, dict):
            print(
                "No correction suggestions received or not a dict, skipping update."
            )  # Debug print
            return

        # Transform suggestions into the state_changes dict format
        state_changes: typing.Dict[typing.Tuple[int, int], CellFullState] = {}

        for (row, col), suggestions in correction_suggestions.items():
            # Fetch existing state to merge, preserving validation info
            existing_state = self._table_state_manager.get_full_cell_state(
                row, col
            )  # Assume this method exists
            if not existing_state:
                existing_state = CellFullState()

            # Update state: Mark as CORRECTABLE and store suggestions
            state_changes[(row, col)] = CellFullState(
                validation_status=ValidationStatus.CORRECTABLE,
                error_details=existing_state.error_details,  # Preserve validation details
                correction_suggestions=suggestions,
            )

        # Update TableStateManager using the update_states method
        try:
            if state_changes:
                self._table_state_manager.update_states(state_changes)
                print(
                    f"Sent {len(state_changes)} correction state updates to TableStateManager."
                )  # Debug
            else:
                print("No correction state changes detected.")  # Debug

        except AttributeError:
            print(f"Error: TableStateManager object has no method 'update_states'")  # Debug print
        except Exception as e:
            print(
                f"Error updating TableStateManager with correction state updates: {e}"
            )  # Debug print

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
