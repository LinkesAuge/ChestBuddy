# Correction Feature UI Mockup

## 1. Correction View

The main Correction View is designed to manage correction rules and apply them to data. It follows the application's standard layout pattern with a header area and content area.

```
+-------------------------------------------------------------------+
|                           HEADER                                   |
|  [Correction Rules]                   [Import] [Export] [Apply]    |
+-------------------------------------------------------------------+
|                                                                    |
|  +-------------------------------------------------------------+   |
|  |                     FILTER CONTROLS                         |   |
|  |  Category: [All ▼]  Status: [All ▼]  Search: [          ]  |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
|  +-------------------------------------------------------------+   |
|  |                       RULES TABLE                           |   |
|  | +-------+----------+------------+----------+---------+---+ |   |
|  | | Order |   From   |     To     | Category | Status  | ⋮ | |   |
|  | +-------+----------+------------+----------+---------+---+ |   |
|  | |   1   | "Cheist" |  "Chest"   | general  | enabled | ⋮ | |   |
|  | |   2   | "PLyer"  |  "Player"  |  player  | enabled | ⋮ | |   |
|  | |   3   | "Wepon"  |  "Weapon"  |   chest  | enabled | ⋮ | |   |
|  | |   4   | "Sorce"  |  "Source"  |  source  | disabled| ⋮ | |   |
|  | |   5   | "Chst"   |  "Chest"   | general  | enabled | ⋮ | |   |
|  | +-------+----------+------------+----------+---------+---+ |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
|  +-------------------------------------------------------------+   |
|  |                     RULE CONTROLS                           |   |
|  |    [Add]  [Edit]  [Delete]  [Move ▲]  [Move ▼]             |   |
|  |    [Move to Top]  [Move to Bottom]  [Toggle Status]         |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
|  +-------------------------------------------------------------+   |
|  |                     SETTINGS PANEL                          |   |
|  |  [✓] Auto-correct after validation                          |   |
|  |  [✓] Correct only invalid entries                           |   |
|  |  [✓] Auto-enable imported rules                             |   |
|  |  [✓] Export only enabled rules                              |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
+-------------------------------------------------------------------+
|                          STATUS BAR                               |
| Total rules: 5 | Enabled: 4 | Disabled: 1                         |
+-------------------------------------------------------------------+
```

### Context Menu for Rules Table

When right-clicking on a rule in the table, a context menu appears with options:

```
+-------------------+
| Edit              |
| Delete            |
| ----------------  |
| Move Up           |
| Move Down         |
| Move to Top       |
| Move to Bottom    |
| ----------------  |
| Enable/Disable    |
+-------------------+
```

## 2. Add/Edit Rule Dialog

Dialog for adding or editing a single correction rule.

```
+---------------------------------------------------+
|              Add/Edit Correction Rule             |
+---------------------------------------------------+
|                                                   |
|  From value:  [                              ]    |
|                                                   |
|  To value:    [                              ]    |
|                                                   |
|  Category:    [Select Category ▼]                 |
|               (general, player, chest_type,       |
|                source)                            |
|                                                   |
|  Status:      (●) Enabled  ( ) Disabled           |
|                                                   |
|  Order:       [   0   ]                           |
|                                                   |
|                                                   |
|  [Add to Validation List]                         |
|                                                   |
|                                                   |
|           [Cancel]        [Save]                  |
|                                                   |
+---------------------------------------------------+
```

## 3. Batch Correction Dialog

Dialog for creating multiple correction rules at once from selected cells.

```
+-------------------------------------------------------------------+
|                     Batch Correction Rules                         |
+-------------------------------------------------------------------+
|                                                                    |
|  Selected values to correct:                                       |
|                                                                    |
|  +-------------------------------------------------------------+   |
|  | Original Value | Column       | Correct To  | Category      |   |
|  +---------------+--------------+------------+--------------+   |
|  | "Plyer"       | player       | [       ▼] | [player    ▼]   |   |
|  | "Chest tipe"  | chest_type   | [       ▼] | [chest_type▼]   |   |
|  | "sorce"       | source       | [       ▼] | [source    ▼]   |   |
|  | "shiel"       | chest_type   | [       ▼] | [chest_type▼]   |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
|  Global options:                                                   |
|  [✓] Auto-enable all rules                                         |
|  [✓] Add new values to validation lists                            |
|                                                                    |
|                                                                    |
|                [Cancel]        [Create Rules]                      |
|                                                                    |
+-------------------------------------------------------------------+
```

## 4. Progress Dialog

Dialog showing progress when applying corrections.

```
+---------------------------------------------------+
|              Applying Corrections                 |
+---------------------------------------------------+
|                                                   |
|  Status: Processing rule 2 of 5...                |
|                                                   |
|  [====================>                  ] 43%    |
|                                                   |
|  Details: Correcting "PLyer" to "Player"          |
|                                                   |
|                                                   |
|                  [Cancel]                         |
|                                                   |
+---------------------------------------------------+
```

## 5. Data View Integration

The data view will show color-coded highlighting for cells:

```
+-------------------------------------------------------------------+
|                         Data View                                  |
+-------------------------------------------------------------------+
|                                                                    |
|  +-------------------------------------------------------------+   |
|  |          |  Player      |  Chest Type  |  Source     | ...  |   |
|  +----------+--------------+--------------+-------------+------+   |
|  | Row 1    |  Player      |  Weapon      |  Dungeon    | ...  |   |
|  | Row 2    |  Player      |  Shield      |  Sorce      | ...  |   |
|  | Row 3    |  PLyer       |  Weapon      |  Cave       | ...  |   |
|  | Row 4    |  John        |  Chest tipe  |  Source     | ...  |   |
|  | Row 5    |  Player      |  Shield      |  Source     | ...  |   |
|  +-------------------------------------------------------------+   |
|                                                                    |
+-------------------------------------------------------------------+

Color Legend:
- Red cells: Invalid without correction rule (e.g., "Chest tipe")
- Orange cells: Invalid with available correction rule (e.g., "PLyer") 
- Green cells: Already corrected (not shown in example)
- Purple cells: Correctable but not invalid (e.g., "Sorce")
```

### Data View Context Menu

When right-clicking on selected cells, a context menu appears:

```
+-------------------------------+
| Copy                          |
| Paste                         |
| ---------------------------   |
| Add Correction Rule           |
| Create Batch Correction Rules |
| ---------------------------   |
| Validate Selection            |
+-------------------------------+
```

## 6. Tooltips

Tooltips will appear when hovering over cells in the data view:

- For invalid cells with correction rule:
  ```
  Invalid: "PLyer"
  Can be corrected to: "Player"
  ```

- For corrected cells:
  ```
  Corrected from "Sorce" to "Source"
  ```

- For correctable cells (not invalid):
  ```
  Can be corrected from "Sorce" to "Source"
  ```

## 7. Color Coding Legend

A small legend will be visible in the data view:

```
+----------------------------------+
|  Color Legend:                   |
|  ● Red: Invalid                  |
|  ● Orange: Invalid (correctable) |
|  ● Green: Corrected              |
|  ● Purple: Correctable           |
+----------------------------------+
```

## 8. Import/Export Dialog

Dialog for importing correction rules with options:

```
+---------------------------------------------------+
|              Import Correction Rules              |
+---------------------------------------------------+
|                                                   |
|  File: [/path/to/rules.csv               ] [...]  |
|                                                   |
|  Options:                                         |
|                                                   |
|  ( ) Replace existing rules                       |
|  (●) Append to existing rules                     |
|                                                   |
|  [✓] Auto-enable imported rules                   |
|                                                   |
|  Encoding: [UTF-8 ▼]                              |
|                                                   |
|                                                   |
|          [Cancel]        [Import]                 |
|                                                   |
+---------------------------------------------------+
```

Export dialog will be similar, with options to export only enabled rules. 