#!/bin/bash

# QuickMCP Test Runner Script with UV support
# Run all tests with coverage reporting using uv

echo "================================"
echo "QuickMCP Test Suite (UV)"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Falling back to standard pytest...${NC}"
    
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}pytest is not installed. Please install with: pip install pytest pytest-asyncio pytest-cov${NC}"
        echo -e "${RED}Or install uv: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
    
    # Run tests with standard pytest
    echo "Running tests with pytest..."
    echo ""
    
    pytest tests/ \
        -v \
        --tb=short \
        --cov=src/quickmcp \
        --cov-report=term-missing \
        --cov-report=html \
        --asyncio-mode=auto \
        "$@"
else
    # Run tests with uv
    echo -e "${GREEN}Using uv for faster test execution...${NC}"
    echo ""
    
    # Ensure dependencies are installed
    uv pip sync 2>/dev/null || uv pip install -e ".[dev]"
    
    # Run tests with uv
    uv run pytest tests/ \
        -v \
        --tb=short \
        --cov=src/quickmcp \
        --cov-report=term-missing \
        --cov-report=html \
        --asyncio-mode=auto \
        "$@"
fi

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