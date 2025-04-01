# Correction System Improvements Plan

## Overview

This document outlines the comprehensive plan for improving the ChestBuddy correction system, addressing current functionality gaps and implementing new features. We've identified several key areas that need to be addressed:

1. **Recursive Correction**: The controller is passing `recursive=True` but the service doesn't implement recursion
2. **Selection-Based Correction**: The `selected_only` parameter isn't properly implemented
3. **Correctable Status Detection**: The "correctable" status now has proper visual integration with validation (✓ Complete)
4. **Auto-Correction Options**: Auto-correction on validation and import (✓ Complete)
5. **TableStateManager**: New component for centralized state management and improved correction display
6. **Simplified Correction Display**: Show only essential information (original value, corrected value, type)

## Progress Update - April 1, 2024

### TableStateManager Implementation Started

We have begun implementing the TableStateManager to improve cell state handling and correction visualization:

1. **Core Components Defined**:
   - CellState enum for state tracking
   - TableStateManager class structure
   - ValidationProgressDialog for user feedback

2. **Key Features**:
   - Batch processing with 100 rows per batch
   - Non-blocking UI updates
   - Comprehensive error handling
   - Detailed correction logging

3. **Implementation Plan**:
   - 8 phases defined with clear deliverables
   - 13-day timeline established
   - Test-driven development approach
   - Performance considerations included

### Simplified Correction Display

We are implementing a streamlined correction display that shows:
- Original value
- Corrected value
- Correction type
- Total corrections counter

## Progress Update - August 2, 2024

### Phase 3: Correctable Status Detection ✓ Complete
We have successfully implemented the algorithmic detection of correctable cells. This builds on the validation visualization system fix that was completed earlier:

1. **Core Implementation**:
   - Enhanced the `CorrectionService` to identify invalid cells that have matching correction rules
   - Implemented integration with the validation service to mark cells as correctable
   - Added comprehensive tests to verify the functionality works correctly

2. **Key Features**:
   - The `get_cells_with_available_corrections` method correctly filters for invalid cells with matching rules
   - The `check_correctable_status` method properly integrates with the validation service
   - Correctable cells are clearly identified in the system, enabling auto-correction workflows

### Phase 4: Auto-Correction Options ✓ Complete

We have successfully implemented the auto-correction options feature, allowing for automatic application of corrections:

1. **Configuration Options**:
   - Added `auto_correct_on_validation` and `auto_correct_on_import` settings to ConfigManager
   - Implemented getters and setters for these options
   - Set default values to False to ensure explicit opt-in by users

2. **Integration Points**:
   - Utilized existing methods in CorrectionController for auto-correction functionality
   - Confirmed proper signal connections in DataViewController for triggering auto-correction
   - Verified that all unit tests pass with the new configuration options

## Progress Update - August 1, 2024

### Validation Visualization System Fix ✓ Complete
We have successfully fixed the validation visualization system, ensuring that different validation statuses (Valid, Invalid, Correctable) are correctly displayed in the data view:

1. **Fixed Components**:
   - ValidationService._update_validation_status now correctly sets status enum values
   - DataView._highlight_invalid_rows properly processes validation statuses
   - ValidationStatusDelegate.paint prioritizes and displays statuses correctly

2. **Visual Integration**:
   - Valid cells displayed with light green background
   - Invalid cells displayed with deep red background and black border
   - Correctable cells displayed with orange background and darker orange border

3. **Status Detection**:
   - ValidationService now detects and properly marks correctable cells with distinct enum value
   - Correctable status is passed through signals to the DataView
   - DataView forwards status to ValidationStatusDelegate for visualization

This marks a significant step toward Phase 3 of our plan (Correctable Status Detection), as the visual part is now complete. We still need to implement the algorithmic detection of correctable cells based on available correction rules.

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

## Timeline and Prioritization (Updated April 1, 2024)

1. ~~**Phase 3**: Complete the algorithmic detection of correctable cells based on available rules~~ ✓ Completed
2. ~~**Phase 4**: Implement auto-correction options~~ ✓ Completed
3. **TableStateManager**: Implement new state management system (13 days)
4. **Phase 1**: Implement recursive correction functionality (2 days)
5. **Phase 2**: Implement selection-based correction (2 days)

Total estimated time remaining: 17 working days

## Acceptance Criteria

1. Recursive correction continues applying rules until no more changes are made
2. Selection-based correction only applies to selected cells
3. ✓ Correctable status detection identifies invalid cells that have matching rules
4. ✓ Auto-correction options can be configured and work correctly
5. TableStateManager properly manages cell states and provides progress feedback
6. Correction display shows only essential information in a clear format

## Testing Strategy

Each phase includes dedicated test cases:
1. Test that recursive correction applies rules until no more changes occur
2. Test that selection-based correction only applies to selected cells
3. ✓ Test that correctable status detection correctly identifies cells that can be corrected
4. ✓ Test that auto-correction options are correctly stored in config and applied when enabled
5. Test TableStateManager state tracking and batch processing
6. Test simplified correction display format and accuracy

## UI Implications

1. Add a "Recursive" checkbox in the correction dialog
2. ✓ Add "Auto-correct on validation" and "Auto-correct on import" options in settings
3. ✓ Update cell highlighting to use distinct colors for different validation statuses
4. Add progress dialog with correction details
5. Update correction log format to show essential information only
6. Add total corrections counter to the UI

## Implementation Priority

1. TableStateManager Core Components
2. Progress Dialog Implementation
3. Batch Processing Logic
4. Error Handling System
5. DataView Integration
6. Simplified Correction Display
7. Recursive Correction
8. Selection-Based Correction

This updated plan reflects our current focus on the TableStateManager implementation while maintaining our commitment to completing the recursive and selection-based correction features.