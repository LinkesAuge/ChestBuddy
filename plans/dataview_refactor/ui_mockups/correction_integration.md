# DataView UI Mockup - Correction Integration

## Overview

This document details the integration between the correction system and the DataView component. The correction system allows users to fix validation issues automatically or with minimal interaction. This integration is critical for improving data quality efficiently and reducing manual correction effort.

## Correction System Concepts

The correction system operates with the following key concepts:

1. **Correction Rules**: Predefined rules that specify how to correct specific data issues
2. **Correction Suggestions**: Possible corrections for a specific data issue
3. **Correction Application**: The process of applying a correction to fix data
4. **Batch Correction**: Applying corrections to multiple cells at once
5. **Correction History**: Record of corrections applied to the data

## Visual Elements for Correction

### Correctable Cell Indication

Cells that can be corrected are visually indicated:

```
+----------------+
|             ▼  |
|                |
| Cell content   |
+----------------+
```

- Light yellow background (#fff3b6)
- Dropdown arrow (▼) in the top-right corner
- Tooltip showing correction information

### Correction Dropdown

Clicking on the correction indicator (▼) shows a dropdown with available corrections:

```
+----------------+      +---------------------------+
|             ▼  |      | Available Corrections     |
|                | ---> | > "John Smith"            |
| JohnSmiht      |      | > "Jon Smith"             |
+----------------+      | > Add Custom...           |
                        +---------------------------+
```

### Batch Correction Dialog

For multiple correctable cells, a batch correction dialog is available:

```
+-------------------------------------------------------------+
| Batch Correction                                      [X]   |
+-------------------------------------------------------------+
| Found 5 cells that can be corrected:                        |
|                                                             |
| [ ] Row 8, Player: "JohnSmiht" → "John Smith"               |
| [ ] Row 12, Player: "MaryJhonson" → "Mary Johnson"          |
| [ ] Row 15, Clan: "GoldenMafia" → "Golden Mafia"            |
| [ ] Row 18, Source: "stream" → "Stream"                     |
| [ ] Row 22, Chest: "siver" → "Silver"                       |
|                                                             |
| [Select All] [Deselect All]     [Apply Selected] [Cancel]   |
+-------------------------------------------------------------+
```

### Correction Preview

Before applying corrections, users can preview the changes:

```
+-------------------------------------------------------------+
| Correction Preview                                    [X]   |
+-------------------------------------------------------------+
|                  Original               Corrected           |
| Row 8:           "JohnSmiht"           "John Smith"         |
| Row 12:          "MaryJhonson"         "Mary Johnson"       |
|                                                             |
| [Apply Corrections] [Cancel]                                |
+-------------------------------------------------------------+
```

### Correction Progress

For large batch corrections, a progress indicator is shown:

```
+-------------------------------------------------------------+
| Applying Corrections                                        |
+-------------------------------------------------------------+
| [====================                    ] 45%              |
| Processed: 45/100 cells                                     |
|                                                             |
| [Cancel]                                                    |
+-------------------------------------------------------------+
```

## Correction Workflows

### Individual Cell Correction

1. **Identification**:
   - User notices a cell with a yellow background and correction indicator (▼)
   - User hovers over the cell to see correction information in tooltip

2. **Correction Selection**:
   - User clicks on the correction indicator (▼)
   - Dropdown shows available corrections
   - User selects the desired correction

3. **Application**:
   - System applies the selected correction
   - Cell updates with corrected value
   - Cell state changes to valid (white background)

### Context Menu Correction

1. **Selection**:
   - User right-clicks on a correctable cell
   - Context menu appears with correction options

2. **Action**:
   - User selects "Apply Correction" from menu
   - If multiple corrections available, submenu displays options
   - User selects specific correction

3. **Result**:
   - System applies correction
   - Cell updates with corrected value
   - Visual feedback confirms correction

### Batch Correction

1. **Initiation**:
   - User selects "Batch Correction" from toolbar or menu
   - System identifies all correctable cells in data or selection

2. **Selection**:
   - Batch correction dialog shows list of correctable cells
   - User selects which corrections to apply
   - Preview shows original and corrected values

3. **Application**:
   - User clicks "Apply Selected"
   - System processes corrections in background
   - Progress indicator shows completion status
   - Results summary shows success/failure counts

### Rule-Based Correction

1. **Setup**:
   - User adds or modifies correction rules
   - Rules specify patterns to match and replacements

2. **Execution**:
   - Validation system identifies cells matching rules
   - Marks them as correctable with appropriate suggestions

3. **Review and Apply**:
   - User reviews suggested corrections
   - Applies individually or in batch
   - System tracks which rules were applied

## User Interface Components

### Correction Toolbar

```
+----------------------------------------------------------------------+
| [Validate] [Batch Correct▼] [Add Rule] [View Rules] [Correction History]|
+----------------------------------------------------------------------+
```

**Options under "Batch Correct" dropdown**:
- **Correct All**: Apply all available corrections
- **Correct Selected**: Apply corrections only to selected cells
- **Correct by Type**: Apply corrections for specific issue types

### Correction Panel

A dockable panel showing correction information:

```
+----------------------------------------------------------------------+
| Correction Panel                                             [_][X]  |
+----------------------------------------------------------------------+
| [Filter: All▼]                                       [Search: ____]  |
|                                                                      |
| Correctable Items:                                                   |
| +------------------------------------------------------------------+ |
| | ▼ Row 8, Player: "JohnSmiht" → "John Smith"                      | |
| | ▼ Row 12, Player: "MaryJhonson" → "Mary Johnson"                 | |
| | ▼ Row 15, Clan: "GoldenMafia" → "Golden Mafia"                   | |
| | ▼ Row 18, Source: "stream" → "Stream"                            | |
| | ▼ Row 22, Chest: "siver" → "Silver"                              | |
| +------------------------------------------------------------------+ |
|                                                                      |
| [Correct Selected] [Correct All] [Add Rule from Selected]            |
+----------------------------------------------------------------------+
```

### Rule Management Dialog

```
+----------------------------------------------------------------------+
| Correction Rules                                             [_][X]  |
+----------------------------------------------------------------------+
| [Add Rule] [Edit Rule] [Delete Rule] [Import] [Export]               |
|                                                                      |
| +------------------------------------------------------------------+ |
| | ID | Pattern  | Replacement | Column | Active | Match Type       | |
| |----+----------+-------------+--------+--------+------------------| |
| | 1  | JohnSmiht| John Smith  | Player |   ✓    | Exact           | |
| | 2  | \bMary.+ | Mary Johnson| Player |   ✓    | Regex           | |
| | 3  | siv(er)  | Silver      | Chest  |   ✓    | Fuzzy (80%)     | |
| +------------------------------------------------------------------+ |
|                                                                      |
| [Test Selected Rule] [Apply Changes] [Cancel]                        |
+----------------------------------------------------------------------+
```

### Correction History Dialog

```
+----------------------------------------------------------------------+
| Correction History                                          [_][X]   |
+----------------------------------------------------------------------+
| [Filter: Today▼]                                    [Search: ____]   |
|                                                                      |
| +------------------------------------------------------------------+ |
| | Timestamp           | User  | Cell       | Original  | Corrected | |
| |---------------------+-------+------------+-----------+-----------| |
| | 2023-04-15 10:30:22 | User1 | R8,Player  | JohnSmiht | John Smith| |
| | 2023-04-15 10:31:05 | User1 | R12,Player | MaryJhons | Mary Jho..| |
| | 2023-04-15 11:15:43 | User2 | R15,Clan   | GoldenMaf | Golden M..| |
| +------------------------------------------------------------------+ |
|                                                                      |
| [Revert Selected] [Export History] [Close]                           |
+----------------------------------------------------------------------+
```

## Data Flow for Correction

The following diagram illustrates the correction data flow:

```
+------------------+     +-------------------+     +-----------------+
| CorrectionService| --> | CorrectionAdapter | --> | TableStateManager|
+------------------+     +-------------------+     +-----------------+
        |                                                 |
        v                                                 v
+------------------+                             +-----------------+
| CorrectionRules  |                             | CellStateManager|
+------------------+                             +-----------------+
        |                                                 |
        v                                                 v
+------------------+     +-------------------+     +-----------------+
| CorrectionEngine | --> | CorrectionResults| --> | ValidationStates |
+------------------+     +-------------------+     +-----------------+
                                                          |
                                                          v
     +-------------------+     +---------------+     +-----------------+
     | DataViewModel     | <-- | ViewAdapter   | <-- | CorrectionStates|
     +-------------------+     +---------------+     +-----------------+
              |
              v
     +-------------------+
     | CellDisplayDelegate|
     +-------------------+
              |
              v
     +-------------------+     +------------------+
     | DataTableView     | --> | CorrectionPopups |
     +-------------------+     +------------------+
```

### Key Components in the Correction Flow:

1. **CorrectionService**: Core service that manages correction rules and applies corrections
2. **CorrectionAdapter**: Adapts correction results to a format usable by UI components
3. **CorrectionRules**: Repository of rules for automatic corrections
4. **CorrectionEngine**: Applies rules to identify and generate corrections
5. **CorrectionResults**: Contains suggested corrections for cells
6. **TableStateManager**: Updates cell states based on correction information
7. **CellStateManager**: Manages visual state including correction indicators
8. **ValidationStates**: Includes correction information in validation states
9. **CorrectionStates**: Specific correction state information for UI
10. **ViewAdapter**: Connects correction states to the data view model
11. **DataViewModel**: Includes correction information in model
12. **CellDisplayDelegate**: Renders correction indicators
13. **CorrectionPopups**: Manages correction dropdown and dialogs

## Detailed Correction Process

1. **Rule Application**:
   - CorrectionService loads correction rules
   - CorrectionEngine applies rules to data
   - Generates CorrectionResults with suggested corrections

2. **State Update**:
   - CorrectionAdapter converts results to UI format
   - TableStateManager updates cell states
   - Cells with corrections available are marked as correctable

3. **UI Representation**:
   - ViewAdapter passes correction state to DataViewModel
   - CellDisplayDelegate renders correction indicators
   - DataTableView displays cells with correction styling

4. **User Interaction**:
   - User clicks correction indicator or uses context menu
   - CorrectionPopups displays correction options
   - User selects correction to apply

5. **Correction Application**:
   - Selected correction is passed to CorrectionService
   - CorrectionService applies correction to data
   - Updated data flows back through system
   - Cell state updates to reflect correction

## Implementation Details

### Correction State Representation

```python
class CorrectionState:
    is_correctable: bool
    suggested_corrections: List[CorrectionSuggestion]
    selected_correction: Optional[CorrectionSuggestion]
    correction_rule_id: Optional[int]

class CorrectionSuggestion:
    original_value: Any
    corrected_value: Any
    confidence: float
    rule_id: Optional[int]
    description: str
```

### Correction UI Elements

```python
class CorrectionIndicator:
    def paint(self, painter, rect):
        # Draw dropdown triangle in top-right corner
        # Use yellow color for correctable state
        pass
        
    def on_click(self, cell_index):
        # Show correction dropdown
        suggestions = get_suggestions_for_cell(cell_index)
        show_correction_dropdown(cell_index, suggestions)
        pass

class CorrectionDropdown(QMenu):
    def __init__(self, parent, cell_index, suggestions):
        super().__init__(parent)
        self.cell_index = cell_index
        self.suggestions = suggestions
        self._populate_menu()
        
    def _populate_menu(self):
        for suggestion in self.suggestions:
            action = QAction(f'"{suggestion.corrected_value}"', self)
            action.triggered.connect(
                lambda: self._apply_correction(suggestion))
            self.addAction(action)
        
        self.addSeparator()
        custom_action = QAction("Add Custom...", self)
        custom_action.triggered.connect(self._show_custom_dialog)
        self.addAction(custom_action)
        
    def _apply_correction(self, suggestion):
        correction_service.apply_correction(
            self.cell_index, suggestion)
        
    def _show_custom_dialog(self):
        # Show dialog for custom correction
        pass
```

### Correction Application

```python
class CorrectionService:
    def apply_correction(self, cell_index, suggestion):
        # Get current value
        current_value = data_model.get_value(cell_index)
        
        # Apply correction
        data_model.set_value(cell_index, suggestion.corrected_value)
        
        # Record in history
        self._add_to_history(
            cell_index, current_value, suggestion.corrected_value)
        
        # Emit signal
        self.correction_applied.emit(
            cell_index, current_value, suggestion.corrected_value)
        
    def apply_batch_corrections(self, corrections):
        # Start progress dialog
        progress = CorrectionProgressDialog(len(corrections))
        progress.show()
        
        success_count = 0
        for i, (cell_index, suggestion) in enumerate(corrections):
            try:
                self.apply_correction(cell_index, suggestion)
                success_count += 1
            except Exception as e:
                # Log error
                logger.error(f"Error applying correction: {e}")
            
            # Update progress
            progress.set_progress(i + 1)
            
        # Show results summary
        show_correction_results(success_count, len(corrections))
```

## Performance Considerations

1. **Efficient Rule Application**:
   - Use optimized algorithms for rule matching
   - Prioritize rules based on likelihood and impact
   - Cache rule application results

2. **Lazy Correction Suggestion**:
   - Generate correction suggestions only when needed
   - Defer complex corrections until requested
   - Pre-compute common corrections

3. **Batch Processing**:
   - Process corrections in batches
   - Use background threads for large correction operations
   - Provide progress feedback for long-running operations

## Accessibility Considerations

1. **Keyboard Accessibility**:
   - Provide keyboard shortcuts for correction operations
   - Ensure all correction dialogs are keyboard navigable
   - Add keyboard focus indicators for correction elements

2. **Screen Reader Support**:
   - Include ARIA attributes for correction elements
   - Provide descriptive text for correction options
   - Ensure screen readers announce correction application

3. **Visual Alternatives**:
   - Provide text descriptions of correction state
   - Use patterns in addition to colors for correction indicators
   - Support high contrast mode for all correction UI elements

## Testing Considerations

### Unit Tests

1. **Correction Rule Application**:
   - Test rule matching logic
   - Test correction generation
   - Test confidence calculation

2. **UI Element Tests**:
   - Test correction indicator rendering
   - Test dropdown menu generation
   - Test batch correction dialog

### Integration Tests

1. **Correction Flow**:
   - Test end-to-end correction workflow
   - Test interaction between correction and validation
   - Test persistence of corrections

2. **User Interaction Tests**:
   - Test mouse and keyboard interaction
   - Test correction dropdown behavior
   - Test batch correction dialog interaction

## Future Enhancements

1. **Machine Learning Integration**:
   - Add ML-based correction suggestions
   - Improve correction confidence with learning
   - Personalize corrections based on user behavior

2. **Advanced Rule Management**:
   - Add rule categorization and organization
   - Support rule sharing between users
   - Implement rule effectiveness metrics

3. **Enhanced Batch Operations**:
   - Add pattern-based batch correction
   - Support conditional correction application
   - Implement undo/redo for batch operations

4. **Integration with External Systems**:
   - Connect to reference data sources
   - Support external validation services
   - Implement cross-dataset correction 