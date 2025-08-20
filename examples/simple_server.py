#!/usr/bin/env python3
"""
Simple MCP Server Example using QuickMCP

This example demonstrates how to create a basic MCP server with tools,
resources, and prompts using the QuickMCP wrapper.

To run:
    python simple_server.py

To test with a client:
    mcp-client stdio -- python simple_server.py
"""

from quickmcp import QuickMCPServer
from datetime import datetime
from typing import Dict, Any, List
import json
import os

# Create the server
server = QuickMCPServer(
    name="quickmcp-example",
    version="1.0.0",
    description="A simple example MCP server built with QuickMCP"
)

# In-memory data store for demonstration
data_store: Dict[str, Any] = {}


# ====================
# Tools
# ====================

@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@server.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@server.tool(description="Perform various calculations")
def calculate(operation: str, x: float, y: float) -> Dict[str, Any]:
    """
    Perform a calculation on two numbers.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        x: First number
        y: Second number
    
    Returns:
        Dictionary with operation, inputs, and result
    """
    operations = {
        "add": x + y,
        "subtract": x - y,
        "multiply": x * y,
        "divide": x / y if y != 0 else None,
    }
    
    if operation not in operations:
        return {
            "error": f"Unknown operation: {operation}",
            "available": list(operations.keys())
        }
    
    return {
        "operation": operation,
        "x": x,
        "y": y,
        "result": operations[operation],
        "timestamp": datetime.now().isoformat()
    }


@server.tool()
def store_data(key: str, value: Any) -> Dict[str, Any]:
    """
    Store data in memory with a key.
    
    Args:
        key: The key to store data under
        value: The value to store (any JSON-serializable type)
    
    Returns:
        Confirmation of storage
    """
    data_store[key] = value
    return {
        "success": True,
        "key": key,
        "message": f"Data stored under key '{key}'",
        "timestamp": datetime.now().isoformat()
    }


@server.tool()
def get_data(key: str) -> Dict[str, Any]:
    """
    Retrieve data from memory by key.
    
    Args:
        key: The key to retrieve data for
    
    Returns:
        The stored data or error if not found
    """
    if key in data_store:
        return {
            "success": True,
            "key": key,
            "value": data_store[key],
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "success": False,
            "key": key,
            "error": f"No data found for key '{key}'",
            "available_keys": list(data_store.keys())
        }


@server.tool()
def list_keys() -> List[str]:
    """List all keys in the data store."""
    return list(data_store.keys())


# ====================
# Resources
# ====================

@server.resource("memory://data/{key}")
def read_memory_data(key: str) -> str:
    """Read data from the in-memory store."""
    if key in data_store:
        return json.dumps(data_store[key], indent=2)
    return f"No data found for key: {key}"


@server.resource("system://info")
def get_system_info() -> str:
    """Get system information."""
    return json.dumps({
        "platform": os.name,
        "python_version": os.sys.version,
        "server_name": server.name,
        "server_version": server.version,
        "tools_available": server.list_tools(),
        "resources_available": server.list_resources(),
        "data_store_size": len(data_store),
        "timestamp": datetime.now().isoformat()
    }, indent=2)


@server.resource("example://greeting/{name}")
def get_greeting(name: str) -> str:
    """Generate a personalized greeting."""
    hour = datetime.now().hour
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    return f"{time_greeting}, {name}! Welcome to the QuickMCP example server."


# ====================
# Prompts
# ====================

@server.prompt()
def code_review(language: str, code: str) -> str:
    """Generate a code review prompt."""
    return f"""Please review the following {language} code:

```{language}
{code}
```

Provide feedback on:
1. Code quality and style
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement
"""


@server.prompt()
def explain_concept(topic: str, level: str = "beginner") -> str:
    """Generate a prompt to explain a concept."""
    return f"""Please explain {topic} at a {level} level.

Include:
- A clear definition
- Why it's important
- Real-world examples
- Common misconceptions
- Related concepts

Make the explanation accessible and engaging for someone at the {level} level."""


@server.prompt()
def data_analysis(data_description: str) -> str:
    """Generate a data analysis prompt."""
    return f"""Analyze the following data:

{data_description}

Please provide:
1. Key statistics and patterns
2. Notable insights
3. Potential correlations
4. Anomalies or outliers
5. Recommendations for further analysis
6. Visualization suggestions
"""


# ====================
# Main entry point
# ====================

if __name__ == "__main__":
    # Print server info
    print(f"Starting {server.name} v{server.version}")
    print(f"Tools: {', '.join(server.list_tools())}")
    print(f"Resources: {', '.join(server.list_resources())}")
    print(f"Prompts: {', '.join(server.list_prompts())}")
    print("-" * 50)
    
    # Run the server (defaults to stdio transport)
    server.run()