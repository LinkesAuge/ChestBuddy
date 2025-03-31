---
title: Active Context - ChestBuddy Application
date: 2024-07-23
---

# Active Development Context

## Active Context - July 23, 2024

### CorrectionView Test Coverage Improvements

We have successfully implemented comprehensive tests for the CorrectionView component in the ChestBuddy application. The test coverage for this component has significantly improved, now reaching 52% coverage of the CorrectionView implementation, and an impressive 96% coverage of the test file itself.

#### Test Improvements Summary

1. **Implemented Test Structure**:
   - Created a robust `MockSignal` class to handle Qt signals in tests
   - Set up fixtures for all necessary dependencies and mock components
   - Implemented comprehensive test cases covering core functionality

2. **Key Test Areas Covered**:
   - Initialization and configuration
   - Controller connection and setup
   - View content updates and error handling
   - Status message display
   - Action button handling
   - Corrections application
   - History request handling
   - Error state management
   - UI component creation and management

3. **Testing Patterns Applied**:
   - Used MockSignal for safe signal connections without access violations
   - Applied proper patching of UI components and methods
   - Carefully mocked class methods to track calls and verify behavior
   - Tested both success and error scenarios

4. **Challenges Overcome**:
   - Fixed initialization issues related to BaseView attributes
   - Properly mocked signal connections to prevent access violations
   - Addressed issues with method patching for UI components
   - Ensured proper testing of signal emissions and handling

#### Next Steps

1. Consider expanding test coverage to additional edge cases
2. Apply similar patterns to other view components with low coverage
3. Continue refining the MockSignal pattern for UI testing
4. Document these approaches in the testing best practices

This work follows our successful ValidationTabView test improvements and continues our progress toward our goal of 95% test coverage across the application.

## Active Context - May 16, 2024

### ValidationTabView Test Coverage Improvements

We have significantly improved the test coverage for the ValidationTabView component in the ChestBuddy application. The coverage has increased from 29% to 80%, which is a substantial improvement.

#### Test Improvements Summary

1. **Identified Key Uncovered Sections**:
   - Exception handling in ValidationTabView's initialization (lines 73-75)
   - Signal connection and disconnection logic (lines 452-564)
   - Validation logic and UI updates (lines 595-602)
   - Checkbox state changes and preferences (lines 615-619)

2. **Added Comprehensive Tests**:
   - Created tests for error handling during initialization
   - Implemented tests for signal connection logic and disconnect handling
   - Added tests for validation result processing
   - Created tests for preference updates through checkbox toggling
   - Added tests for edge cases like missing models and widget styling

3. **Implemented Test Patterns**:
   - Used MockSignal class to avoid PySide6 Signal connection issues
   - Applied proper patching techniques for UI components
   - Improved test fixtures to better represent real-world usage
   - Used assert_any_call to handle multiple status bar updates

4. **Challenges Overcome**:
   - Fixed issues with PySide6 signal handling in tests
   - Addressed UI component testing challenges by using real QWidgets where necessary
   - Implemented proper exception testing for components that catch exceptions internally
   - Created more robust tests that don't break from implementation changes

#### Next Steps

1. Apply similar test improvement patterns to other view components
2. Update documentation on best practices for Qt UI testing
3. Consider adding more integration tests between ValidationTabView and other components
4. Implement better test organization for future UI component tests

This work brings us closer to our goal of 95% test coverage for all components in the application.

### Recent Codebase Cleanup
- Added deprecation warnings to `chestbuddy/ui/correction_tab.py`, `chestbuddy/ui/chart_tab.py`, `chestbuddy/ui/views/correction_view_adapter.py`, marking these components as legacy
- Added deprecation warnings to `chestbuddy/ui/views/chart_view_adapter.py`, noting that it will be replaced by a future ChartView component
- Implemented new `ChartView` component to replace `ChartViewAdapter` and `ChartTab`, following the same pattern as `CorrectionView`
- Removed `chestbuddy/core/service_locator.py` and consolidated to `chestbuddy/utils/service_locator.py`
- Deleted `chestbuddy/ui/validation_tab.py` as it's been fully replaced by ValidationTabView
- Documented migration status of UI components in `codebase_cleanup.md`
- Updated `tests/test_main_window.py` to work with the new MainWindow constructor, fixing test failures
- Created comprehensive tests for `ChartView` in `tests/unit/ui/views/test_chart_view.py`

### Key Tasks in Progress
1. Modernizing the UI architecture from tab-based to view-based design
2. ✅ Updated MainWindow to use ChartView directly instead of ChartViewAdapter
3. ✅ Created tests for the new ChartView component
4. ✅ Improved test coverage for ValidationTabView from 29% to 80%
5. Update remaining tests to use the new view-based components directly

## Recent Codebase Cleanup

We have performed a cleanup of redundant code in the ChestBuddy application:

1. **Removed redundant service_locator.py** from the core directory, as it duplicated functionality in utils/service_locator.py
2. **Added deprecation warnings** to legacy UI components that are being phased out:
   - correction_tab.py
   - chart_tab.py
   - correction_view_adapter.py (identified that MainWindow already uses CorrectionView directly)
   - chart_view_adapter.py (identified that it will need a ChartView replacement)
3. **Deleted legacy UI component** no longer in use:
   - validation_tab.py (replaced by ValidationTabView)
   - Updated test_ui_components.py to use ValidationTabView
4. **Implemented new modern components**:
   - Created ChartView to replace ChartViewAdapter and ChartTab
   - Maintained API compatibility for smooth transition
5. **Marked signal_tracer.py** as a debug-only utility
6. **Created documentation** for future cleanup tasks in memory-bank/codebase_cleanup.md
7. **Documented migration status** of UI components in codebase_cleanup.md
8. **Created tests** for the new ChartView component in tests/unit/ui/views/test_chart_view.py

These changes are part of our ongoing effort to modernize the codebase by moving from the tab-based UI to a view-based architecture. The next step is to update remaining tests to use the new view components, followed by the removal of the deprecated adapter and legacy tab components.

## UI Architecture Modernization Progress

### Completed
- ✅ ValidationTab → ValidationTabView: Component deleted and replaced
- ✅ CorrectionTab → CorrectionView: MainWindow now uses CorrectionView directly
- ✅ ChartView implementation: Created modern replacement for ChartTab/ChartViewAdapter
- ✅ Updated MainWindow to use ChartView directly
- ✅ Created comprehensive tests for ChartView

### In Progress
- 🔄 Updating remaining tests to use view-based components
- 🔄 Preparing for removal of legacy components

### Next Steps
1. Update remaining ChartTab and ChartViewAdapter tests to use ChartView
2. Remove deprecated adapter classes and legacy tab components
3. Clean up any remaining references to legacy components

## Current Focus: Complete CorrectionView UI Implementation

We are currently focused on completing the UI implementation for the correction feature in the ChestBuddy application, specifically the CorrectionView. This involves implementing the remaining UI elements according to the mockup design and ensuring proper integration with the existing functionality.

### Implemented Features

- ✅ Status bar in CorrectionRuleView showing rule counts (Total: X | Enabled: Y | Disabled: Z)
- ✅ Color legend in DataView explaining the different highlight colors for cells
- ✅ Consistent cell highlighting with colors matching the legend
- ✅ Update mechanism for cell highlighting via update_cell_highlighting method
- ✅ Import/Export buttons in the header of CorrectionRuleView
- ✅ Fixed deletion issues where the wrong rules were being deleted
- ✅ Simplified CorrectionRule data structure by removing redundant 'order' and 'description' fields

### Missing Features

- 🔄 Context menu for data cells with options for individual and batch correction
- 🔄 Enhanced Import/Export dialog with file format selection and preview
- 🔄 Improved batch correction dialog with better pattern recognition
- 🔄 Settings panel with configuration options

### Current Tasks

1. Implement context menu for DataView cells with the following options:
   - Apply correction rules to selected cells
   - Apply specific rule to selected cells
   - Batch correction for similar values
   - View validation details

2. Enhance Import/Export dialog with:
   - File format selection (CSV, Excel, JSON)
   - Preview of rules before importing
   - Options for handling duplicates
   - Filtering options for export

3. Improve batch correction dialog:
   - Better pattern recognition for similar errors
   - Preview of validation results
   - Auto-correction suggestions
   - Optimization for multiple cell selection

4. Add settings panel with configuration checkboxes for:
   - Auto-correction preferences
   - Validation options
   - Display settings

### Next Steps

1. Implement context menu for rule table with quick actions
2. Connect settings to ConfigManager for persistence
3. Enhance filter controls with additional options
4. Create unit tests for new UI components

### Key Decisions

1. Replaced MainWindow status bar with dedicated QStatusBar in CorrectionView
2. Implementation of file dialog integration for rule import/export
3. Use of Test-Driven Development (TDD) for remaining features
4. Follow UI component style guidelines from mockup
5. Prioritize user experience with responsive feedback
6. Simplified CorrectionRule data structure by removing 'order' field and implementing implicit ordering
7. Further simplified CorrectionRule by removing unused 'description' field
8. Added robust error handling for all rule operations

## Recent Model Changes

We've made important simplifications to the correction rule data model:

1. **Removed Order Field**: The 'order' field has been removed from CorrectionRule. Rules are now ordered implicitly by their position in the list, making the code more intuitive and removing redundancy.

2. **Removed Description Field**: The 'description' field has been removed as it was unused and added unnecessary complexity to the data structure.

3. **Fixed Deletion Issues**: Implemented a more robust approach to rule deletion that prevents multiple rules from being deleted accidentally.

These changes have significantly simplified the data structure and made the correction feature more maintainable.

## DataView Integration

The integration between the DataView and correction components is a critical part of the implementation, focusing on user experience and visual feedback.

### Current Integration Work

1. Context Menu Integration
   - Adding context menu for cells to perform corrections
   - Connecting menu actions to the controller
   - Handling selection states for contextual options

2. Visual Feedback
   - Cell highlighting based on correction status
   - Color-coded cells for different states
   - Tooltips providing details on cell status

3. Controller Enhancements
   - Adding methods to apply corrections to selections
   - Implementing batch correction operations
   - Optimizing validation and correction workflows

4. UI Flow Implementation
   - Ensuring smooth transitions between dialogs
   - Maintaining UI state during operations
   - Providing progress feedback for long-running tasks

### Recent Changes

1. Added Import/Export buttons to CorrectionRuleView header
2. Fixed test compatibility issues
3. Updated cell highlighting to match color legend
4. Enhanced CorrectionController with cell status methods
5. Simplified CorrectionRule data structure
6. Fixed issues with rule deletion

## Implementation Plan

The implementation is divided into phases:

### Phase 1: Core Data Model ✓
- ✅ Implement CorrectionRule and CorrectionRuleManager
- ✅ Create unit tests for model classes
- ✅ Simplify data structure by removing redundant fields

### Phase 2: Services Layer ✓
- ✅ Implement CorrectionService with two-pass algorithm
- ✅ Add configuration integration
- ✅ Create unit tests for services

### Phase 3: Controller Layer ✓
- ✅ Implement CorrectionController and background worker
- ✅ Handle rule management operations
- ✅ Create unit tests for controller
- ✅ Fix deletion issues with robust error handling

### Phase 4: UI Components (In Progress)
- ✅ Create CorrectionView and rule table
- ✅ Implement edit rule dialog
- ✅ Implement batch correction dialog (basic functionality)
- ✅ Add progress dialog for feedback
- ✅ Add status bar with rule counts
- ✅ Implement Import/Export buttons in header
- 🔄 Create context menu for DataView cells
- 🔄 Enhance Import/Export dialog
- 🔄 Improve batch correction dialog
- 🔄 Add settings panel with configuration options

### Phase 5: Data View Integration (In Progress)
- ✅ Add cell highlighting based on status
- ✅ Add color legend for highlighting
- ✅ Add tooltips for cell status
- 🔄 Implement context menu integration
- 🔄 Complete end-to-end testing and refinement

### Phase 6: Testing and Optimization (Next)
- 🔄 Create integration tests
- 🔄 Optimize performance for large datasets
- 🔄 Ensure proper encoding support

## Current Test Status

After implementing the correction feature UI components and data view integration, the test status is:

- 448 passing tests (79%)
- 49 failing tests (9%)
- 62 errors (11%)
- 6 skipped tests (1%)

### Known Issues

1. Performance issues with cell highlighting for large datasets
2. Tooltip display sometimes not appearing correctly
3. Selection handling in batch correction dialog needs improvement
4. Import/Export dialog needs better error handling

## Ongoing Discussions

1. Performance optimizations for large datasets
2. View communication strategies
3. Error handling approaches for correction operations
4. UX refinements for batch operations

## Active Development Focus

**Last Update:** May 16, 2024

We're working on migrating the application from tab-based interfaces to the new view-based architecture, which provides better separation of concerns and improved component reusability.

### Current Task Focus

- Completing migration from tab-based UI to view-based architecture
- Cleaning up redundant code and adding deprecation warnings to legacy components
- ✅ Implementing new ChartView component to replace ChartViewAdapter
- ✅ Creating comprehensive tests for ChartView
- Updating remaining legacy tests to use modern view components

### Recent Codebase Cleanup

- **May 16, 2024**: Created unit tests for ChartView in tests/unit/ui/views/test_chart_view.py
- **May 16, 2024**: Added deprecation warnings to `correction_view_adapter.py` (MainWindow already uses CorrectionView directly)
- **May 16, 2024**: Added deprecation warnings to `chart_view_adapter.py` and updated MainWindow to use ChartView directly
- **May 16, 2024**: Fixed imports in views/__init__.py to remove non-existent components
- **May 15, 2024**: Removed redundant ServiceLocator implementation (deleted `chestbuddy/core/service_locator.py`)
- **May 15, 2024**: Added deprecation warnings to legacy UI components (CorrectionTab and ChartTab)
- **May 15, 2024**: Added debugging utility notice to signal_tracer.py

### Next Steps

1. Update remaining tests to use view-based components directly
2. Fix remaining failing tests related to the UI migration
3. Remove deprecated components once all dependencies are addressed
4. Finalize documentation to reflect the new architecture

### Development Environment

- Using uv for package management and virtual environment
- Active Python version: 3.12.9
- IDE: Cursor
- PySide6 6.8.2.1 for Qt UI components

### Focus Areas

- UI architecture improvements
- Test coverage enhancement
- Code quality and maintainability 
- Documentation updates

## Current Focus

The primary focus is updating and modernizing the UI architecture of the application. We are transitioning from a tab-based interface to a more modern view-based architecture.

### Status

1. **ChartView Implementation**: Complete
   - Successfully created a separate ChartView component
   - MainWindow now uses ChartView directly rather than embedding it in a tab
   - All ChartView unit tests have been fixed and are passing

2. **MainWindow Updates**: In Progress
   - Updated to use the new view-based approach
   - Several tests still need updates due to changes in menu structure and file operations
   - Navigation sidebar has been integrated

3. **ValidationTabView**: In Progress
   - Initial implementation complete
   - Tests being developed
   - Some signal/slot connections need refinement

4. **CorrectionView**: Planned
   - Design finalized
   - Implementation planned after ValidationTabView is complete

### Next Steps

1. **Testing**:
   - Update remaining MainWindow tests to work with new architecture - Test update plan created
   - Create comprehensive ValidationTabView tests
   - Plan CorrectionView tests

2. **Implementation**:
   - Complete ValidationTabView signal handling
   - Implement CorrectionView
   - Replace all legacy tab components with view components

3. **Bug Fixes**:
   - Fix signal disconnection warnings during application close
   - Address C++ object deletion issues with data model in tests
   - Update menu structure tests

### Recent Changes

1. **Architecture**:
   - Refactored MainWindow to use view components instead of tabs
   - Created separate ChartView component with full functionality
   - Updated navigation system to switch between views

2. **Testing**:
   - Fixed ChartView tests to work with new component structure
   - Updated test fixtures to handle view components
   - Added signal testing improvements
   - Created comprehensive test update plan for MainWindow tests

3. **UI/UX**:
   - Improved navigation sidebar visuals
   - Enhanced status bar feedback
   - Updated menu structure to reflect new architecture

### Current Challenges

1. **Test Compatibility**:
   - Many tests were designed for the old tab-based architecture
   - Need to update tests to match new component structure without changing test intent
   - Signal testing is more complex with the new architecture
   - Created test update plan to address systematically

2. **Signal Management**:
   - Signal disconnection warnings during application close
   - Need to improve signal/slot connection management
   - Some signals not properly disconnected when views are destroyed

3. **View Lifecycle**:
   - Ensuring proper initialization and cleanup of view components
   - Managing shared resources between views
   - Coordinating view transitions

---

## MainWindow Tests Update Plan

To address the testing challenges with the new view-based architecture, we've created a comprehensive test update plan that outlines how to update the MainWindow tests. The plan is stored in `memory-bank/test_update_plan.md` and includes:

1. **Understanding the Architectural Changes**:
   - From tab-based to view-based
   - Controller-based coordination
   - Signal flow changes
   - Menu structure updates

2. **Test Update Strategy**:
   - Categorizing tests by update complexity
   - Controller call verification patterns
   - Signal verification patterns
   - Component initialization considerations

3. **Implementation Plan**:
   - Phase 1: Basic test fixes
   - Phase 2: Core functionality tests
   - Phase 3: Advanced tests
   - Phase 4: Final review

4. **Specific Test Examples**:
   - Menu action tests
   - View navigation tests
   - File operation tests
   - UI state tests
   - Signal handling tests

This plan will guide the updates to all MainWindow tests to align with the new architecture.

---

## Technical Decisions

### View-Based Architecture

**Decision**: Replace tab-based interface with dedicated view components.

**Rationale**:
- Improved separation of concerns
- Better testability of individual components
- More modern UI approach
- Easier to add new views or rearrange existing ones

**Implementation**:
- Each view is a self-contained QWidget subclass
- MainWindow manages view switching and coordination
- Views communicate through signals/slots and view controllers
- Common functionality extracted to base classes or utility functions

### Signal/Slot Architecture

We're reinforcing our commitment to a signal/slot architecture for component communication:

1. **View Components**:
   - Emit signals when user actions occur
   - Provide slots for external actions to affect the view
   - Do not directly call methods on other components

2. **Controllers**:
   - Connect signals from views to appropriate handlers
   - Coordinate between models and views
   - Manage application state

3. **Services**:
   - Provide business logic implementation
   - Emit signals when state changes
   - Accept calls from controllers to perform operations

### Testing Strategy

We're updating our testing approach to match the new architecture:

1. **Component Tests**:
   - Test each view component in isolation
   - Mock dependencies (models, services)
   - Verify signals are emitted correctly
   - Verify UI updates in response to external signals

2. **Integration Tests**:
   - Test interactions between components
   - Verify correct signal propagation
   - Test data flow through the system

3. **Signal Testing**:
   - Use qtbot.waitSignal for asynchronous operations
   - Test signal emissions with correct parameters
   - Test signal chains (when one signal triggers another)
   
4. **Controller-Based Testing**:
   - Test through controller interfaces rather than direct UI inspection
   - Verify controller methods are called with correct parameters
   - Focus on behavior rather than implementation details

---

## UI State

### Current Components

1. **MainWindow**:
   - Acts as the container for all views
   - Manages menu actions
   - Handles file operations
   - Manages application state

2. **ChartView**:
   - Displays data visualizations
   - Allows switching between chart types
   - Provides customization options
   - Handles user interactions with charts

3. **ValidationTabView**:
   - Manages validation rules
   - Displays validation results
   - Allows editing/creation of validation rules
   - Provides data filtering based on validation status

4. **DashboardView**:
   - Displays summary information
   - Shows recent activity
   - Provides quick access to common tasks

### Planned Components

1. **CorrectionView**:
   - Manages correction rules
   - Displays correction results
   - Allows editing/creation of correction rules
   - Provides data transformation functionality

2. **SettingsView**:
   - Manages application settings
   - Provides configuration options
   - Handles import/export of settings

3. **ReportView**:
   - Generates reports from data
   - Provides report templates
   - Allows customization of reports
   - Handles export to various formats

---

## Data Architecture

### Core Models

1. **ChestDataModel**:
   - Central data structure for application
   - Stores imported data
   - Provides access to data through Qt's Model/View framework
   - Handles data updates and notifications

2. **ValidationListModel**:
   - Stores validation rules
   - Provides access to validation lists
   - Handles validation rule updates

3. **ValidationResultModel**:
   - Stores validation results
   - Maps results to data rows
   - Provides filtering based on validation status

### Key Services

1. **ValidationService**:
   - Performs data validation
   - Manages validation rules
   - Provides validation results

2. **CorrectionService**:
   - Applies correction rules to data
   - Manages correction rule definitions
   - Handles data transformations

3. **ConfigManager**:
   - Manages application configuration
   - Handles settings persistence
   - Provides access to configuration options

---

## Testing Status

### Passing Tests

1. **ChartView Tests**:
   - All tests passing
   - Chart creation tests
   - Chart type switching tests
   - Data update tests
   - User interaction tests

2. **Model Tests**:
   - Most ChestDataModel tests passing
   - ValidationListModel tests passing
   - ValidationResultModel tests passing

3. **Service Tests**:
   - ValidationService tests passing
   - ConfigManager tests passing
   - Most CorrectionService tests passing

### Failing Tests

1. **MainWindow Tests**:
   - File operation tests failing (updated menu structure)
   - Tab switching tests failing (no longer using tabs)
   - View coordination tests need updates
   - Test update plan created to address these systematically

2. **Integration Tests**:
   - Some signal chain tests failing
   - View interaction tests need updates

### New Tests Needed

1. **View Component Tests**:
   - ValidationTabView tests
   - CorrectionView tests
   - SettingsView tests

2. **Controller Tests**:
   - ViewStateController tests
   - DataViewController tests
   - UIStateController tests

---

## Current Bugs/Issues

1. **Signal Disconnection Warnings**:
   - Warnings when application closes:
   ```
   QObject::disconnect: Unexpected null parameter
   ```
   - Likely caused by components being destroyed before signals are disconnected
   - Need to implement proper cleanup in component destructors

2. **C++ Object Deletion Issues**:
   - Some tests fail with:
   ```
   RuntimeError: Internal C++ object (ChestDataModel) already deleted.
   ```
   - Need to ensure proper ownership and lifecycle management
   - Use ParentObject pattern more consistently

3. **Menu Structure Tests**:
   - Tests expecting old menu structure
   - Need to update tests to match new menu organization
   - Some actions moved to view-specific menus

4. **File Operation Changes**:
   - File operations now handled by FileOperationsController
   - Tests directly calling MainWindow methods need updates
   - Need to test controller instead of implementation details

5. **Inconsistent View State**:
   - Sometimes views don't update when data changes
   - Need to ensure all views are properly connected to data model signals
   - Some signal connections missing or incorrect

# Active Context

## Current Focus

The current focus is on improving the correction system in ChestBuddy to address several identified issues and enhance functionality.

## Correction System Improvement Project (2023-04-01)

### Overview

We are implementing a series of improvements to the correction system to address the issue of corrections not being applied correctly. The detailed plans and documentation for this work are located in:

- `plans/correction_system_improvements_plan.md` - Detailed implementation plan using Test-Driven Development
- `plans/correction_ui_mockup.md` - User interface mockups for the improved correction system
- `plans/correction_system_technical_implementation.md` - Technical implementation details

### Key Issues Identified

1. **Recursive Correction:** Currently, corrections are only applied once. If a corrected value would match another rule, that secondary correction is not applied.
2. **Selection-Based Correction:** Users should be able to apply corrections to a specific selection of cells.
3. **Correctable Status Detection:** The system needs to identify which invalid entries can be fixed with available correction rules.
4. **Auto-Correction Options:** More flexible configuration for when corrections are automatically applied.

### Implementation Approach

We are following a Test-Driven Development approach across four primary phases:

1. **Phase 1: Recursive Correction**
   - Implement and test recursive correction functionality
   - Fix the current issue with the `apply_corrections` method parameters

2. **Phase 2: Selection-Based Correction**
   - Enable applying corrections to selected data only
   - Implement context menu and UI integration

3. **Phase 3: Correctable Status Detection**
   - Extend ValidationStatus enum with CORRECTABLE state
   - Implement detection of correctable entries

4. **Phase 4: Auto-Correction Options**
   - Add configuration options for auto-correction
   - Implement UI components for correction settings

## Recent Changes

- Fixed a bug in the `_apply_corrections_task` method where it was incorrectly passing the `recursive` parameter to the `apply_corrections` method
- Created comprehensive planning documents for the correction system improvements
- Designed UI mockups for the improved correction features

## Next Steps

1. Implement tests for the recursive correction functionality
2. Implement recursive correction in the CorrectionService and CorrectionController
3. Update the ValidationStatus enum to include correctable states
4. Implement the UI changes according to the mockups
5. Update the configuration manager to include new correction settings

## Active Decisions

- We have decided to extend the ValidationStatus enum with CORRECTABLE and CORRECTED states
- We will implement the recursive correction with cycle detection to prevent infinite loops
- We will add selection-based correction with context menu integration
- We will enhance the correction UI to show correctable items and correction counts
