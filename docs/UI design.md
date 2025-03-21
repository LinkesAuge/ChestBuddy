# ChestBuddy UI Design

## Overall Layout

```
┌────────────────────────────────────────────────────────────────────┐
│                        ChestBuddy Application                       │
├────────────┬───────────────────────────────────────────────────────┤
│            │                                                       │
│            │                                                       │
│            │                                                       │
│  Navigation│                  Main Content Area                    │
│    Bar     │                                                       │
│            │                                                       │
│            │                                                       │
│            │                                                       │
├────────────┴───────────────────────────────────────────────────────┤
│                             Status Bar                             │
└────────────────────────────────────────────────────────────────────┘
```

## Navigation Bar (Left Side)

```
┌────────────┐
│ ChestBuddy │
│   (Logo)   │
├────────────┤
│ Dashboard  │
├────────────┤
│ Data       │
│  - Import  │
│  - Validate│
│  - Correct │
│  - Export  │
├────────────┤
│ Analysis   │
│  - Tables  │
│  - Charts  │
├────────────┤
│ Reports    │
├────────────┤
│ Settings   │
│  - Lists   │
│  - Rules   │
│  - Prefs   │
├────────────┤
│            │
│            │
│            │
│            │
│            │
│            │
├────────────┤
│ Help       │
└────────────┘
```

## Detailed Section Designs

### 1. Dashboard View

```
┌────────────────────────────────────────────────────────────────────┐
│ Dashboard                                                    ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │ Current     │ │ Validation  │ │ Correction  │ │ Last        │    │
│ │ Dataset     │ │ Status      │ │ Status      │ │ Import      │    │
│ │ 2,345 rows  │ │ 95% valid   │ │ 87 corrected│ │ 2023-03-21  │    │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                                     │
│ ┌─────────────────────────┐      ┌─────────────────────────┐       │
│ │ Recent Files            │      │ Top Players             │       │
│ │                         │      │                         │       │
│ │ - March_Chests.csv      │      │ [Bar Chart Preview]     │       │
│ │ - February_Chests.csv   │      │                         │       │
│ │ - January_Chests.csv    │      │                         │       │
│ └─────────────────────────┘      └─────────────────────────┘       │
│                                                                     │
│ ┌─────────────────────────┐      ┌─────────────────────────┐       │
│ │ Top Chest Sources       │      │ Quick Actions           │       │
│ │                         │      │                         │       │
│ │ [Pie Chart Preview]     │      │ [Import] [Validate]     │       │
│ │                         │      │ [Analyze] [Generate     │       │
│ │                         │      │           Report]       │       │
│ └─────────────────────────┘      └─────────────────────────┘       │
└────────────────────────────────────────────────────────────────────┘
```

### 2. Data Management - Import View

```
┌────────────────────────────────────────────────────────────────────┐
│ Data Management > Import                                     ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ ┌───────────────────────────┐  │
│ │ Import Settings                 │ │ File Preview              │  │
│ │                                 │ │                           │  │
│ │ File: [Browse...] file.csv      │ │ ┌───┬────────┬─────────┐  │  │
│ │                                 │ │ │Date│Player  │Location │  │  │
│ │ Encoding: [Auto-detect ▼]       │ │ ├───┼────────┼─────────┤  │  │
│ │                                 │ │ │3/21│Feldjäg│Crypt L25│  │  │
│ │ Delimiter: [Comma ▼]            │ │ │3/21│User2  │Castle   │  │  │
│ │                                 │ │ │3/22│User3  │Mine     │  │  │
│ │ Has Header: [✓]                 │ │ └───┴────────┴─────────┘  │  │
│ │                                 │ │                           │  │
│ │ Date Format: [YYYY-MM-DD ▼]     │ │ File Status:              │  │
│ │                                 │ │ Valid CSV, 248 rows       │  │
│ │ Skip Rows: [0]                  │ │ Encoding: UTF-8           │  │
│ │                                 │ │                           │  │
│ │ Options:                        │ │ Column Mapping:           │  │
│ │ [✓] Auto-validate after import  │ │ Date: [Date ▼]            │  │
│ │ [✓] Auto-correct common errors  │ │ Player: [Player Name ▼]   │  │
│ │ [ ] Replace current dataset     │ │ Source: [Source/Loc ▼]    │  │
│ │ [✓] Remember settings           │ │ Chest: [Chest Type ▼]     │  │
│ │                                 │ │ Value: [Value ▼]          │  │
│ └─────────────────────────────────┘ └───────────────────────────┘  │
│                                                                     │
│ [Cancel]                [Import Preview]              [Import Now]  │
└────────────────────────────────────────────────────────────────────┘
```

### 3. Data Management - Validation View

```
┌────────────────────────────────────────────────────────────────────┐
│ Data Management > Validate                                   ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Validation Controls                                             │ │
│ │ [✓] Players   [✓] Chest Types   [✓] Locations   [ ] Values     │ │
│ │                                                                 │ │
│ │ Match Type: [Exact ▼]  [Validate Selected]  [Validate All]     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Data Table                                              Filter ▼│ │
│ │ ┌────┬──────┬────────────┬────────────┬────────┬────────────┐  │ │
│ │ │Date │Player│Source/Loc  │Chest Type  │Value   │Status      │  │ │
│ │ ├────┼──────┼────────────┼────────────┼────────┼────────────┤  │ │
│ │ │3/21 │User1 │Crypt L25   │Fire Chest  │275     │✓           │  │ │
│ │ │3/21 │User2 │Castle      │Wood Chest  │150     │✓           │  │ │
│ │ │3/22 │Usre3 │Mine L15    │Stone Chest │125     │❌ Player    │  │ │
│ │ │3/22 │User4 │Forst       │Gold Chest  │350     │❌ Location  │  │ │
│ │ │3/23 │User5 │Tower       │Chest Type? │200     │❌ Chest Type│  │ │
│ │ └────┴──────┴────────────┴────────────┴────────┴────────────┘  │ │
│ │                                                                 │ │
│ │ Showing rows 1-5 of 248                      [< 1 2 3 ... >]   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│ │ Validation Summary          │   │ Quick Corrections           │  │
│ │                             │   │                             │  │
│ │ Total Entries: 248          │   │ Player "Usre3" → "User3"    │  │
│ │ Valid: 203 (81.9%)          │   │ [Apply]                     │  │
│ │ Invalid Players: 12         │   │                             │  │
│ │ Invalid Locations: 18       │   │ Location "Forst" → "Forest" │  │
│ │ Invalid Chest Types: 15     │   │ [Apply]                     │  │
│ │                             │   │                             │  │
│ │ [View Detailed Report]      │   │ [View All Suggestions]      │  │
│ └─────────────────────────────┘   └─────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 4. Data Management - Correction View

```
┌────────────────────────────────────────────────────────────────────┐
│ Data Management > Correction                                 ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Correction Rules                                                │ │
│ │ Category: [All Categories ▼]   [Apply Selected]  [Apply All]    │ │
│ │                                                                 │ │
│ │ ┌────┬──────────┬──────────────┬──────────┬────────┐           │ │
│ │ │    │From      │To            │Category  │Enabled │           │ │
│ │ ├────┼──────────┼──────────────┼──────────┼────────┤           │ │
│ │ │[✓] │Usre      │User          │Player    │✓       │           │ │
│ │ │[✓] │Forst     │Forest        │Location  │✓       │           │ │
│ │ │[✓] │Feldjager │Feldjäger     │Player    │✓       │           │ │
│ │ │[✓] │FireChest │Fire Chest    │Chest     │✓       │           │ │
│ │ └────┴──────────┴──────────────┴──────────┴────────┘           │ │
│ │                                                                 │ │
│ │ [Add Rule]  [Edit Rule]  [Delete Rule]  [Import/Export Rules]  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Data Preview                                           Filter ▼ │ │
│ │ ┌────┬──────┬────────────┬────────────┬────────┬────────────┐  │ │
│ │ │Date │Player│Source/Loc  │Chest Type  │Value   │Changes     │  │ │
│ │ ├────┼──────┼────────────┼────────────┼────────┼────────────┤  │ │
│ │ │3/21 │User1 │Crypt L25   │Fire Chest  │275     │None        │  │ │
│ │ │3/22 │Usre3 │Mine L15    │Stone Chest │125     │Usre3→User3 │  │ │
│ │ │3/22 │User4 │Forst       │Gold Chest  │350     │Forst→Forest│  │ │
│ │ │3/23 │User5 │Tower       │FireChest   │200     │FireChest→..│  │ │
│ │ └────┴──────┴────────────┴────────────┴────────┴────────────┘  │ │
│ │                                                                 │ │
│ │ [Undo Last]  [Redo]                           [Apply Changes]  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### 5. Analysis - Data Table View

```
┌────────────────────────────────────────────────────────────────────┐
│ Analysis > Data Table                                        ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Filters & Controls                                              │ │
│ │                                                                 │ │
│ │ Date Range: [2023-03-01] to [2023-03-31]                       │ │
│ │                                                                 │ │
│ │ Players: [All ▼]  Locations: [All ▼]  Chest Types: [All ▼]     │ │
│ │                                                                 │ │
│ │ Min Value: [0]    Max Value: [1000]    [Apply Filters]         │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Data Table                            Search: [____________]    │ │
│ │ ┌────┬──────┬────────────┬────────────┬────────┬────────────┐  │ │
│ │ │Date │Player│Source/Loc  │Chest Type  │Value   │Clan        │  │ │
│ │ ├────┼──────┼────────────┼────────────┼────────┼────────────┤  │ │
│ │ │3/21 │User1 │Crypt L25   │Fire Chest  │275     │Alliance1   │  │ │
│ │ │3/21 │User2 │Castle      │Wood Chest  │150     │Alliance1   │  │ │
│ │ │3/22 │User3 │Mine L15    │Stone Chest │125     │Alliance2   │  │ │
│ │ │3/22 │User4 │Forest      │Gold Chest  │350     │Alliance1   │  │ │
│ │ │3/23 │User5 │Tower       │Fire Chest  │200     │Alliance2   │  │ │
│ │ └────┴──────┴────────────┴────────────┴────────┴────────────┘  │ │
│ │                                                                 │ │
│ │ Showing 5 of 248 entries                     [< 1 2 3 ... >]   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│ │ Summary Statistics          │   │ Actions                     │  │
│ │                             │   │                             │  │
│ │ Total Entries: 248          │   │ [Export to CSV]             │  │
│ │ Total Value: 54,370         │   │ [Create Chart]              │  │
│ │ Average Value: 219.2        │   │ [Generate Report]           │  │
│ │ Players: 32                 │   │ [Save Filter]               │  │
│ │ Chest Types: 8              │   │                             │  │
│ │ Top Location: Forest (42)   │   │                             │  │
│ └─────────────────────────────┘   └─────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 6. Analysis - Charts View

```
┌────────────────────────────────────────────────────────────────────┐
│ Analysis > Charts                                           ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│ │ Chart Controls              │   │ Chart Display               │  │
│ │                             │   │                             │  │
│ │ Chart Type: [Bar Chart ▼]   │   │                             │  │
│ │                             │   │                             │  │
│ │ Data Selection:             │   │     [Visualization Area]    │  │
│ │ X-Axis: [Player ▼]          │   │                             │  │
│ │ Y-Axis: [Value ▼]           │   │                             │  │
│ │ Group By: [Chest Type ▼]    │   │                             │  │
│ │                             │   │                             │  │
│ │ Filters:                    │   │                             │  │
│ │ Date: [Last 30 Days ▼]      │   │                             │  │
│ │ Min Value: [0]              │   │                             │  │
│ │ Chest Types: [All ▼]        │   │                             │  │
│ │                             │   │                             │  │
│ │ Chart Options:              │   │                             │  │
│ │ Title: [Player Values by    │   │                             │  │
│ │        Chest Type]          │   │                             │  │
│ │ [✓] Show Legend            │   │                             │  │
│ │ [✓] Show Values            │   │                             │  │
│ │ [ ] 3D View                │   │                             │  │
│ │ Color Scheme: [Default ▼]   │   │                             │  │
│ │                             │   │                             │  │
│ │ [Generate Chart]            │   │ [Save Image]  [Add to Report] │
│ └─────────────────────────────┘   └─────────────────────────────┘  │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Saved Charts                                                    │ │
│ │                                                                 │ │
│ │ [Player Performance]  [Chest Type Values]  [Location Analysis]  │ │
│ │                                                                 │ │
│ │ [Create New Collection]           [Manage Chart Collections]    │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### 7. Reports View

```
┌────────────────────────────────────────────────────────────────────┐
│ Reports                                                      ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│ │ Report Builder              │   │ Preview                     │  │
│ │                             │   │                             │  │
│ │ Template: [Standard ▼]      │   │                             │  │
│ │ Title: [Monthly Chest Report]   │                             │  │
│ │                             │   │     [Report Preview]        │  │
│ │ Sections:                   │   │                             │  │
│ │ [✓] Cover Page             │   │                             │  │
│ │ [✓] Executive Summary      │   │                             │  │
│ │ [✓] Player Analysis        │   │                             │  │
│ │ [✓] Chest Type Analysis    │   │                             │  │
│ │ [✓] Location Analysis      │   │                             │  │
│ │ [ ] Alliance Comparison    │   │                             │  │
│ │ [✓] Data Tables            │   │                             │  │
│ │                             │   │                             │  │
│ │ Include Charts:             │   │                             │  │
│ │ [✓] Top Players            │   │                             │  │
│ │ [✓] Chest Type Distribution│   │                             │  │
│ │ [✓] Value by Location      │   │                             │  │
│ │ [ ] Time Trends            │   │                             │  │
│ │                             │   │                             │  │
│ │ Theme: [Total Battle ▼]     │   │                             │  │
│ │                             │   │                             │  │
│ │ [Generate Report]           │   │ [Export HTML]  [Export PDF]   │
│ └─────────────────────────────┘   └─────────────────────────────┘  │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Saved Reports                                                   │ │
│ │                                                                 │ │
│ │ [Mar 2023 Report]  [Feb 2023 Report]  [Player Performance Q1]  │ │
│ │                                                                 │ │
│ │ [Manage Reports]                                                │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### 8. Settings - Validation Lists

```
┌────────────────────────────────────────────────────────────────────┐
│ Settings > Validation Lists                                  ⚙️ ❓ │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│ │ List Management             │   │ List Editor                 │  │
│ │                             │   │                             │  │
│ │ List Type: [Players ▼]      │   │ Player Names:               │  │
│ │                             │   │ ┌─────────────────────────┐ │  │
│ │ Active List: [Default ▼]    │   │ │User1                    │ │  │
│ │                             │   │ │User2                    │ │  │
│ │ List Actions:               │   │ │User3                    │ │  │
│ │ [New List]                  │   │ │User4                    │ │  │
│ │ [Import List]               │   │ │User5                    │ │  │
│ │ [Export List]               │   │ │Feldjäger                │ │  │
│ │ [Delete List]               │   │ │                         │ │  │
│ │                             │   │ │                         │ │  │
│ │ Validation Settings:        │   │ │                         │ │  │
│ │ [✓] Case Sensitive         │   │ └─────────────────────────┘ │  │
│ │ [ ] Allow Partial Matches  │   │                             │  │
│ │ [✓] Suggest Corrections    │   │ [Add]  [Edit]  [Remove]      │  │
│ │                             │   │                             │  │
│ │ [✓] Auto-update on import  │   │ Search: [____________]      │  │
│ │                             │   │                             │  │
│ │ [Apply Settings]            │   │ [Save Changes]              │  │
│ └─────────────────────────────┘   └─────────────────────────────┘  │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Validation Statistics                                           │ │
│ │                                                                 │ │
│ │ Players: 32 entries                                             │ │
│ │ Chest Types: 8 entries                                          │ │
│ │ Locations: 15 entries                                           │ │
│ │                                                                 │ │
│ │ Last Updated: 2023-03-21                                        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## Design Notes

### Color Scheme
- Primary: Dark blue (#1A2C42)
- Secondary: Gold (#D4AF37)
- Accent: Light blue (#4A90E2)
- Success: Green (#28A745)
- Error: Red (#DC3545)
- Background: Dark gray (#2D3748)
- Text: White (#FFFFFF) and light gray (#E2E8F0)

### Typography
- Primary font: Roboto or Open Sans
- Header size: 18-24px
- Body text: 14-16px
- Data tables: 14px
- Use bold for headers and important information

### Navigation Behavior
- Collapsible navigation for more workspace
- Visual highlighting for current section
- Expandable sub-sections
- Keyboard shortcuts for power users

### Responsive Design
- Adjustable panels with splitters
- Collapsible sections for small screens
- Consistent minimum widths for usability
- Scrollable areas for larger datasets

### Workflow Guidance
- Clear step-by-step workflow
- Visual progress indicators
- Contextual help tooltips
- Status messages in the status bar 