# Correction System Technical Implementation

## Architecture Overview

This document outlines the technical implementation details for the improved correction system in ChestBuddy. The implementation covers the core components, data flow, and integration points.

## Core Components

### 1. Validation Status Extension

First, we need to extend the `ValidationStatus` enum to include a correctable state:

```python
class ValidationStatus(Enum):
    VALID = 0
    INVALID = 1
    CORRECTABLE = 2  # New status for invalid entries that can be fixed
    CORRECTED = 3    # New status for entries that were corrected
```

### 2. Correction Service Enhancement

The `CorrectionService` class needs significant updates:

```python
class CorrectionService:
    """
    Service for applying corrections to data based on correction rules.
    
    Attributes:
        _correction_rules (List[CorrectionRule]): List of correction rules
        _data_model (DataModel): The data model to apply corrections to
    """
    
    def apply_corrections(self, 
                          only_invalid: bool = False, 
                          recursive: bool = False,
                          selection: Optional[List[QModelIndex]] = None) -> int:
        """
        Apply corrections to data.
        
        Args:
            only_invalid: Apply corrections only to invalid entries
            recursive: Whether to recursively apply corrections until no more matches
            selection: Optional list of selected indices to apply corrections to
            
        Returns:
            int: Number of corrections applied
        """
        # Implementation details...
```

### 3. Correction Controller Updates

The `CorrectionController` needs to handle recursive corrections and selection-based correction:

```python
class CorrectionController(QObject):
    """
    Controller for managing the correction system.
    
    Attributes:
        _correction_service (CorrectionService): The service for applying corrections
        _data_controller (DataController): Controller for data operations
        _validation_controller (ValidationController): Controller for validation operations
    """
    
    def apply_corrections(self, 
                         only_invalid: bool = True, 
                         recursive: bool = False,
                         selection: Optional[List[QModelIndex]] = None) -> None:
        """
        Apply corrections to data.
        
        Args:
            only_invalid: Apply corrections only to invalid entries
            recursive: Whether to recursively apply corrections until no more matches
            selection: Optional list of selected indices to apply corrections to
        """
        # Implementation details...
        
    def _apply_corrections_task(self,
                               only_invalid: bool = True,
                               recursive: bool = False,
                               selection: Optional[List[QModelIndex]] = None) -> None:
        """
        Background task for applying corrections.
        
        Args:
            only_invalid: Apply corrections only to invalid entries
            recursive: Whether to recursively apply corrections until no more matches
            selection: Optional list of selected indices to apply corrections to
        """
        # Implementation details...
```

### 4. Configuration Manager Extension

The `ConfigManager` needs to be extended to handle new correction settings:

```python
class ConfigManager:
    """
    Manager for application configuration.
    """
    
    def initialize_defaults(self) -> None:
        """Initialize default configuration values."""
        # Existing settings...
        
        # New correction settings
        self.set_value("correction/auto_correct_on_validation", True)
        self.set_value("correction/auto_correct_on_import", True)
        self.set_value("correction/apply_recursively", False)
        self.set_value("correction/auto_save_after_corrections", False)
```

### 5. Data View Integration

The `DataView` class needs to show correctable status and integrate with the selection-based correction:

```python
class DataView(QTableView):
    """
    View for displaying data with validation and correction status.
    """
    
    def _setup_context_menu(self) -> None:
        """Setup the context menu for the data view."""
        menu = QMenu(self)
        
        # Add correction actions
        apply_corrections_action = menu.addAction("Apply corrections")
        apply_corrections_action.triggered.connect(self._apply_corrections_to_selection)
        
        # Other menu items...
        
    def _apply_corrections_to_selection(self) -> None:
        """Apply corrections to the selected cells."""
        selection = self.selectedIndexes()
        if selection:
            self._correction_controller.apply_corrections(
                only_invalid=True,
                recursive=self._config_manager.get_value("correction/apply_recursively", False),
                selection=selection
            )
```

## Data Flow

The following sequence diagrams illustrate the key data flows in the correction system:

### Recursive Correction Flow

```
┌─────────┐         ┌────────────────────┐         ┌──────────────────┐         ┌──────────────┐
│ DataView │         │ CorrectionController │         │ CorrectionService │         │ DataController │
└────┬────┘         └──────────┬─────────┘         └────────┬─────────┘         └───────┬──────┘
     │                         │                             │                          │
     │ apply_corrections(recursive=True)                     │                          │
     │────────────────────────>│                             │                          │
     │                         │                             │                          │
     │                         │ _apply_corrections_task(recursive=True)                │
     │                         │─────────────────────────────>                          │
     │                         │                             │                          │
     │                         │                             │ apply_corrections(recursive=True)
     │                         │                             │─────────────────────────>│
     │                         │                             │                          │
     │                         │                             │                    ┌─────┴────┐
     │                         │                             │                    │ Apply 1st │
     │                         │                             │                    │  round    │
     │                         │                             │                    └─────┬────┘
     │                         │                             │                          │
     │                         │                             │ corrected = true         │
     │                         │                             │<─────────────────────────┘
     │                         │                             │                          │
     │                         │                             │                    ┌─────┴────┐
     │                         │                             │                    │ Apply 2nd │
     │                         │                             │ While corrected    │  round    │
     │                         │                             │─────────────────────────────────>
     │                         │                             │                    └─────┬────┘
     │                         │                             │                          │
     │                         │                             │ corrected = false        │
     │                         │                             │<─────────────────────────┘
     │                         │                             │                          │
     │                         │ corrections_applied         │                          │
     │<─────────────────────────────────────────────────────┘                          │
     │                         │                             │                          │
     │ refresh_view()          │                             │                          │
     │─────────────────────────┼─────────────────────────────┼─────────────────────────>
     │                         │                             │                          │
```

### Selection-Based Correction Flow

```
┌─────────┐         ┌────────────────────┐         ┌──────────────────┐
│ DataView │         │ CorrectionController │         │ CorrectionService │
└────┬────┘         └──────────┬─────────┘         └────────┬─────────┘
     │                         │                             │
     │ _apply_corrections_to_selection()                     │
     │────────────────────────>│                             │
     │                         │                             │
     │                         │ apply_corrections(selection=selection)
     │                         │─────────────────────────────>
     │                         │                             │
     │                         │                             │
     │                         │                           ┌─┴─────────────┐
     │                         │                           │ Filter to only │
     │                         │                           │ process indices│
     │                         │                           │ in selection   │
     │                         │                           └─┬─────────────┘
     │                         │                             │
     │                         │                           ┌─┴─────────────┐
     │                         │                           │ Apply rules to │
     │                         │                           │ filtered items │
     │                         │                           └─┬─────────────┘
     │                         │                             │
     │                         │ corrections_applied         │
     │<─────────────────────────────────────────────────────┘
     │                         │                             │
     │ refresh_view()          │                             │
     │─────────────────────────┼─────────────────────────────>
     │                         │                             │
```

## Database Schema Updates

The validation status in the database needs to be extended:

```sql
-- Update to validation_status column in data table
ALTER TABLE data 
ADD COLUMN validation_status INT DEFAULT 0; -- 0: VALID, 1: INVALID, 2: CORRECTABLE, 3: CORRECTED
```

## Configuration Changes

The `config.ini` file will include new settings:

```ini
[correction]
auto_correct_on_validation=true
auto_correct_on_import=true
apply_recursively=false
auto_save_after_corrections=false

[display]
show_validation_indicators=true
show_correction_indicators=true
highlight_corrected_cells=false
```

## Test Driven Development Approach

### Testing the ValidationStatus Extension

```python
# tests/unit/core/model/test_validation_status.py

def test_validation_status_enum():
    # Test that the ValidationStatus enum has been extended with new statuses
    assert ValidationStatus.VALID.value == 0
    assert ValidationStatus.INVALID.value == 1
    assert ValidationStatus.CORRECTABLE.value == 2
    assert ValidationStatus.CORRECTED.value == 3
```

### Testing the CorrectionService

```python
# tests/unit/core/services/test_correction_service.py

def test_apply_corrections_recursive():
    # Setup test data with a chain of correctable values
    data_model = create_mock_data_model()
    correction_service = CorrectionService(data_model)
    
    # Add rules that form a chain: A -> B -> C
    correction_service.add_rule(CorrectionRule("A", "B", "test"))
    correction_service.add_rule(CorrectionRule("B", "C", "test"))
    
    # Apply corrections with recursive=True
    corrections = correction_service.apply_corrections(recursive=True)
    
    # Verify both corrections were applied
    assert corrections == 2
    assert data_model.get_value_at(0, 0) == "C"
```

### Testing the CorrectionController

```python
# tests/unit/core/controllers/test_correction_controller.py

def test_apply_corrections_to_selection():
    # Setup test controllers and services
    correction_controller = create_mock_correction_controller()
    
    # Create a selection of model indices
    selection = [QModelIndex(0, 0), QModelIndex(1, 1)]
    
    # Apply corrections to selection
    correction_controller.apply_corrections(selection=selection)
    
    # Verify corrections were only applied to selected cells
    # This will depend on the mock implementation
```

## Performance Considerations

- The recursive correction feature could potentially lead to infinite loops if rules form a cycle. Implementation should include:
  - Cycle detection
  - Maximum iteration limit
  - Logging of recursive correction chains

- For large datasets, selective correction on a subset of data should be optimized to avoid processing the entire dataset.

## Error Handling

- Rules that would create correction cycles should be detected and warned about.
- UI should indicate when a correction could not be applied.
- Error reporting should be enhanced to provide details on why corrections failed.

## Security Considerations

- Input validation for correction rules to prevent injection attacks
- Audit logging of correction operations
- User permission checks for correction operations

## Feature Rollout Plan

The implementation will be phased:

1. Phase 1: Core validation status extension and recursive correction
2. Phase 2: Selection-based correction and UI updates
3. Phase 3: Advanced features (auto-correct options, rule management)
4. Phase 4: UI/UX improvements and performance optimization

## Conclusion

This implementation plan provides a comprehensive approach to enhancing the correction system. By following this plan and the associated TDD approach, we can ensure that the correction system is robust, maintainable, and meets user requirements. 