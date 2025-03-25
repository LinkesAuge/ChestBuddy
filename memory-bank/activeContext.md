---
title: Active Context - ChestBuddy Application
date: 2024-03-25
---

# Active Context: ChestBuddy Application

## Current State

The application architecture is stable with all core functionality implemented. The application has successfully transitioned to a controller-based architecture, with all UI components now using the appropriate controllers for business logic operations.

### Completed Components

- **Controller Architecture**: All key controllers have been implemented (FileOperations, Progress, ErrorHandling, ViewState, DataView, UIState)
- **UI Component Refactoring**: All UI components have been refactored to use controllers
  - **ChartViewAdapter**: Updated to use the DataViewController for chart operations
  - **ValidationViewAdapter**: Updated to use the DataViewController for validation operations
  - **CorrectionViewAdapter**: Updated to use the DataViewController for correction operations
  - **DataViewAdapter**: Updated to use the DataViewController for data handling
- **Integration Testing**: Comprehensive integration tests verify controllers work correctly with UI components
- **Signal-Based Communication**: Robust signal-based communication between controllers and UI components

### Application Architecture

The application architecture follows a clean controller-based organization:

1. **Core Layer**:
   - Models: ChestDataModel, ValidationModel
   - Services: CSVService, ValidationService, CorrectionService, ChartService
   - Controllers: FileOperationsController, ProgressController, ErrorHandlingController, ViewStateController, DataViewController, UIStateController

2. **UI Layer**:
   - MainWindow: Main application window (delegates to controllers)
   - Views: Dashboard, Data, Validation, Correction, Charts

3. **Utils Layer**:
   - Configuration
   - Logging
   - File operations helpers

### Current UI Navigation

The navigation system uses a sidebar that provides access to:

1. **Dashboard**: Overview of data and recent files
2. **Data**: Tabular view of imported data
3. **Validation**: View and resolve validation issues
4. **Correction**: Apply automated corrections to data
5. **Charts**: Visualize data in various chart formats

### Known Issues

1. **Memory Usage**: Large datasets (>100,000 rows) can consume significant memory
2. **UI Performance**: Updates to the UI thread can cause momentary freezing with large datasets
3. **Thread Cleanup**: Minor QThread object deletion warning at shutdown (non-critical)

### Column Name Standardization

The application supports diverse CSV file formats through:

- Column name mapping to standardize input data (using `EXPECTED_COLUMNS = ["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE", "CLAN"]`)
- Case-insensitive comparison for column identification
- Regular expression patterns for fuzzy matching similar columns
- Default column templates for easy mapping

## Application Architecture

The current application architecture follows these patterns:

```mermaid
graph TD
    App[App Controller] --> UI[UI Components]
    App --> Services[Services]
    App --> Models[Data Models]
    App --> Controllers[Controllers]
    
    UI -->|Signals| App
    App -->|Updates| UI
    
    Services --> Models
    Services --> Workers[Background Workers]
    
    Workers -->|Signals| Services
    Services -->|Signals| App
    
    Controllers --> Services
    Controllers -->|Updates| UI
    UI -->|Signals| Controllers
    
    Controllers -->|Coordination| Controllers
```

### Controller Relationships

```mermaid
graph TD
    App[ChestBuddyApp] --> VSCT[ViewStateController]
    App --> DVCT[DataViewController]
    App --> UICT[UIStateController]
    App --> FOCT[FileOperationsController]
    App --> PRCT[ProgressController]
    App --> ERCT[ErrorHandlingController]
    
    VSCT <-->|View State Coordination| DVCT
    UICT <-->|UI Updates| VSCT
    UICT <-->|Action States| DVCT
    ERCT -->|Error Handling| PRCT
    
    style VSCT fill:#2C5282,color:#fff
    style DVCT fill:#2C5282,color:#fff
    style UICT fill:#2C5282,color:#fff
    style FOCT fill:#2C5282,color:#fff
    style PRCT fill:#2C5282,color:#fff
    style ERCT fill:#2C5282,color:#fff
```

## Current UI Navigation 

The implemented UI navigation structure:

```mermaid
graph LR
    Start((Start)) --> Dashboard
    Dashboard -->|Import| Data
    Dashboard -->|Quick Action| Validation
    Dashboard -->|Quick Action| Charts
    Dashboard -->|Recent File| Data
    SideNav -->|Navigate| Dashboard
    SideNav -->|Navigate| Data
    SideNav -->|Navigate| Validation
    SideNav -->|Navigate| Correction
    SideNav -->|Navigate| Charts
    
    Data -->|Validate| Validation
    Validation -->|Apply Corrections| Correction
    Correction -->|Show Results| Charts
    
    style Start fill:#1a3055,color:#fff
    style Dashboard fill:#234a87,color:#fff
    style Data fill:#234a87,color:#fff
    style Validation fill:#234a87,color:#fff
    style Correction fill:#234a87,color:#fff
    style Charts fill:#234a87,color:#fff
    style SideNav fill:#1a3055,color:#fff
```

## Key Components

### Core Components
- **UIStateController**: Centralizes UI-specific state management (status messages, action states, UI themes)
- **DataViewController**: Handles data operations, validation, correction with signal-based communication
- **ViewStateController**: Manages view state, transitions, and histories
- **ErrorHandlingController**: Provides centralized error handling with typed error categories
- **FileOperationsController**: Manages file operations (opening, saving, recent files)
- **ProgressController**: Manages progress reporting with visual feedback
- **CSV Loading System**: Chunked processing with incremental progress updates
- **Background Worker System**: Thread management for long-running operations
- **UI Component Library**: Reusable UI components (ActionButton, ActionToolbar, EmptyStateWidget, FilterBar)
- **Navigation System**: Sidebar with data-dependent state handling

## Dashboard UI

### Dashboard with No Data Loaded

```
+-----------------------------------------------------+
|                     ChestBuddy                      |
+------------+----------------------------------------+
|            |                                        |
| Dashboard  |  Dashboard                             |
|            |  +---------------------------------+   |
| Data ⊗     |  |         Welcome to ChestBuddy   |   |
|            |  |                                 |   |
| Analysis ⊗ |  | No data loaded. Import data to  |   |
|            |  | start analyzing your chest data.|   |
| Reports ⊗  |  |                                 |   |
|            |  |  +-------------------------+    |   |
| Settings   |  |  |       IMPORT DATA      |    |   |
|            |  |  +-------------------------+    |   |
| Help       |  |                                 |   |
|            |  +---------------------------------+   |
|            |                                        |
|            |  Statistics                            |
|            |  +--------+ +--------+ +--------+     |
|            |  | Dataset | |Validated| |Corrections| |
|            |  |  0 rows | |   N/A   | |    0     | |
|            |  +--------+ +--------+ +--------+     |
|            |                                        |
|            |  Recent Files                          |
|            |  No recent files                       |
+------------+----------------------------------------+
```

### Dashboard with Data Loaded

```
+-----------------------------------------------------+
|                     ChestBuddy                      |
+------------+----------------------------------------+
|            |                                        |
| Dashboard  |  Dashboard                             |
|            |                                        |
| Data       |  Quick Actions                         |
|            |  +--------+ +--------+ +--------+     |
| Analysis   |  | Import  | |Validate| |Export  |     |
|  • Tables  |  |  Data   | |  Data  | |  Data  |     |
|  • Charts  |  +--------+ +--------+ +--------+     |
|            |                                        |
| Reports    |  Statistics                            |
|            |  +--------+ +--------+ +--------+     |
| Settings   |  | Dataset | |Validated| |Corrections| |
|  • Lists   |  | 125 rows| |  94%    | |    15    | |
|  • Rules   |  +--------+ +--------+ +--------+     |
|  • Prefs   |                                        |
|            |  Recent Files                          |
| Help       |  • chest_data_2023-03-11.csv          |
|            |  • older_data_2023-02-15.csv          |
|            |                                        |
|            |  [Chart visualization]                 |
+------------+----------------------------------------+
```

## Recent Improvements

File import and data loading have been stabilized with several bug fixes:

1. **Fixed File Import Dialog Duplication**
   - Added state tracking flags to prevent multiple dialogs
   - Implemented try/finally blocks to reset flags properly
   - Added better logging for dialog state tracking

2. **Improved Data Loading**
   - Enhanced error handling in CSV load operations
   - Fixed signal blockage issues for data model updates
   - Improved cancellation handling and state cleanup
   - Added detailed logging for better debugging

3. **Fixed Signal Connections**
   - Enhanced connections for data loading signals
   - Added error handling for signal connections
   - Improved state tracking for data loaded status

4. **Type Annotation Improvements**
   - Fixed PySide6 signal compatibility by using built-in Python types
   - Created comprehensive type annotation tests
   - Documented signal parameter types consistently

5. **Progress Reporting Enhancements**
   - Added incremental progress updates during CSV loading
   - Improved progress dialog with file-specific information
   - Added automatic dialog closing after operations complete