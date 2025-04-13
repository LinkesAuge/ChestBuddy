"""
validation_adapter.py

Connects the ValidationService to the TableStateManager.
"""

from PySide6.QtCore import QObject, Slot
import pandas as pd
import typing
import logging

# Updated import
from chestbuddy.core.services import ValidationService
from chestbuddy.core.table_state_manager import TableStateManager, CellFullState, CellState
from chestbuddy.core.enums.validation_enums import ValidationStatus

# Placeholder types for clarity
# ValidationService = typing.NewType("ValidationService", QObject)
# TableStateManager = typing.NewType("TableStateManager", QObject)
# ValidationStatus = typing.NewType("ValidationStatus", str)  # Assuming enum/str

logger = logging.getLogger(__name__)


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
        # Assuming ValidationService has a 'validation_changed' signal
        # that emits validation results (e.g., a DataFrame)
        try:
            # Connect to the correct signal name
            self._validation_service.validation_changed.connect(self._on_validation_complete)
            print("Successfully connected validation_changed signal.")  # Debug print
        except AttributeError:
            print(
                f"Error: ValidationService object has no signal 'validation_changed'"
            )  # Debug print
            # Handle error or log appropriately
        except Exception as e:
            print(f"Error connecting validation_changed signal: {e}")  # Debug print

    @Slot(object)
    def _on_validation_complete(self, validation_results: pd.DataFrame) -> None:
        """
        Slot to handle the validation_changed signal from ValidationService.

        Processes the validation results DataFrame and updates the TableStateManager.
        """
        if not isinstance(validation_results, pd.DataFrame):
            logger.error(
                "ValidationAdapter received invalid data type for validation_results:"
                f" {type(validation_results)}"
            )
            return

        logger.info(f"ValidationAdapter received validation_changed: {type(validation_results)}")

        try:
            logger.debug(
                "Incoming validation_results DataFrame:\n%s", validation_results.to_string()
            )

            # Ensure headers map is available
            self._headers_map = self._table_state_manager.headers_map
            if not self._headers_map:
                logger.warning(
                    "Headers map not available in ValidationAdapter. Cannot process"
                    " validation results."
                )
                return

            new_states = {}  # Initialize here
            initial_new_states_count = len(new_states)  # Now safe to access
            logger.debug(f"Initial new_states count: {initial_new_states_count}")

            # Iterate through validation results (rows = data rows, columns = validation details)
            for row_idx, row_data in validation_results.iterrows():
                # Iterate through columns involved in validation (e.g., 'PLAYER_valid', 'PLAYER_status', etc.)
                # We need to group status and message by the original column name
                original_columns = set(self._headers_map.keys())  # Get actual data column names

                for base_col_name in original_columns:
                    status_col = f"{base_col_name}_status"
                    message_col = f"{base_col_name}_message"
                    valid_col = (
                        f"{base_col_name}_valid"  # Optional, for simple valid/invalid checks
                    )

                    if status_col in row_data.index and message_col in row_data.index:
                        status_value = row_data[status_col]
                        message_value = row_data[message_col]

                        # Map DataFrame status (e.g., ValidationStatus.INVALID) to CellState
                        try:
                            # Attempt direct mapping if ValidationStatus enum is used
                            if isinstance(status_value, ValidationStatus):
                                cell_state_status = CellState(status_value.value)  # Map enum value
                            elif isinstance(status_value, CellState):
                                cell_state_status = status_value  # Already CellState
                            elif (
                                isinstance(status_value, str)
                                and status_value in CellState.__members__
                            ):
                                # Handle string representation if needed
                                cell_state_status = CellState[status_value]
                            elif pd.isna(status_value):
                                # If status is NaN/None, assume NOT_VALIDATED or derive from context
                                cell_state_status = CellState.NOT_VALIDATED  # Default assumption
                                # Check if _valid column indicates VALID
                                if valid_col in row_data.index and row_data[valid_col] is True:
                                    cell_state_status = CellState.VALID
                            else:
                                # Fallback or error for unexpected status types
                                logger.warning(
                                    f"Unexpected status type for {base_col_name} at row {row_idx}: {type(status_value)}, value: {status_value}. Setting to NOT_VALIDATED."
                                )
                                cell_state_status = CellState.NOT_VALIDATED

                        except (ValueError, KeyError) as e:
                            logger.error(
                                f"Error mapping validation status '{status_value}' to CellState for {base_col_name} at row {row_idx}: {e}"
                            )
                            cell_state_status = CellState.NOT_VALIDATED  # Default on error

                        error_details = str(message_value) if pd.notna(message_value) else ""

                        # Get the corresponding column index in the data model
                        if base_col_name in self._headers_map:
                            col_idx = self._headers_map[base_col_name]

                            # Get current state to compare
                            current_full_state = self._table_state_manager.get_full_cell_state(
                                row_idx, col_idx
                            )

                            # --- Start Debug Logging for specific cell (1, 2) ---
                            # if row_idx == 1 and col_idx == 2: # Example: Check cell (1, 'SOURCE')
                            #    logger.debug(f"[Debug Cell (1, 2)] Incoming Status: {cell_state_status}, Msg: '{error_details}'")
                            #    logger.debug(f"[Debug Cell (1, 2)] Current Full State: {current_full_state}")
                            # --- End Debug Logging ---

                            # Determine if an update is needed
                            needs_update = False
                            partial_update = {}

                            if current_full_state.validation_status != cell_state_status:
                                needs_update = True
                                partial_update["validation_status"] = cell_state_status
                            # Only update error_details if the status indicates an error state
                            # and the message is different or wasn't set previously.
                            # Don't overwrite existing details if the new status is VALID/NOT_VALIDATED
                            # unless the new message is explicitly empty for a valid state.
                            if cell_state_status in [CellState.INVALID, CellState.CORRECTABLE]:
                                if current_full_state.error_details != error_details:
                                    needs_update = True
                                    partial_update["error_details"] = error_details
                            elif (
                                cell_state_status == CellState.VALID
                                and current_full_state.error_details
                            ):
                                # Clear error message if state becomes valid
                                needs_update = True
                                partial_update["error_details"] = ""  # Clear message

                            # --- Start Debug Logging for specific cell (1, 2) ---
                            # if row_idx == 1 and col_idx == 2:
                            #     logger.debug(f"[Debug Cell (1, 2)] Needs Update: {needs_update}")
                            #     logger.debug(f"[Debug Cell (1, 2)] Partial Update: {partial_update}")
                            # --- End Debug Logging ---

                            if needs_update:
                                # If starting from default, create full state, otherwise update existing
                                # We use partial_update to merge into the existing state or a default one
                                merged_state_dict = current_full_state._asdict()
                                merged_state_dict.update(partial_update)
                                # Crucially, preserve existing correction suggestions unless overwritten
                                # (Validation typically doesn't generate suggestions, so preserve)
                                if "correction_suggestions" not in partial_update:
                                    merged_state_dict["correction_suggestions"] = (
                                        current_full_state.correction_suggestions
                                    )

                                new_cell_state = CellFullState(**merged_state_dict)

                                new_states[(row_idx, col_idx)] = new_cell_state
                                # --- Start Debug Logging for specific cell (1, 2) ---
                                # if row_idx == 1 and col_idx == 2:
                                #     logger.debug(f"[Debug Cell (1, 2)] Added to new_states: {new_cell_state}")
                                # --- End Debug Logging ---

                        else:
                            logger.warning(f"Column '{base_col_name}' not found in headers map.")

            final_new_states_count = len(new_states)
            logger.debug(
                f"Processed validation results. Initial states: {initial_new_states_count}, Final states to update: {final_new_states_count}"
            )

            # Update the TableStateManager only if there are changes
            if new_states:
                self._table_state_manager.update_states(new_states)
                logger.info(
                    f"Updated TableStateManager with {len(new_states)} validation state changes."
                )
            else:
                logger.info("No validation state changes detected after processing results.")

        except Exception as e:
            logger.error(
                f"Error processing validation results in ValidationAdapter: {e}", exc_info=True
            )

    def disconnect_signals(self):
        """Disconnect signals to prevent issues during cleanup."""
        try:
            # Disconnect from the correct signal name
            self._validation_service.validation_changed.disconnect(self._on_validation_complete)
            print("Successfully disconnected validation_changed signal.")  # Debug print
        except RuntimeError:
            print("Signal already disconnected or connection failed initially.")  # Debug print
        except AttributeError:
            print(
                f"Error disconnecting: ValidationService object has no signal 'validation_changed'"
            )  # Debug print
        except Exception as e:
            print(f"Error disconnecting validation_changed signal: {e}")  # Debug print
