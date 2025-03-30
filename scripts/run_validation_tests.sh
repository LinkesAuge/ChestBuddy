#!/bin/bash

# Script to run all validation-related tests to verify the validation workflow integration

# Set up color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Running Validation Integration Tests${NC}"
echo -e "${BLUE}============================================${NC}"

# Create directory for test results
RESULTS_DIR="test_results"
mkdir -p $RESULTS_DIR

# Function to run a test and check its result
run_test() {
    local test_path=$1
    local test_name=$(basename $test_path)
    
    echo -e "${YELLOW}Running test: ${test_name}${NC}"
    
    # Run the test and save output
    python -m pytest $test_path -v > "$RESULTS_DIR/${test_name%.py}_output.txt" 2>&1
    
    # Check if test passed
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Test passed: ${test_name}${NC}"
        return 0
    else
        echo -e "${RED}❌ Test failed: ${test_name}${NC}"
        echo -e "${RED}See details in: $RESULTS_DIR/${test_name%.py}_output.txt${NC}"
        return 1
    fi
}

# List of validation-related test files
VALIDATION_TESTS=(
    "tests/test_validation_service.py"
    "tests/test_validation_list_model.py"
    "tests/ui/test_validation_list_view.py"
    "tests/ui/test_validation_preferences_view.py"
    "tests/ui/test_validation_tab_view.py"
    "tests/ui/widgets/test_validation_status_delegate.py"
    "tests/test_ui_state_controller.py"
    "tests/integration/test_ui_state_controller_validation_integration.py"
    "tests/integration/test_validation_view_controller_integration.py"
    "tests/integration/test_validation_workflow_end_to_end.py"
)

# Track failures
FAILURES=0

# Run each test
for test in "${VALIDATION_TESTS[@]}"; do
    if [ -f "$test" ]; then
        run_test "$test" || ((FAILURES++))
    else
        echo -e "${RED}Test file not found: ${test}${NC}"
        ((FAILURES++))
    fi
    echo ""
done

# Run all validation tests with a keyword filter
echo -e "${YELLOW}Running all tests with 'validation' in the name or docstring${NC}"
python -m pytest -xvs -k "validation" > "$RESULTS_DIR/all_validation_tests_output.txt" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All validation keyword tests passed${NC}"
else
    echo -e "${RED}❌ Some validation keyword tests failed${NC}"
    echo -e "${RED}See details in: $RESULTS_DIR/all_validation_tests_output.txt${NC}"
    ((FAILURES++))
fi

# Summary
echo -e "${BLUE}============================================${NC}"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All validation tests passed!${NC}"
    exit 0
else
    echo -e "${RED}${FAILURES} test groups failed!${NC}"
    echo -e "${RED}See test results in the ${RESULTS_DIR} directory${NC}"
    exit 1
fi 