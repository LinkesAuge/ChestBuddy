from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Slot
import dataclasses


class DataViewController:
    def __init__(self, view: QTableView):
        self._connect_view_signals(view)
        self._connect_model_signals()
        self._connect_state_manager_signals()

        # Connect validation request signal from the view
        if hasattr(view, "cell_edit_validation_requested"):
            view.cell_edit_validation_requested.connect(self._on_cell_edit_validation_requested)
            logger.debug(
                "Connected DataTableView.cell_edit_validation_requested to controller slot."
            )
        else:
            logger.warning("DataTableView does not have cell_edit_validation_requested signal.")

    def _connect_view_signals(self, view):
        """Connect signals from the DataTableView."""
        # Existing signal connections...
        if hasattr(view, "selection_changed_signal"):
            view.selection_changed_signal.connect(self._on_view_selection_changed)
        if hasattr(view, "context_menu_requested_signal"):
            view.context_menu_requested_signal.connect(self._on_view_context_menu_requested)
        if hasattr(view, "correction_action_triggered"):
            view.correction_action_triggered.connect(self._on_correction_action_triggered)

    @Slot(QModelIndex, str)
    def _on_cell_edit_validation_requested(self, index: QModelIndex, new_value: str):
        """Handle validation request for an edited cell."""
        if (
            not index.isValid()
            or self._validation_service is None
            or self._table_state_manager is None
        ):
            logger.warning(
                "_on_cell_edit_validation_requested: Invalid index or missing service/manager."
            )
            return

        column_name = self._data_view_model.headerData(index.column(), Qt.Orientation.Horizontal)
        logger.info(
            f"Controller received validation request for Row {index.row()}, Col {index.column()} ('{column_name}'), New Value: '{new_value}'"
        )

        # --- Check if column is validatable ---
        validatable_columns = [
            ValidationService.PLAYER_COLUMN,
            ValidationService.CHEST_COLUMN,
            ValidationService.SOURCE_COLUMN,
        ]
        if column_name not in validatable_columns:
            logger.debug(
                f"Column '{column_name}' is not configured for list validation. Skipping cell edit validation."
            )
            # Optionally, reset any previous validation state for this cell if needed
            # self._table_state_manager.update_states({(index.row(), index.column()): CellFullState(validation_status=CellState.VALID)})
            return

        # --- Call ValidationService ---
        try:
            validation_status, message = self._validation_service.validate_single_entry(
                column_name, new_value
            )
            logger.debug(
                f"Single entry validation result: Status={validation_status}, Message='{message}'"
            )

        except Exception as e:
            logger.error(f"Error calling validate_single_entry: {e}")
            validation_status = ValidationStatus.INVALID  # Assume invalid on error
            message = f"Validation error: {e}"

        # --- Update TableStateManager ---
        try:
            # Map ValidationStatus enum (from service) to CellState enum (for state manager)
            # Assuming direct mapping or similar enum values for now.
            # Adjust mapping if enums differ significantly.
            try:
                cell_state_status = CellState(
                    validation_status.value
                )  # Assumes CellState has same values as ValidationStatus
            except ValueError:
                logger.error(
                    f"Could not map ValidationStatus '{validation_status}' to CellState. Defaulting to INVALID."
                )
                cell_state_status = CellState.INVALID
                message = message or "Invalid validation status mapping."

            # Get current state to merge with
            current_full_state = self._table_state_manager.get_full_cell_state(
                index.row(), index.column()
            )
            if current_full_state is None:
                current_full_state = CellFullState()

            # Prepare update dictionary, only changing validation fields
            update_dict = {
                "validation_status": cell_state_status,
                "error_details": message or "",  # Ensure empty string if no message
            }

            # Merge changes into a new state object
            merged_state_dict = dataclasses.asdict(current_full_state)
            merged_state_dict.update(update_dict)

            # Create the final state object
            new_state = CellFullState(**merged_state_dict)

            # Update the state manager for the specific cell
            self._table_state_manager.update_states({(index.row(), index.column()): new_state})
            logger.info(
                f"Updated TableStateManager for cell ({index.row()}, {index.column()}) with state: {new_state}"
            )

        except Exception as e:
            logger.error(
                f"Error updating TableStateManager after cell edit validation: {e}", exc_info=True
            )

    def _on_view_selection_changed(self, selected_rows: list):
        # Implementation of _on_view_selection_changed method
        pass

    def _connect_model_signals(self):
        # Implementation of _connect_model_signals method
        pass

    def _connect_state_manager_signals(self):
        # Implementation of _connect_state_manager_signals method
        pass

    def _on_view_context_menu_requested(self, index: QModelIndex):
        # Implementation of _on_view_context_menu_requested method
        pass

    def _on_correction_action_triggered(self, index: QModelIndex):
        # Implementation of _on_correction_action_triggered method
        pass
