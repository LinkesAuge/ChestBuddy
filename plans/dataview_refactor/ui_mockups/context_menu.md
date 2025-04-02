# DataView UI Mockup - Context Menu

## Overview

This document provides detailed mockups of the context menu designs for the DataView component. The context menu is a critical part of the user interaction model, providing quick access to actions based on the current selection and cell state.

## Context Menu Design Principles

1. **Context-Sensitive**: Menu content adapts based on selection and cell state
2. **Hierarchical Organization**: Actions are grouped by function
3. **Visual Clarity**: Icons and separators for easy scanning
4. **Extensibility**: Design allows for easy addition of new actions
5. **Keyboard Accessibility**: All actions have keyboard shortcuts

## Basic Context Menu (Single Cell Selection)

When a single cell is selected and right-clicked, the basic context menu appears:

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
| > Add to...               |
| > Validation              |
+---------------------------+
```

## Multi-Cell Selection Context Menu

When multiple cells are selected, the context menu adapts to show actions that can be applied to all selected cells:

```
+---------------------------+
| ✓ Copy                 C  |
| ✓ Paste                V  |
| ✓ Cut                  X  |
| ✓ Delete             Del  |
+---------------------------+
| ✓ Reset Values         R  |
+---------------------------+
| > Batch Operations        |
| > Validation              |
+---------------------------+
```

## Row Selection Context Menu

When one or more rows are selected (using row selectors), the context menu shows row-specific options:

```
+---------------------------+
| ✓ Copy Rows            C  |
| ✓ Paste Rows           V  |
| ✓ Cut Rows             X  |
| ✓ Delete Rows        Del  |
+---------------------------+
| ✓ Insert Row Above     A  |
| ✓ Insert Row Below     B  |
| ✓ Duplicate Rows       D  |
+---------------------------+
| > Batch Operations        |
| > Validation              |
+---------------------------+
```

## Column Selection Context Menu

When one or more columns are selected (using column headers), the context menu shows column-specific options:

```
+---------------------------+
| ✓ Copy Column          C  |
| ✓ Paste Column         V  |
| ✓ Hide Column          H  |
+---------------------------+
| ✓ Insert Column Left    L  |
| ✓ Insert Column Right   R  |
+---------------------------+
| ✓ Sort Ascending        A  |
| ✓ Sort Descending       D  |
| ✓ Clear Sorting         X  |
+---------------------------+
| > Filter                   |
+---------------------------+
```

## Context Menus for Special Cell States

### Invalid Cell Context Menu

When right-clicking on a cell marked as invalid, additional validation-related options appear:

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
| ! View Validation Error    |
+---------------------------+
| > Add to...               |
| > Validation              |
+---------------------------+
```

### Correctable Cell Context Menu

When right-clicking on a cell marked as correctable, correction options appear:

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
| ✓ Apply Correction     Y  |
| > View Suggested Corrections|
+---------------------------+
| > Add to...               |
| > Validation              |
+---------------------------+
```

## Submenu Details

### "Add to..." Submenu

This submenu provides options for adding the selected cell data to various lists:

```
+---------------------------+
| > Add to...               |
|   +---------------------+ |
|   | ✓ Correction List   | |
|   | ✓ Validation List   | |
|   | ✓ Exclusion List    | |
|   +---------------------+ |
+---------------------------+
```

### "Validation" Submenu

This submenu provides validation-related actions:

```
+---------------------------+
| > Validation              |
|   +---------------------+ |
|   | ✓ Validate Selected | |
|   | ✓ Validate All      | |
|   | ✓ Clear Validation  | |
|   +---------------------+ |
+---------------------------+
```

### "Batch Operations" Submenu

This submenu provides batch processing options for multiple selected cells:

```
+---------------------------+
| > Batch Operations        |
|   +---------------------+ |
|   | ✓ Fill Series       | |
|   | ✓ Fill Down         | |
|   | ✓ Clear Contents    | |
|   | ✓ Apply Format      | |
|   +---------------------+ |
+---------------------------+
```

### "View Suggested Corrections" Submenu

For correctable cells, this submenu shows available corrections:

```
+---------------------------+
| > View Suggested Corrections|
|   +---------------------+ |
|   | ✓ "John Smith"      | |
|   | ✓ "Jon Smith"       | |
|   | ✓ Add Custom...     | |
|   +---------------------+ |
+---------------------------+
```

## Cell Type-Specific Context Menu Items

The context menu can also include items specific to the data type of the selected cell:

### Date Cells

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
| ✓ Set to Today         T  |
| > Format Date             |
+---------------------------+
```

### Numeric Cells

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
| > Number Format           |
| > Calculate               |
+---------------------------+
```

## Visual Design

### Menu Item Structure

Each menu item follows this structure:

```
+---------------------------+
| Icon Label        Shortcut|
+---------------------------+
```

- **Icon**: Visual indicator of the action (16x16 pixels)
- **Label**: Text description of the action
- **Shortcut**: Keyboard shortcut, right-aligned

### Color Scheme

- **Background**: White (#ffffff)
- **Selected Item Background**: Light blue (#d0e7ff)
- **Text**: Black (#000000)
- **Disabled Text**: Gray (#888888)
- **Separator**: Light gray (#e0e0e0)

### Icons

Standard icons will be used for common actions:

- **Copy**: Clipboard icon
- **Paste**: Clipboard with paper icon
- **Cut**: Scissors icon
- **Delete**: Trash can icon
- **Edit**: Pencil icon
- **Validation**: Checkmark icon
- **Correction**: Magic wand icon

## Interaction Models

### Keyboard Interaction

- **Arrow Keys**: Navigate through menu items
- **Enter/Space**: Activate selected item
- **Escape**: Close menu
- **Right Arrow**: Open submenu
- **Left Arrow**: Close submenu
- **Shortcut Key**: Directly activate item

### Mouse Interaction

- **Click**: Activate item
- **Hover**: Highlight item
- **Right-click**: Close menu
- **Hover over submenu item**: Open submenu

## Accessibility Considerations

- All menu items will have appropriate ARIA roles and labels
- Keyboard navigation for all menu operations
- Color contrast will meet WCAG 2.0 AA standards
- Tooltips will be available for all menu items

## Implementation Notes

1. Use Qt's QMenu and QAction system for menu creation
2. Create a MenuFactory class to generate context-sensitive menus
3. Implement a plugin system for extending the menu with custom actions
4. Use signals and slots to connect menu actions to their handlers
5. Support right-to-left languages with appropriate menu layout

## Future Enhancements

1. User-customizable menu items
2. Context-sensitive icons that change based on cell state
3. Recent actions section for frequently used operations
4. Expandable/collapsible groups for complex menus 