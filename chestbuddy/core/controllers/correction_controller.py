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
        self._worker = BackgroundWorker()

        # Connect signals
        self._worker.started.connect(lambda: logger.debug("Correction task started"))
        self._worker.progress.connect(self._on_corrections_progress)
        self._worker.finished.connect(self._on_corrections_completed)
        self._worker.error.connect(self._on_corrections_error)

        # Start the task with the proper function and parameters
        self._worker.run_task(self._apply_corrections_task, only_invalid=only_invalid)

        # Start the worker (this starts the background thread)
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

    def get_rules(self):
        """
        Get all correction rules.

        Returns:
            List[CorrectionRule]: List of correction rules
        """
        try:
            return self._rule_manager.get_rules()
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
