@echo off
REM Script to run all validation-related tests to verify the validation workflow integration

echo ============================================
echo Running Validation Integration Tests
echo ============================================

REM Create directory for test results
set RESULTS_DIR=test_results
if not exist %RESULTS_DIR% mkdir %RESULTS_DIR%

REM Run individual validation tests
echo Running test: test_validation_service.py
python -m pytest tests/test_validation_service.py -v > "%RESULTS_DIR%\test_validation_service_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_service.py
) else (
    echo [FAIL] test_validation_service.py - See details in: %RESULTS_DIR%\test_validation_service_output.txt
)

echo Running test: test_validation_list_model.py
python -m pytest tests/test_validation_list_model.py -v > "%RESULTS_DIR%\test_validation_list_model_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_list_model.py
) else (
    echo [FAIL] test_validation_list_model.py - See details in: %RESULTS_DIR%\test_validation_list_model_output.txt
)

echo Running test: test_validation_list_view.py
python -m pytest tests/ui/test_validation_list_view.py -v > "%RESULTS_DIR%\test_validation_list_view_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_list_view.py
) else (
    echo [FAIL] test_validation_list_view.py - See details in: %RESULTS_DIR%\test_validation_list_view_output.txt
)

echo Running test: test_validation_preferences_view.py
python -m pytest tests/ui/test_validation_preferences_view.py -v > "%RESULTS_DIR%\test_validation_preferences_view_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_preferences_view.py
) else (
    echo [FAIL] test_validation_preferences_view.py - See details in: %RESULTS_DIR%\test_validation_preferences_view_output.txt
)

echo Running test: test_validation_tab_view.py
python -m pytest tests/ui/test_validation_tab_view.py -v > "%RESULTS_DIR%\test_validation_tab_view_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_tab_view.py
) else (
    echo [FAIL] test_validation_tab_view.py - See details in: %RESULTS_DIR%\test_validation_tab_view_output.txt
)

echo Running test: test_ui_state_controller.py
python -m pytest tests/test_ui_state_controller.py -v > "%RESULTS_DIR%\test_ui_state_controller_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_ui_state_controller.py
) else (
    echo [FAIL] test_ui_state_controller.py - See details in: %RESULTS_DIR%\test_ui_state_controller_output.txt
)

echo Running test: test_ui_state_controller_validation_integration.py
python -m pytest tests/integration/test_ui_state_controller_validation_integration.py -v > "%RESULTS_DIR%\test_ui_state_controller_validation_integration_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_ui_state_controller_validation_integration.py
) else (
    echo [FAIL] test_ui_state_controller_validation_integration.py - See details in: %RESULTS_DIR%\test_ui_state_controller_validation_integration_output.txt
)

echo Running test: test_validation_view_controller_integration.py
python -m pytest tests/integration/test_validation_view_controller_integration.py -v > "%RESULTS_DIR%\test_validation_view_controller_integration_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_view_controller_integration.py
) else (
    echo [FAIL] test_validation_view_controller_integration.py - See details in: %RESULTS_DIR%\test_validation_view_controller_integration_output.txt
)

echo Running test: test_validation_workflow_end_to_end.py
python -m pytest tests/integration/test_validation_workflow_end_to_end.py -v > "%RESULTS_DIR%\test_validation_workflow_end_to_end_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] test_validation_workflow_end_to_end.py
) else (
    echo [FAIL] test_validation_workflow_end_to_end.py - See details in: %RESULTS_DIR%\test_validation_workflow_end_to_end_output.txt
)

echo Running all tests with 'validation' in the name or docstring
python -m pytest -xvs -k "validation" > "%RESULTS_DIR%\all_validation_tests_output.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [PASS] All validation keyword tests
) else (
    echo [FAIL] Some validation keyword tests failed - See details in: %RESULTS_DIR%\all_validation_tests_output.txt
)

echo ============================================
echo Test run complete
echo See detailed results in the %RESULTS_DIR% directory
echo ============================================

pause 