"""
validation_adapter.py

Connects the ValidationService to the TableStateManager.
"""

from PySide6.QtCore import QObject, Slot
import pandas as pd
import typing

# Placeholder imports - adjust based on actual locations
# from chestbuddy.core.services import ValidationService
# from chestbuddy.core.managers import TableStateManager
# from chestbuddy.core.enums import ValidationStatus

# Placeholder types for clarity
ValidationService = typing.NewType("ValidationService", QObject)
TableStateManager = typing.NewType("TableStateManager", QObject)
ValidationStatus = typing.NewType("ValidationStatus", str)  # Assuming enum/str


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

        # Directly pass the results DataFrame to the TableStateManager
        try:
            # Assuming TableStateManager handles the transformation internally
            self._table_state_manager.update_cell_states_from_validation(validation_results)
            print(f"Passed validation results DataFrame to TableStateManager.")  # Debug print
        except AttributeError:
            print(
                f"Error: TableStateManager object has no method 'update_cell_states_from_validation'"
            )  # Debug print
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
