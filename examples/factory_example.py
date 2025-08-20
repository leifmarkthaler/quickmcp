#!/usr/bin/env python
"""
Example of using MCP Factory to create servers from existing Python code.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp.factory import MCPFactory, create_mcp_from_module, mcp_tool


# Example 1: Python module with various functions
def calculate_sum(numbers: list) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list) -> float:
    """Calculate the average of a list of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0


def find_max(numbers: list) -> float:
    """Find the maximum value in a list."""
    return max(numbers) if numbers else None


def find_min(numbers: list) -> float:
    """Find the minimum value in a list."""
    return min(numbers) if numbers else None


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def count_words(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


def _private_function():
    """This is a private function (won't be exposed by default)."""
    return "private"


# Example 2: Class-based tools
class TextProcessor:
    """A class for processing text."""
    
    def __init__(self):
        self.processed_count = 0
    
    def uppercase(self, text: str) -> str:
        """Convert text to uppercase."""
        self.processed_count += 1
        return text.upper()
    
    def lowercase(self, text: str) -> str:
        """Convert text to lowercase."""
        self.processed_count += 1
        return text.lower()
    
    def title_case(self, text: str) -> str:
        """Convert text to title case."""
        self.processed_count += 1
        return text.title()
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {"processed_count": self.processed_count}


# Example 3: Functions with decorator
@mcp_tool
def decorated_add(a: float, b: float) -> float:
    """Add two numbers (decorated)."""
    return a + b


@mcp_tool(name="multiply_numbers", description="Multiply two numbers together")
def decorated_multiply(a: float, b: float) -> float:
    """Multiply two numbers (decorated)."""
    return a * b


def not_decorated_function():
    """This function is not decorated."""
    return "not decorated"


def demo_module_factory():
    """Demo: Create MCP server from current module."""
    print("=" * 60)
    print("Demo 1: Create MCP server from current module")
    print("=" * 60)
    
    factory = MCPFactory(name="math-tools")
    server = factory.from_module(__file__, include_private=False)
    
    print(f"Created server: {server.name}")
    print(f"Description: {server.description}")
    print(f"Tools created: {len(server.list_tools())}")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    return server


def demo_class_factory():
    """Demo: Create MCP server from a class."""
    print("\n" + "=" * 60)
    print("Demo 2: Create MCP server from TextProcessor class")
    print("=" * 60)
    
    factory = MCPFactory()
    server = factory.from_class(TextProcessor)
    
    print(f"Created server: {server.name}")
    print(f"Description: {server.description}")
    print(f"Tools created: {len(server.list_tools())}")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    return server


def demo_functions_dict():
    """Demo: Create MCP server from dictionary of functions."""
    print("\n" + "=" * 60)
    print("Demo 3: Create MCP server from selected functions")
    print("=" * 60)
    
    # Select specific functions
    selected_functions = {
        "sum": calculate_sum,
        "avg": calculate_average,
        "reverse": reverse_string,
        "word_count": count_words
    }
    
    factory = MCPFactory(name="selected-tools")
    server = factory.from_functions(selected_functions)
    
    print(f"Created server: {server.name}")
    print(f"Tools created: {len(server.list_tools())}")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    return server


def demo_decorated_functions():
    """Demo: Create MCP server from decorated functions only."""
    print("\n" + "=" * 60)
    print("Demo 4: Create MCP server from decorated functions")
    print("=" * 60)
    
    factory = MCPFactory()
    server = factory.from_file_with_decorators(__file__, decorator_name="mcp_tool")
    
    print(f"Created server: {server.name}")
    print(f"Tools created: {len(server.list_tools())}")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    return server


def main():
    """Run all demos."""
    print("QuickMCP Factory Examples")
    print("=" * 60)
    
    # Run demos
    server1 = demo_module_factory()
    server2 = demo_class_factory()
    server3 = demo_functions_dict()
    server4 = demo_decorated_functions()
    
    print("\n" + "=" * 60)
    print("Factory Examples Complete!")
    print("=" * 60)
    
    # Optionally run one of the servers
    if "--run" in sys.argv:
        print("\nRunning the math-tools server...")
        server1.run()


if __name__ == "__main__":
    main()