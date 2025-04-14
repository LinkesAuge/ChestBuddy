"""
validation_adapter.py

Connects the ValidationService to the TableStateManager.
"""

from PySide6.QtCore import QObject, Slot
import pandas as pd
import typing
import logging
import dataclasses

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
        # Assuming ValidationService has a 'validation_complete' signal
        # that emits validation results (e.g., a DataFrame)
        try:
            # Connect to the correct signal name
            self._validation_service.validation_complete.connect(self._on_validation_complete)
        except AttributeError:
            logger.error(
                f"Error connecting signal: ValidationService object has no signal 'validation_complete'"
            )
        except Exception as e:
            logger.error(f"Error connecting validation_complete signal: {e}")

    @Slot(object)
    def _on_validation_complete(self, validation_results: pd.DataFrame) -> None:
        """
        Slot to handle the validation_complete signal from ValidationService.

        Processes the validation results DataFrame (status_df) and updates the TableStateManager.
        """
        if not isinstance(validation_results, pd.DataFrame):
            logger.error(
                "ValidationAdapter received invalid data type for validation_results:"
                f" {type(validation_results)}"
            )
            return

        status_df = validation_results
        logger.info(f"ValidationAdapter received validation_complete: Rows={len(status_df)}")

        try:
            logger.debug("Incoming validation status DataFrame:\n%s", status_df.to_string())

            # Ensure headers map is available from the state manager
            self._headers_map = self._table_state_manager.headers_map
            if not self._headers_map:
                logger.warning(
                    "Headers map not available in ValidationAdapter. Cannot process"
                    " validation results."
                )
                return

            new_states: typing.Dict[typing.Tuple[int, int], CellFullState] = {}

            # Iterate through the rows (index) of the status DataFrame
            for row_idx in status_df.index:
                # Iterate through the original data columns using the headers map
                for base_col_name, col_idx in self._headers_map.items():
                    status_col = f"{base_col_name}_status"
                    message_col = f"{base_col_name}_message"

                    # Check if status and message columns exist for this base column
                    if status_col in status_df.columns and message_col in status_df.columns:
                        status_value = status_df.at[row_idx, status_col]
                        message_value = status_df.at[row_idx, message_col]

                        # --- Map ValidationStatus to CellState ---
                        cell_state_status = CellState.NORMAL  # Default state is NORMAL
                        if isinstance(status_value, ValidationStatus):
                            if status_value == ValidationStatus.VALID:
                                cell_state_status = CellState.VALID
                            elif status_value == ValidationStatus.INVALID:
                                cell_state_status = CellState.INVALID
                            elif status_value == ValidationStatus.CORRECTABLE:
                                cell_state_status = CellState.CORRECTABLE
                            elif status_value == ValidationStatus.NOT_VALIDATED:
                                cell_state_status = CellState.NORMAL
                            elif status_value == ValidationStatus.INVALID_ROW:
                                cell_state_status = CellState.INVALID
                        elif not pd.isna(status_value):
                            # Handle cases where status might be non-enum but not NaN (e.g., old format?)
                            logger.warning(
                                f"Unexpected status type {type(status_value)} for {base_col_name} at row {row_idx}. Value: {status_value}. Setting to NORMAL."
                            )
                            cell_state_status = CellState.NORMAL
                        # --- End Mapping ---

                        error_details = str(message_value) if pd.notna(message_value) else ""

                        # --- Create Full State, Preserving Suggestions --- #
                        # Get current state ONLY to retrieve existing suggestions
                        current_state = self._table_state_manager.get_full_cell_state(
                            row_idx, col_idx
                        )
                        existing_suggestions = (
                            current_state.correction_suggestions if current_state else []
                        )

                        # Create the new full state based ONLY on validation results + existing suggestions
                        new_cell_state = CellFullState(
                            validation_status=cell_state_status,
                            error_details=error_details,
                            correction_suggestions=existing_suggestions,  # Preserve suggestions
                        )
                        new_states[(row_idx, col_idx)] = new_cell_state
                        # --- End State Creation ---

            final_new_states_count = len(new_states)
            logger.debug(
                f"Processed validation results. Final states to update: {final_new_states_count}"
            )

            # Update the TableStateManager with ALL processed states
            # Let the state manager determine actual changes and emit signals
            if new_states:
                logger.info(
                    f"---> ValidationAdapter: Calling update_states with {len(new_states)} states."
                )  # DEBUG
                # DEBUG: Log a sample state
                if new_states:
                    sample_key = next(iter(new_states))
                    logger.debug(
                        f"---> ValidationAdapter: Sample state for {sample_key}: {new_states[sample_key]}"
                    )
                # --- END DEBUG ---
                self._table_state_manager.update_states(new_states)
                logger.info(
                    f"<--- ValidationAdapter: update_states call finished. Sent {len(new_states)} states to TableStateManager."
                )  # DEBUG
            else:
                logger.info("No validation states generated to send to TableStateManager.")

        except Exception as e:
            logger.error(
                f"Error processing validation results in ValidationAdapter: {e}", exc_info=True
            )

    def disconnect_signals(self):
        """Disconnect signals to prevent issues during cleanup."""
        try:
            # Disconnect from the correct signal name
            self._validation_service.validation_complete.disconnect(self._on_validation_complete)
        except RuntimeError:
            # Signal already disconnected or connection failed initially.
            logger.debug("Signal validation_complete already disconnected or connection failed.")
        except AttributeError:
            # Error disconnecting: ValidationService object has no signal 'validation_complete'
            logger.error(
                "Error disconnecting: ValidationService has no signal 'validation_complete'"
            )
        except Exception as e:
            logger.error(f"Error disconnecting validation_complete signal: {e}")
