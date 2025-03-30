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
    correction_error = Signal(str)  # Error message

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

    def apply_corrections(self, only_invalid=False):
        """
        Apply corrections in a background thread.

        Args:
            only_invalid (bool): If True, only apply corrections to invalid cells
        """
        # Clean up any existing worker
        self._cleanup_worker()

        # Emit signal that correction has started
        self.correction_started.emit("Applying correction rules")

        # Create a new worker for the background task
        self._worker = BackgroundWorker(self._apply_corrections_task, only_invalid=only_invalid)

        # Connect signals
        self._worker.started.connect(lambda: logger.debug("Correction task started"))
        self._worker.progress.connect(self._on_corrections_progress)
        self._worker.finished.connect(self._on_corrections_completed)
        self._worker.error.connect(self._on_corrections_error)

        # Start the task
        self._worker.start()

        logger.info(f"Started applying corrections (only_invalid={only_invalid})")

    def _apply_corrections_task(self, only_invalid=False, progress_callback=None):
        """
        Background task for applying corrections.

        Args:
            only_invalid (bool): If True, only apply corrections to invalid cells
            progress_callback (callable): Function to report progress

        Returns:
            Dict[str, int]: Correction statistics
        """
        # Report initial progress
        if progress_callback:
            progress_callback(0, 100)

        # Apply corrections
        correction_stats = self._correction_service.apply_corrections(only_invalid=only_invalid)

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

    def add_rule(self, rule):
        """
        Add a new correction rule.

        Args:
            rule (CorrectionRule): The rule to add

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.add_rule(rule)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Added rule: {rule}")
            return result
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            self.correction_error.emit(f"Error adding rule: {str(e)}")
            return False

    def update_rule(self, index, rule):
        """
        Update an existing rule.

        Args:
            index (int): The index of the rule to update
            rule (CorrectionRule): The updated rule

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.update_rule(index, rule)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Updated rule at index {index}: {rule}")
            return result
        except Exception as e:
            logger.error(f"Error updating rule: {e}")
            self.correction_error.emit(f"Error updating rule: {str(e)}")
            return False

    def delete_rule(self, index):
        """
        Delete a rule.

        Args:
            index (int): The index of the rule to delete

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.delete_rule(index)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Deleted rule at index {index}")
            return result
        except Exception as e:
            logger.error(f"Error deleting rule: {e}")
            self.correction_error.emit(f"Error deleting rule: {str(e)}")
            return False

    def reorder_rule(self, from_index, to_index):
        """
        Change rule order.

        Args:
            from_index (int): The current index of the rule
            to_index (int): The target index for the rule

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.move_rule(from_index, to_index)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Moved rule from index {from_index} to {to_index}")
            return result is not None and True
        except Exception as e:
            logger.error(f"Error reordering rule: {e}")
            self.correction_error.emit(f"Error reordering rule: {str(e)}")
            return False

    def move_rule_to_top(self, index):
        """
        Move rule to top of category.

        Args:
            index (int): The index of the rule to move

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.move_rule_to_top(index)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Moved rule at index {index} to top")
            return result is not None and True
        except Exception as e:
            logger.error(f"Error moving rule to top: {e}")
            self.correction_error.emit(f"Error moving rule to top: {str(e)}")
            return False

    def move_rule_to_bottom(self, index):
        """
        Move rule to bottom of category.

        Args:
            index (int): The index of the rule to move

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.move_rule_to_bottom(index)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Moved rule at index {index} to bottom")
            return result is not None and True
        except Exception as e:
            logger.error(f"Error moving rule to bottom: {e}")
            self.correction_error.emit(f"Error moving rule to bottom: {str(e)}")
            return False

    def toggle_rule_status(self, index):
        """
        Toggle a rule's enabled/disabled status.

        Args:
            index (int): The index of the rule to toggle

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.toggle_rule_status(index)

            # Update view if available
            if result and self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Toggled status for rule at index {index}")
            return result is not None and True
        except Exception as e:
            logger.error(f"Error toggling rule status: {e}")
            self.correction_error.emit(f"Error toggling rule status: {str(e)}")
            return False

    def get_rules(self, category=None, status=None):
        """
        Get rules with optional filtering.

        Args:
            category (str, optional): Filter by rule category
            status (str, optional): Filter by rule status

        Returns:
            List[CorrectionRule]: List of rules matching the filters
        """
        try:
            return self._rule_manager.get_rules(category=category, status=status)
        except Exception as e:
            logger.error(f"Error getting rules: {e}")
            self.correction_error.emit(f"Error getting rules: {str(e)}")
            return []

    def get_prioritized_rules(self):
        """
        Get rules sorted for application priority.

        Returns:
            List[CorrectionRule]: Prioritized list of rules
        """
        try:
            return self._rule_manager.get_prioritized_rules()
        except Exception as e:
            logger.error(f"Error getting prioritized rules: {e}")
            self.correction_error.emit(f"Error getting prioritized rules: {str(e)}")
            return []

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

    def get_correction_preview(self, rule):
        """
        Get preview of corrections that would be applied by a rule.

        Args:
            rule (CorrectionRule): The rule to preview

        Returns:
            List[Tuple[int, int, str, str]]: List of (row, column, old_value, new_value) tuples
        """
        try:
            return self._correction_service.get_correction_preview(rule)
        except Exception as e:
            logger.error(f"Error getting correction preview: {e}")
            self.correction_error.emit(f"Error getting correction preview: {str(e)}")
            return []

    def import_rules(self, file_path, replace_existing=False):
        """
        Import correction rules from a file.

        Args:
            file_path (str): Path to the rules file
            replace_existing (bool): Whether to replace existing rules

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.load_rules(
                file_path=file_path, replace_existing=replace_existing
            )

            # Update view if available
            if self._view and hasattr(self._view, "update_rule_list"):
                self._view.update_rule_list()

            logger.info(f"Imported rules from {file_path} (replace_existing={replace_existing})")
            return result
        except Exception as e:
            logger.error(f"Error importing rules: {e}")
            self.correction_error.emit(f"Error importing rules: {str(e)}")
            return False

    def export_rules(self, file_path, only_enabled=False):
        """
        Export correction rules to a file.

        Args:
            file_path (str): Path to save the rules
            only_enabled (bool): Whether to export only enabled rules

        Returns:
            bool: Success status
        """
        try:
            result = self._rule_manager.save_rules(file_path=file_path, only_enabled=only_enabled)
            logger.info(f"Exported rules to {file_path} (only_enabled={only_enabled})")
            return result
        except Exception as e:
            logger.error(f"Error exporting rules: {e}")
            self.correction_error.emit(f"Error exporting rules: {str(e)}")
            return False
