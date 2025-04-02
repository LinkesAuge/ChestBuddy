# DataView UI Mockup - Main View

## Overview

This document presents a comprehensive UI mockup of the refactored DataView component. Since we can't include actual images in this markdown file, we use ASCII art and detailed descriptions to represent the UI elements and their interactions.

## Main DataView Layout

The DataView will have the following primary components:

```
+----------------------------------------------------------------------+
| +------------------------------------------------------------------+ |
| | Toolbar with actions                                              | |
| +------------------------------------------------------------------+ |
| +---------------------------+ +-----------------------------------+ |
| | Filter/Search Panel       | | View Options                      | |
| +---------------------------+ +-----------------------------------+ |
| +------------------------------------------------------------------+ |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |Header|Header|Header|Header|Header|Header|Header|Header|     | | |
| | |  1   |  2   |  3   |  4   |  5   |  6   |  7   |  8   | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  A1  |  A2  |  A3  |  A4  |  A5  |  A6  |  A7  |  A8  | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  B1  |  B2  |  B3  |  B4  |  B5  |  B6  |  B7  |  B8  | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  C1  |  C2  |  C3  |  C4 ▼|  C5  |  C6  |  C7  |  C8  | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  D1  |  D2 ✗|  D3  |  D4  |  D5  |  D6  |  D7  |  D8  | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  E1  |  E2  |  E3 ✗|  E4  |  E5 ✗|  E6  |  E7  |  E8  | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| | |  ... |  ... |  ... |  ... |  ... |  ... |  ... |  ... | ... | | |
| | +------+------+------+------+------+------+------+------+-----+ | |
| +------------------------------------------------------------------+ |
| +------------------------------------------------------------------+ |
| | Status bar with information about selection and validation        | |
| +------------------------------------------------------------------+ |
+----------------------------------------------------------------------+
```

## Component Descriptions

### Toolbar

The toolbar provides quick access to common actions:

```
+----------------------------------------------------------------------+
| [Import▼] [Export▼] | [Copy] [Paste] [Delete] | [Validate] [Correct] |
+----------------------------------------------------------------------+
```

**Features:**
- Import/Export dropdown menus for file operations
- Standard editing operations (Copy, Paste, Delete)
- Validation and correction actions
- Customizable with additional actions

### Filter and Search Panel

```
+------------------------------------------+
| Search: [___________________] [🔍]       |
| Filters: [Add Filter ▼]                  |
| Applied: Column1 = "Value" [✕]           |
|          Column3 > 100      [✕]          |
+------------------------------------------+
```

**Features:**
- Search box with auto-completion
- Filter creation dropdown
- List of applied filters with ability to remove
- Support for complex filter expressions

### View Options

```
+------------------------------------------+
| Columns: [Manage Columns ▼]              |
| Group by: [None ▼]                       |
| Sort: Column1 (↑), Column3 (↓)           |
+------------------------------------------+
```

**Features:**
- Column visibility management
- Grouping options
- Sorting indicators and controls

### Data Table

```
+------+------+------+------+------+------+------+
|Header|Header|Header|Header|Header|Header|Header|
|  1   |  2   |  3   |  4   |  5   |  6   |  7   |
+------+------+------+------+------+------+------+
|  A1  |  A2  |  A3  |  A4  |  A5  |  A6  |  A7  |
+------+------+------+------+------+------+------+
|  B1  |  B2  |  B3  |  B4  |  B5  |  B6  |  B7  |
+------+------+------+------+------+------+------+
|  C1  |  C2  |  C3  |  C4 ▼|  C5  |  C6  |  C7  |
+------+------+------+------+------+------+------+
|  D1  |  D2 ✗|  D3  |  D4  |  D5  |  D6  |  D7  |
+------+------+------+------+------+------+------+
|  E1  |  E2  |  E3 ✗|  E4  |  E5 ✗|  E6  |  E7  |
+------+------+------+------+------+------+------+
```

**Features:**
- Column headers with sort indicators and resize handles
- Grid cells with data
- Validation status indicators (✗ for invalid, ▼ for correctable)
- Support for custom cell renderers based on data type
- Row and column selection

### Status Bar

```
+----------------------------------------------------------------------+
| Selected: 3 rows, 4 columns | Validation: 4 invalid cells, 1 correctable |
+----------------------------------------------------------------------+
```

**Features:**
- Information about current selection
- Summary of validation status
- Additional context-specific information

## Validation Status Visualization

The DataView will use visual cues to indicate validation status:

### Cell States

1. **Normal Cell**
   ```
   +------+
   |  A1  |
   +------+
   ```
   - Regular background color
   - Standard text formatting
   
2. **Invalid Cell**
   ```
   +------+
   |  A2 ✗ |
   +------+
   ```
   - Light red background (#ffb6b6)
   - Error icon in the corner
   - Tooltip showing validation error message
   
3. **Correctable Cell**
   ```
   +------+
   |  A3 ▼ |
   +------+
   ```
   - Light yellow background (#fff3b6)
   - Correction indicator icon
   - Tooltip showing suggested correction
   - Click on indicator shows correction options

4. **Selected Cell**
   ```
   +------+
   |[[ A4 ]]|
   +------+
   ```
   - Highlighted border
   - Different background color
   
5. **Focused Cell**
   ```
   +=======+
   || A5  ||
   +=======+
   ```
   - Bold border
   - Additional visual emphasis

### Combined States

Cells can have combined states, with the validation status indicators always visible:

```
+=======+
|| A2 ✗ ||  (Invalid + Focused)
+=======+

+------+
|[[ A3 ▼]]|  (Correctable + Selected)
+------+
```

## Color Scheme

The DataView will use the following color scheme:

- **Background Colors**:
  - Normal cell: White (#ffffff)
  - Invalid cell: Light red (#ffb6b6)
  - Correctable cell: Light yellow (#fff3b6)
  - Selected cell: Light blue (#d0e7ff)
  - Alternate row: Very light gray (#f9f9f9)

- **Text Colors**:
  - Normal text: Black (#000000)
  - Header text: Dark gray (#333333)
  - Invalid cell text: Dark red (#aa0000)
  - Correctable cell text: Dark brown (#806600)

- **Border Colors**:
  - Normal border: Light gray (#e0e0e0)
  - Selected border: Medium blue (#4a86e8)
  - Focused border: Dark blue (#2c5bb8)

## Interaction Models

### Cell Selection

- **Single-click**: Select a single cell
- **Ctrl+click**: Add/remove cell from selection
- **Shift+click**: Select range from last selected cell
- **Drag**: Select range of cells

### Cell Editing

- **Double-click**: Start editing cell in-place
- **F2**: Start editing selected cell
- **Enter**: Commit edit and move to cell below
- **Tab**: Commit edit and move to next cell
- **Escape**: Cancel edit

### Context Menu

Right-clicking on the table will show a context menu with options that depend on the selection and cell state:

```
+-------------------------+
| Copy                    |
| Paste                   |
| Delete                  |
+-------------------------+
| Edit                    |
+-------------------------+
| Add to correction list  |
| Add to validation list  |
+-------------------------+
| Apply correction        | (Only shown for correctable cells)
+-------------------------+
```

### Header Interaction

- **Click**: Sort by column (toggle ascending/descending)
- **Shift+click**: Add column to multi-sort
- **Right-click**: Show header context menu
- **Drag**: Resize column
- **Drag header**: Reorder column

## Validation Status Tooltip

When hovering over a cell with validation issues, a tooltip will appear:

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
| Validation Warning                         |
| -------------------------------------------+
| Value "JohnSmiht" could be corrected.      |
| Suggested correction: "John Smith"         |
| Column: "Player Name"                      |
| Click ▼ icon to apply correction           |
+--------------------------------------------+
```

## Responsive Behavior

The DataView will adapt to different window sizes:

- Columns will resize proportionally when the window is resized
- Horizontal and vertical scrollbars will appear when needed
- Toolbar will collapse less frequently used actions into dropdown menus on smaller screens
- Filter panel can be collapsed/expanded

## Accessibility Considerations

- High contrast mode support
- Keyboard navigation for all operations
- Screen reader support with ARIA attributes
- Focus indicators visible in all states

## Implementation Notes

- Use Qt's delegate system for custom cell rendering
- Implement custom painters for validation indicators
- Use signal/slot system for state updates
- Cache cell states to improve rendering performance 