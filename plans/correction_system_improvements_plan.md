# Correction System Improvements Plan

## Overview

This document outlines the comprehensive plan for improving the ChestBuddy correction system, addressing current functionality gaps and implementing new features. We've identified several key issues with the current implementation that need to be addressed:

1. **Recursive Correction**: The controller is passing `recursive=True` but the service doesn't implement recursion
2. **Selection-Based Correction**: The `selected_only` parameter isn't properly implemented
3. **Correctable Status Detection**: The "correctable" status needs proper integration with validation
4. **Auto-Correction Options**: Auto-correction on validation and import aren't implemented

## Implementation Approach

We will follow a test-driven development (TDD) approach for all improvements:

1. Write tests first
2. Implement the feature
3. Verify test passing
4. Refactor if needed

## Detailed Implementation Plan

### Phase 1: Recursive Correction Implementation

#### 1.1: Test for Recursive Correction (Day 1)

```python
def test_recursive_correction(self, mocker):
    """Test that corrections are applied recursively until no more changes occur."""
    # Mock dependencies
    mock_service = mocker.Mock()
    mock_rule_manager = mocker.Mock()
    mock_config_manager = mocker.Mock()
    mock_validation_service = mocker.Mock()
    
    # Configure mock service to return different results for each call
    # First call: 5 corrections, second call: 3 corrections, third call: 0 corrections
    mock_service.apply_corrections.side_effect = [
        {"total_corrections": 5, "corrected_rows": 3, "corrected_cells": 5},
        {"total_corrections": 3, "corrected_rows": 2, "corrected_cells": 3},
        {"total_corrections": 0, "corrected_rows": 0, "corrected_cells": 0}
    ]
    
    # Create controller with mocks
    controller = CorrectionController(
        mock_service, mock_rule_manager, mock_config_manager, mock_validation_service
    )
    
    # Mock data hash method to simulate data changes
    controller._get_data_hash = mocker.Mock()
    controller._get_data_hash.side_effect = ["hash1", "hash2", "hash3", "hash3"]
    
    # Call the method with recursive=True
    result = controller._apply_corrections_task(recursive=True)
    
    # Verify service was called three times
    assert mock_service.apply_corrections.call_count == 3
    
    # Verify accumulated statistics
    assert result["total_corrections"] == 8  # 5 + 3
    assert result["corrected_rows"] == 3  # Max value
    assert result["corrected_cells"] == 5  # Max value
    assert result["iterations"] == 3
```

#### 1.2: Implement Recursive Correction (Day 1-2)

```python
def _apply_corrections_task(
    self, only_invalid=False, recursive=True, selected_only=False, progress_callback=None
):
    """
    Background task for applying corrections with recursive support.
    
    Args:
        only_invalid (bool): If True, only apply corrections to invalid cells
        recursive (bool): If True, apply corrections recursively until no more changes
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
    
    logger.info(f"Starting correction process: only_invalid={only_invalid}, recursive={recursive}, selected_only={selected_only}")
    
    # Apply corrections iteratively if recursive is True
    while iteration < self.MAX_ITERATIONS:
        # Apply a single round of corrections
        current_stats = self._correction_service.apply_corrections(only_invalid=only_invalid)
        
        # Update accumulated statistics
        total_stats["total_corrections"] += current_stats["total_corrections"]
        # Take the maximum values for rows and cells as they might overlap
        total_stats["corrected_rows"] = max(total_stats["corrected_rows"], current_stats["corrected_rows"])
        total_stats["corrected_cells"] = max(total_stats["corrected_cells"], current_stats["corrected_cells"])
        
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
    
    # Add iteration count to statistics
    total_stats["iterations"] = iteration
    
    # Report final progress
    if progress_callback:
        progress_callback(100, 100)
    
    logger.info(f"Correction completed after {iteration} iterations: {total_stats}")
    return total_stats
```

Also need to add the `MAX_ITERATIONS` constant to prevent infinite loops:

```python
# Maximum recursive iterations to prevent infinite loops
MAX_ITERATIONS = 10
```

### Phase 2: Selection-Based Correction Implementation

#### 2.1: Test for Selection-Based Correction (Day 3)

```python
def test_selection_based_correction(self, mocker):
    """Test that corrections are applied only to selected cells when selected_only=True."""
    # Mock dependencies
    mock_service = mocker.Mock()
    mock_rule_manager = mocker.Mock()
    mock_config_manager = mocker.Mock()
    mock_validation_service = mocker.Mock()
    mock_data_model = mocker.Mock()
    mock_view = mocker.Mock()
    
    # Configure mocks
    mock_service.apply_corrections.return_value = {
        "total_corrections": 5, 
        "corrected_rows": 3, 
        "corrected_cells": 5
    }
    
    # Setup selected cells
    mock_view.get_selected_indexes.return_value = [(0, 1), (1, 2), (2, 3)]
    
    # Create controller with mocks
    controller = CorrectionController(
        mock_service, mock_rule_manager, mock_config_manager, mock_validation_service
    )
    controller._view = mock_view
    controller._data_model = mock_data_model
    
    # Add filter methods to data model mock
    mock_data_model.apply_selection_filter = mocker.Mock()
    mock_data_model.restore_from_filtered_changes = mocker.Mock()
    
    # Call the method with selected_only=True
    result = controller._apply_corrections_task(selected_only=True)
    
    # Verify selection filter was applied
    mock_data_model.apply_selection_filter.assert_called_once()
    
    # Verify data was restored after correction
    mock_data_model.restore_from_filtered_changes.assert_called_once()
    
    # Verify service was called with the filtered data
    assert mock_service.apply_corrections.call_count == 1
```

#### 2.2: Implement Selection-Based Correction (Day 3-4)

```python
def _apply_corrections_task(
    self, only_invalid=False, recursive=True, selected_only=False, progress_callback=None
):
    """
    Background task for applying corrections with recursive and selection support.
    
    Args:
        only_invalid (bool): If True, only apply corrections to invalid cells
        recursive (bool): If True, apply corrections recursively until no more changes
        selected_only (bool): If True, only apply to selected cells
        progress_callback (callable): Function to report progress
        
    Returns:
        Dict[str, int]: Correction statistics
    """
    # Handle selected_only case
    filtering_applied = False
    
    try:
        # Apply selection filtering if needed
        if selected_only and self._view and hasattr(self._view, "get_selected_indexes"):
            selected_indexes = self._view.get_selected_indexes()
            
            if not selected_indexes:
                logger.info("No cells selected for correction")
                return {"total_corrections": 0, "corrected_rows": 0, "corrected_cells": 0, "iterations": 0}
            
            logger.info(f"Applying corrections to {len(selected_indexes)} selected cells")
            
            # Apply temporary filter to data model
            if hasattr(self._data_model, "apply_selection_filter"):
                self._data_model.apply_selection_filter(selected_indexes)
                filtering_applied = True
        
        # Recursive correction implementation as above
        # ...
        
    finally:
        # Restore data if filtering was applied
        if filtering_applied and hasattr(self._data_model, "restore_from_filtered_changes"):
            logger.debug("Restoring data after selection-based correction")
            self._data_model.restore_from_filtered_changes()
    
    return total_stats
```

### Phase 3: Correctable Status Detection Implementation

#### 3.1: Test for Correctable Status Detection (Day 5)

```python
def test_check_correctable_status(self, mocker):
    """Test that invalid cells with matching rules are marked as correctable."""
    # Mock dependencies
    mock_data_model = mocker.Mock()
    mock_rule_manager = mocker.Mock()
    mock_validation_service = mocker.Mock()
    
    # Create test data
    import pandas as pd
    test_data = pd.DataFrame({
        "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "PLAYER": ["Player1", "InvalidPlayer", "Player3"],
        "SOURCE": ["Source1", "Source2", "InvalidSource"]
    })
    
    # Configure validation status
    from chestbuddy.core.validation_enums import ValidationStatus
    validation_df = pd.DataFrame({
        "duplicates": [None, None, None],
        "player_validation": [None, "Invalid player", None],
        "PLAYER_valid": [True, False, True],
        "source_validation": [None, None, "Invalid source"],
        "SOURCE_valid": [True, True, False],
        "DATE_valid": [True, True, True]
    })
    
    # Configure mocks
    mock_data_model.data = test_data
    mock_validation_service.get_validation_status.return_value = validation_df
    
    # Configure rule manager to return matching rules for specific values
    def has_matching_rule_mock(value, column_name):
        if value == "InvalidPlayer" and column_name == "PLAYER":
            return True
        return False
        
    # Create service with mocks
    service = CorrectionService(
        mock_rule_manager, mock_data_model, mock_validation_service
    )
    service._has_matching_rule = mocker.Mock(side_effect=has_matching_rule_mock)
    
    # Call the method
    service.check_correctable_status()
    
    # Verify the validation status was updated correctly
    updated_status = mock_validation_service.set_validation_status.call_args[0][0]
    
    # Invalid player should be marked as correctable
    assert updated_status.at[1, "PLAYER_valid"] == ValidationStatus.CORRECTABLE
    
    # Invalid source should remain invalid (no matching rule)
    assert updated_status.at[2, "SOURCE_valid"] == ValidationStatus.INVALID
    
    # Valid cells should remain valid
    assert updated_status.at[0, "PLAYER_valid"] == ValidationStatus.VALID
```

#### 3.2: Implement Correctable Status Detection (Day 5-6)

```python
def check_correctable_status(self):
    """
    Check which invalid cells can be corrected with available rules.
    
    Updates the validation status to mark invalid cells as correctable
    if they have a matching correction rule.
    
    Returns:
        int: Number of correctable cells identified
    """
    data = self._data_model.data
    if data is None or data.empty:
        logger.warning("No data available to check for correctable cells")
        return 0
    
    logger.info("Checking for correctable cells")
    
    # Get validation status
    validation_status = self._validation_service.get_validation_status()
    if validation_status is None:
        logger.warning("No validation status available")
        return 0
    
    correctable_count = 0
    
    # Create a copy to avoid modifying during iteration
    validation_copy = validation_status.copy()
    
    # Map column indices to names for validation status
    col_validation_map = {}
    for col_idx, col_name in enumerate(data.columns):
        col_validation_map[col_idx] = f"{col_name}_valid"
    
    # Check each cell
    for row_idx in range(len(data)):
        for col_idx in range(len(data.columns)):
            col_name = data.columns[col_idx]
            status_col = col_validation_map.get(col_idx)
            
            if status_col not in validation_copy.columns:
                continue
                
            # Get current validation status
            current_status = validation_copy.at[row_idx, status_col]
            
            # Skip cells that aren't invalid
            if current_status != ValidationStatus.INVALID:
                continue
                
            # Check if this cell has a matching correction rule
            cell_value = data.at[row_idx, col_name]
            if self._has_matching_rule(cell_value, col_name):
                # Update status to CORRECTABLE
                validation_copy.at[row_idx, status_col] = ValidationStatus.CORRECTABLE
                correctable_count += 1
                logger.debug(f"Cell [{row_idx}, {col_idx}] '{cell_value}' marked as correctable")
    
    # Update the validation status
    if correctable_count > 0:
        logger.info(f"Identified {correctable_count} correctable cells")
        self._validation_service.set_validation_status(validation_copy)
    
    return correctable_count
```

### Phase 4: Auto-Correction Options Implementation

#### 4.1: Test for Auto-Correction Configuration (Day 7)

```python
def test_auto_correction_config(self):
    """Test auto-correction configuration options."""
    # Create config manager with a temporary file
    import tempfile
    import os
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Create config manager
        from chestbuddy.utils.config import ConfigManager
        config = ConfigManager(temp_path)
        
        # Test default values
        assert config.get_auto_correct_on_validation() is False
        assert config.get_auto_correct_on_import() is False
        
        # Test setting values
        config.set_auto_correct_on_validation(True)
        assert config.get_auto_correct_on_validation() is True
        
        config.set_auto_correct_on_import(True)
        assert config.get_auto_correct_on_import() is True
        
        # Test setting back to false
        config.set_auto_correct_on_validation(False)
        assert config.get_auto_correct_on_validation() is False
        
        # Verify settings were saved to file
        config.save()
        
        # Create a new instance to verify persistence
        config2 = ConfigManager(temp_path)
        assert config2.get_auto_correct_on_import() is True
        assert config2.get_auto_correct_on_validation() is False
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

#### 4.2: Implement Auto-Correction Configuration (Day 7-8)

```python
def get_auto_correct_on_validation(self):
    """
    Get whether to automatically apply corrections after validation.
    
    Returns:
        bool: True if auto-correction on validation is enabled
    """
    return self.get_boolean("Correction", "auto_correct_on_validation", False)
    
def set_auto_correct_on_validation(self, value):
    """
    Set whether to automatically apply corrections after validation.
    
    Args:
        value (bool): True to enable auto-correction on validation
    """
    self.set("Correction", "auto_correct_on_validation", str(value))
    
def get_auto_correct_on_import(self):
    """
    Get whether to automatically apply corrections on import.
    
    Returns:
        bool: True if auto-correction on import is enabled
    """
    return self.get_boolean("Correction", "auto_correct_on_import", False)
    
def set_auto_correct_on_import(self, value):
    """
    Set whether to automatically apply corrections on import.
    
    Args:
        value (bool): True to enable auto-correction on import
    """
    self.set("Correction", "auto_correct_on_import", str(value))
```

#### 4.3: Implement Workflow Integration (Day 8-9)

```python
def _on_data_imported(self):
    """
    Handle data import completion with validation and auto-correction.
    """
    # Always check correctable status on import
    if self._correction_service:
        self._correction_service.check_correctable_status()
        logger.debug("Checked correctable status after import")
    
    # Apply auto-validation if enabled
    auto_validate = self._config_manager.get_auto_validate()
    if auto_validate and self._validation_service:
        logger.info("Auto-validation enabled, validating imported data")
        self._validation_service.validate_data()
        
        # Apply auto-correction if enabled
        auto_correct = self._config_manager.get_auto_correct_on_import()
        if auto_correct and self._correction_controller:
            logger.info("Auto-correction on import enabled, applying corrections")
            self._correction_controller.apply_corrections(only_invalid=True)
    
    # Update UI state
    self._update_ui_state()

def _on_validation_completed(self):
    """
    Handle validation completion with auto-correction.
    """
    # Check which invalid cells are correctable
    if self._correction_service:
        self._correction_service.check_correctable_status()
        logger.debug("Checked correctable status after validation")
    
    # Apply auto-correction if enabled
    auto_correct = self._config_manager.get_auto_correct_on_validation()
    if auto_correct and self._correction_controller:
        logger.info("Auto-correction on validation enabled, applying corrections")
        self._correction_controller.apply_corrections(only_invalid=True)
    
    # Update UI state
    self._update_ui_state()
```

### Phase 5: Settings UI Implementation

#### 5.1: Update Settings UI (Day 10-11)

```python
def _setup_ui(self):
    """Set up the settings UI with correction options."""
    # ... existing code ...
    
    # Create correction settings group
    correction_group = QGroupBox("Correction Settings")
    correction_layout = QVBoxLayout()
    
    # Create checkbox options
    self._auto_correct_on_validation = QCheckBox("Automatically apply corrections after validation")
    self._auto_correct_on_import = QCheckBox("Automatically apply corrections on import")
    
    # Initialize checkbox states
    self._auto_correct_on_validation.setChecked(
        self._config_manager.get_auto_correct_on_validation()
    )
    self._auto_correct_on_import.setChecked(
        self._config_manager.get_auto_correct_on_import()
    )
    
    # Add to layout
    correction_layout.addWidget(self._auto_correct_on_validation)
    correction_layout.addWidget(self._auto_correct_on_import)
    correction_group.setLayout(correction_layout)
    
    # Add to main layout
    self._layout.addWidget(correction_group)
    
    # ... existing code ...

def _apply_settings(self):
    """Apply all settings."""
    # ... existing code ...
    
    # Apply correction settings
    self._config_manager.set_auto_correct_on_validation(
        self._auto_correct_on_validation.isChecked()
    )
    self._config_manager.set_auto_correct_on_import(
        self._auto_correct_on_import.isChecked()
    )
    
    # ... existing code ...
```

### Phase 6: Integration Testing

#### 6.1: Create Integration Tests (Day 12-14)

```python
def test_correction_workflow_e2e(self, qtbot, main_window):
    """Test the complete correction workflow end-to-end."""
    # Import test data with invalid entries
    # ... import code ...
    
    # Verify validation shows invalid cells
    # ... validation check code ...
    
    # Verify correctable cells are marked correctly
    # ... check correctable status ...
    
    # Apply corrections
    # Access correction view
    main_window._set_active_view('correction')
    correction_view = main_window._views['correction']
    
    # Get apply button and click it
    apply_button = correction_view._rule_view._apply_button
    qtbot.mouseClick(apply_button, Qt.LeftButton)
    
    # Wait for correction to complete
    qtbot.waitUntil(lambda: not hasattr(correction_view._correction_controller, '_worker') 
                   or correction_view._correction_controller._worker is None)
    
    # Verify corrections were applied
    # ... check correction results ...
```

## Enhanced UI Features

### Updated UI Components

1. **Settings Panel with Auto-Correction Options**
   - Add checkboxes for auto-correction on validation
   - Add checkboxes for auto-correction on import
   - Add correction configuration options
   - Add UI for recursive correction options

2. **Improved Data View Integration**
   - Enhanced cell highlighting for correctable cells
   - Tooltip showing correction rule that would be applied
   - Context menu with correction options
   - Status indicator in status bar showing correctable cell count

3. **Correction View Enhancements**
   - Rules table with correctable count column
   - Preview feature showing affected cells
   - Enhanced rule editor with validation
   - Import/Export with format options

## Implementation Timeline

### Week 1
- Phase 1: Test and implement recursive correction
- Phase 2: Test and implement selection-based correction

### Week 2
- Phase 3: Test and implement correctable status detection
- Phase 4: Test and implement auto-correction options

### Week 3
- Phase 5: Test and implement UI components
- Phase 6: Create integration tests

### Week 4
- Final testing and bug fixes
- Documentation updates
- Performance optimization

## Success Criteria

1. **Functionality**
   - Recursive correction works properly
   - Selection-based correction works properly
   - Correctable status is properly detected and displayed
   - Auto-correction options work as expected

2. **Test Coverage**
   - Test coverage of new features is at least 90%
   - All test cases pass consistently

3. **Documentation**
   - Code is properly documented with docstrings
   - User documentation is updated
   - Memory-bank entries are updated

4. **Performance**
   - Correction operation completes within acceptable time limits
   - UI remains responsive during correction operations

## Risk Management

1. **Performance with Large Datasets**
   - Risk: Recursive correction could be slow with large datasets
   - Mitigation: Add progress reporting, cancel option, and batch processing

2. **Integration Issues**
   - Risk: New features might conflict with existing code
   - Mitigation: Comprehensive integration testing and incremental implementation

3. **UI Responsiveness**
   - Risk: Complex operations might freeze the UI
   - Mitigation: Ensure all operations run in background threads with proper progress reporting

## Conclusion

This plan outlines a comprehensive approach to improving the correction system in ChestBuddy. Following this plan will address the current issues with the system and add new features to enhance the user experience. The test-driven development approach will ensure high quality and maintainability of the code. 