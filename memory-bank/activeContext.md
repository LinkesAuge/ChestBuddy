---
title: ChestBuddy Active Development Context
date: 2024-03-30
---

# Active Context

*Last Updated: March 30, 2024*

## Current Focus

The current focus is on refactoring the correction feature in the ChestBuddy application. This refactoring will implement a more targeted, mapping-based approach for data corrections, replacing the existing general correction strategies with a precise system for mapping incorrect values to their correct equivalents.

### Key Aspects

#### 1. Precise Cell-Level Corrections
- Implementing a mapping-based correction system that allows correcting specific cell values
- Supporting category-based rules (player, chest_type, source, general)
- Implementing rule prioritization (specific over general, order-based within categories)

#### 2. CSV-Based Rule Management
- Supporting import/export functionality for correction rules
- Implementing alphabetical sorting capabilities
- Enabling/disabling individual rules
- Ensuring UTF-8 encoding support for German and international characters

#### 3. Improved UI Experience
- Designing an intuitive interface for rule management
- Implementing batch creation for multiple rules
- Providing visual feedback through color-coded cell highlighting
- Adding status bar for statistics and summary information

#### 4. Performance Considerations
- Implementing background processing for large datasets
- Creating progress dialog with cancelation capability
- Ensuring responsive UI during processing
- Providing summary information upon completion

#### 5. Integration with Validation
- Connecting correction system with existing validation functionality
- Adding option to correct only invalid entries
- Implementing visual indicators for invalid and correctable cells

## Implementation Plan

### Phase 1: Core Data Model (Days 1-2)
- Create `CorrectionRule` model class
- Implement `CorrectionRuleManager` for rule storage and operations
- Develop unit tests for model layer

### Phase 2: Services Layer (Days 3-4)
- Implement `CorrectionService` with two-pass algorithm
- Add configuration integration through ConfigManager
- Create unit tests for services layer

### Phase 3: Controller Layer (Days 5-6)
- Implement `CorrectionController` for mediating between views and services
- Develop background worker for processing large datasets
- Develop unit tests for controller layer

### Phase 4: UI Implementation (Days 7-10)
- Create `CorrectionView` for rule management
- Implement `CorrectionRuleTable` for displaying and editing rules
- Add `BatchCorrectionDialog` for creating multiple rules at once
- Develop `CorrectionProgressDialog` for processing feedback

### Phase 5: Data View Integration (Days 11-12)
- Implement cell highlighting based on correction status
- Add context menu integration for creating rules from cells
- Create tooltips showing correction details

### Phase 6: Testing and Optimization (Days 13-14)
- Develop integration tests for end-to-end workflows
- Optimize performance for large datasets
- Ensure proper encoding support for international characters

## Current Tasks

1. **Design and Implement Model Layer**
   - Create `CorrectionRule` class with attributes and methods
   - Implement `CorrectionRuleManager` for CRUD operations
   - Develop serialization/deserialization for CSV format

2. **Develop Services Layer**
   - Implement two-pass correction algorithm
   - Create integration with ConfigManager
   - Build connection with ValidationService

3. **Create Controller and Worker Classes**
   - Implement `CorrectionController` with required methods
   - Develop background worker for processing
   - Set up signal/slot connections for UI updates

4. **Design and Implement UI Components**
   - Create rule management view with table and controls
   - Implement batch correction dialog
   - Develop progress dialog with cancelation

5. **Integrate with Data View**
   - Add cell highlighting functionality
   - Implement context menu actions
   - Create tooltips for cell status

## Technical Decisions

1. **Two-Pass Correction Algorithm**
   - First pass: Apply general rules to all columns
   - Second pass: Apply category-specific rules to their respective columns
   - Within each pass, rules are applied in order of priority

2. **Background Processing Pattern**
   - Use `QThread` with worker object pattern
   - Implement progress reporting through signals
   - Handle cancelation and error cases

3. **CSV File Format**
   - Use UTF-8 encoding with fallback to latin1
   - Header format: To,From,Category,Status,Order
   - Support import/export with options for appending/overwriting

4. **Rule Prioritization**
   - General rules applied first (to all columns)
   - Category-specific rules applied second (to specific columns)
   - Within each category, rules applied in order specified
   - User can reorder rules to change priority

## Ongoing Discussions

1. **Future Enhancements**
   - Potential implementation of smart matching using NLP techniques
   - Additional optimizations for very large datasets
   - Enhanced rule suggestion based on validation patterns

2. **Performance Considerations**
   - Vectorized operations for efficiently processing large datasets
   - Chunked processing to maintain UI responsiveness
   - Caching validation results to avoid redundant calculations
