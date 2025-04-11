"""
correction_adapter.py

Connects the CorrectionService to the TableStateManager for correction states.
"""

from PySide6.QtCore import QObject, Slot
import typing

# Placeholder imports - adjust based on actual locations
# from chestbuddy.core.services import CorrectionService
# from chestbuddy.core.managers import TableStateManager

# Placeholder types for clarity
CorrectionService = typing.NewType("CorrectionService", QObject)
TableStateManager = typing.NewType("TableStateManager", QObject)
CorrectionState = typing.NewType(
    "CorrectionState", object
)  # Type depends on what state manager needs


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

        # Transform suggestions into a list of (row, col) tuples for cells with suggestions
        correctable_cells = [
            (row, col)
            for (row, col), suggestions in correction_suggestions.items()
            if suggestions  # Only include if there are actual suggestions
        ]

        if not correctable_cells:
            print("No cells found with correctable suggestions.")  # Debug print
            return

        # Update TableStateManager using the specific method for marking cells correctable
        try:
            self._table_state_manager.update_cell_states_from_correctable(correctable_cells)
            print(
                f"Updating TableStateManager marking {len(correctable_cells)} cells as correctable."
            )  # Debug print
        except AttributeError:
            print(
                f"Error: TableStateManager object has no method 'update_cell_states_from_correctable'"
            )  # Debug print
        except Exception as e:
            print(f"Error updating TableStateManager with correctable cells: {e}")  # Debug print

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
