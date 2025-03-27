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

### 3.4 Correction View
- **Layout**: Split view with data table and correction panel
- **Components**:
  - Data table showing errors/warnings
  - Correction panel with form fields
  - Action buttons for applying corrections
- **Interactions**:
  - Select row to load in correction panel
  - Form validation with visual feedback
  - Apply button to save changes

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