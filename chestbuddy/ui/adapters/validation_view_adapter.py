"""
Adapter for the Validation View.
"""
import logging
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal, Slot

from chestbuddy.core.data_model import ChestDataModel
from chestbuddy.ui.validation.validation_rules import ValidationRules
from chestbuddy.ui.components.updatable_view import UpdatableView
from chestbuddy.ui.validation.validation_tab_view import ValidationTabView
from chestbuddy.ui.adapters.helpers.setup_validation_operations import setup_validation_operations
from chestbuddy.ui.validation.validation_operation import ValidationOperation

logger = logging.getLogger(__name__)


class ValidationViewAdapter(QObject):
    """
    Adapter for the Validation View that bridges the data model and UI components.
    
    This adapter handles the communication between the data model and the validation views,
    updates the validation state, and provides filtering functionality.
    """
    
    # Signals emitted by the adapter
    refresh_needed = Signal()
    filter_changed = Signal(str, bool)  # filter text, is regex
    
    def __init__(
        self, 
        data_model: ChestDataModel,
        view: ValidationTabView,
    ) -> None:
        """
        Initialize the ValidationViewAdapter.
        
        Args:
            data_model: The chest data model to validate
            view: The validation tab view to connect
        """
        super().__init__()
        
        # Store references to model and view
        self.data_model = data_model
        self.view = view
        
        # Create validation components
        self.validation_rules = ValidationRules()
        self.operations: List[ValidationOperation] = []
        
        # Connect signals
        self._connect_signals()
        
        # Initialize validation operations
        self._initialize_operations()
    
    def _initialize_operations(self) -> None:
        """Initialize the validation operations from the validation rules."""
        logger.debug("Initializing validation operations")
        self.operations = setup_validation_operations(
            self.validation_rules,
            self.data_model
        )
    
    def _connect_signals(self) -> None:
        """Connect signals between the data model, view, and this adapter."""
        # Connect model signals
        self.data_model.data_changed.connect(self._on_data_changed)
        
        # Connect to validation updates
        self.validation_rules.validation_updated.connect(self._on_validation_updated)
        
        # Connect view signals if view implements UpdatableView
        if isinstance(self.view, UpdatableView):
            self.refresh_needed.connect(self.view.request_update)
    
    def _on_data_changed(self) -> None:
        """Handle data model changes by requesting a view update."""
        logger.debug("Data model changed, requesting validation view update")
        self.refresh_needed.emit()
    
    def _on_validation_updated(self) -> None:
        """
        Handle validation updates by scheduling a debounced view update.
        
        This method is called when the validation state changes. It uses
        schedule_update with debouncing to prevent recursive validation
        updates that could lead to infinite loops or stack overflows.
        """
        logger.debug("Validation updated, scheduling view update with debounce")
        if isinstance(self.view, UpdatableView):
            self.view.schedule_update(debounce_ms=100)
    
    def refresh(self) -> None:
        """Refresh the validation view by emitting the refresh signal."""
        logger.debug("Refreshing validation view")
        self.refresh_needed.emit()
    
    @Slot(str, bool)
    def set_filter(self, filter_text: str, is_regex: bool = False) -> None:
        """
        Set a new filter for the validation view.
        
        Args:
            filter_text: The text to filter by
            is_regex: Whether the filter text is a regular expression
        """
        logger.debug(f"Setting validation filter: '{filter_text}', regex={is_regex}")
        self.filter_changed.emit(filter_text, is_regex)