# DataView UI Mockup - Validation Integration

## Overview

This document details the integration between the validation system and the DataView component, focusing on how validation statuses are visualized, updated, and interacted with by users. Proper validation visualization is critical for helping users identify and correct data issues efficiently.

## Validation Status Types

The validation system uses the following status types, each requiring distinct visual representation:

1. **VALID**: Cell contains valid data
2. **INVALID**: Cell contains invalid data that must be corrected
3. **CORRECTABLE**: Cell contains data with issues that can be automatically corrected
4. **WARNING**: Cell contains data that is technically valid but may need attention
5. **INFO**: Cell contains data with informational notices

## Visual Representation

### Cell Background Colors

Each validation status has a distinct background color:

| Status      | Background Color | Hex Code | Description                            |
|-------------|------------------|----------|----------------------------------------|
| VALID       | White            | #ffffff  | Regular cell background                |
| INVALID     | Light Red        | #ffb6b6  | Clearly indicates error                |
| CORRECTABLE | Light Yellow     | #fff3b6  | Indicates fixable issue                |
| WARNING     | Light Orange     | #ffe4b6  | Indicates potential issue              |
| INFO        | Light Blue       | #b6e4ff  | Provides additional information        |

### Status Indicators

In addition to background colors, cells will display status indicators in the top-right corner:

```
INVALID:                CORRECTABLE:            WARNING:                 INFO:
+----------------+      +----------------+      +----------------+      +----------------+
|             ✗  |      |             ▼  |      |             !  |      |             i  |
|                |      |                |      |                |      |                |
| Cell content   |      | Cell content   |      | Cell content   |      | Cell content   |
+----------------+      +----------------+      +----------------+      +----------------+
```

The indicators will be:
- **INVALID**: Red "X" symbol (✗)
- **CORRECTABLE**: Yellow dropdown arrow (▼)
- **WARNING**: Orange exclamation mark (!)
- **INFO**: Blue information icon (i)

### Combined States

Cells can have combined states - validation status plus selection or focus state:

```
Selected + Invalid:           Focused + Correctable:
+------------------+          +====================+
|[[             ✗ ]]|          ||             ▼    ||
|[[                ]]|          ||                  ||
|[[ Cell content   ]]|          || Cell content     ||
+------------------+          +====================+
```

## Validation Data Flow

The following diagram illustrates how validation data flows through the system:

```
+------------------+     +-------------------+     +------------------+
| ValidationService| --> | ValidationAdapter | --> | TableStateManager|
+------------------+     +-------------------+     +------------------+
        |                                                  |
        v                                                  v
+------------------+                             +------------------+
| ValidationResults|                             | CellStateManager |
+------------------+                             +------------------+
                                                         |
                                                         v
     +-------------------+     +---------------+     +------------------+
     | DataViewModel     | <-- | ViewAdapter   | <-- | ValidationStates |
     +-------------------+     +---------------+     +------------------+
              |
              v
     +-------------------+
     | CellDisplayDelegate|
     +-------------------+
              |
              v
     +-------------------+
     | DataTableView     |
     +-------------------+
```

### Key Components in the Validation Flow:

1. **ValidationService**: Core service that performs validation and generates validation results
2. **ValidationAdapter**: Adapts validation results to a format usable by the UI components
3. **TableStateManager**: Manages the state of all cells in the table
4. **CellStateManager**: Handles the visual state of individual cells
5. **ValidationStates**: Contains the current validation state for all cells
6. **ViewAdapter**: Connects validation states to the data view model
7. **DataViewModel**: Model for the view that includes validation state information
8. **CellDisplayDelegate**: Custom delegate that renders cells based on their state
9. **DataTableView**: The UI component that displays the data and validation indicators

## Detailed Data Flow Process

1. **Validation Initiation**:
   - User triggers validation (manually or automatically on data change)
   - ValidationService performs validation on the data

2. **Validation Results Generation**:
   - ValidationService creates a ValidationResults object
   - Results contain status for each cell and error/warning messages

3. **Adaptation to UI**:
   - ValidationAdapter converts ValidationResults to a format usable by UI
   - Extracts cell coordinates, status types, and messages

4. **State Management**:
   - TableStateManager updates the CellStateManager with new validation states
   - CellStateManager maps validation statuses to visual states

5. **Model Update**:
   - ViewAdapter notifies DataViewModel of state changes
   - DataViewModel includes validation state in its data representation

6. **Visual Rendering**:
   - CellDisplayDelegate renders cells based on their current state
   - DataTableView displays the rendering with appropriate colors and indicators

## Tooltip Integration

When hovering over cells with validation issues, tooltips will provide detailed information:

```
+--------------------------------------------+
| Validation Error                           |
| -------------------------------------------+
| Value "abc" is not a valid number.         |
| Expected format: Numeric value             |
| Column: "Score"                            |
+--------------------------------------------+
```

For correctable cells:

```
+--------------------------------------------+
| Correctable Issue                          |
| -------------------------------------------+
| Value "JohnSmiht" could be corrected.      |
| Suggested correction: "John Smith"         |
| Column: "Player Name"                      |
| Click ▼ icon to apply correction           |
+--------------------------------------------+
```

## User Interaction with Validation

### Validation Indicators

1. **Hovering**:
   - Hovering over a cell with a validation issue shows a tooltip with details
   - Tooltip includes the issue description, expected format, and column name

2. **Clicking on Indicators**:
   - Clicking the CORRECTABLE indicator (▼) shows available corrections
   - Clicking the INVALID indicator (✗) opens a dialog with validation details
   - Clicking the WARNING indicator (!) shows warning details
   - Clicking the INFO indicator (i) shows informational details

### Context Menu Integration

The context menu will include validation-related options:

```
+---------------------------+
| ✓ Copy                 C  |
| ✓ Paste                V  |
| ✓ Cut                  X  |
| ✓ Delete             Del  |
+---------------------------+
| ✓ Edit                 E  |
| ✓ Reset Value          R  |
+---------------------------+
| ! View Validation Error    |  (For invalid cells)
| ✓ Apply Correction     Y  |  (For correctable cells)
+---------------------------+
```

### Correction Workflow

For correctable cells, clicking the indicator shows a popup with correction options:

```
+--------------------------------------------+
| Available Corrections                      |
| -------------------------------------------+
| > "John Smith"                             |
| > "Jon Smith"                              |
| > Add Custom...                            |
+--------------------------------------------+
```

### Validation Summary

A validation summary will be available in the status bar:

```
+----------------------------------------------------------------------+
| Validation: 4 invalid cells, 1 correctable, 2 warnings               |
+----------------------------------------------------------------------+
```

Clicking on this summary opens a validation panel with a list of all issues:

```
+------------------------------------------------------------------+
| Validation Results                                               |
+------------------------------------------------------------------+
| ✗ Row 3, Score: "abc" is not a valid number                      |
| ✗ Row 5, Date: "2023/13/45" is not a valid date                  |
| ✗ Row 7, Player: "unknown" is not in the player list             |
| ✗ Row 12, Chest: Empty value is not allowed                      |
| ▼ Row 8, Player: "JohnSmiht" could be corrected to "John Smith"  |
| ! Row 15, Score: Value 8000 is unusually high                    |
+------------------------------------------------------------------+
```

## Implementation Details

### Cell State Management

1. **State Representation**:
   ```python
   class CellState:
       validation_status: ValidationStatus
       is_selected: bool
       is_focused: bool
       has_custom_format: bool
       custom_format: Optional[CellFormat]
       tooltip_text: Optional[str]
   ```

2. **Validation Status Mapping**:
   ```python
   class ValidationStatusMapper:
       def map_status_to_color(status: ValidationStatus) -> QColor:
           if status == ValidationStatus.INVALID:
               return QColor("#ffb6b6")
           elif status == ValidationStatus.CORRECTABLE:
               return QColor("#fff3b6")
           # ... other mappings
           
       def map_status_to_icon(status: ValidationStatus) -> QIcon:
           if status == ValidationStatus.INVALID:
               return QIcon(":/icons/invalid.png")
           elif status == ValidationStatus.CORRECTABLE:
               return QIcon(":/icons/correctable.png")
           # ... other mappings
   ```

3. **Cell Rendering**:
   ```python
   class CellDisplayDelegate(QStyledItemDelegate):
       def paint(self, painter, option, index):
           # Get cell state from model
           cell_state = index.data(CellStateRole)
           
           # Apply background color based on validation status
           if cell_state.validation_status != ValidationStatus.VALID:
               bg_color = ValidationStatusMapper.map_status_to_color(
                   cell_state.validation_status)
               painter.fillRect(option.rect, bg_color)
               
           # Draw content
           super().paint(painter, option, index)
           
           # Draw validation indicator if needed
           if cell_state.validation_status != ValidationStatus.VALID:
               icon = ValidationStatusMapper.map_status_to_icon(
                   cell_state.validation_status)
               icon_rect = QRect(
                   option.rect.right() - 16, 
                   option.rect.top(), 
                   16, 16)
               icon.paint(painter, icon_rect)
   ```

### Signal-Slot Connections

```python
# In initialization code
validation_service.validation_complete.connect(
    validation_adapter.on_validation_complete)
validation_adapter.validation_state_changed.connect(
    table_state_manager.update_cell_states_from_validation)
table_state_manager.cell_states_changed.connect(
    view_adapter.on_cell_states_changed)
view_adapter.data_changed.connect(
    data_view_model.on_data_changed)
```

### Tooltip Implementation

```python
class DataTableView(QTableView):
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            pos = event.pos()
            index = self.indexAt(pos)
            if index.isValid():
                cell_state = self.model().data(index, CellStateRole)
                if (cell_state.validation_status != ValidationStatus.VALID 
                        and cell_state.tooltip_text):
                    QToolTip.showText(event.globalPos(), 
                                     cell_state.tooltip_text)
                    return True
        return super().event(event)
```

## Performance Considerations

1. **Efficient State Updates**:
   - Only update cells that have changed state
   - Use batch updates rather than individual cell updates
   - Consider using a sparse representation for validation states

2. **Lazy Loading**:
   - Load validation states only for visible cells
   - Update states asynchronously for large datasets

3. **Caching**:
   - Cache validation results and states
   - Pre-compute states for frequently accessed regions

## Accessibility Considerations

1. **Color Blind Support**:
   - Use patterns in addition to colors
   - Ensure sufficient contrast
   - Provide icon indicators that don't rely on color

2. **Screen Reader Support**:
   - Add ARIA attributes for validation states
   - Ensure all tooltips are accessible
   - Provide keyboard navigation for validation interactions

3. **Keyboard Navigation**:
   - Tab navigation to validation indicators
   - Keyboard shortcuts for validation actions
   - Focus indication for validation elements

## Testing Considerations

### Unit Tests

1. **Validation State Mapping**:
   - Test mapping of validation statuses to colors
   - Test mapping of validation statuses to icons
   - Test combined states (validation + selection)

2. **Cell Rendering**:
   - Test rendering of different validation states
   - Test indicator positioning
   - Test tooltip generation

### Integration Tests

1. **Data Flow**:
   - Test validation results propagation
   - Test state updates in response to validation
   - Test UI updates in response to state changes

2. **User Interaction**:
   - Test tooltip display on hover
   - Test indicator clicks
   - Test context menu integration

### Visual Tests

1. **Appearance**:
   - Test visual rendering of all states
   - Test contrast and visibility
   - Test responsiveness and layout

## Future Enhancements

1. **Severity Levels**:
   - Add support for different severity levels within each status type
   - Use visual cues to indicate severity

2. **Batch Validation Display**:
   - Add a dedicated validation panel for batch operations
   - Implement filtering and sorting of validation issues

3. **Validation History**:
   - Track validation changes over time
   - Show validation improvement metrics

4. **Custom Validation Visualizations**:
   - Allow users to customize how validation issues are displayed
   - Support different visualization modes for different data types 