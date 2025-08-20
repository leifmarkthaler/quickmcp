#!/bin/bash

# QuickMCP Setup Script with UV
# Fast installation and setup using uv package manager

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     QuickMCP Setup with UV 🚀         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check for Python
if ! command_exists python3 && ! command_exists python; then
    echo -e "${RED}❌ Python is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Get Python command
if command_exists python3; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Install UV if not present
if ! command_exists uv; then
    echo ""
    echo -e "${YELLOW}UV is not installed. Installing UV for faster package management...${NC}"
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        # Unix-like systems (Linux, macOS)
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command_exists uv; then
            echo -e "${GREEN}✓ UV installed successfully${NC}"
        else
            echo -e "${YELLOW}⚠ UV installed but not in PATH. Please run:${NC}"
            echo -e "${YELLOW}  export PATH=\"\$HOME/.cargo/bin:\$PATH\"${NC}"
            echo -e "${YELLOW}  And add it to your shell profile (~/.bashrc, ~/.zshrc, etc.)${NC}"
            echo ""
            echo -e "${YELLOW}Falling back to pip installation...${NC}"
            USE_PIP=true
        fi
    else
        echo -e "${YELLOW}Automatic UV installation not supported on this OS.${NC}"
        echo -e "${YELLOW}Please install manually from: https://github.com/astral-sh/uv${NC}"
        echo ""
        echo -e "${YELLOW}Falling back to pip installation...${NC}"
        USE_PIP=true
    fi
else
    echo -e "${GREEN}✓ UV is already installed${NC}"
fi

# Create virtual environment if it doesn't exist
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo -e "${BLUE}Creating virtual environment...${NC}"
    
    if command_exists uv && [ -z "$USE_PIP" ]; then
        uv venv "$VENV_DIR"
    else
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo -e "${BLUE}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source "$VENV_DIR/Scripts/activate"
else
    # Unix-like
    source "$VENV_DIR/bin/activate"
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo ""
echo -e "${BLUE}Installing QuickMCP and dependencies...${NC}"

if command_exists uv && [ -z "$USE_PIP" ]; then
    # Use UV for fast installation
    echo -e "${GREEN}Using UV for fast installation...${NC}"
    
    # Install package in editable mode with all extras
    uv pip install -e ".[all]"
    
    # Ensure test dependencies are installed
    uv pip install pytest pytest-asyncio pytest-cov
    
    echo -e "${GREEN}✓ Dependencies installed with UV${NC}"
else
    # Fallback to pip
    echo -e "${YELLOW}Using pip for installation...${NC}"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install package in editable mode with all extras
    pip install -e ".[all]"
    
    # Ensure test dependencies are installed
    pip install pytest pytest-asyncio pytest-cov
    
    echo -e "${GREEN}✓ Dependencies installed with pip${NC}"
fi

# Run tests to verify installation
echo ""
echo -e "${BLUE}Running tests to verify installation...${NC}"

if command_exists uv && [ -z "$USE_PIP" ]; then
    uv run pytest tests/ -v --tb=short -x -q
else
    pytest tests/ -v --tb=short -x -q
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed. Please check the output above.${NC}"
fi

# Display next steps
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Setup Complete! 🎉                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}QuickMCP is now installed and ready to use!${NC}"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Try the examples: python examples/simple_server.py"
echo "3. Create your own MCP server!"
echo ""
echo "For more information, see the README.md"

# Create a simple quickstart script
cat > quickstart.py << 'EOF'
#!/usr/bin/env python
"""QuickMCP Quickstart - A simple example to get you started."""

from quickmcp import QuickMCPServer

# Create a server
server = QuickMCPServer("my-first-server")

@server.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to QuickMCP! 🎉"

@server.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    print("Starting QuickMCP server...")
    print("This server has the following tools:")
    for tool in server.list_tools():
        print(f"  - {tool}")
    print("\nServer is ready! Use with an MCP client.")
    server.run()
EOF

chmod +x quickstart.py

echo ""
echo -e "${BLUE}Created quickstart.py - Run it with: python quickstart.py${NC}"
echo ""