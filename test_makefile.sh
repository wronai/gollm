#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a test and display result
test_make_target() {
    local target=$1
    local description=$2
    
    echo -e "${YELLOW}Testing: ${description} (make ${target})...${NC}"
    
    # Run the test
    ansible-playbook test_makefile.yml --tags "${target}" -v
    
    # Check the result
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED: make ${target}${NC}\n"
        return 0
    else
        echo -e "${RED}✗ FAILED: make ${target}${NC}\n"
        return 1
    fi
}

# Create a temporary directory for logs
LOG_DIR="/tmp/gollm_test_$(date +%s)"
mkdir -p "${LOG_DIR}"

# List of targets to test
declare -A TARGETS=(
    [help]="Display help information"
    [setup]="Setup development environment"
    [test]="Run tests"
    [test-coverage]="Run tests with coverage"
    [lint]="Run linters"
    [format]="Format code"
    [build]="Build package"
    [docs]="Build documentation"
    [clean]="Clean build artifacts"
)

# Test each target
PASSED=0
FAILED=0
SKIPPED=0

echo "Starting Makefile tests..."

for target in "${!TARGETS[@]}"; do
    description="${TARGETS[$target]}"
    LOG_FILE="${LOG_DIR}/${target}.log"
    
    # Skip certain targets if needed
    if [[ "$target" == "publish" || "$target" == "publish-test" ]]; then
        echo -e "${YELLOW}SKIPPING: make ${target} (requires manual testing)${NC}"
        ((SKIPPED++))
        continue
    fi
    
    # Run the test and capture output
    test_make_target "$target" "$description" &> "$LOG_FILE"
    
    # Check result
    if [ $? -eq 0 ]; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    
    # Show last 5 lines of log
    echo "Last 5 lines of output:"
    tail -n 5 "$LOG_FILE"
    echo -e "\nFull log: ${LOG_FILE}\n"
done

# Print summary
echo -e "\nTest Summary:"
echo -e "${GREEN}✓ PASSED: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ FAILED: ${FAILED}${NC}"
fi
if [ $SKIPPED -gt 0 ]; then
    echo -e "${YELLOW}↷ SKIPPED: ${SKIPPED}${NC}"
fi

exit $((FAILED > 0 ? 1 : 0))
