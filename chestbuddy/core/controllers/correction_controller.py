"""
correction_controller.py

Description: Controller for coordinating correction operations including rule management and applying corrections
Usage:
    controller = CorrectionController(correction_service, rule_manager, config_manager)
    controller.set_view(correction_view)
    controller.apply_corrections()
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from PySide6.QtCore import Signal, QObject, QThread

from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.utils.background_processing import BackgroundWorker

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionController(BaseController):
    """
    Controller for coordinating correction operations.

    Mediates between views and services, handles user interactions
    and manages configuration.

    Attributes:
        correction_started (Signal): Emitted when correction operation starts
        correction_progress (Signal): Emitted to report correction progress
        correction_completed (Signal): Emitted when correction operation completes
        correction_error (Signal): Emitted when correction operation encounters an error
    """

    # Define signals
    correction_started = Signal(str)  # Operation description
    correction_progress = Signal(int, int)  # current, total
    correction_completed = Signal(object)  # Statistics dictionary
    correction_error = Signal(str)

    def __init__(self, correction_service, rule_manager, config_manager, signal_manager=None):
        """
        Initialize the CorrectionController with required dependencies.

        Args:
            correction_service: Service for applying corrections
            rule_manager: Manager for correction rules
            config_manager: Manager for application configuration
            signal_manager: Optional manager for signal tracking
        """
        super().__init__(signal_manager)
        self._correction_service = correction_service
        self._rule_manager = rule_manager
        self._config_manager = config_manager
        self._view = None
        self._worker = None
        self._worker_thread = None

        logger.debug("CorrectionController initialized")

    def __del__(self):
        """Clean up resources when the controller is deleted."""
        self._cleanup_worker()
        super().__del__()

    def set_view(self, view):
        """
        Set the correction view.

        Args:
            view: The view to connect with this controller
        """
        self._view = view
        logger.debug("CorrectionController: View set")

    def apply_corrections(self, only_invalid=False, recursive=True, selected_only=False):
        """
        Apply corrections in a background thread.

        Args:
            only_invalid (bool): If True, only apply corrections to invalid cells
            recursive (bool): If True, apply corrections recursively
            selected_only (bool): If True, only apply to selected cells
        """
        # Clean up any existing worker
        self._cleanup_worker()

        # Emit signal that correction has started
        self.correction_started.emit("Applying correction rules")

        # Create a new worker for the background task
        self._worker = BackgroundWorker()

        # Connect signals
        self._worker.started.connect(lambda: logger.debug("Correction task started"))
        self._worker.progress.connect(self._on_corrections_progress)
        self._worker.finished.connect(self._on_corrections_completed)
        self._worker.error.connect(self._on_corrections_error)

        # Start the task with the proper function and parameters
        self._worker.run_task(
            self._apply_corrections_task,
            only_invalid=only_invalid,
            recursive=recursive,
            selected_only=selected_only,
        )

        # Start the worker (this starts the background thread)
        self._worker.start()

        logger.info(
            f"Started applying corrections (only_invalid={only_invalid}, recursive={recursive}, selected_only={selected_only})"
        )

    def _apply_corrections_task(
        self, only_invalid=False, recursive=True, selected_only=False, progress_callback=None
    ):
        """
        Background task for applying corrections.

        Args:
            only_invalid (bool): If True, only apply corrections to invalid cells
            recursive (bool): If True, apply corrections recursively
            selected_only (bool): If True, only apply to selected cells
            progress_callback (callable): Function to report progress

        Returns:
            Dict[str, int]: Correction statistics
        """
        # Report initial progress
        if progress_callback:
            progress_callback(0, 100)

        # Apply corrections
        correction_stats = self._correction_service.apply_corrections(
            only_invalid=only_invalid, recursive=recursive, selected_only=selected_only
        )

        # Report final progress
        if progress_callback:
            progress_callback(100, 100)

        return correction_stats

    def _on_corrections_progress(self, current, total):
        """
        Handle progress updates from the background task.

        Args:
            current (int): Current progress value
            total (int): Total progress value
        """
        # Forward the progress signal
        self.correction_progress.emit(current, total)
        logger.debug(f"Correction progress: {current}/{total}")

    def _on_corrections_completed(self, correction_stats):
        """
        Handle completion of the correction task.

        Args:
            correction_stats (Dict[str, int]): Statistics about applied corrections
        """
        # Clean up worker
        self._cleanup_worker()

        # Refresh the view if available
        if self._view and hasattr(self._view, "refresh"):
            self._view.refresh()

        # Emit completion signal
        self.correction_completed.emit(correction_stats)

        logger.info(f"Corrections completed: {correction_stats}")

    def _on_corrections_error(self, error_message):
        """
        Handle errors from the correction task.

        Args:
            error_message (str): The error message
        """
        # Clean up worker
        self._cleanup_worker()

        # Emit error signal
        self.correction_error.emit(error_message)

        logger.error(f"Correction error: {error_message}")

    def _cleanup_worker(self):
        """Clean up background worker resources."""
        if self._worker:
            try:
                self._worker.stop()
            except Exception as e:
                logger.error(f"Error stopping worker: {e}")

            self._worker = None
            self._worker_thread = None
            logger.debug("Correction worker cleaned up")

    def save_rules(self):
        """
        Save correction rules to configuration.

        Returns:
            bool: Success status
        """
        try:
            # Delegate to rule manager
            self._rule_manager.save_rules()
            logger.info("Correction rules saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving correction rules: {e}")
            self.correction_error.emit(f"Error saving rules: {str(e)}")
            return False

    def load_rules(self):
        """
        Load correction rules from configuration.

        Returns:
            bool: Success status
        """
        try:
            # Delegate to rule manager
            self._rule_manager.load_rules()
            logger.info("Correction rules loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading correction rules: {e}")
            self.correction_error.emit(f"Error loading rules: {str(e)}")
            return False

    def export_rules(self, file_path):
        """
        Export correction rules to a file.

        Args:
            file_path (str): Path to export file

        Returns:
            bool: Success status
        """
        try:
            # Delegate to rule manager
            self._rule_manager.export_rules(file_path)
            logger.info(f"Correction rules exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting correction rules: {e}")
            self.correction_error.emit(f"Error exporting rules: {str(e)}")
            return False

    def import_rules(self, file_path, replace=False):
        """
        Import correction rules from a file.

        Args:
            file_path (str): Path to import file
            replace (bool): Whether to replace existing rules

        Returns:
            bool: Success status
        """
        try:
            # Delegate to rule manager
            self._rule_manager.import_rules(file_path, replace=replace)
            logger.info(f"Correction rules imported from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing correction rules: {e}")
            self.correction_error.emit(f"Error importing rules: {str(e)}")
            return False

    def add_rule(self, rule):
        """
        Add a new correction rule.

        Args:
            rule (CorrectionRule): Rule to add

        Returns:
            bool: Success status
        """
        try:
            # Add rule to manager
            self._rule_manager.add_rule(rule)
            logger.info(f"Added correction rule: {rule}")
            return True
        except Exception as e:
            logger.error(f"Error adding correction rule: {e}")
            self.correction_error.emit(f"Error adding rule: {str(e)}")
            return False

    def update_rule(self, index, rule):
        """
        Update an existing rule.

        Args:
            index (int): Index of rule to update
            rule (CorrectionRule): Updated rule

        Returns:
            bool: Success status
        """
        try:
            # Update rule in manager
            self._rule_manager.update_rule(index, rule)
            logger.info(f"Updated correction rule at index {index}: {rule}")
            return True
        except Exception as e:
            logger.error(f"Error updating correction rule: {e}")
            self.correction_error.emit(f"Error updating rule: {str(e)}")
            return False

    def delete_rule(self, index):
        """
        Delete a correction rule.

        Args:
            index (int): Index of rule to delete

        Returns:
            bool: Success status
        """
        try:
            # Get the rule for logging
            rule = self._rule_manager.get_rule(index)

            # Delete rule from manager
            self._rule_manager.delete_rule(index)
            logger.info(f"Deleted correction rule at index {index}: {rule}")
            return True
        except Exception as e:
            logger.error(f"Error deleting correction rule: {e}")
            self.correction_error.emit(f"Error deleting rule: {str(e)}")
            return False

    def clear_rules(self):
        """
        Delete all correction rules.

        Returns:
            bool: Success status
        """
        try:
            # Clear rules in manager
            self._rule_manager.clear_rules()
            logger.info("Cleared all correction rules")
            return True
        except Exception as e:
            logger.error(f"Error clearing correction rules: {e}")
            self.correction_error.emit(f"Error clearing rules: {str(e)}")
            return False

    def get_rules(self, status=None, category=None, search_term=None):
        """
        Get all correction rules.

        Args:
            status (str, optional): Filter rules by status (e.g., "enabled", "disabled").
                                   If None, returns all rules.
            category (str, optional): Filter rules by category. If None, returns rules for all categories.
            search_term (str, optional): Filter rules that contain the search term in 'from_value',
                                      'to_value', or 'description'. Case-insensitive.

        Returns:
            List[CorrectionRule]: List of correction rules
        """
        try:
            return self._rule_manager.get_rules(
                category=category, status=status, search_term=search_term
            )
        except Exception as e:
            logger.error(f"Error getting correction rules: {e}")
            self.correction_error.emit(f"Error getting rules: {str(e)}")
            return []

    def get_rule(self, index):
        """
        Get a specific correction rule.

        Args:
            index (int): Index of rule to get

        Returns:
            CorrectionRule: The correction rule
        """
        try:
            return self._rule_manager.get_rule(index)
        except Exception as e:
            logger.error(f"Error getting correction rule: {e}")
            self.correction_error.emit(f"Error getting rule: {str(e)}")
            return None

    def apply_single_rule(self, rule, only_invalid=False):
        """
        Apply a single correction rule.

        Args:
            rule (CorrectionRule): The rule to apply
            only_invalid (bool): If True, only apply to invalid cells

        Returns:
            bool: Success status
        """
        try:
            # Emit signal that correction has started
            self.correction_started.emit(f"Applying rule: {rule.from_value} -> {rule.to_value}")

            # Apply the rule
            stats = self._correction_service.apply_single_rule(rule, only_invalid=only_invalid)

            # Refresh the view if available
            if self._view and hasattr(self._view, "refresh"):
                self._view.refresh()

            # Emit completion signal
            self.correction_completed.emit(stats)

            logger.info(f"Applied single rule: {rule} (stats: {stats})")
            return True
        except Exception as e:
            logger.error(f"Error applying single rule: {e}")
            self.correction_error.emit(f"Error applying rule: {str(e)}")
            return False

    def get_cells_with_available_corrections(self):
        """
        Get list of cells that have available corrections.

        Returns:
            List[Tuple[int, int]]: List of (row, column) tuples for cells that can be corrected
        """
        try:
            return self._correction_service.get_cells_with_available_corrections()
        except Exception as e:
            logger.error(f"Error getting cells with available corrections: {e}")
            self.correction_error.emit(f"Error getting correctable cells: {str(e)}")
            return []

    def get_validation_service(self):
        """
        Get the validation service used by the correction service.

        Returns:
            ValidationService: The validation service
        """
        try:
            if self._correction_service and hasattr(
                self._correction_service, "get_validation_service"
            ):
                return self._correction_service.get_validation_service()
            return None
        except Exception as e:
            logger.error(f"Error getting validation service: {e}")
            return None

    def get_correction_status(self):
        """
        Get correction status for all cells in the data.

        Returns:
            Dict with keys:
                - invalid_cells: List of (row, col) tuples for invalid cells
                - corrected_cells: List of (row, col) tuples for cells already corrected
                - correctable_cells: List of (row, col) tuples for cells with applicable rules
                - tooltips: Dict mapping (row, col) to tooltip text
        """
        result = {
            "invalid_cells": [],
            "corrected_cells": [],
            "correctable_cells": [],
            "tooltips": {},
        }

        try:
            # Check if services are available
            if not self._correction_service:
                logger.warning("Cannot get correction status: Correction service not available")
                return result

            validation_service = self.get_validation_service()
            if not validation_service:
                logger.warning("Cannot get correction status: Validation service not available")
                return result

            # Get validation status
            validation_status = validation_service.get_validation_status()
            if validation_status is None or validation_status.empty:
                logger.debug("No validation status available")
                return result

            # Get correction rules
            rules = self.get_rules(status="enabled")

            # Get data from correction service
            data = self._correction_service.get_data()
            if data is None or data.empty:
                logger.debug("No data available")
                return result

            # Process each cell
            for row_idx in range(len(data)):
                for col_idx in range(len(data.columns)):
                    value = data.iloc[row_idx, col_idx]
                    col_name = data.columns[col_idx]

                    # Check if cell is invalid
                    is_invalid = False
                    if row_idx in validation_status.index:
                        if col_name in validation_status.columns:
                            is_invalid = not validation_status.loc[row_idx, col_name]

                    if is_invalid:
                        result["invalid_cells"].append((row_idx, col_idx))

                    # Check if cell has applicable rules
                    applicable_rules = self.get_applicable_rules(value, col_name)

                    if applicable_rules:
                        result["correctable_cells"].append((row_idx, col_idx))

                        # Create tooltip
                        tooltip = f"Original: {value}\n"
                        if len(applicable_rules) == 1:
                            tooltip += f"Can be corrected to: {applicable_rules[0].to_value}"
                        else:
                            tooltip += f"Multiple corrections available: "
                            tooltip += ", ".join([r.to_value for r in applicable_rules])

                        result["tooltips"][(row_idx, col_idx)] = tooltip

            # Get correction history to identify already corrected cells
            correction_history = self._correction_service.get_correction_history()
            for record in correction_history:
                row_idx = record.get("row")
                col_idx = record.get("column")
                if row_idx is not None and col_idx is not None:
                    result["corrected_cells"].append((row_idx, col_idx))

                    # Update tooltip for corrected cells
                    tooltip = f"Original: {record.get('old_value')}\n"
                    tooltip += f"Corrected to: {record.get('new_value')}\n"
                    tooltip += f"Rule: {record.get('rule_description', 'Unknown')}"

                    result["tooltips"][(row_idx, col_idx)] = tooltip

            logger.debug(
                f"Correction status: {len(result['invalid_cells'])} invalid, "
                + f"{len(result['corrected_cells'])} corrected, "
                + f"{len(result['correctable_cells'])} correctable cells"
            )
            return result

        except Exception as e:
            logger.error(f"Error getting correction status: {e}")
            self.correction_error.emit(f"Error getting correction status: {str(e)}")
            return result

    def get_applicable_rules(self, value, column_name=None):
        """
        Get rules applicable to a specific value and column.

        Args:
            value: The cell value to check
            column_name: Optional column name for category-specific rules

        Returns:
            List of applicable CorrectionRule objects
        """
        applicable_rules = []

        try:
            # Get all enabled rules
            rules = self.get_rules(status="enabled")

            # Find applicable rules
            for rule in rules:
                if rule.from_value == str(value):
                    # Check category if specified
                    if column_name and rule.category:
                        if rule.category == column_name:
                            applicable_rules.append(rule)
                    elif not rule.category:
                        # General rule with no category
                        applicable_rules.append(rule)

            return applicable_rules

        except Exception as e:
            logger.error(f"Error getting applicable rules: {e}")
            self.correction_error.emit(f"Error getting applicable rules: {str(e)}")
            return []

    def apply_rules_to_selection(self, selection, recursive=True, only_invalid=True):
        """
        Apply correction rules to a selection of cells.

        Args:
            selection: List of dict with keys row, col, value, column_name
            recursive: Whether to apply corrections recursively
            only_invalid: Whether to only correct invalid cells

        Returns:
            Dict with correction results
        """
        # Prepare result structure
        result = {"corrected_cells": [], "errors": []}

        try:
            # Check if correction service is available
            if not self._correction_service:
                error_msg = "Correction service not available"
                result["errors"].append(error_msg)
                self.correction_error.emit(error_msg)
                return result

            # Signal that correction has started
            self.correction_started.emit(f"Applying corrections to {len(selection)} selected cells")

            # Apply corrections to each selected cell
            corrected_count = 0
            for cell in selection:
                row = cell.get("row")
                col = cell.get("col")
                value = cell.get("value")
                column_name = cell.get("column_name")

                # Get applicable rules
                rules = self.get_applicable_rules(value, column_name)

                if not rules:
                    continue

                # Apply the highest priority rule (first in list)
                rule = rules[0]

                try:
                    # Apply the correction
                    success = self._correction_service.apply_correction_to_cell(
                        row=row, col=col, rule=rule, recursive=recursive, only_invalid=only_invalid
                    )

                    if success:
                        corrected_count += 1
                        result["corrected_cells"].append(
                            {"row": row, "col": col, "from": value, "to": rule.to_value}
                        )
                except Exception as e:
                    error_msg = f"Error correcting cell ({row}, {col}): {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            # Signal completion
            stats = {"corrected_cells": corrected_count, "errors": len(result["errors"])}
            self.correction_completed.emit(stats)

            # Refresh the view if available
            if self._view and hasattr(self._view, "refresh"):
                self._view.refresh()

            logger.info(
                f"Applied rules to selection: {corrected_count} cells corrected, {len(result['errors'])} errors"
            )
            return result

        except Exception as e:
            error_msg = f"Error applying rules to selection: {str(e)}"
            result["errors"].append(error_msg)
            self.correction_error.emit(error_msg)
            logger.error(error_msg)
            return result
