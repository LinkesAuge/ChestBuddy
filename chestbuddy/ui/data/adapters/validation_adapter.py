"""
validation_adapter.py

Connects the ValidationService to the TableStateManager.
"""

from PySide6.QtCore import QObject, Slot
import pandas as pd
import typing

# Placeholder imports - adjust based on actual locations
from chestbuddy.core.services import ValidationService
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState, CellState
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

    @Slot(object)
    def _on_validation_complete(self, validation_results: pd.DataFrame):
        """
        Slot to handle the validation_complete signal from ValidationService.

        Transforms validation results (expected DataFrame) and updates the
        TableStateManager, preserving existing correction information.

        Args:
            validation_results: The validation results DataFrame.
                                Expected to have columns like 'ColumnName_status'
                                and optional 'ColumnName_details'.
        """
        print(f"ValidationAdapter received validation_complete: {type(validation_results)}")
        if validation_results is None or not isinstance(validation_results, pd.DataFrame):
            print("Validation results are None or not a DataFrame, skipping update.")
            return

        if validation_results.empty:
            print("Validation results DataFrame is empty, skipping update.")
            return

        state_changes: typing.Dict[typing.Tuple[int, int], CellFullState] = {}
        col_names = self._table_state_manager.get_column_names()
        col_map = {name: i for i, name in enumerate(col_names)}
        num_rows = len(validation_results)

        print(f"Processing {num_rows} rows, using column map: {col_map}")  # Debug

        # --- Efficient Iteration over DataFrame --- #
        # Create lookup for status/details columns that exist
        status_cols_present = {
            f"{name}_status": name
            for name in col_names
            if f"{name}_status" in validation_results.columns
        }
        details_cols_present = {
            f"{name}_details": name
            for name in col_names
            if f"{name}_details" in validation_results.columns
        }

        # Iterate using itertuples for potentially better performance
        for row_idx, row_data in enumerate(
            validation_results.itertuples(index=False, name="ValidationRow")
        ):
            row_data_dict = row_data._asdict()  # Convert NamedTuple to dict for easier access

            # Process Status Columns
            for status_col, base_col_name in status_cols_present.items():
                if status_col in row_data_dict:
                    col_idx = col_map.get(base_col_name)
                    if col_idx is None:
                        continue  # Skip if column not found in table

                    key = (row_idx, col_idx)
                    status = row_data_dict[status_col]
                    # Convert status if it's not already CellState enum (e.g., bool, int)
                    if not isinstance(status, CellState):
                        # Basic conversion, might need refinement based on service output
                        if str(status).lower() in ("invalid", "false", "0"):
                            status = CellState.INVALID
                        # Add other conversions if needed (e.g., for CORRECTABLE, WARNING)
                        else:
                            status = CellState.VALID  # Default to valid if not recognized

                    # Get existing state or create default
                    current_full_state = (
                        self._table_state_manager.get_full_cell_state(row_idx, col_idx)
                        or CellFullState()
                    )

                    # Create update object, preserving existing details/suggestions
                    change_state = CellFullState(
                        validation_status=status,
                        error_details=current_full_state.error_details,
                        correction_suggestions=current_full_state.correction_suggestions,
                    )
                    state_changes[key] = change_state  # Add/overwrite in changes dict

            # Process Details Columns
            for details_col, base_col_name in details_cols_present.items():
                if details_col in row_data_dict:
                    col_idx = col_map.get(base_col_name)
                    if col_idx is None:
                        continue  # Skip if column not found

                    key = (row_idx, col_idx)
                    details = row_data_dict[details_col]

                    # Get the state to update (either from current changes or existing)
                    state_to_update = state_changes.get(
                        key,
                        self._table_state_manager.get_full_cell_state(row_idx, col_idx)
                        or CellFullState(),
                    )

                    # Update details
                    state_to_update.error_details = str(details) if details is not None else None
                    state_changes[key] = state_to_update  # Ensure it's in the changes dict

        # --- Update TableStateManager --- #
        try:
            if state_changes:
                # Filter out states that haven't actually changed from the default
                # This avoids unnecessary signals if validation confirms everything is NORMAL
                # However, we MUST send updates if details/suggestions were added/removed
                # even if validation_status remains NORMAL.
                # The `update_states` method handles merging and only emitting if needed.
                self._table_state_manager.update_states(state_changes)
                print(
                    f"Sent {len(state_changes)} potential state updates to TableStateManager."
                )  # Debug
            else:
                print("No validation state changes detected.")  # Debug
        except AttributeError as e:
            print(f"Error: TableStateManager missing method or attribute: {e}")  # Debug
        except Exception as e:
            print(f"Error updating TableStateManager: {e}")  # Debug

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
