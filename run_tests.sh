#!/bin/bash

# QuickMCP Test Runner Script
# Run all tests with coverage reporting

echo "================================"
echo "QuickMCP Test Suite"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest is not installed. Please install with: pip install pytest pytest-asyncio pytest-cov${NC}"
    exit 1
fi

# Run tests with coverage
echo "Running tests with coverage..."
echo ""

pytest tests/ \
    -v \
    --tb=short \
    --cov=src/quickmcp \
    --cov-report=term-missing \
    --cov-report=html \
    --asyncio-mode=auto \
    "$@"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi