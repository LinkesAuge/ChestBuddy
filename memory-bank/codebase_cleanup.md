# Codebase Cleanup Documentation

## Summary

This document records cleanup activities performed on the ChestBuddy codebase to reduce redundancy and technical debt.

## Completed Cleanup Actions (2024-05-15)

1. **Removed Redundant Service Locator Implementation**
   - Deleted `chestbuddy/core/service_locator.py` 
   - All code now uses `chestbuddy/utils/service_locator.py`

2. **Added Deprecation Warnings to Legacy UI Components**
   - Added warnings to `chestbuddy/ui/correction_tab.py`
   - Added warnings to `chestbuddy/ui/chart_tab.py`
   - Marked signal_tracer.py as a debug-only utility
   - Added warnings to `chestbuddy/ui/views/correction_view_adapter.py` (2024-05-16)
   - Added warnings to `chestbuddy/ui/views/chart_view_adapter.py` (2024-05-16)

3. **Deleted Legacy Components**
   - Deleted `chestbuddy/ui/validation_tab.py` as it has been replaced by ValidationTabView
   - Updated tests in `tests/test_ui_components.py` to use ValidationTabView

## Current Refactoring Status

1. **UI Component Migration Progress**
   - ValidationTab → ValidationTabView: ✓ Complete (component deleted)
   - CorrectionTab → CorrectionView: 🔄 In Progress
     - MainWindow now uses CorrectionView directly
     - CorrectionViewAdapter still uses CorrectionTab and is marked deprecated
   - ChartTab → ChartView: 🔄 In Progress
     - ChartViewAdapter still depends on ChartTab and is marked deprecated
     - ChartView component needs to be implemented

2. **Adapter Status**
   - ValidationViewAdapter: Uses ValidationTabView (modern component)
   - CorrectionViewAdapter: Still uses CorrectionTab (legacy component)
     - Now marked deprecated with warnings
     - Will be removed once all code uses CorrectionView directly
   - ChartViewAdapter: Still uses ChartTab (legacy component)
     - Now marked deprecated with warnings
     - Will be replaced by ChartView in a future release

## Future Cleanup Tasks

1. **Remove Remaining Legacy UI Components**
   - Once all adapter views are refactored to not depend on legacy components, remove:
     - `chestbuddy/ui/correction_tab.py`
     - `chestbuddy/ui/chart_tab.py`
     - `chestbuddy/ui/views/correction_view_adapter.py`
     - `chestbuddy/ui/views/chart_view_adapter.py`

2. **Update Tests**
   - Update remaining tests to use the new view-based components directly
   - Tests to be updated include:
     - `tests/test_chart_tab.py`
     - `tests/test_chart_tab_simple.py`
     - `tests/test_mainwindow_chart_integration.py`
   - Completed test updates:
     - `tests/test_main_window.py` - Updated fixtures to support the new MainWindow constructor (2024-05-16)
       - Added mock objects for all required dependencies
       - Updated assertions to focus on core functionality rather than specific UI implementation

3. **Refactor Adapter Views**
   - Refactor these adapter views to not depend on the legacy components:
     - `chestbuddy/ui/views/chart_view_adapter.py`

4. **Implement Missing View Components**
   - Create `ChartView` component to replace `ChartViewAdapter` and `ChartTab`
   - Follow the same pattern as `CorrectionView`

5. **Organize Debug Utilities**
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

## Migration Notes

### CorrectionTab to CorrectionView
- The main application window already uses CorrectionView directly
- CorrectionViewAdapter was kept for backward compatibility but is now marked deprecated
- CorrectionView has been designed with the same signals as CorrectionViewAdapter for compatibility
- Once all code uses CorrectionView directly, both CorrectionViewAdapter and CorrectionTab can be removed

### ChartTab to ChartView
- ChartViewAdapter currently wraps ChartTab but has been marked as deprecated
- A new ChartView component needs to be implemented following the same pattern as CorrectionView
- The MainWindow still imports and uses ChartViewAdapter
- Once ChartView is implemented, MainWindow should be updated to use it directly 