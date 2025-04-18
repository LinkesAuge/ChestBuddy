"""
correction_controller.py

Description: Controller for coordinating correction operations including rule management and applying corrections
Usage:
    controller = CorrectionController(correction_service, rule_manager, config_manager)
    controller.set_view(correction_view)
    controller.apply_corrections()
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Callable
from PySide6.QtCore import Signal, QObject, QThread, Slot, QModelIndex
from PySide6.QtWidgets import QMessageBox

from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.utils.background_processing import BackgroundWorker
from chestbuddy.core.services import CorrectionService, ValidationService
from chestbuddy.ui.dialogs import CorrectionPreviewDialog

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
        status_message_changed (Signal): Emitted for general status updates
    """

    # Define signals
    correction_started = Signal(str)  # Operation description
    correction_progress = Signal(int, int)  # current, total
    correction_completed = Signal(object)  # Statistics dictionary
    correction_error = Signal(str)
    status_message_changed = Signal(str)  # For general status updates

    # Maximum recursive iterations to prevent infinite loops
    MAX_ITERATIONS = 10

    def __init__(
        self,
        correction_service,
        rule_manager,
        config_manager,
        validation_service=None,
        signal_manager=None,
    ):
        """
        Initialize the CorrectionController with required dependencies.

        Args:
            correction_service: Service for applying corrections
            rule_manager: Manager for correction rules
            config_manager: Manager for application configuration
            validation_service: Service for validation
            signal_manager: Optional manager for signal tracking
        """
        super().__init__(signal_manager)
        self._correction_service = correction_service
        self._rule_manager = rule_manager
        self._config_manager = config_manager
        self._validation_service = validation_service
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
            recursive (bool): If True, apply corrections recursively until no more changes occur
            selected_only (bool): If True, only apply to selected cells
            progress_callback (callable): Function to report progress

        Returns:
            Dict[str, int]: Correction statistics
        """
        # Initialize accumulators for statistics
        total_stats = {"total_corrections": 0, "corrected_rows": 0, "corrected_cells": 0}
        iteration = 0

        # Report initial progress
        if progress_callback:
            progress_callback(0, 100)

        # Track data state for detecting changes
        previous_hash = None
        current_hash = self._get_data_hash()

        logger.info(
            f"Starting correction process: only_invalid={only_invalid}, recursive={recursive}, selected_only={selected_only}"
        )

        # Handle selection-based correction
        if (
            selected_only
            and hasattr(self, "_view")
            and self._view is not None
            and hasattr(self._view, "get_selected_indexes")
        ):
            # Get selected indexes
            selected_indexes = self._view.get_selected_indexes()

            # If there are selected indexes, apply selection filtering
            if selected_indexes and hasattr(self, "_data_model") and self._data_model is not None:
                self._data_model.apply_selection_filter(selected_indexes)

        try:
            # Apply corrections iteratively if recursive is True
            while iteration < self.MAX_ITERATIONS:
                # Apply a single round of corrections
                current_stats = self._correction_service.apply_corrections(
                    only_invalid=only_invalid
                )

                # Update accumulated statistics
                total_stats["total_corrections"] += current_stats["total_corrections"]
                # Take the maximum values for rows and cells as they might overlap
                total_stats["corrected_rows"] = max(
                    total_stats["corrected_rows"], current_stats["corrected_rows"]
                )
                total_stats["corrected_cells"] = max(
                    total_stats["corrected_cells"], current_stats["corrected_cells"]
                )

                # Update progress
                if progress_callback:
                    progress = min(90, int(90 * (iteration + 1) / self.MAX_ITERATIONS))
                    progress_callback(progress, 100)

                iteration += 1
                logger.debug(f"Correction iteration {iteration}: {current_stats}")

                # Stop if no corrections were made or we're not in recursive mode
                if current_stats["total_corrections"] == 0 or not recursive:
                    break

                # Check if data has changed
                previous_hash = current_hash
                current_hash = self._get_data_hash()
                if previous_hash == current_hash:
                    logger.debug("No data changes detected, stopping recursive correction")
                    break
        finally:
            # Clean up selection filtering
            if selected_only and hasattr(self, "_data_model") and self._data_model is not None:
                self._data_model.restore_from_filtered_changes()

        # Add iteration count to statistics
        total_stats["iterations"] = iteration

        # Report final progress
        if progress_callback:
            progress_callback(100, 100)

        logger.info(f"Correction completed after {iteration} iterations: {total_stats}")
        return total_stats

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
            self._rule_manager.import_rules(file_path, replace=replace, save_as_default=True)
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
            if rule is None:
                logger.error(f"Rule at index {index} not found for deletion")
                self.correction_error.emit(f"Error deleting rule: Rule at index {index} not found")
                return False

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

    def get_rules(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> List[CorrectionRule]:
        """
        Get correction rules with optional filtering.

        Args:
            category (str, optional): Filter by category (player, chest_type, etc.)
            status (str, optional): Filter by status (enabled, disabled)
            search_term (str, optional): Filter rules containing this text in 'from_value' or
                'to_value'. Case-insensitive.

        Returns:
            List[CorrectionRule]: Filtered correction rules
        """
        return self._rule_manager.get_rules(
            category=category,
            status=status,
            search_term=search_term,
        )

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
        # First try to use the directly stored validation service
        if self._validation_service:
            return self._validation_service

        # Fall back to getting from correction service
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

    def reorder_rule(self, index, direction):
        """
        Reorder a rule by moving it up or down.

        Args:
            index (int): Index of rule to move
            direction (int): -1 to move up, 1 to move down

        Returns:
            bool: Success status
        """
        try:
            # Calculate the target index
            rules = self._rule_manager.get_rules()
            if not (0 <= index < len(rules)):
                logger.error(f"Invalid rule index for reordering: {index}")
                return False

            target_index = index + direction
            if not (0 <= target_index < len(rules)):
                logger.error(f"Cannot move rule to index {target_index}")
                return False

            # Move rule
            self._rule_manager.move_rule(index, target_index)
            logger.info(f"Reordered rule from index {index} to {target_index}")
            return True
        except Exception as e:
            logger.error(f"Error reordering rule: {e}")
            self.correction_error.emit(f"Error reordering rule: {str(e)}")
            return False

    def toggle_rule_status(self, index):
        """
        Toggle a rule's enabled/disabled status.

        Args:
            index (int): Index of rule to toggle

        Returns:
            bool: Success status
        """
        try:
            # Toggle rule status
            self._rule_manager.toggle_rule_status(index)
            logger.info(f"Toggled status of rule at index {index}")
            return True
        except Exception as e:
            logger.error(f"Error toggling rule status: {e}")
            self.correction_error.emit(f"Error toggling rule status: {str(e)}")
            return False

    def move_rule_to_top(self, index):
        """
        Move a rule to the top of its category.

        Args:
            index (int): Index of rule to move

        Returns:
            bool: Success status
        """
        try:
            # Move rule to top
            self._rule_manager.move_rule_to_top(index)
            logger.info(f"Moved rule at index {index} to top")
            return True
        except Exception as e:
            logger.error(f"Error moving rule to top: {e}")
            self.correction_error.emit(f"Error moving rule to top: {str(e)}")
            return False

    def move_rule_to_bottom(self, index):
        """
        Move a rule to the bottom of its category.

        Args:
            index (int): Index of rule to move

        Returns:
            bool: Success status
        """
        try:
            # Move rule to bottom
            self._rule_manager.move_rule_to_bottom(index)
            logger.info(f"Moved rule at index {index} to bottom")
            return True
        except Exception as e:
            logger.error(f"Error moving rule to bottom: {e}")
            self.correction_error.emit(f"Error moving rule to bottom: {str(e)}")
            return False

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

    def _get_data_hash(self):
        """
        Get a hash of the current data model state.

        Returns:
            str: Hash of the current data state
        """
        if (
            not hasattr(self._correction_service, "_data_model")
            or self._correction_service._data_model is None
        ):
            return None

        try:
            data_str = str(self._correction_service._data_model.data)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating data hash: {e}")
            return None

    def auto_correct_after_validation(self, results=None):
        """
        Apply auto-correction after validation if enabled.

        This method checks the configuration to see if auto-correction
        after validation is enabled, and if so, applies corrections
        to invalid cells.

        Args:
            results: Optional validation results (ignored, but needed for signal compatibility)

        Returns:
            bool: True if auto-correction was applied, False otherwise
        """
        # Always check for correctable cells after validation
        if hasattr(self._correction_service, "check_correctable_status"):
            try:
                num_correctable = self._correction_service.check_correctable_status()
                logger.info(
                    f"Checked for correctable cells after validation: {num_correctable} cells marked as correctable"
                )
            except Exception as e:
                logger.error(f"Error checking for correctable cells after validation: {e}")

        if not self._config_manager:
            return False

        # Check if auto-correction is enabled
        auto_correct = self._config_manager.get_auto_correct_on_validation()
        if not auto_correct:
            logger.debug("Auto-correction after validation is disabled")
            return False

        # Apply corrections to invalid cells only
        logger.info("Applying auto-correction after validation")
        self.apply_corrections(only_invalid=True, recursive=True)
        return True

    def auto_correct_on_import(self, data=None):
        """
        Apply auto-correction on import if enabled.

        This method checks the configuration to see if auto-correction
        on import is enabled, and if so, applies corrections to all cells.

        Args:
            data: Optional data parameter (ignored, but may be needed for signal compatibility)

        Returns:
            bool: True if auto-correction was applied, False otherwise
        """
        # Always check for correctable cells after import
        if hasattr(self._correction_service, "check_correctable_status"):
            try:
                num_correctable = self._correction_service.check_correctable_status()
                logger.info(
                    f"Checked for correctable cells after import: {num_correctable} cells marked as correctable"
                )
            except Exception as e:
                logger.error(f"Error checking for correctable cells after import: {e}")

        if not self._config_manager:
            return False

        # Check if auto-correction is enabled
        auto_correct = self._config_manager.get_auto_correct_on_import()
        if not auto_correct:
            logger.debug("Auto-correction on import is disabled")
            return False

        # Apply corrections to all cells
        logger.info("Applying auto-correction on import")
        self.apply_corrections(only_invalid=False, recursive=True)
        return True

    @Slot(QModelIndex, object)
    def apply_correction_from_ui(self, index: QModelIndex, suggestion: Any):
        """
        Slot to receive correction requests from the UI (e.g., CorrectionDelegate).

        Args:
            index: The QModelIndex of the cell to correct.
            suggestion: The CorrectionSuggestion object selected by the user.
        """
        # --- Basic Validation ---
        if not index.isValid():
            logger.warning("apply_correction_from_ui received an invalid index.")
            self.correction_error.emit("Cannot apply correction to an invalid cell index.")
            return
        if suggestion is None or not hasattr(suggestion, "corrected_value"):
            logger.warning(f"apply_correction_from_ui received an invalid suggestion: {suggestion}")
            self.correction_error.emit("Invalid correction suggestion received from UI.")
            return
        # --- End Basic Validation ---

        row = index.row()
        col = index.column()
        corrected_value = suggestion.corrected_value

        logger.info(
            f"Applying correction from UI: Index=({row},{col}), Suggestion='{corrected_value}'"
        )
        try:
            # Call the NEW service method
            success = self._correction_service.apply_ui_correction(row, col, corrected_value)

            if success:
                logger.info("Correction applied successfully via UI request.")
                # Optional: emit completion signal or trigger revalidation?
                # self.correction_completed.emit(...)
            else:
                logger.warning("Correction via UI request reported no changes or failed.")
                # Maybe emit a different signal or just log?

        except AttributeError as e:
            # This specific error shouldn't happen now, but keep general exception handling
            logger.error(
                f"CorrectionService is missing the expected method apply_ui_correction: {e}"
            )
            self.correction_error.emit("Internal error: Correction service method not found.")
        except Exception as e:
            logger.error(f"Error applying correction from UI: {e}", exc_info=True)
            self.correction_error.emit(f"Error applying correction: {e}")

    @Slot(int, int, object)
    def handle_correction_selected(self, row: int, col: int, corrected_value: Any):
        """
        Handle a correction selection from the UI (typically from a delegate).

        This method receives a correction selection from the new DataView refactoring
        components and applies it to the specified cell.

        Args:
            row (int): The row index of the cell to correct
            col (int): The column index of the cell to correct
            corrected_value (Any): The value to apply as the correction
        """
        logger.info(f"Handling correction selection: row={row}, col={col}, value={corrected_value}")

        try:
            # Get the appropriate model index if we need a QModelIndex
            if hasattr(self._correction_service, "apply_ui_correction"):
                # Use the new dedicated method if available
                self._correction_service.apply_ui_correction(row, col, corrected_value)
                self.status_message_changed.emit(f"Applied correction at row {row}, column {col}")
            else:
                # Legacy fallback - construct a model index and use the old method
                logger.warning(
                    "Using legacy correction application method - service doesn't implement apply_ui_correction"
                )
                from PySide6.QtCore import QModelIndex

                model_index = QModelIndex()  # This is a placeholder - need real model index
                self.apply_correction_from_ui(model_index, corrected_value)

            # Emit completed signal with minimal stats
            self.correction_completed.emit(
                {"corrected_cells": 1, "corrected_rows": 1, "total_corrections": 1}
            )

        except Exception as e:
            logger.error(f"Error applying correction: {e}")
            self.correction_error.emit(f"Failed to apply correction: {e}")

    def connect_view(self, view: "CorrectionRuleView"):
        """Connect signals from the CorrectionRuleView."""
        self._view = view
        # Connect existing signals
        view.apply_corrections_requested.connect(self._on_apply_corrections_requested)
        view.rule_added.connect(self._on_rule_added)
        view.rule_edited.connect(self._on_rule_edited)
        view.rule_deleted.connect(self._on_rule_deleted)

        # Connect NEW preview signal
        if hasattr(view, "preview_rule_requested"):
            view.preview_rule_requested.connect(self._on_preview_rule_requested)
        else:
            log = getattr(self, "_logger", logger)
            log.warning("CorrectionRuleView does not have preview_rule_requested signal.")

        # ... (other connections like filter changes, etc.) ...

    @Slot(CorrectionRule)
    def _on_preview_rule_requested(self, rule: CorrectionRule):
        """Handle request to preview a specific correction rule."""
        log = getattr(self, "_logger", logger)

        if not rule:
            log.warning("Preview requested for invalid rule.")
            return

        log.info(
            f"Preview requested for rule ID: {rule.id} ('{rule.from_value}' -> '{rule.to_value}')"
        )

        try:
            # Assuming get_correction_preview returns List[Tuple[int, str, Any, Any]]
            preview_data = self._correction_service.get_correction_preview(rule)
            log.debug(f"Preview generated {len(preview_data)} potential changes.")

            if not preview_data:
                msg_box = QMessageBox(self._view)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("Rule Preview")
                msg_box.setText("This rule currently does not affect any data.")
                msg_box.exec()
                return

            # --- Show Preview Dialog ---
            log.info("Showing Correction Preview Dialog.")
            preview_dialog = CorrectionPreviewDialog(preview_data, self._view)
            preview_dialog.exec()

        except Exception as e:
            log.error(f"Error generating correction preview for rule {rule.id}: {e}", exc_info=True)
            error_box = QMessageBox(self._view)
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("Preview Error")
            error_box.setText(f"Could not generate preview for rule.\nError: {e}")
            error_box.exec()
