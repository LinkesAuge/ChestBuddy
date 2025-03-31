# Codebase Cleanup Documentation

## Summary

This document records cleanup activities performed on the ChestBuddy codebase to reduce redundancy and technical debt.

## Completed Cleanup Actions (2024-05-15)

1. **Removed Redundant Service Locator Implementation**
   - Deleted `chestbuddy/core/service_locator.py` 
   - All code now uses `chestbuddy/utils/service_locator.py`

2. **Added Deprecation Warnings to Legacy UI Components**
   - Added warnings to `chestbuddy/ui/validation_tab.py`
   - Added warnings to `chestbuddy/ui/correction_tab.py`
   - Added warnings to `chestbuddy/ui/chart_tab.py`
   - Marked signal_tracer.py as a debug-only utility

## Future Cleanup Tasks

1. **Remove Legacy UI Components**
   - Once all adapter views are refactored to not depend on legacy components, remove:
     - `chestbuddy/ui/validation_tab.py`
     - `chestbuddy/ui/correction_tab.py`
     - `chestbuddy/ui/chart_tab.py`

2. **Update Tests**
   - Update tests to use the new view-based components directly
   - Tests to be updated include:
     - `tests/test_ui_components.py`
     - `tests/test_main_window.py`
     - `tests/test_chart_tab.py`
     - `tests/test_chart_tab_simple.py`
     - `tests/test_mainwindow_chart_integration.py`

3. **Refactor Adapter Views**
   - Refactor these adapter views to not depend on the legacy components:
     - `chestbuddy/ui/views/chart_view_adapter.py`
     - `chestbuddy/ui/views/validation_view_adapter.py`
     - `chestbuddy/ui/views/correction_view_adapter.py`

4. **Organize Debug Utilities**
   - Move debug-only utilities to a dedicated debug or tools directory
   - Consider creating a proper debug module for development tools

## Implementation Guidelines

When refactoring adapter views:
1. Copy essential functionality from the legacy components
2. Remove dependencies on legacy components
3. Update tests to work with refactored components
4. Apply consistent naming conventions 
5. Ensure backward compatibility with existing signals

## Monitoring Plan

1. Watch for deprecation warnings during development and testing
2. Monitor test results to ensure functionality is maintained
3. Track any issues related to the refactored components
4. Document any regressions or unexpected behavior 