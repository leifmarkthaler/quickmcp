#!/usr/bin/env python
"""The absolute simplest QuickMCP example - just 5 lines!"""

from mcplite.quick import tool, run

@tool
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}! 👋"

@tool
def add(a: int, b: int) -> int:
    """Add numbers."""
    return a + b

# That's it! Run it:
run()