# ChestBuddy UI/UX Documentation

## 1. Application Structure

The ChestBuddy application follows a two-panel layout structure:

### Main Layout
- **Left Panel**: Dark-themed sidebar navigation (#333333)
- **Right Panel**: Content area with slightly lighter background (#2D3748)
- **Content Organization**: Tab-based interface for different functional areas

### Navigation Flow
- Sidebar provides access to main application sections
- Active section is highlighted with a gold accent bar (#D4AF37)
- Content area displays the active section's interface
- Status bar at bottom provides feedback and application state information

## 2. Design System

### 2.1 Color Palette

#### Primary Colors
- **PRIMARY**: #1A2C42 (Dark blue) - Main application color
- **PRIMARY_DARK**: #0F1A2A (Darker blue) - For active states and headers
- **PRIMARY_LIGHT**: #263D5A (Lighter blue) - For hover states and secondary elements
- **SECONDARY**: #D4AF37 (Gold) - Accent color for highlights and important elements

#### Background Colors
- **DARK_CONTENT_BG**: #2D3748 (Dark gray) - Content area background
- **BG_DARK**: #2D3748 (Dark gray) - Alternative dark background
- **BG_MEDIUM**: #4A5568 (Medium gray) - Medium darkness background
- **BG_LIGHT**: #718096 (Light gray) - Lighter background for contrast
- **SIDEBAR_BG**: #333333 (Dark gray) - Sidebar specific background

#### Text Colors
- **TEXT_LIGHT**: #FFFFFF (White) - Primary text on dark backgrounds
- **TEXT_MUTED**: #E2E8F0 (Light gray) - Secondary text on dark backgrounds
- **TEXT_DISABLED**: #889EB8 (Muted blue-gray) - Disabled text
- **TEXT_PRIMARY**: #2D3748 (Dark gray) - Main text color
- **TEXT_SECONDARY**: #718096 (Medium gray) - Secondary text color

#### State Colors
- **SUCCESS**: #28A745 (Green) - Success states and indicators
- **ERROR**: #DC3545 (Red) - Error states and indicators
- **WARNING**: #FFC107 (Amber/Yellow) - Warning states and indicators
- **INFO**: #17A2B8 (Cyan) - Information states and indicators
- **DISABLED**: #4A5568 (Gray) - Disabled states

#### Border Colors
- **BORDER**: #CBD5E0 - Standard border
- **BORDER_LIGHT**: #E2E8F0 - Light border
- **BORDER_DARK**: #2D3748 - Dark gray border
- **DARK_BORDER**: #4A5568 - Border for dark theme elements

### 2.2 Typography

- **Primary Font**: Segoe UI
- **Base Font Size**: 9pt
- **Headings**: 
  - Large (14px, bold)
  - Medium (13px, bold)
  - Small (12px, bold)
- **Body Text**: 9pt normal
- **Small Text**: 8pt
- **Font Weights**: Regular and Bold

### 2.3 Spacing and Layout

- **Padding**:
  - Content areas: 16px
  - Containers: 8px
  - Buttons: 6px 12px
  - List items: 6px 8px
- **Margins**:
  - Between components: 16px
  - Between related elements: 8px
  - Between buttons in toolbar: 10px
- **Border Radius**:
  - Buttons and inputs: 4px
  - Containers: 4px
  - Scrollbar handles: 6px

### 2.4 Components

#### Buttons
- **Standard Button**:
  - Background: #1A2C42 (PRIMARY)
  - Text: #FFFFFF (TEXT_LIGHT)
  - Border: 1px solid #4A5568 (DARK_BORDER)
  - Border Radius: 4px
  - Padding: 6px 12px
  - Hover: Background lightens to #263D5A (PRIMARY_LIGHT)
  - Active: Background darkens to #0F1A2A (PRIMARY_DARK)
  - Disabled: Gray background with muted text

- **Primary Button**:
  - Background: #D4AF37 (SECONDARY)
  - Text: #0F1A2A (PRIMARY_DARK)
  - Other styles same as standard

- **Secondary Button**:
  - Background: #263D5A (PRIMARY_LIGHT)
  - Border: 1px solid #D4AF37 (SECONDARY)
  - Text: #FFFFFF (TEXT_LIGHT)

- **Success/Danger Buttons**:
  - Use success/error colors with appropriate text

#### Input Fields
- **Text Input**:
  - Background: #263D5A (PRIMARY_LIGHT)
  - Text: #FFFFFF (TEXT_LIGHT)
  - Border: 1px solid #4A5568 (DARK_BORDER)
  - Border Radius: 4px
  - Padding: 4px 8px
  - Focus: Border changes to #D4AF37 (SECONDARY)

- **Search Input**:
  - Includes search icon
  - Has clear button
  - Otherwise follows text input styling

#### Lists and Tables
- **List Widget**:
  - Background: #1A2C42 (PRIMARY)
  - Item Padding: 6px 8px
  - Item Border-bottom: 1px solid #4A5568 (DARK_BORDER)
  - Selected Item: Background #263D5A (PRIMARY_LIGHT) with left gold border
  - Hover: Background lightens

- **Table View**:
  - Background: #263D5A (PRIMARY_LIGHT)
  - Text: #FFFFFF (TEXT_LIGHT)
  - Grid Lines: #4A5568 (DARK_BORDER)
  - Headers: Background #0F1A2A (PRIMARY_DARK)
  - Alternating Rows: #0F1A2A (PRIMARY_DARK)
  - Selected Row: Background #1A2C42 (PRIMARY) with gold text

#### Dialogs and Popups
- **Dialog**:
  - Background: #2D3748 (BG_DARK)
  - Border: 1px solid #4A5568 (DARK_BORDER)
  - Border Radius: 4px
  - Box Shadow: soft shadow for elevation

- **Context Menu**:
  - Background: #1A2C42 (PRIMARY)
  - Border: 1px solid #4A5568 (DARK_BORDER)
  - Item Padding: 6px 24px 6px 8px
  - Selected Item: Background #263D5A (PRIMARY_LIGHT) with gold text
  - Separator: 1px solid #4A5568 (DARK_BORDER)

- **Multi-Entry Dialog**:
  - Background: #1A2C42 (PRIMARY)
  - Border: 1px solid #4A5568 (DARK_BORDER)
  - Border Radius: 6px
  - Text Area: #263D5A (PRIMARY_LIGHT) background with monospace font
  - Primary Button: Gold accent (#D4AF37)
  - Cancel Button: Dark background (#1A2C42)
  - Helper Text: Small, italicized text in muted color
  - Minimum Size: 500x400 pixels
  - Resizable: True to accommodate various amounts of input text

#### Scrollbars
- **Vertical Scrollbar**:
  - Width: 12px
  - Background: #0F1A2A (PRIMARY_DARK)
  - Handle: #263D5A (PRIMARY_LIGHT)
  - Handle Border Radius: 6px
  - Handle Hover: #D4AF37 (SECONDARY)

- **Horizontal Scrollbar**:
  - Height: 12px
  - Otherwise matches vertical scrollbar

## 3. View Specifications

### 3.1 Dashboard View
- **Layout**: Card-based layout with stats and summary information
- **Components**:
  - Statistical summary cards
  - Recent activity section
  - Quick action buttons
- **Empty State**: Shows guidance for users with no data

### 3.2 Data View
- **Layout**: Full-width table with toolbar above
- **Components**:
  - Data table with sortable columns
  - Filter controls
  - Search field
  - Action buttons for data operations
- **Interactions**:
  - Click column header to sort
  - Right-click row for context menu
  - Double-click cell to view details

### 3.3 Validation View
- **Layout**: Three-column layout using QSplitter for adjustable widths
- **Columns**:
  - Players list
  - Chest types list
  - Sources list
- **Components per Column**:
  - Header with title and count
  - Search input with icon
  - Action buttons (Add, Remove, Import, Export)
  - List widget with entries
- **Bottom Elements**:
  - Toolbar with Preferences and Validate buttons
  - Status bar showing validation statistics
- **Special Components**:
  - MultiEntryDialog for adding multiple entries at once
  - Confirmation dialog for deleting multiple entries
  - Import/Export dialogs with overwrite/append options

### 3.4 Correction View
- **Layout**: Two-panel design with rule table and controls
- **Components**:
  - Rule management table with sorting and filtering
  - Action buttons for rule operations
  - Toggle controls for correction settings
  - Status bar with statistics
  - Import/export functionality
- **Interactions**:
  - Double-click row to edit rule
  - Right-click for context menu
  - Drag and drop for reordering
  - Column header click for sorting
  - Mouse or keyboard for selection

### Correction UI Components

#### Rule Table
- **Headers**: To, From, Category, Status, Actions
- **Actions Column**: Up/down buttons for reordering
- **Status Column**: Checkmark for enabled, X for disabled
- **Sorting**: Click column headers to sort alphabetically
- **Selection**: Multi-select support for batch operations
- **Context Menu**: Full set of rule operations
- **Row Height**: 30px for comfortable viewing
- **Alternate Row Colors**: #0F1A2A for odd rows

#### Rule Management Dialogs

**Add/Edit Rule Dialog**:
- Modal dialog with form layout
- To field with dropdown suggestions from validation lists
- From field with text input
- Category radio buttons (player, chest_type, source, general)
- Status checkbox (enabled/disabled)
- Validation to ensure required fields are filled
- Option to add new "To" values to validation lists

**Batch Rule Creation Dialog**:
- Grid layout for multiple rule entries
- From column showing selected cell values
- Category dropdown for each entry
- To field dropdown with validation list suggestions
- Toggle for enabling all rules
- Toggle for adding new values to validation lists

#### Correction Controls
- **Auto-correct**: Toggle for auto-correction after validation
- **Correct Invalid Only**: Toggle to limit correction to invalid cells
- **Auto-enable New Rules**: Toggle for default status of new/imported rules
- **Action Buttons**: Import, Export, Apply Corrections
- **Statistics Display**: Total rules count, enabled/disabled count
- **Status Bar**: Information about last correction operation

#### Progress Dialog
- Modal dialog showing correction progress
- Progress bar with percentage
- Status text showing current operation
- Detail text with statistics
- Cancel button for interrupting operation
- Summary display after completion

### Data View Integration

#### Cell Highlighting
- **Red**: Invalid cells without correction rules
- **Orange**: Invalid cells with correction rules
- **Green**: Corrected cells
- **Purple**: Cells that can be corrected with existing rules

#### Context Menu Integration
- Right-click cell to access "Add Correction Rule" option
- Multi-select cells for "Create Batch Correction Rules"
- Option to immediately apply rules after creation

#### Tooltips
- Hover over highlighted cells to see correction information
- Tooltip shows available correction rule details
- Includes category and status information

### Keyboard Navigation
- Arrow keys to navigate table
- Enter to edit selected rule
- Delete to remove selected rule(s)
- Ctrl+Up/Down to move rules
- Ctrl+Home/End to move to top/bottom
- Ctrl+A to select all rules
- Ctrl+F to focus search field

### 3.5 Chart View
- **Layout**: Chart display with controls panel
- **Components**:
  - Chart rendering area
  - Chart type selector
  - Data series controls
  - Export options
- **Chart Types**:
  - Bar charts
  - Pie charts
  - Line charts
- **Interactions**:
  - Change chart type
  - Toggle data series visibility
  - Adjust chart properties
  - Export chart as image

## 4. Interaction Patterns

### Navigation
- Sidebar navigation for main sections
- Tab navigation within sections where applicable
- Back button for returning to previous views
- Breadcrumbs for complex navigation paths

### Data Interaction
- **Selection**: Single-click for selection, double-click for edit/detail
- **Context Menus**: Right-click for contextual actions
- **Drag and Drop**: Support for reordering where applicable
- **Keyboard Navigation**: Tab index for form fields, arrow keys for lists

### Feedback Patterns
- **Loading States**: Progress bars for operations over 1 second
- **Success Feedback**: Brief status messages and/or icon changes
- **Error Handling**: 
  - Inline validation for forms
  - Error dialogs for system errors
  - Visual indicators for validation issues
- **Empty States**: Helpful messages and actions when no data exists

### Animations
- Subtle transitions between views (250ms duration)
- Hover effects for interactive elements
- Loading indicators for asynchronous operations

## 5. Key UX Principles

- **Consistency:** Maintain consistent styling (colors, fonts, spacing) throughout the application.
- **Clarity:** Use clear labels and icons.
- **Feedback:** Provide visual feedback for user actions (e.g., hover effects, selection changes, copy-to-clipboard success).
- **Efficiency:** Minimize the number of clicks required to perform common tasks.
- **Discoverability:** Make it easy for users to find and understand the application's features.

## 6. UX Rubric

UX Rubric to rate the quality of your UI/UX design:

| Category                   | Description | A                                                                                                                              | B                                                                                                                              | C                                                                                                                          | D                                                                                                                    | F                                                                                                                       |
| -------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Color Palette**          | Weight: 1x  | Colors are masterfully integrated, perfectly reflecting the brand and balancing contrast for optimal usability.                | Colors are thoughtfully selected, support brand identity, and maintain a mostly consistent visual hierarchy.                   | A serviceable color scheme is present, though minor inconsistencies or contrast issues reduce overall effectiveness.       | Colors are partially aligned with the brand but fail to follow best practices in contrast or hierarchy.              | Colors are chosen at random, creating visual confusion and lacking any cohesive theme or brand alignment.               |
| **Layout & Grid**          | Weight: 1x  | Grid usage is expertly executed, ensuring balanced spacing, alignment consistency, and a crisp, professional structure.        | A purposeful grid strategy creates a cohesive layout; minor alignment or spacing issues may still be noticed.                  | Layout generally follows a grid, though some elements deviate; overall structure is acceptable but not optimal.            | Some grid principles are followed, but spacing is inconsistent and visual alignment suffers in key sections.         | No clear structure or grid system in place, resulting in a disorganized and hard-to-navigate layout.                    |
| **Typography**             | Weight: 1x  | Typography is outstanding, with well-chosen fonts, impeccable kerning, and a clean hierarchy that enhances user engagement.    | Typography choices reflect a solid visual hierarchy and balanced kerning; minor refinements may further improve readability.   | Typography is functional with moderately consistent styles, though headlines, body text, and spacing could be refined.     | Font selection is somewhat appropriate but lacks clear organization; kerning and leading inconsistencies persist.    | Font choices are erratic or unreadable, with rampant inconsistencies in size, weight, or familial styles.               |
| **Hierarchy & Navigation** | Weight: 1x  | Flawless content hierarchy with intuitive navigation that effortlessly guides users to core features and information.          | Content levels are well-defined, and primary navigation is accessible; minor tweaks could enhance usability further.           | A straightforward hierarchy is established, though key actions or navigation items could be more prominently displayed.    | Some attempt at prioritizing content is visible, yet users may struggle to locate important features easily.         | Information is scattered without clear importance levels; navigation elements are unrecognizable or absent.             |
| **Accessibility**          | Weight: 1x  | Fully meets or exceeds accessibility best practices, ensuring all users can easily interact with and understand the dashboard. | The design largely complies with accessibility standards; minor improvements could include more robust testing or refinements. | Basic accessibility measures are present, though certain features like keyboard navigation or ARIA tags may be incomplete. | Some attempts to address accessibility are made, yet many crucial guidelines (e.g., color contrast) remain unmet.    | Design disregards accessibility guidelines altogether, using low contrast, illegible fonts, and no accessible patterns. |
| **Spacing & Alignment**    | Weight: 1x  | A perfectly balanced layout with deliberate spacing; every element is precisely aligned for maximum readability.               | Thoughtful use of white space and alignment creates a clean layout with only minor areas needing adjustment.                   | Spacing and alignment are mostly consistent, though certain sections need refinement to enhance clarity.                   | Some uniformity in spacing is emerging, but inconsistent alignment detracts from legibility and overall visual flow. | Visual clutter dominates due to no consistent margins, padding, or alignment, making the interface look unfinished.     |

## 5. Performance Patterns

### 5.1 Chunked Processing for UI Responsiveness

To maintain UI responsiveness during intensive operations like table population, data validation, or file loading, the application implements a chunked processing pattern:

#### Pattern Implementation
- **Concept**: Break large operations into smaller chunks processed sequentially with UI updates between chunks
- **Mechanism**: Use Qt's timer system (QTimer.singleShot) to yield to the event loop
- **Chunk Size**: Typically 200 items per chunk for table operations
- **Progress Indication**: Update progress indicators between chunks

#### Applied Examples

**Table Population**:
- Main implementation in DataView.populate_table() method
- Processes 200 rows per chunk
- Provides visual feedback on progress during population
- Maintains UI responsiveness even with datasets of 10,000+ rows

**Data Import**:
- Implementation in MultiCSVLoadTask
- Processes files in chunks with progress reporting
- Allows cancellation during the operation

#### Best Practices

1. **Appropriate Chunk Size**:
   - Balance between performance and responsiveness
   - 100-200 items works well for most operations
   - Adjust based on operation complexity

2. **Progress Feedback**:
   - Always provide visual indication of progress
   - Update status bar or progress dialog between chunks
   - Consider percent-complete indicators for longer operations

3. **Cancelable Operations**:
   - Include cancellation capability for long operations
   - Check for cancellation between chunks
   - Clean up resources properly if canceled

4. **Implementation Pattern**:
   ```python
   def process_operation(self):
       # Initialize
       self._items_to_process = len(items)
       self._current_index = 0
       self._in_progress = True
       
       # Start chunked processing
       self._process_chunk()
   
   def _process_chunk(self):
       if not self._in_progress:
           return
           
       chunk_size = 200
       end_index = min(self._current_index + chunk_size, self._items_to_process)
       
       # Process this chunk
       for idx in range(self._current_index, end_index):
           # Process item
           
       # Update progress and schedule next chunk
       self._current_index = end_index
       if self._current_index < self._items_to_process:
           QTimer.singleShot(0, self._process_chunk)
       else:
           self._finalize_operation()
   ```

5. **UI Thread Considerations**:
   - For very complex operations, consider true background processing
   - For simpler operations, chunked processing often provides a good balance
   - Always update UI elements in the main thread

### 5.2 Debouncing and Throttling

For UI events that can fire rapidly (like resize, scrolling, or text input), implement debouncing or throttling:

- **Debouncing**: Wait until a pause in the event stream before processing
- **Throttling**: Process at most once per specified time interval

The application uses the SignalManager's throttling capabilities to improve UI performance for frequent events.

### 5.3 Lazy Loading

For components or data that might not be immediately needed:

- Load only when needed/visible
- Implement placeholder states for unloaded content
- Load in background when idle time is available

## DataView Refactoring UI/UX Specifications

### Overview
The DataView component is being refactored to enhance user experience, improve visual feedback, and provide more intuitive interactions with tabular data in ChestBuddy.

### Visual Design

#### Component Layout
![DataView Component Layout](https://placeholder.com/dataview-layout)

The DataView consists of these visual components:

1. **DataTable**: The main tabular display
   - Custom header with enhanced interaction
   - Grid cells with validation status indicators
   - Selection highlighting for active cells
   - Correction indicators for cells with available corrections

2. **Toolbar**: Controls above the table
   - Filter controls
   - View options
   - Action buttons
   - Status indicators

3. **Context Menu**: Right-click action menu
   - Cell-specific actions
   - Selection-aware options
   - Validation actions
   - Correction suggestions

#### Color Scheme

| Element | Default | Selected | Invalid | Correctable | Warning |
|---------|---------|----------|---------|-------------|---------|
| Cell Background | #FFFFFF | #E3F2FD | #FFCDD2 | #FFF8E1 | #FFE0B2 |
| Cell Border | #E0E0E0 | #2196F3 | #F44336 | #FFC107 | #FF9800 |
| Text | #212121 | #212121 | #212121 | #212121 | #212121 |
| Icons | #757575 | #2196F3 | #F44336 | #FFC107 | #FF9800 |

#### Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Header | System | 14px | Medium | #424242 |
| Cell Text | System | 13px | Regular | #212121 |
| Tooltip | System | 12px | Regular | #FFFFFF |
| Error Message | System | 12px | Medium | #F44336 |

### Interaction Design

#### Cell Interactions

| Interaction | Behavior |
|-------------|----------|
| Single Click | Select cell |
| Double Click | Enter edit mode |
| Right Click | Show context menu |
| Shift+Click | Extend selection |
| Ctrl+Click | Add to selection |
| Tab | Move to next cell |
| Enter | Confirm edit / Move down |
| Esc | Cancel edit |

#### Validation Feedback

| State | Visual Indicator | Interaction |
|-------|------------------|-------------|
| Valid | No indicator | Standard interactions |
| Invalid | Red background, error icon | Hover shows error tooltip |
| Correctable | Yellow background, suggestion icon | Hover shows correction options |
| Warning | Orange background, warning icon | Hover shows warning message |
| Info | Blue background, info icon | Hover shows information message |

#### Correction Workflow

1. User encounters a cell with correction indicator (yellow background)
2. On hover, tooltip shows available correction(s)
3. User can:
   - Click suggestion icon to see all options
   - Right-click for correction context menu
   - Use keyboard shortcut (Alt+C) to apply suggested correction

#### Context Menu Design

![Context Menu](https://placeholder.com/context-menu)

The context menu adapts based on:
- Cell content type
- Validation state
- Available corrections
- Selection state (single vs. multiple)

### Responsiveness

The DataView is designed to adapt to different container sizes:

- Columns resize proportionally
- Long text truncates with ellipsis
- Headers remain visible when scrolling vertically
- First column(s) can be frozen for horizontal scrolling

### Accessibility Features

- Keyboard navigation for all interactions
- Screen reader support for cell content and status
- High contrast mode compatible
- Customizable font sizing
- ARIA attributes for enhanced assistive technology support

### User Workflows

#### Data Exploration Flow
1. Load data into DataView
2. Sort/filter to find relevant information
3. Select cells of interest
4. View details or perform actions
5. Export or share results

#### Data Correction Flow
1. Identify cells with validation issues
2. Review suggested corrections
3. Apply appropriate corrections
4. Verify corrected data
5. Save changes

#### Data Selection Flow
1. Select individual or multiple cells
2. Perform bulk operations via context menu
3. Copy/paste selection
4. Apply formatting or validation to selection

### UX Improvements Over Previous Version

1. **Clearer Validation Feedback**
   - More distinctive visual indicators
   - Detailed error messages
   - Contextual correction suggestions

2. **Enhanced Cell Interaction**
   - More responsive selection behavior
   - Improved editing experience
   - Better multi-cell operations

3. **Optimized Performance**
   - Faster rendering for large datasets
   - Smoother scrolling experience
   - Reduced lag during filtering/sorting

4. **More Intuitive Context Menu**
   - Organized by operation type
   - Prioritizes common actions
   - Provides visual cues for available options

### UX Evaluation Criteria

The refactored DataView will be evaluated against these criteria:

1. **Clarity**: Are status indicators clearly visible and understandable?
2. **Efficiency**: Can users accomplish tasks with minimal steps?
3. **Consistency**: Do interactions follow established patterns?
4. **Feedback**: Does the system provide clear feedback for all actions?
5. **Performance**: Does the interface remain responsive with large datasets?
6. **Accessibility**: Can all users access all functionality regardless of abilities?

### Future UX Enhancements (Planned)

1. Customizable columns (reorder, resize, hide)
2. Advanced filtering with visual query builder
3. Conditional formatting capabilities
4. Expanded cell rendering options for different data types
5. Data visualization features integrated with cell selection