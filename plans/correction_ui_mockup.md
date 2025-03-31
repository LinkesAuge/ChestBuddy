# Correction System UI Mockup

## Overview

This mockup illustrates the updated user interface components for the improved correction system in ChestBuddy. The improvements include enhanced settings options, better data view integration, and an improved correction view.

## Settings Panel

The settings panel will include a new section for correction settings:

```
+------------------------------------------+
| Settings                                 |
+------------------------------------------+
| ┌─ Validation Settings ─────────────────┐|
| │                                      │|
| │ [✓] Validate on import               │|
| │ [✓] Mark duplicates as invalid       │|
| │ [ ] Clear validation on file change   │|
| │                                      │|
| └──────────────────────────────────────┘|
|                                          |
| ┌─ Correction Settings ───────────────┐  |
| │                                    │  |
| │ [✓] Auto-correct on validation     │  |
| │ [✓] Auto-correct on import         │  |
| │ [ ] Apply corrections recursively   │  |
| │ [ ] Auto-save after corrections     │  |
| │                                    │  |
| └────────────────────────────────────┘  |
|                                          |
| ┌─ Display Settings ──────────────────┐  |
| │                                    │  |
| │ [✓] Show validation indicators     │  |
| │ [✓] Show correction indicators     │  |
| │ [ ] Highlight corrected cells      │  |
| │                                    │  |
| └────────────────────────────────────┘  |
|                                          |
|                   [Cancel] [Apply] [OK]  |
+------------------------------------------+
```

## Data View Integration

The data view will include enhanced cell highlighting and context menu options:

```
+----------------------------------------------------------+
| Data View                                                |
+----------------------------------------------------------+
| ┌─ Color Legend ──────────────────────────────────────┐  |
| │                                                     │  |
| │ ■ Valid                                            │  |
| │ ■ Invalid                                          │  |
| │ ■ Invalid (correctable)                            │  |
| │ ■ Corrected                                        │  |
| │                                                     │  |
| └─────────────────────────────────────────────────────┘  |
|                                                          |
| +--------+------------+------------+-----------+-------+ |
| | Date   | Player     | Source     | ChestType | Score | |
| +--------+------------+------------+-----------+-------+ |
| | Jan 1  | Player1    | Source1    | Gold      | 100   | |
| +--------+------------+------------+-----------+-------+ |
| | Jan 2  | InvldPlyr  | Source2    | Silver    | 200   | |
| +--------+------------+------------+-----------+-------+ |
| | Jan 3  | Player3    | InvldSrc   | Bronze    | 300   | |
| +--------+------------+------------+-----------+-------+ |
|                                                          |
| +---------- Context Menu ----------+                     |
| | Apply corrections                |                     |
| | Apply selected rule...           |                     |
| | -------------------------        |                     |
| | Create correction rule           |                     |
| | View validation details          |                     |
| | -------------------------        |                     |
| | Copy                             |                     |
| | Paste                            |                     |
| | Reset cell                       |                     |
| +--------------------------------- +                     |
|                                                          |
| Status: Invalid: 10, Correctable: 5, Corrected: 0        |
+----------------------------------------------------------+
```

## Correction View

The correction view will be enhanced with a correctable count column and improved rule management:

```
+----------------------------------------------------------+
| Correction View                                           |
+----------------------------------------------------------+
| [ Import ] [ Export ] [ Add Rule ] [ Delete ]             |
|                                                          |
| ┌─ Correction Rules ────────────────────────────────────┐|
| │                                                      │|
| │ +--------+--------+----------+--------+------------+ │|
| │ | From   | To     | Category | Status | Correctable| │|
| │ +--------+--------+----------+--------+------------+ │|
| │ | InvldP | Player | Player   | ✓      | 5          | │|
| │ +--------+--------+----------+--------+------------+ │|
| │ | InvldS | Source | Source   | ✓      | 3          | │|
| │ +--------+--------+----------+--------+------------+ │|
| │ | BadVal | Good   | General  | ✓      | 0          | │|
| │ +--------+--------+----------+--------+------------+ │|
| │                                                      │|
| └──────────────────────────────────────────────────────┘|
|                                                          |
| ┌─ Preview ────────────────────────────────────────────┐|
| │                                                      │|
| │ The selected rule will affect 5 cells:              │|
| │                                                      │|
| │ - Row 2, Player: "InvldPlyr" → "Player"             │|
| │ - Row 5, Player: "InvldPlyr" → "Player"             │|
| │ - Row 8, Player: "InvldPlyr" → "Player"             │|
| │ - Row 12, Player: "InvldPlyr" → "Player"            │|
| │ - Row 15, Player: "InvldPlyr" → "Player"            │|
| │                                                      │|
| └──────────────────────────────────────────────────────┘|
|                                                          |
| [ Apply Selected ] [ Apply All ] [ Apply to Invalid Only ]|
|                                                          |
| Status: Total: 3 | Enabled: 3 | Disabled: 0              |
+----------------------------------------------------------+
```

## Rule Editor Dialog

The rule editor dialog will include improved validation:

```
+----------------------------------------------------------+
| Edit Correction Rule                                      |
+----------------------------------------------------------+
|                                                          |
| From Value:  [InvldPlyr_________________________]        |
|              (The value to be corrected)                 |
|                                                          |
| To Value:    [Player___________________________]         |
|              (The corrected value)                       |
|                                                          |
| Category:    [Player▼_________________________]         |
|              (General, Player, Source, ChestType)        |
|                                                          |
| Status:      [✓] Enabled                                |
|                                                          |
| ┌─ Validation ────────────────────────────────────────┐  |
| │                                                    │  |
| │ This rule will correct 5 cells in the current data │  |
| │                                                    │  |
| │ No conflicts detected with other rules             │  |
| │                                                    │  |
| └────────────────────────────────────────────────────┘  |
|                                                          |
|                             [Cancel] [Apply] [Save Rule] |
+----------------------------------------------------------+
```

## Import/Export Dialog

The enhanced import/export dialog will include format options and preview:

```
+----------------------------------------------------------+
| Import/Export Correction Rules                           |
+----------------------------------------------------------+
|                                                          |
| Operation:  (•) Import  ( ) Export                       |
|                                                          |
| File:       [C:\Users\...\rules.csv___________] [Browse] |
|                                                          |
| Format:     [CSV▼_________________________]              |
|             (CSV, Excel, JSON)                           |
|                                                          |
| Options:    [✓] Replace existing rules                  |
|             [✓] Validate rules on import                |
|             [ ] Auto-enable imported rules               |
|                                                          |
| ┌─ Preview ────────────────────────────────────────────┐|
| │                                                      │|
| │ From     | To       | Category | Status              │|
| │ ---------+----------+----------+-------------------- │|
| │ InvldPlyr| Player   | Player   | Enabled             │|
| │ InvldSrc | Source   | Source   | Enabled             │|
| │ BadVal   | Good     | General  | Enabled             │|
| │                                                      │|
| │ 3 rules will be imported                             │|
| │                                                      │|
| └──────────────────────────────────────────────────────┘|
|                                                          |
|                                      [Cancel] [Import]   |
+----------------------------------------------------------+
```

## Status Bar Integration

The status bar will include correction information:

```
+----------------------------------------------------------+
| Main Window                                              |
+----------------------------------------------------------+
| [File] [Edit] [View] [Tools] [Help]                      |
|                                                          |
| +--- Navigation ---+  +---------------------------+      |
| | Dashboard        |  |                          |      |
| | Data             |  |       Content Area       |      |
| | Validation       |  |                          |      |
| | Correction       |  |                          |      |
| | Charts           |  |                          |      |
| | Settings         |  |                          |      |
| +-----------------+  +---------------------------+      |
|                                                          |
| Status: Data loaded: 12,387 rows | Invalid: 10 | Correctable: 5 |
+----------------------------------------------------------+
```

## Workflow Visualization

This diagram illustrates the integration of the correction system with the data import and validation workflow:

```
                  +---------------+
                  |  Import Data  |
                  +-------+-------+
                          |
                          v
           +-------------+--------------+
           |  Check Correctable Status  |
           +-------------+--------------+
                          |
                          v
           +--------------+-------------+    No     +---------------+
           | Auto-Validation Enabled?   +---------->|   User Loads  |
           +--------------+-------------+           |     Data      |
                          | Yes                     +-------+-------+
                          v                                 |
          +---------------+---------------+                 |
          |      Validate Data            |<----------------+
          +---------------+---------------+
                          |
                          v
          +---------------+---------------+    No
          | Auto-Correction on Validation?+------------+
          +---------------+---------------+            |
                          | Yes                        |
                          v                            |
          +---------------+---------------+            |
          |     Apply Corrections         |            |
          |     (only_invalid=True)       |            |
          +-------------------------------+            |
                                                       |
                                                       v
                                         +-------------+-------------+
                                         |      User Interaction     |
                                         +-------------------------+-+
                                                                   |
                                          +----------------------+ |
                                          | Apply Corrections    |<+
                                          +----------------------+
```

## Cell Status Color Legend

The colors used for cell status in the DataView:

| Status                | Color      | Hex Code | Description                       |
|-----------------------|------------|----------|-----------------------------------|
| Valid                 | Light Green| #C8E6C9  | Cell passes validation           |
| Invalid               | Light Red  | #FFCDD2  | Cell fails validation            |
| Invalid (correctable) | Orange     | #FFE0B2  | Cell is invalid but can be fixed |
| Corrected             | Blue-green | #B2DFDB  | Cell was corrected               |

## Mobile Responsiveness

On smaller screens, the layout will adapt:

- Settings panel will use accordions for sections
- Data view will have horizontal scrolling
- Preview section will be collapsible
- Rule editor will use a simplified view

## Accessibility Considerations

- All colors meet WCAG 2.1 AA contrast requirements
- Keyboard navigation is fully supported
- Screen reader support with ARIA labels
- Focus indicators for all interactive elements 