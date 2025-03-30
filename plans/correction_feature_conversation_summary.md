# Correction Feature Refactoring: Conversation Summary

## Project Background

The ChestBuddy application needs a refactored correction feature to replace the existing general correction strategies with a more targeted, mapping-based approach for data corrections. The user has specified requirements for a robust, user-friendly system that allows precise cell-level corrections using a CSV format for mapping incorrect values to correct ones.

## Key Requirements

1. **Precise Cell-Level Corrections**
   - Replace general corrections with mapping-based approach
   - Support category-based rules (player, chest_type, source, general)
   - Implement rule prioritization (order-based within categories)

2. **CSV-Based Rule Management**
   - Support for import/export functionality
   - Alphabetical sorting capabilities
   - Enable/disable individual rules
   - UTF-8 encoding support for German and international characters

3. **Improved UI Experience**
   - Dropdown lists for entries
   - Status bar for statistics
   - Multiple cell selection for batch corrections
   - Color-coded cell highlighting
   - Intuitive rule management interface

4. **Performance Optimization**
   - Background processing for large datasets
   - Progress dialog during corrections
   - Responsive UI during processing
   - Confirmation dialog as part of progress dialog
   - Summary displayed in status bar upon completion

5. **Integration with Validation**
   - Option to correct only invalid entries
   - Visual indicators for invalid and correctable cells
   - Tooltips showing correction details

## Architectural Approach

The implementation will follow an MVC (Model-View-Controller) architecture with clear separation of concerns:

1. **Model Layer**
   - `CorrectionRule` class for representing individual rules
   - `CorrectionRuleManager` for rule storage and management

2. **Service Layer**
   - `CorrectionService` for implementing correction algorithms
   - Two-pass algorithm for applying rules in priority order
   - Integration with validation system

3. **Controller Layer**
   - `CorrectionController` for mediating between views and services
   - Background processing using `CorrectionWorker`
   - Configuration management

4. **View Layer**
   - `CorrectionView` for rule management UI
   - `CorrectionRuleTable` for rule display and interaction
   - `BatchCorrectionDialog` for creating multiple rules
   - `CorrectionProgressDialog` for feedback during processing

## Implementation Plan

The implementation is divided into six phases spanning approximately 14 days:

1. **Core Data Model (Days 1-2)**
   - Implement `CorrectionRule` and `CorrectionRuleManager`
   - Create unit tests for model classes

2. **Services Layer (Days 3-4)**
   - Implement `CorrectionService` with two-pass algorithm
   - Add configuration integration
   - Create unit tests for services

3. **Controller Layer (Days 5-6)**
   - Implement `CorrectionController` and background worker
   - Handle rule management operations
   - Create unit tests for controller

4. **UI Implementation (Days 7-10)**
   - Create `CorrectionView` and rule table
   - Implement batch correction dialog
   - Add progress dialog for feedback

5. **Data View Integration (Days 11-12)**
   - Add cell highlighting based on status
   - Implement context menu integration
   - Add tooltips for cell status

6. **Testing and Optimization (Days 13-14)**
   - Create integration tests
   - Optimize performance for large datasets
   - Ensure proper encoding support

## UI Mockups and Features

### Correction View
- Rule table with columns for from/to values, category, status
- Buttons for add, edit, delete rules
- Import/export buttons
- Reordering capabilities (move up/down/top/bottom)
- Status bar showing statistics

### Batch Creation Dialog
- Grid interface for multiple rule creation
- Dropdowns for categories and to-values
- Options for auto-enable and add to validation
- Preview capability

### Progress Dialog
- Progress bar showing current/total operations
- Status message with current operation
- Confirmation button for applying changes
- Cancel button for aborting operation

### Data View Integration
- Color-coded highlighting:
  - Red: Invalid without correction
  - Orange: Invalid with available correction
  - Green: Corrected cell
  - Purple: Correctable but not invalid/corrected
- Context menu options for creating correction rules
- Tooltips showing correction details

## Technical Decisions

1. **Two-Pass Correction Algorithm**
   - First pass: Apply general rules
   - Second pass: Apply category-specific rules
   - Within each pass, apply rules in order of priority

2. **Background Processing**
   - Use `QThread` and worker pattern for UI responsiveness
   - Implement progress reporting and cancelation
   - Handle errors gracefully

3. **CSV File Format**
   - UTF-8 encoding with fallback to latin1
   - Header format: To,From,Category,Status,Order
   - Support for import/export with options

4. **Configuration Integration**
   - Store settings in ConfigManager
   - Options for auto-correct after validation
   - Option to correct only invalid cells
   - Option for imported rules auto-enable

5. **Rule Prioritization**
   - General rules applied first (to all columns)
   - Category-specific rules applied second (to specific columns)
   - Within each category, rules applied in order specified

## Open Questions and Future Enhancements

1. Future implementation of smart matching using NLP techniques
2. Additional optimizations for very large datasets
3. Enhanced rule suggestion based on validation patterns

## Timeline and Milestones

- **Days 1-2**: Core Data Model Implementation
- **Days 3-4**: Services Layer Implementation
- **Days 5-6**: Controller Layer Implementation
- **Days 7-10**: UI Implementation
- **Days 11-12**: Data View Integration
- **Days 13-14**: Testing and Optimization 