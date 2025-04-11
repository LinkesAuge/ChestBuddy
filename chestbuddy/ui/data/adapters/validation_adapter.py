"""
validation_adapter.py

Connects the ValidationService to the TableStateManager.
"""

from PySide6.QtCore import QObject, Slot
import pandas as pd
import typing

# Placeholder imports - adjust based on actual locations
from chestbuddy.core.services import ValidationService
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Placeholder types for clarity
# ValidationService = typing.NewType("ValidationService", QObject)
# TableStateManager = typing.NewType("TableStateManager", QObject)
# ValidationStatus = typing.NewType("ValidationStatus", str)  # Assuming enum/str


class ValidationAdapter(QObject):
    """
    Listens for validation results from ValidationService and updates
    the TableStateManager accordingly.
    """

    def __init__(
        self,
        validation_service: ValidationService,
        table_state_manager: TableStateManager,
        parent: QObject = None,
    ):
        """
        Initialize the ValidationAdapter.

        Args:
            validation_service: The application's ValidationService instance.
            table_state_manager: The application's TableStateManager instance.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._validation_service = validation_service
        self._table_state_manager = table_state_manager

        self._connect_signals()

    def _connect_signals(self):
        """Connect signals from the ValidationService."""
        # Assuming ValidationService has a 'validation_complete' signal
        # that emits validation results (e.g., a DataFrame)
        # Adjust signal name and signature as needed
        try:
            self._validation_service.validation_complete.connect(self._on_validation_complete)
            print("Successfully connected validation_complete signal.")  # Debug print
        except AttributeError:
            print(
                f"Error: ValidationService object has no signal 'validation_complete'"
            )  # Debug print
            # Handle error or log appropriately
        except Exception as e:
            print(f"Error connecting validation_complete signal: {e}")  # Debug print

    @Slot(object)  # Adjust type hint based on actual signal payload (e.g., pd.DataFrame)
    def _on_validation_complete(self, validation_results):
        """
        Slot to handle the validation_complete signal from ValidationService.

        Updates the TableStateManager with the received results.

        Args:
            validation_results: The validation results (DataFrame expected).
        """
        print(
            f"ValidationAdapter received validation_complete: {type(validation_results)}"
        )  # Debug print
        if validation_results is None or not isinstance(validation_results, pd.DataFrame):
            print("Validation results are None or not a DataFrame, skipping update.")  # Debug print
            return

        # Transform the results DataFrame into the format needed by TableStateManager
        # Assuming validation_results DataFrame has columns like 'ColumnName_status'
        # and potentially 'ColumnName_details'.
        state_changes: typing.Dict[typing.Tuple[int, int], CellFullState] = {}
        num_rows = len(validation_results)
        col_map = {name: i for i, name in enumerate(self._table_state_manager.get_column_names())}

        for row_idx in range(num_rows):
            for col_name, col_idx in col_map.items():
                status_col = f"{col_name}_status"
                details_col = f"{col_name}_details"

                status = validation_results.iloc[row_idx].get(status_col, ValidationStatus.VALID)
                details = validation_results.iloc[row_idx].get(details_col, None)

                # We only need to store changes from the default VALID state
                if status != ValidationStatus.VALID or details:
                    # Fetch existing state to merge, preserving correction info
                    existing_state = self._table_state_manager.get_full_cell_state(
                        row_idx, col_idx
                    )  # Assume this method exists
                    if not existing_state:
                        existing_state = CellFullState()

                    state_changes[(row_idx, col_idx)] = CellFullState(
                        validation_status=status,
                        error_details=details,
                        correction_suggestions=existing_state.correction_suggestions,  # Preserve suggestions
                    )

        # Update the TableStateManager with the transformed changes
        try:
            # Assuming TableStateManager has an update_states method
            if state_changes:
                self._table_state_manager.update_states(state_changes)
                print(f"Sent {len(state_changes)} state updates to TableStateManager.")  # Debug
            else:
                print("No validation state changes detected.")  # Debug
        except AttributeError:
            print(f"Error: TableStateManager object has no method 'update_states'")  # Debug print
        except Exception as e:
            print(f"Error updating TableStateManager: {e}")  # Debug print

    def disconnect_signals(self):
        """Disconnect signals to prevent issues during cleanup."""
        try:
            self._validation_service.validation_complete.disconnect(self._on_validation_complete)
            print("Successfully disconnected validation_complete signal.")  # Debug print
        except RuntimeError:
            print("Signal already disconnected or connection failed initially.")  # Debug print
        except AttributeError:
            print(
                f"Error disconnecting: ValidationService object has no signal 'validation_complete'"
            )  # Debug print
        except Exception as e:
            print(f"Error disconnecting validation_complete signal: {e}")  # Debug print
