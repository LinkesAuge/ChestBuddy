# Correction Feature Refactoring: Detailed Implementation Plan

## Overview

This plan provides a comprehensive roadmap for refactoring the ChestBuddy application's correction feature to implement a more targeted, mapping-based approach for data corrections. The redesign will replace the existing general correction strategies with a precise system for mapping incorrect values to their correct equivalents.

## Project Goals

1. **Create a mapping-based correction system** that allows precise cell-level corrections
2. **Support category-based rules** (player, chest_type, source, general)
3. **Implement rule prioritization** (specific over general, order-based within categories)
4. **Develop an intuitive UI** for rule management, batch creation, and visual feedback
5. **Optimize for performance** while maintaining UI responsiveness
6. **Integrate with validation system** for identifying and correcting invalid data

## Implementation Phases

### Phase 1: Core Data Model (Days 1-2)

#### 1.1 CorrectionRule Model Class

```python
# core/models/correction_rule.py
class CorrectionRule:
    """
    Model class representing a correction rule mapping.
    
    Attributes:
        to_value (str): The correct value
        from_value (str): The incorrect value to be replaced
        category (str): The category (player, chest_type, source, general)
        status (str): The rule status (enabled or disabled)
        order (int): The rule's priority order within its category
    """
    
    def __init__(self, to_value, from_value, category, status="enabled", order=0):
        self.to_value = to_value
        self.from_value = from_value
        self.category = category
        self.status = status
        self.order = order
        
    def __eq__(self, other):
        """Enable equality comparison between rules."""
        if not isinstance(other, CorrectionRule):
            return False
        return (self.to_value == other.to_value and
                self.from_value == other.from_value and
                self.category == other.category)
                
    def __repr__(self):
        """String representation for debugging."""
        return f"CorrectionRule(to='{self.to_value}', from='{self.from_value}', " \
               f"category='{self.category}', status='{self.status}', order={self.order})"
                
    def to_dict(self):
        """Convert rule to dictionary for serialization."""
        return {
            'To': self.to_value,
            'From': self.from_value,
            'Category': self.category,
            'Status': self.status,
            'Order': self.order
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create rule from dictionary."""
        order = data.get('Order', 0)
        if isinstance(order, str) and order.strip() == '':
            order = 0
        return cls(
            to_value=data.get('To', ''),
            from_value=data.get('From', ''),
            category=data.get('Category', 'general'),
            status=data.get('Status', 'enabled'),
            order=int(order)
        )
```

#### 1.2 CorrectionRuleManager

```python
# core/models/correction_rule_manager.py
class CorrectionRuleManager:
    """
    Manager for loading, saving, and organizing correction rules.
    
    Implements rule storage, CRUD operations, and rule prioritization.
    """
    
    def __init__(self, config_manager=None):
        """Initialize with optional config manager."""
        self._rules = []
        self._config_manager = config_manager
        self._default_rules_path = Path("data/corrections/correction_rules.csv")
        
    def load_rules(self, file_path=None):
        """Load rules from CSV file."""
        # Implementation details...
        
    def save_rules(self, file_path=None):
        """Save rules to CSV file."""
        # Implementation details...
        
    def add_rule(self, rule):
        """Add a new rule to the manager."""
        # Implementation details...
        
    def update_rule(self, index, updated_rule):
        """Update an existing rule."""
        # Implementation details...
        
    def delete_rule(self, index):
        """Delete a rule by index."""
        # Implementation details...
        
    def get_rule(self, index):
        """Get a rule by index."""
        # Implementation details...
        
    def get_rules(self, category=None, status=None):
        """Get rules with optional filtering."""
        # Implementation details...
        
    def move_rule(self, from_index, to_index):
        """Move a rule to change its priority."""
        # Implementation details...
        
    def move_rule_to_top(self, index):
        """Move a rule to the top of its category."""
        # Implementation details...
        
    def move_rule_to_bottom(self, index):
        """Move a rule to the bottom of its category."""
        # Implementation details...
        
    def toggle_rule_status(self, index):
        """Toggle a rule's enabled/disabled status."""
        # Implementation details...
        
    def get_prioritized_rules(self):
        """
        Get rules sorted for application priority:
        1. General rules first
        2. Category-specific rules
        Within each group, sorted by order
        """
        # Implementation details...
```

#### 1.3 Unit Tests for Model Layer

```python
# tests/test_correction_rule.py
def test_correction_rule_creation():
    """Test the creation of correction rules."""
    # Test code...
    
def test_rule_equality():
    """Test rule equality comparison."""
    # Test code...
    
def test_to_from_dict():
    """Test conversion to/from dictionary."""
    # Test code...
    
# tests/test_correction_rule_manager.py
def test_loading_rules():
    """Test loading rules from CSV."""
    # Test code...
    
def test_saving_rules():
    """Test saving rules to CSV."""
    # Test code...
    
def test_rule_operations():
    """Test CRUD operations."""
    # Test code...
    
def test_rule_ordering():
    """Test rule prioritization and ordering."""
    # Test code...
```

### Phase 2: Services Layer (Days 3-4)

#### 2.1 CorrectionService

```python
# core/services/correction_service.py
class CorrectionService:
    """
    Service for applying correction rules to data.
    
    Implements the two-pass correction algorithm and integration
    with validation system.
    """
    
    def __init__(self, rule_manager, data_model, validation_service=None):
        """Initialize with required dependencies."""
        self._rule_manager = rule_manager
        self._data_model = data_model
        self._validation_service = validation_service
        self._correction_history = []
        
    def apply_corrections(self, only_invalid=False):
        """
        Apply all enabled correction rules to the data.
        
        Args:
            only_invalid: Whether to only correct invalid cells
            
        Returns:
            Dictionary with correction statistics
        """
        # Implementation details...
        
    def apply_single_rule(self, rule, only_invalid=False):
        """
        Apply a single correction rule to the data.
        
        Args:
            rule: The CorrectionRule to apply
            only_invalid: Whether to only correct invalid cells
            
        Returns:
            Dictionary with correction statistics for this rule
        """
        # Implementation details...
        
    def get_cells_with_available_corrections(self):
        """
        Get list of cells that have available corrections.
        
        Returns:
            List of (row, column) tuples for cells that can be corrected
        """
        # Implementation details...
        
    def get_correction_preview(self, rule):
        """
        Get preview of corrections that would be applied by a rule.
        
        Returns:
            List of (row, column, old_value, new_value) tuples
        """
        # Implementation details...
        
    def create_rule_from_cell(self, row, column, to_value):
        """
        Create a new correction rule from a cell selection.
        
        Args:
            row: The row index
            column: The column name
            to_value: The correct value
            
        Returns:
            New CorrectionRule instance
        """
        # Implementation details...
        
    def get_correction_history(self):
        """Get the history of applied corrections."""
        return self._correction_history
```

#### 2.2 Configuration Integration

```python
# core/config/config_manager.py (Extension)

# Add methods to ConfigManager
def init_correction_settings(self):
    """Initialize default correction settings."""
    if "correction" not in self._config:
        self._config["correction"] = {
            "auto_correct_after_validation": False,
            "correct_only_invalid": True,
            "auto_enable_imported_rules": True,
            "export_only_enabled": True
        }
        self.save_config()

def get_correction_setting(self, key, default=None):
    """Get a correction setting value."""
    if "correction" not in self._config:
        self.init_correction_settings()
    return self._config["correction"].get(key, default)

def set_correction_setting(self, key, value):
    """Set a correction setting value."""
    if "correction" not in self._config:
        self.init_correction_settings()
    self._config["correction"][key] = value
    self.save_config()
```

#### 2.3 Two-Pass Correction Algorithm

```python
def _apply_rules_two_pass(self, rules, only_invalid=False):
    """
    Apply correction rules in two passes:
    1. First pass: Apply general rules
    2. Second pass: Apply category-specific rules
    
    Args:
        rules: List of CorrectionRule objects
        only_invalid: Whether to only correct invalid cells
        
    Returns:
        Tuple of (updated_dataframe, corrections_applied)
    """
    # Get data copy
    data = self._data_model.data.copy()
    corrections_applied = {}
    
    # First pass: Apply general rules
    general_rules = [r for r in rules if r.category == 'general' and r.status == 'enabled']
    for rule in general_rules:
        # Apply to all three columns (player, chest_type, source)
        for column in ['player', 'chest_type', 'source']:
            # Only apply to invalid cells if specified
            if only_invalid:
                mask = (data[column] == rule.from_value) & (~data[f"{column}_valid"])
            else:
                mask = data[column] == rule.from_value
                
            # Track corrections before applying
            rows_affected = data.index[mask].tolist()
            if rows_affected:
                for row in rows_affected:
                    if row not in corrections_applied:
                        corrections_applied[row] = {}
                    corrections_applied[row][column] = (rule.from_value, rule.to_value)
            
            # Apply correction
            data.loc[mask, column] = rule.to_value
    
    # Second pass: Apply category-specific rules
    category_columns = {'player': 'player', 'chest_type': 'chest_type', 'source': 'source'}
    for category, column in category_columns.items():
        category_rules = [r for r in rules if r.category == category and r.status == 'enabled']
        for rule in category_rules:
            # Only apply to invalid cells if specified
            if only_invalid:
                mask = (data[column] == rule.from_value) & (~data[f"{column}_valid"])
            else:
                mask = data[column] == rule.from_value
                
            # Track corrections before applying
            rows_affected = data.index[mask].tolist()
            if rows_affected:
                for row in rows_affected:
                    if row not in corrections_applied:
                        corrections_applied[row] = {}
                    corrections_applied[row][column] = (rule.from_value, rule.to_value)
            
            # Apply correction
            data.loc[mask, column] = rule.to_value
    
    return data, corrections_applied
```

#### 2.4 Unit Tests for Services Layer

```python
# tests/test_correction_service.py
def test_two_pass_algorithm():
    """Test the two-pass correction algorithm."""
    # Test code...
    
def test_apply_corrections():
    """Test applying corrections to data."""
    # Test code...
    
def test_only_invalid_parameter():
    """Test correcting only invalid cells."""
    # Test code...
    
def test_validation_integration():
    """Test integration with validation service."""
    # Test code...
    
def test_correction_history():
    """Test correction history tracking."""
    # Test code...
```

### Phase 3: Controller Layer (Days 5-6)

#### 3.1 CorrectionController

```python
# core/controllers/correction_controller.py
class CorrectionController(BaseController):
    """
    Controller for coordinating correction operations.
    
    Mediates between views and services, handles user interactions
    and manages configuration.
    """
    
    # Signals
    correction_started = Signal(str)  # Operation description
    correction_progress = Signal(int, int)  # current, total
    correction_completed = Signal(dict)  # Statistics
    correction_error = Signal(str)  # Error message
    
    def __init__(self, correction_service, config_manager, signal_manager=None):
        """Initialize with required dependencies."""
        super().__init__(signal_manager)
        self._correction_service = correction_service
        self._config_manager = config_manager
        self._view = None
        self._worker = None
        self._worker_thread = None
        
    def set_view(self, view):
        """Set the correction view."""
        self._view = view
        
    def apply_corrections(self):
        """Apply corrections in the background thread."""
        # Implementation details...
        
    def add_rule(self, rule):
        """Add a new correction rule."""
        # Implementation details...
        
    def update_rule(self, index, rule):
        """Update an existing rule."""
        # Implementation details...
        
    def delete_rule(self, index):
        """Delete a rule."""
        # Implementation details...
        
    def reorder_rule(self, from_index, to_index):
        """Change rule order."""
        # Implementation details...
        
    def move_rule_to_top(self, index):
        """Move rule to top of category."""
        # Implementation details...
        
    def move_rule_to_bottom(self, index):
        """Move rule to bottom of category."""
        # Implementation details...
        
    def toggle_rule_status(self, index):
        """Toggle rule enabled/disabled status."""
        # Implementation details...
        
    def import_rules(self, file_path, append=True):
        """Import rules from file."""
        # Implementation details...
        
    def export_rules(self, file_path, only_enabled=False):
        """Export rules to file."""
        # Implementation details...
        
    def get_settings(self):
        """Get correction settings."""
        # Implementation details...
        
    def update_settings(self, settings):
        """Update correction settings."""
        # Implementation details...
        
    def create_rules_from_selected_cells(self, selections, to_values, categories=None):
        """Create rules from selected cells in batch."""
        # Implementation details...
        
    def _on_worker_progress(self, current, total):
        """Handle progress update from worker."""
        # Implementation details...
        
    def _on_worker_result(self, result):
        """Handle worker completion."""
        # Implementation details...
        
    def _on_worker_error(self, error):
        """Handle worker error."""
        # Implementation details...
```

#### 3.2 Background Worker Implementation

```python
# core/workers/correction_worker.py
class CorrectionWorker(QObject):
    """Worker for applying corrections in a background thread."""
    
    # Signals
    progress = Signal(int, int)  # current, total
    result = Signal(dict)  # correction results
    error = Signal(str)  # error message
    finished = Signal()  # work complete
    
    def __init__(self, correction_service, only_invalid=False):
        """Initialize with correction service."""
        super().__init__()
        self._correction_service = correction_service
        self._only_invalid = only_invalid
        self._cancelled = False
        
    def run(self):
        """Execute correction processing in background."""
        try:
            # Get rules and prepare for processing
            rules = self._correction_service.get_prioritized_rules()
            total_rules = len(rules)
            results = {"processed": 0, "corrected": 0, "rules_applied": 0}
            
            # Process rules
            for i, rule in enumerate(rules):
                if self._cancelled:
                    break
                    
                # Apply single rule
                rule_result = self._correction_service.apply_single_rule(
                    rule, only_invalid=self._only_invalid
                )
                
                # Update results
                results["processed"] += rule_result["processed"]
                results["corrected"] += rule_result["corrected"]
                if rule_result["corrected"] > 0:
                    results["rules_applied"] += 1
                
                # Report progress
                self.progress.emit(i + 1, total_rules)
                
            self.result.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
    
    def cancel(self):
        """Cancel the correction process."""
        self._cancelled = True
```

#### 3.3 Unit Tests for Controller Layer

```python
# tests/test_correction_controller.py
def test_rule_operations():
    """Test rule management operations."""
    # Test code...
    
def test_apply_corrections():
    """Test applying corrections through controller."""
    # Test code...
    
def test_background_processing():
    """Test background worker functionality."""
    # Test code...
    
def test_configuration_integration():
    """Test integration with configuration manager."""
    # Test code...
    
def test_import_export():
    """Test rule import/export operations."""
    # Test code...
```

### Phase 4: UI Implementation (Days 7-10)

#### 4.1 CorrectionView

```python
# ui/views/correction_view.py
class CorrectionView(BaseView):
    """
    View for correction rule management.
    
    Provides UI for managing correction rules and applying corrections.
    """
    
    # Signals
    rule_added = Signal(object)  # CorrectionRule
    rule_updated = Signal(int, object)  # index, CorrectionRule
    rule_deleted = Signal(int)  # index
    rule_moved = Signal(int, int)  # from_index, to_index
    rule_moved_to_top = Signal(int)  # index
    rule_moved_to_bottom = Signal(int)  # index
    rule_status_toggled = Signal(int)  # index
    import_requested = Signal(str, bool)  # file_path, append
    export_requested = Signal(str, bool)  # file_path, only_enabled
    apply_corrections_requested = Signal()  # No parameters
    settings_updated = Signal(dict)  # settings dict
    
    def __init__(self, controller, parent=None):
        """Initialize with controller."""
        super().__init__("Correction", parent)
        self._controller = controller
        self._controller.set_view(self)
        self._setup_ui()
        self._connect_signals()
        self._populate_view()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def _setup_rule_table(self):
        """Set up the rule table component."""
        # Implementation details...
        
    def _setup_controls(self):
        """Set up the control panel components."""
        # Implementation details...
        
    def _setup_status_bar(self):
        """Set up the status bar components."""
        # Implementation details...
        
    def _connect_signals(self):
        """Connect signals and slots."""
        # Implementation details...
        
    def _populate_view(self):
        """Populate the view with initial data."""
        # Implementation details...
        
    def _on_add_rule_clicked(self):
        """Handle add rule button click."""
        # Implementation details...
        
    def _on_edit_rule(self, index):
        """Handle rule editing."""
        # Implementation details...
        
    def _on_delete_rule(self, index):
        """Handle rule deletion."""
        # Implementation details...
        
    def _on_move_rule_up(self, index):
        """Handle moving rule up."""
        # Implementation details...
        
    def _on_move_rule_down(self, index):
        """Handle moving rule down."""
        # Implementation details...
        
    def _on_move_rule_to_top(self, index):
        """Handle moving rule to top."""
        # Implementation details...
        
    def _on_move_rule_to_bottom(self, index):
        """Handle moving rule to bottom."""
        # Implementation details...
        
    def _on_toggle_rule_status(self, index):
        """Handle toggling rule status."""
        # Implementation details...
        
    def _on_import_clicked(self):
        """Handle import button click."""
        # Implementation details...
        
    def _on_export_clicked(self):
        """Handle export button click."""
        # Implementation details...
        
    def _on_apply_corrections_clicked(self):
        """Handle apply corrections button click."""
        # Implementation details...
        
    def _on_setting_changed(self, key, value):
        """Handle setting change."""
        # Implementation details...
        
    def _on_correction_started(self, operation):
        """Handle correction started event."""
        # Implementation details...
        
    def _on_correction_progress(self, current, total):
        """Handle correction progress event."""
        # Implementation details...
        
    def _on_correction_completed(self, results):
        """Handle correction completed event."""
        # Implementation details...
        
    def _on_correction_error(self, error):
        """Handle correction error event."""
        # Implementation details...
        
    def update_rule_list(self, rules):
        """Update the rule table with current rules."""
        # Implementation details...
        
    def update_status_bar(self, message):
        """Update the status bar with a message."""
        # Implementation details...
        
    def update_statistics(self, total_rules, enabled_rules, disabled_rules):
        """Update the statistics display."""
        # Implementation details...
```

#### 4.2 CorrectionRuleTable

```python
# ui/components/correction_rule_table.py
class CorrectionRuleTable(QTableView):
    """
    Table view for displaying and managing correction rules.
    
    Provides sorting, filtering, and drag-drop reordering.
    """
    
    # Signals
    rule_selected = Signal(int)  # index
    rule_double_clicked = Signal(int)  # index
    rule_deleted = Signal(int)  # index
    rule_moved = Signal(int, int)  # from_index, to_index
    rule_moved_to_top = Signal(int)  # index
    rule_moved_to_bottom = Signal(int)  # index
    rule_status_toggled = Signal(int)  # index
    
    def __init__(self, parent=None):
        """Initialize the table view."""
        super().__init__(parent)
        self._setup_ui()
        self._setup_model()
        self._setup_context_menu()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def _setup_model(self):
        """Set up the table model."""
        # Implementation details...
        
    def _setup_context_menu(self):
        """Set up the context menu."""
        # Implementation details...
        
    def contextMenuEvent(self, event):
        """Handle context menu events."""
        # Implementation details...
        
    def mousePressEvent(self, event):
        """Handle mouse press events for drag-drop."""
        # Implementation details...
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag-drop."""
        # Implementation details...
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for drag-drop."""
        # Implementation details...
        
    def update_rules(self, rules):
        """Update the table with current rules."""
        # Implementation details...
        
    def get_selected_indices(self):
        """Get the indices of selected rows."""
        # Implementation details...
        
    def _on_header_clicked(self, logical_index):
        """Handle header click for sorting."""
        # Implementation details...
```

#### 4.3 BatchCorrectionDialog

```python
# ui/dialogs/batch_correction_dialog.py
class BatchCorrectionDialog(QDialog):
    """
    Dialog for creating multiple correction rules at once.
    
    Provides a grid interface for batch rule creation.
    """
    
    def __init__(self, selections, validation_service=None, parent=None):
        """Initialize with selected cells."""
        super().__init__(parent)
        self._selections = selections
        self._validation_service = validation_service
        self._rules = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def _populate_grid(self):
        """Populate the grid with selected cells."""
        # Implementation details...
        
    def _setup_category_dropdown(self, row, category):
        """Set up category dropdown for a grid row."""
        # Implementation details...
        
    def _setup_to_value_dropdown(self, row, category):
        """Set up to-value dropdown for a grid row."""
        # Implementation details...
        
    def _on_category_changed(self, row, category):
        """Handle category change for a row."""
        # Implementation details...
        
    def _on_add_to_validation_toggled(self, checked):
        """Handle add-to-validation toggle."""
        # Implementation details...
        
    def _on_enable_all_toggled(self, checked):
        """Handle enable-all toggle."""
        # Implementation details...
        
    def get_rules(self):
        """Get the created correction rules."""
        # Implementation details...
        
    def add_to_validation_checked(self):
        """Check if add-to-validation is enabled."""
        # Implementation details...
        
    def auto_enable_checked(self):
        """Check if auto-enable is enabled."""
        # Implementation details...
```

#### 4.4 ProgressDialog

```python
# ui/dialogs/correction_progress_dialog.py
class CorrectionProgressDialog(QDialog):
    """
    Dialog for showing correction progress.
    
    Provides progress bar, status text, and cancel button.
    """
    
    # Signals
    cancelled = Signal()  # No parameters
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.setWindowTitle("Applying Corrections")
        self.setMinimumWidth(400)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def update_progress(self, current, total):
        """Update the progress bar."""
        # Implementation details...
        
    def update_status(self, message):
        """Update the status message."""
        # Implementation details...
        
    def update_detail(self, message):
        """Update the detail message."""
        # Implementation details...
        
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        # Implementation details...
```

### Phase 5: Data View Integration (Days 11-12)

#### 5.1 Cell Highlighting

```python
# ui/views/data_view.py (Extension)

def update_cell_highlighting(self):
    """Update cell highlighting in DataView."""
    # Get cells that need highlighting
    invalid_cells = self._get_invalid_cells()
    corrected_cells = self._get_corrected_cells()
    correctable_cells = self._get_correctable_cells()
    
    # Apply highlights
    for row, col in invalid_cells:
        if (row, col) in correctable_cells:
            # Invalid with correction rule (orange)
            self._highlight_cell(row, col, "orange")
        else:
            # Invalid without correction rule (red)
            self._highlight_cell(row, col, "red")
            
    for row, col in corrected_cells:
        # Corrected cells (green)
        self._highlight_cell(row, col, "green")
        
    for row, col in correctable_cells:
        if (row, col) not in invalid_cells and (row, col) not in corrected_cells:
            # Correctable but not invalid or corrected (purple)
            self._highlight_cell(row, col, "purple")
```

#### 5.2 Context Menu Integration

```python
# ui/views/data_view.py (Extension)

def _setup_context_menu(self):
    """Set up the context menu."""
    # Add existing menu items
    # ...
    
    # Add correction-related items
    self._add_correction_rule_action = QAction("Add Correction Rule", self)
    self._add_correction_rule_action.triggered.connect(self._on_add_correction_rule)
    self._context_menu.addAction(self._add_correction_rule_action)
    
    self._add_batch_correction_action = QAction("Create Batch Correction Rules", self)
    self._add_batch_correction_action.triggered.connect(self._on_add_batch_correction)
    self._context_menu.addAction(self._add_batch_correction_action)
    
def _on_add_correction_rule(self):
    """Handle add correction rule action."""
    # Get selected cell
    selected_indices = self._table_view.selectedIndexes()
    if not selected_indices:
        return
        
    # Get row and column
    index = selected_indices[0]
    row = index.row()
    column = self._table_view.model().headerData(index.column(), Qt.Horizontal)
    value = self._table_view.model().data(index, Qt.DisplayRole)
    
    # Emit signal to notify controller
    self.add_correction_rule_requested.emit(row, column, value)
    
def _on_add_batch_correction(self):
    """Handle add batch correction action."""
    # Get selected cells
    selected_indices = self._table_view.selectedIndexes()
    if not selected_indices:
        return
        
    # Get row/column/value for each selected cell
    selections = []
    for index in selected_indices:
        row = index.row()
        column = self._table_view.model().headerData(index.column(), Qt.Horizontal)
        value = self._table_view.model().data(index, Qt.DisplayRole)
        selections.append((row, column, value))
        
    # Emit signal to notify controller
    self.add_batch_correction_rules_requested.emit(selections)
```

#### 5.3 Tooltips for Cell Status

```python
# ui/views/data_view.py (Extension)

def _setup_tooltips(self):
    """Set up tooltips for cells."""
    # In the model delegate:
    def paint(self, painter, option, index):
        # Regular painting
        # ...
        
        # Add tooltip based on cell status
        if (row, column) in self._corrected_cells:
            tooltip = f"Corrected from '{original}' to '{value}'"
            self.parent().setToolTip(tooltip)
        elif (row, column) in self._correctable_cells:
            rule = self._get_applicable_rule(row, column)
            tooltip = f"Can be corrected from '{value}' to '{rule.to_value}'"
            self.parent().setToolTip(tooltip)
        elif (row, column) in self._invalid_cells:
            if (row, column) in self._correctable_cells:
                tooltip = "Invalid with available correction rule"
            else:
                tooltip = "Invalid without correction rule"
            self.parent().setToolTip(tooltip)
```

### Phase 6: Testing and Optimization (Days 13-14)

#### 6.1 Integration Tests

```python
# tests/test_correction_integration.py
def test_full_correction_workflow():
    """Test the full correction workflow from end to end."""
    # Test code...
    
def test_controller_view_integration():
    """Test the integration between controller and view."""
    # Test code...
    
def test_validation_integration():
    """Test the integration with validation system."""
    # Test code...
    
def test_dataview_highlighting():
    """Test the data view highlighting functionality."""
    # Test code...
```

#### 6.2 Performance Optimization

```python
# Optimization techniques
1. Vectorized operations in pandas
2. Chunked processing for large datasets
3. Efficient rule filtering before application
4. Caching of validation results
5. Background processing for UI responsiveness
```

#### 6.3 Localization and Encoding Support

```python
# Ensuring proper encoding support
1. Use UTF-8 encoding for all file operations
2. Handle fallback to latin1 if needed
3. Test with international characters
4. Ensure proper display in UI components
```

## Timeline

- **Days 1-2**: Core Data Model Implementation
- **Days 3-4**: Services Layer Implementation
- **Days 5-6**: Controller Layer Implementation
- **Days 7-10**: UI Implementation
- **Days 11-12**: Data View Integration
- **Days 13-14**: Testing and Optimization

## Testing Strategy

1. **Unit Tests**: Test individual components (models, services, controllers)
2. **Integration Tests**: Test component interactions and workflows
3. **UI Tests**: Test UI components and user interactions
4. **Performance Tests**: Test with large datasets and rule sets

## Validation Criteria

- All correction rules are properly loaded, saved, and prioritized
- The two-pass algorithm correctly applies rules based on priority
- UI components allow effective rule management
- Cell highlighting correctly reflects correction status
- Performance is acceptable with large datasets
- International characters are properly supported

## Open Questions

1. Future implementation of smart matching using NLP
2. Additional optimizations for very large datasets
3. Enhanced rule suggestion based on validation patterns

## Resources

- Existing correction_rules.csv in data/corrections/
- Current CorrectionTab, CorrectionViewAdapter, and CorrectionService
- ChestDataModel and ValidationService integration points 