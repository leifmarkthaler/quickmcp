"""
Example utility library that can be converted to an MCP server.

This demonstrates how any Python module with useful functions
can instantly become an MCP server using the factory.
"""

import json
import hashlib
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


# String utilities
def clean_text(text: str) -> str:
    """Remove extra whitespace and clean up text."""
    return ' '.join(text.split())


def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)


def word_frequency(text: str) -> Dict[str, int]:
    """Calculate word frequency in text."""
    words = text.lower().split()
    frequency = {}
    for word in words:
        word = re.sub(r'[^\w\s]', '', word)
        if word:
            frequency[word] = frequency.get(word, 0) + 1
    return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))


# Data encoding/decoding
def encode_base64(text: str) -> str:
    """Encode text to base64."""
    return base64.b64encode(text.encode()).decode()


def decode_base64(encoded: str) -> str:
    """Decode base64 text."""
    return base64.b64decode(encoded).decode()


def hash_text(text: str, algorithm: str = "sha256") -> str:
    """Generate hash of text using specified algorithm."""
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm not in algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    hasher = algorithms[algorithm]()
    hasher.update(text.encode())
    return hasher.hexdigest()


# JSON utilities
def pretty_json(data: Any, indent: int = 2) -> str:
    """Convert data to pretty-printed JSON string."""
    return json.dumps(data, indent=indent, sort_keys=True, default=str)


def flatten_json(nested: Dict, separator: str = ".") -> Dict:
    """Flatten nested JSON/dict structure."""
    def _flatten(obj, parent_key=""):
        items = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{separator}{k}" if parent_key else k
                items.extend(_flatten(v, new_key).items())
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_key = f"{parent_key}[{i}]"
                items.extend(_flatten(v, new_key).items())
        else:
            items.append((parent_key, obj))
        return dict(items)
    
    return _flatten(nested)


def unflatten_json(flat: Dict, separator: str = ".") -> Dict:
    """Unflatten a flattened dict structure."""
    result = {}
    for key, value in flat.items():
        parts = key.split(separator)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


# Date/time utilities
def format_timestamp(timestamp: float = None, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a timestamp as a string."""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    return datetime.fromtimestamp(timestamp).strftime(format)


def parse_date(date_str: str, format: str = "%Y-%m-%d") -> Dict[str, Any]:
    """Parse a date string and return components."""
    dt = datetime.strptime(date_str, format)
    return {
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "weekday": dt.strftime("%A"),
        "iso": dt.isoformat(),
        "timestamp": dt.timestamp()
    }


def add_days(date_str: str, days: int, format: str = "%Y-%m-%d") -> str:
    """Add days to a date string."""
    dt = datetime.strptime(date_str, format)
    new_dt = dt + timedelta(days=days)
    return new_dt.strftime(format)


def date_difference(date1: str, date2: str, format: str = "%Y-%m-%d") -> Dict[str, int]:
    """Calculate difference between two dates."""
    dt1 = datetime.strptime(date1, format)
    dt2 = datetime.strptime(date2, format)
    diff = dt2 - dt1
    
    return {
        "days": diff.days,
        "seconds": diff.seconds,
        "total_seconds": int(diff.total_seconds()),
        "weeks": diff.days // 7,
        "months": diff.days // 30  # Approximate
    }


# List/data utilities
def remove_duplicates(items: List[Any]) -> List[Any]:
    """Remove duplicates from a list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, later values override earlier ones."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def filter_dict(data: Dict, keys: List[str], exclude: bool = False) -> Dict:
    """Filter dictionary to include/exclude specific keys."""
    if exclude:
        return {k: v for k, v in data.items() if k not in keys}
    else:
        return {k: v for k, v in data.items() if k in keys}


# Validation utilities
def validate_email(email: str) -> bool:
    """Validate if string is a valid email address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL."""
    pattern = r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)$'
    return bool(re.match(pattern, url))


def validate_json(json_str: str) -> Dict[str, Any]:
    """Validate and parse JSON string."""
    try:
        data = json.loads(json_str)
        return {"valid": True, "data": data}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}


# Conversion utilities
def bytes_to_human(bytes_val: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5/9


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color code."""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_code: str) -> Dict[str, int]:
    """Convert hex color code to RGB values."""
    hex_code = hex_code.lstrip('#')
    return {
        "r": int(hex_code[0:2], 16),
        "g": int(hex_code[2:4], 16),
        "b": int(hex_code[4:6], 16)
    }


if __name__ == "__main__":
    # This module can be run as an MCP server using:
    # mcp-factory utils_library.py
    print("This is a utility library. Use mcp-factory to run it as an MCP server:")
    print("  mcp-factory utils_library.py")
    print("\nAvailable functions:")
    import inspect
    for name, obj in inspect.getmembers(inspect.getmodule(inspect.currentframe())):
        if inspect.isfunction(obj) and not name.startswith('_'):
            doc = obj.__doc__ or "No description"
            print(f"  - {name}: {doc.strip().split('.')[0]}")