#!/bin/bash
# Test execution script for DataLogicEngine
# Ensures proper environment setup before running tests

set -e  # Exit on error

echo "========================================="
echo "DataLogicEngine Test Runner"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found. Installing dependencies...${NC}"
    pip install -q pytest pytest-cov pytest-asyncio
    echo -e "${GREEN}✓ Test dependencies installed${NC}"
fi

# Set test environment variables
export FLASK_ENV=testing
export TESTING=true
export SECRET_KEY=test-secret-key-for-testing-only
export SESSION_SECRET=test-session-secret-for-testing-only
export JWT_SECRET_KEY=test-jwt-secret-for-testing-only
export DATABASE_URL=sqlite:///test.db

echo ""
echo "Environment: TESTING"
echo "Database: SQLite (in-memory)"
echo ""

# Parse command line arguments
COVERAGE=false
VERBOSE=false
FAILED_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --failed|-f)
            FAILED_ONLY=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python -m pytest tests/"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$FAILED_ONLY" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --lf"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=backend --cov=core --cov-report=html --cov-report=term"
    echo "Running tests with coverage..."
else
    echo "Running tests..."
fi

echo "Command: $PYTEST_CMD"
echo ""
echo "========================================="
echo ""

# Run tests
$PYTEST_CMD
TEST_EXIT_CODE=$?

echo ""
echo "========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo ""
    echo "To debug:"
    echo "  - Run with verbose: ./scripts/run_tests.sh --verbose"
    echo "  - Run failed only: ./scripts/run_tests.sh --failed"
    echo "  - Check logs: cat logs/test_*.log"
fi

if [ "$COVERAGE" = true ]; then
    echo ""
    echo "Coverage report generated: htmlcov/index.html"
fi

echo "========================================="

exit $TEST_EXIT_CODE
