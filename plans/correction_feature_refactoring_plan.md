# Correction Feature Refactoring Plan

## Status Update - May 11, 2024

### Completed Features:
- ✅ Status bar in CorrectionRuleView showing rule counts in the format "Total rules: X | Enabled: Y | Disabled: Z"
- ✅ Color legend in DataView explaining the different highlight colors
- ✅ Consistent cell highlighting system matching the color legend
- ✅ Update mechanism for cell highlighting via update_cell_highlighting method

### In Progress:
- 🔄 Import/Export buttons in the header
- 🔄 Settings panel with configuration options
- 🔄 Context menu for rule actions

### Next Steps (Prioritized):

#### 1. Import/Export Buttons in Header
- Add Import/Export buttons to the CorrectionRuleView header
- Connect buttons to existing controller methods
- Implement file dialog integration
- Test integration with existing import/export functionality

```python
# ui/views/correction_rule_view.py - updates
def _setup_header_actions(self):
    """Set up actions in the header area."""
    header_layout = QHBoxLayout()
    
    # Title label
    title_label = QLabel("Correction Rules")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    header_layout.addWidget(title_label)
    
    header_layout.addStretch()
    
    # Import button
    self._import_button = QPushButton("Import Rules")
    self._import_button.setIcon(QIcon(":/icons/import.png"))
    self._import_button.clicked.connect(lambda: self._on_action_clicked("import"))
    header_layout.addWidget(self._import_button)
    
    # Export button
    self._export_button = QPushButton("Export Rules")
    self._export_button.setIcon(QIcon(":/icons/export.png"))
    self._export_button.clicked.connect(lambda: self._on_action_clicked("export"))
    header_layout.addWidget(self._export_button)
    
    return header_layout
```

#### 2. Settings Panel Enhancement
- Complete the settings panel with all configuration options from mockup
- Connect settings to ConfigManager for persistence
- Update UI to match mockup style
- Add tooltips for settings options

```python
# ui/views/correction_rule_view.py - updates
def _setup_settings_panel(self):
    """Set up the settings panel."""
    settings_group = QGroupBox("Correction Settings")
    settings_layout = QVBoxLayout(settings_group)
    
    # Recursive option
    self._recursive_checkbox = QCheckBox("Apply corrections recursively")
    self._recursive_checkbox.setToolTip(
        "Apply corrections repeatedly until no more changes are made"
    )
    self._recursive_checkbox.setChecked(True)
    settings_layout.addWidget(self._recursive_checkbox)
    
    # Only invalid cells option
    self._correct_invalid_only_checkbox = QCheckBox("Only correct invalid cells")
    self._correct_invalid_only_checkbox.setToolTip(
        "Only apply corrections to cells marked as invalid"
    )
    self._correct_invalid_only_checkbox.setChecked(True)
    settings_layout.addWidget(self._correct_invalid_only_checkbox)
    
    # Auto-enable new rules option
    self._auto_enable_checkbox = QCheckBox("Auto-enable new rules")
    self._auto_enable_checkbox.setToolTip(
        "Automatically enable new rules when they are created"
    )
    self._auto_enable_checkbox.setChecked(True)
    settings_layout.addWidget(self._auto_enable_checkbox)
    
    # Add to validation list option
    self._add_to_validation_checkbox = QCheckBox("Add corrected values to validation lists")
    self._add_to_validation_checkbox.setToolTip(
        "Automatically add corrected values to the appropriate validation lists"
    )
    self._add_to_validation_checkbox.setChecked(False)
    settings_layout.addWidget(self._add_to_validation_checkbox)
    
    # Apply corrections button
    self._apply_button = QPushButton("Apply Corrections")
    self._apply_button.setObjectName("primaryButton")
    settings_layout.addWidget(self._apply_button)
    
    # Load settings from config
    self._load_settings_from_config()
    
    # Connect setting changes to config
    self._recursive_checkbox.toggled.connect(self._on_setting_changed)
    self._correct_invalid_only_checkbox.toggled.connect(self._on_setting_changed)
    self._auto_enable_checkbox.toggled.connect(self._on_setting_changed)
    self._add_to_validation_checkbox.toggled.connect(self._on_setting_changed)
    
    return settings_group

def _load_settings_from_config(self):
    """Load settings from the configuration."""
    config = ConfigManager.instance()
    
    # Set checkbox states from config with defaults
    self._recursive_checkbox.setChecked(
        config.get_value("correction", "recursive", True)
    )
    self._correct_invalid_only_checkbox.setChecked(
        config.get_value("correction", "correct_invalid_only", True)
    )
    self._auto_enable_checkbox.setChecked(
        config.get_value("correction", "auto_enable_rules", True)
    )
    self._add_to_validation_checkbox.setChecked(
        config.get_value("correction", "add_to_validation", False)
    )

def _on_setting_changed(self):
    """Save settings when they change."""
    config = ConfigManager.instance()
    
    # Save settings to config
    config.set_value(
        "correction", "recursive", self._recursive_checkbox.isChecked()
    )
    config.set_value(
        "correction", "correct_invalid_only", self._correct_invalid_only_checkbox.isChecked()
    )
    config.set_value(
        "correction", "auto_enable_rules", self._auto_enable_checkbox.isChecked()
    )
    config.set_value(
        "correction", "add_to_validation", self._add_to_validation_checkbox.isChecked()
    )
```

#### 3. Context Menu for Rules
- Implement context menu for the rule table
- Connect menu actions to existing rule management methods
- Test context menu functionality

```python
# ui/views/correction_rule_view.py - updates
def _setup_table(self):
    """Set up the rule table."""
    # Existing table setup code...
    
    # Add context menu support
    self._rule_table.setContextMenuPolicy(Qt.CustomContextMenu)
    self._rule_table.customContextMenuRequested.connect(self._show_context_menu)
    
def _show_context_menu(self, position):
    """Show context menu for rule table."""
    # Get selected item
    if not self._rule_table.selectedItems():
        return
        
    # Create menu
    menu = QMenu()
    
    # Add actions
    edit_action = menu.addAction("Edit")
    delete_action = menu.addAction("Delete")
    menu.addSeparator()
    
    move_menu = menu.addMenu("Move")
    move_up_action = move_menu.addAction("Move Up")
    move_down_action = move_menu.addAction("Move Down")
    move_top_action = move_menu.addAction("Move to Top")
    move_bottom_action = move_menu.addAction("Move to Bottom")
    
    menu.addSeparator()
    toggle_action = menu.addAction("Enable/Disable")
    apply_single_action = menu.addAction("Apply This Rule Only")
    
    # Show menu and handle action
    action = menu.exec_(self._rule_table.viewport().mapToGlobal(position))
    
    # Connect actions to handlers
    if action == edit_action:
        self._on_edit_rule()
    elif action == delete_action:
        self._on_delete_rule()
    elif action == move_up_action:
        self._on_move_rule_up()
    elif action == move_down_action:
        self._on_move_rule_down()
    elif action == move_top_action:
        self._on_move_rule_to_top()
    elif action == move_bottom_action:
        self._on_move_rule_to_bottom()
    elif action == toggle_action:
        self._on_toggle_status()
    elif action == apply_single_action:
        self._on_apply_single_rule()

def _on_apply_single_rule(self):
    """Apply only the selected rule."""
    rule_id = self._get_selected_rule_id()
    if rule_id is None:
        return
    
    only_invalid = self._correct_invalid_only_checkbox.isChecked()
    success = self._controller.apply_single_rule(rule_id, only_invalid)
    
    if success:
        QMessageBox.information(
            self, "Rule Applied", "The selected rule was applied successfully."
        )
    else:
        QMessageBox.warning(
            self, "Rule Application Failed", "Failed to apply the selected rule."
        )
```

## Implementation Plan Overview

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

### Phase 1: Core Data Model (Completed ✅)

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

### Phase 2: Services Layer (Completed ✅)

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

### Phase 3: Controller Layer (Completed ✅)

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

### Phase 4: UI Components (In Progress 🔄)

#### 4.1 CorrectionView

```python
# ui/views/correction_view.py
class CorrectionView(BaseView):
    """
    Main view for the correction feature.
    
    Provides interfaces for:
    - Managing correction rules
    - Applying corrections
    - Visualizing correction results
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._correction_controller = None
        self._rule_view = None
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def set_correction_controller(self, controller):
        """Set the correction controller."""
        # Implementation details...
        
    def _initialize_rule_view(self):
        """Initialize the rule view component."""
        # Implementation details...
        
    def _refresh_view_content(self):
        """Refresh the view content."""
        # Implementation details...
        
    def _on_action_clicked(self, action_id):
        """Handle action button clicks."""
        # Implementation details...
        
    def _on_corrections_completed(self, stats):
        """Handle correction completion."""
        # Implementation details...
        
    def _on_correction_error(self, error_message):
        """Handle correction errors."""
        # Implementation details...
```

#### 4.2 CorrectionRuleView

```python
# ui/views/correction_rule_view.py
class CorrectionRuleView(QWidget):
    """
    Widget for displaying and managing correction rules.
    
    Features:
    - Rule table with sorting
    - Filter controls
    - Rule management buttons
    - Status bar with rule counts
    """
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._rules = []
        
        self._setup_ui()
        self._connect_signals()
        self._update_categories_filter()
        self._refresh_rule_table()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def _connect_signals(self):
        """Connect signals and slots."""
        # Implementation details...
        
    def _refresh_rule_table(self):
        """Refresh the rule table with current rules."""
        # Implementation details...
        
    def _update_categories_filter(self):
        """Update the category filter with available categories."""
        # Implementation details...
        
    def _update_status_bar(self):
        """Update the status bar with rule counts."""
        # Get rules from controller 
        rules = self._controller.get_rules()
        total_rules = len(rules)
        enabled_rules = sum(1 for rule in rules if rule.status == "enabled")
        disabled_rules = total_rules - enabled_rules

        self._status_bar.showMessage(
            f"Total rules: {total_rules} | Enabled: {enabled_rules} | Disabled: {disabled_rules}"
        )
    def _update_button_states(self):
        """Update button states based on selection."""
        # Implementation details...
        
    def _get_selected_rule_id(self):
        """Get the ID of the selected rule."""
        # Implementation details...
        
    def _on_filter_changed(self):
        """Handle filter changes."""
        # Implementation details...
        
    def _on_reset_filters(self):
        """Reset all filters to default values."""
        # Implementation details...
        
    def _on_add_rule(self):
        """Add a new correction rule."""
        # Implementation details...
        
    def _on_edit_rule(self):
        """Edit the selected correction rule."""
        # Implementation details...
        
    def _on_delete_rule(self):
        """Delete the selected correction rule."""
        # Implementation details...
        
    def _on_move_rule_up(self):
        """Move the selected rule up."""
        # Implementation details...
        
    def _on_move_rule_down(self):
        """Move the selected rule down."""
        # Implementation details...
```

#### 4.3 Completing CorrectionView UI

To ensure the CorrectionView UI matches the mockup design in `correction_feature_ui_mockup.html`, we need to implement several missing features:

##### Status Bar Implementation
```python
# ui/views/correction_view.py - updates
def _setup_ui(self):
    """Set up the UI components."""
    super()._setup_ui()
    
    # Add dedicated status bar
    self._status_bar = QStatusBar()
    self._status_bar.setFixedHeight(24)  # Make it smaller to match mockup
    self.layout().addWidget(self._status_bar)
    
    # Rest of setup...

def _update_status_bar(self):
    """Update status bar with rule information."""
    if self._rule_view:
        total_rules = len(self._correction_controller.get_rules())
        enabled_rules = len(self._correction_controller.get_rules(status="enabled"))
        disabled_rules = total_rules - enabled_rules
        
        self._status_bar.showMessage(
            f"Total rules: {total_rules} | Enabled: {enabled_rules} | Disabled: {disabled_rules}"
        )
```

##### Header Action Buttons
```python
# ui/views/correction_view.py - updates
def _add_action_buttons(self):
    """Add action buttons to the header."""
    # Import/Export buttons
    self.add_header_action("import", "Import")
    self.add_header_action("export", "Export")
    self.add_header_action("apply", "Apply Corrections")

def _on_action_clicked(self, action_id):
    """Handle action button clicks."""
    if action_id == "apply":
        self._apply_corrections()
    elif action_id == "import":
        self._import_rules()
    elif action_id == "export":
        self._export_rules()
        
def _import_rules(self):
    """Import correction rules from file."""
    if not self._correction_controller:
        return
        
    file_path, _ = QFileDialog.getOpenFileName(
        self, "Import Correction Rules", "", "CSV Files (*.csv);;All Files (*)"
    )
    
    if file_path:
        dialog = ImportExportDialog(
            file_path=file_path, 
            is_import=True, 
            parent=self
        )
        
        if dialog.exec():
            options = dialog.get_options()
            success = self._correction_controller.import_rules(
                file_path=options["file_path"],
                replace_existing=options["replace_existing"]
            )
            
            if success:
                self._show_status_message("Rules imported successfully")
            else:
                self._show_status_message("Error importing rules")
                
def _export_rules(self):
    """Export correction rules to file."""
    if not self._correction_controller:
        return
        
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export Correction Rules", "", "CSV Files (*.csv);;All Files (*)"
    )
    
    if file_path:
        dialog = ImportExportDialog(
            file_path=file_path, 
            is_import=False, 
            parent=self
        )
        
        if dialog.exec():
            options = dialog.get_options()
            success = self._correction_controller.export_rules(
                file_path=options["file_path"],
                only_enabled=options["only_enabled"]
            )
            
            if success:
                self._show_status_message("Rules exported successfully")
            else:
                self._show_status_message("Error exporting rules")
```

##### Settings Panel
```python
# ui/views/correction_rule_view.py - updates
def _setup_settings_panel(self):
    """Set up the settings panel."""
    settings_group = QGroupBox("Correction Settings")
    settings_layout = QVBoxLayout(settings_group)
    
    # Recursive option
    self._recursive_checkbox = QCheckBox("Apply corrections recursively")
    self._recursive_checkbox.setToolTip(
        "Apply corrections repeatedly until no more changes are made"
    )
    self._recursive_checkbox.setChecked(True)
    settings_layout.addWidget(self._recursive_checkbox)
    
    # Only invalid cells option
    self._correct_invalid_only_checkbox = QCheckBox("Only correct invalid cells")
    self._correct_invalid_only_checkbox.setToolTip(
        "Only apply corrections to cells marked as invalid"
    )
    self._correct_invalid_only_checkbox.setChecked(True)
    settings_layout.addWidget(self._correct_invalid_only_checkbox)
    
    # Auto-enable new rules option
    self._auto_enable_checkbox = QCheckBox("Auto-enable new rules")
    self._auto_enable_checkbox.setToolTip(
        "Automatically enable new rules when they are created"
    )
    self._auto_enable_checkbox.setChecked(True)
    settings_layout.addWidget(self._auto_enable_checkbox)
    
    # Add to validation list option
    self._add_to_validation_checkbox = QCheckBox("Add corrected values to validation lists")
    self._add_to_validation_checkbox.setToolTip(
        "Automatically add corrected values to the appropriate validation lists"
    )
    self._add_to_validation_checkbox.setChecked(False)
    settings_layout.addWidget(self._add_to_validation_checkbox)
    
    # Apply corrections button
    self._apply_button = QPushButton("Apply Corrections")
    self._apply_button.setObjectName("primaryButton")
    settings_layout.addWidget(self._apply_button)
    
    # Load settings from config
    self._load_settings_from_config()
    
    # Connect setting changes to config
    self._recursive_checkbox.toggled.connect(self._on_setting_changed)
    self._correct_invalid_only_checkbox.toggled.connect(self._on_setting_changed)
    self._auto_enable_checkbox.toggled.connect(self._on_setting_changed)
    self._add_to_validation_checkbox.toggled.connect(self._on_setting_changed)
    
    return settings_group

def _load_settings_from_config(self):
    """Load settings from the configuration."""
    config = ConfigManager.instance()
    
    # Set checkbox states from config with defaults
    self._recursive_checkbox.setChecked(
        config.get_value("correction", "recursive", True)
    )
    self._correct_invalid_only_checkbox.setChecked(
        config.get_value("correction", "correct_invalid_only", True)
    )
    self._auto_enable_checkbox.setChecked(
        config.get_value("correction", "auto_enable_rules", True)
    )
    self._add_to_validation_checkbox.setChecked(
        config.get_value("correction", "add_to_validation", False)
    )

def _on_setting_changed(self):
    """Save settings when they change."""
    config = ConfigManager.instance()
    
    # Save settings to config
    config.set_value(
        "correction", "recursive", self._recursive_checkbox.isChecked()
    )
    config.set_value(
        "correction", "correct_invalid_only", self._correct_invalid_only_checkbox.isChecked()
    )
    config.set_value(
        "correction", "auto_enable_rules", self._auto_enable_checkbox.isChecked()
    )
    config.set_value(
        "correction", "add_to_validation", self._add_to_validation_checkbox.isChecked()
    )
```

##### Complete Rule Control Buttons
```python
# ui/views/correction_rule_view.py - updates
def _setup_rule_controls(self):
    """Set up rule control buttons."""
    controls_layout = QHBoxLayout()
    
    self._add_button = QPushButton("Add")
    self._edit_button = QPushButton("Edit")
    self._delete_button = QPushButton("Delete")
    self._move_up_button = QPushButton("Move ▲")
    self._move_down_button = QPushButton("Move ▼")
    self._move_top_button = QPushButton("Move to Top")
    self._move_bottom_button = QPushButton("Move to Bottom")
    self._toggle_status_button = QPushButton("Toggle Status")
    
    controls_layout.addWidget(self._add_button)
    controls_layout.addWidget(self._edit_button)
    controls_layout.addWidget(self._delete_button)
    controls_layout.addWidget(self._move_up_button)
    controls_layout.addWidget(self._move_down_button)
    controls_layout.addWidget(self._move_top_button)
    controls_layout.addWidget(self._move_bottom_button)
    controls_layout.addWidget(self._toggle_status_button)
    
    return controls_layout

def _connect_rule_control_signals(self):
    """Connect signals for rule control buttons."""
    self._add_button.clicked.connect(self._on_add_rule)
    self._edit_button.clicked.connect(self._on_edit_rule)
    self._delete_button.clicked.connect(self._on_delete_rule)
    self._move_up_button.clicked.connect(self._on_move_rule_up)
    self._move_down_button.clicked.connect(self._on_move_rule_down)
    self._move_top_button.clicked.connect(self._on_move_rule_to_top)
    self._move_bottom_button.clicked.connect(self._on_move_rule_to_bottom)
    self._toggle_status_button.clicked.connect(self._on_toggle_status)
```

##### Context Menu for Rules
```python
# ui/views/correction_rule_view.py - updates
def _setup_table(self):
    """Set up the rule table."""
    # Existing table setup code...
    
    # Add context menu support
    self._rule_table.setContextMenuPolicy(Qt.CustomContextMenu)
    self._rule_table.customContextMenuRequested.connect(self._show_context_menu)
    
def _show_context_menu(self, position):
    """Show context menu for rule table."""
    if not self._rule_table.selectedItems():
        return
        
    menu = QMenu()
    
    edit_action = menu.addAction("Edit")
    delete_action = menu.addAction("Delete")
    menu.addSeparator()
    move_up_action = menu.addAction("Move Up")
    move_down_action = menu.addAction("Move Down")
    move_top_action = menu.addAction("Move to Top")
    move_bottom_action = menu.addAction("Move to Bottom")
    menu.addSeparator()
    toggle_action = menu.addAction("Enable/Disable")
    
    action = menu.exec_(self._rule_table.viewport().mapToGlobal(position))
    
    if action == edit_action:
        self._on_edit_rule()
    elif action == delete_action:
        self._on_delete_rule()
    elif action == move_up_action:
        self._on_move_rule_up()
    elif action == move_down_action:
        self._on_move_rule_down()
    elif action == move_top_action:
        self._on_move_rule_to_top()
    elif action == move_bottom_action:
        self._on_move_rule_to_bottom()
    elif action == toggle_action:
        self._on_toggle_status()
```

#### 4.4 AddEditRuleDialog

```python
# ui/dialogs/add_edit_rule_dialog.py
class AddEditRuleDialog(QDialog):
    """
    Dialog for adding or editing correction rules.
    
    Features:
    - Input fields for rule properties
    - Validation of inputs
    - Category selection
    - Status toggle
    """
    
    def __init__(self, validation_service=None, parent=None, rule=None):
        super().__init__(parent)
        self._validation_service = validation_service
        self._rule = rule
        
        self._setup_ui()
        self._connect_signals()
        
        if rule:
            self._populate_fields(rule)
            self.setWindowTitle("Edit Correction Rule")
        else:
            self.setWindowTitle("Add Correction Rule")
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Implementation details...
        
    def _connect_signals(self):
        """Connect signals and slots."""
        # Implementation details...
        
    def _populate_fields(self, rule):
        """Populate dialog fields with rule data."""
        # Implementation details...
        
    def get_rule(self):
        """Get the correction rule from dialog data."""
        # Implementation details...
        
    def _validate_inputs(self):
        """Validate user inputs."""
        # Implementation details...
```

### Phase 5: Data View Integration (In Progress 🔄)

#### 5.1 Cell Highlighting (Completed ✅)

We've updated the cell highlighting to use consistent colors that match the color legend:

```python
# ui/data_view.py

def _highlight_correction_cells(self):
    """Highlight cells based on correction status."""
    # Define colors
    invalid_color = QColor(255, 182, 182)  # Light red
    correctable_color = QColor(255, 214, 165)  # Light orange
    corrected_color = QColor(182, 255, 182)  # Light green
    purple_color = QColor(214, 182, 255)  # Light purple
    
    # Get cells that need highlighting
    invalid_cells = self._get_invalid_cells()
    corrected_cells = self._get_corrected_cells()
    correctable_cells = self._get_correctable_cells()
    
    # Apply highlights
    for row, col in invalid_cells:
        if (row, col) in correctable_cells:
            # Invalid with correction rule (orange)
            self._highlight_cell(row, col, correctable_color)
        else:
            # Invalid without correction rule (red)
            self._highlight_cell(row, col, invalid_color)
            
    for row, col in corrected_cells:
        # Corrected cells (green)
        self._highlight_cell(row, col, corrected_color)
        
    for row, col in correctable_cells:
        if (row, col) not in invalid_cells and (row, col) not in corrected_cells:
            # Correctable but not invalid or corrected (purple)
            self._highlight_cell(row, col, purple_color)
```

We've also added the update_cell_highlighting method to delegate to _highlight_correction_cells:

```python
def update_cell_highlighting(self):
    """
    Update cell highlighting based on validation and correction status.
    
    This method delegates to _highlight_correction_cells to apply the appropriate
    highlighting to cells based on their validation and correction status.
    """
    self._highlight_correction_cells()
```

#### 5.2 Color Legend (Completed ✅)

We've added a color legend to the DataView to explain the highlighting colors:

```python
# ui/data_view.py

def _create_color_legend(self) -> QGroupBox:
    """
    Create a color legend explaining the cell highlighting colors.
    
    Returns:
        QGroupBox: The color legend widget
    """
    legend = QGroupBox("Color Legend")
    legend_layout = QVBoxLayout(legend)
    
    # Create the legend items
    for color, text in [
        ("#FFB6B6", "Invalid"),  # Light red
        ("#FFD6A5", "Invalid (correctable)"),  # Light orange
        ("#B6FFB6", "Corrected"),  # Light green
        ("#D6B6FF", "Correctable")  # Light purple
    ]:
        item_layout = QHBoxLayout()
        
        # Create color box
        color_box = QLabel()
        color_box.setFixedSize(16, 16)
        color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        item_layout.addWidget(color_box)
        
        # Create text label
        text_label = QLabel(text)
        item_layout.addWidget(text_label)
        item_layout.addStretch()
        
        legend_layout.addLayout(item_layout)
    
    legend_layout.addStretch()
    return legend
```

Tests have been added to verify the color legend:

```python
# tests/unit/ui/views/test_data_view_highlighting.py

def test_color_legend(data_view):
    """Test that the data view has a color legend explaining the highlighting colors."""
    # Check if the color legend exists
    assert hasattr(data_view, "_color_legend"), "DataView should have a _color_legend attribute"

    # Check the color legend is a QGroupBox
    assert isinstance(data_view._color_legend, QGroupBox), "Color legend should be a QGroupBox"

    # Check the color legend has the right title
    assert data_view._color_legend.title() == "Color Legend", (
        "Color legend should have title 'Color Legend'"
    )

    # Get all labels in the color legend
    labels = data_view._color_legend.findChildren(QLabel)

    # Check that there are enough labels (at least 8 - 4 color blocks and 4 text labels)
    assert len(labels) >= 8, "Color legend should have at least 8 QLabel widgets"

    # Check for text labels with the right descriptions
    label_texts = [label.text() for label in labels if label.text()]
    assert any("Invalid" in text for text in label_texts), "Should have a label for 'Invalid' cells"
    assert any("Invalid (correctable)" in text for text in label_texts), (
        "Should have a label for 'Invalid (correctable)' cells"
    )
    assert any("Corrected" in text for text in label_texts), (
        "Should have a label for 'Corrected' cells"
    )
    assert any("Correctable" in text for text in label_texts), (
        "Should have a label for 'Correctable' cells"
    )

    # Check for color blocks with different colors
    color_blocks = [label for label in labels if not label.text() and label.styleSheet()]
    assert len(color_blocks) >= 4, "Should have at least 4 color block QLabels"
```

#### 5.3 Context Menu Integration

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

#### 5.4 Tooltips for Cell Status

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

### Phase 6: Testing and Optimization (Next)

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
- **Days 7-9**: UI Components Implementation
- **Days 10-11**: Data View Integration
- **Days 12-13**: Testing and Optimization

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