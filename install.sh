#!/bin/bash
# QuickMCP Quick Install Script
# One-line installation: curl -sSL https://raw.githubusercontent.com/leifmarkthaler/quickmcp/main/install.sh | bash

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}QuickMCP Quick Installer${NC}"
echo "========================"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found Python: $($PYTHON --version)"

# Install QuickMCP
echo -e "\n${BLUE}Installing QuickMCP...${NC}"

# Try uv first (much faster)
if command -v uv &> /dev/null; then
    echo "Using uv (fast)..."
    uv pip install git+https://github.com/leifmarkthaler/quickmcp.git
else
    echo "Using pip..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install git+https://github.com/leifmarkthaler/quickmcp.git
fi

# Create a test file
cat > quickmcp_test.py << 'EOF'
from quickmcp import QuickMCPServer

server = QuickMCPServer("test")

@server.tool()
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}! 👋"

if __name__ == "__main__":
    tools = server.list_tools()
    print(f"✓ QuickMCP is working! Found {len(tools)} tool(s): {tools}")
    print("\nYou can now create MCP servers! Try running:")
    print("  python quickmcp_test.py")
EOF

# Test installation
echo -e "\n${BLUE}Testing installation...${NC}"
$PYTHON quickmcp_test.py

echo -e "\n${GREEN}✅ QuickMCP installed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Run the test server: python quickmcp_test.py"
echo "2. Check examples: https://github.com/leifmarkthaler/quickmcp/tree/main/examples"
echo "3. Read quickstart: https://github.com/leifmarkthaler/quickmcp/blob/main/QUICKSTART.md"
echo ""
echo "Happy coding! 🚀"