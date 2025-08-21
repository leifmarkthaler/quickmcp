#!/usr/bin/env python
"""
Basic File Server - A QuickMCP server for file system operations.

This example demonstrates how to create an MCP server that provides
file system access with various tools and resources for reading,
searching, and managing files.

Safety features:
- Restricted to a base directory (sandbox mode)
- Path traversal prevention
- File size limits for reading
- Whitelist/blacklist for file extensions
"""

import os
import json
import mimetypes
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import fnmatch
import hashlib

from mcplite import QuickMCPServer

# Configuration
DEFAULT_BASE_DIR = os.getcwd()  # Default to current directory
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size for reading
ALLOWED_EXTENSIONS = None  # None means all, or set like {'.txt', '.py', '.md'}
BLOCKED_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib'}  # Security: block executables
MAX_SEARCH_RESULTS = 100

# Create the server
server = QuickMCPServer(
    name="file-server",
    version="1.0.0",
    description="File system operations server with safety features",
    enable_autodiscovery=True,
    discovery_metadata={
        "category": "filesystem",
        "capabilities": ["read", "list", "search", "metadata"],
    }
)

# Initialize base directory
base_dir = Path(DEFAULT_BASE_DIR).resolve()


def safe_path(path: str) -> Optional[Path]:
    """
    Validate and resolve a path, ensuring it's within the base directory.
    
    Args:
        path: Path to validate
        
    Returns:
        Resolved Path object or None if invalid
    """
    try:
        # Resolve the path
        resolved = (base_dir / path).resolve()
        
        # Check if it's within base directory
        if not str(resolved).startswith(str(base_dir)):
            return None
            
        return resolved
    except Exception:
        return None


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def is_allowed_file(path: Path) -> bool:
    """Check if file extension is allowed."""
    ext = path.suffix.lower()
    
    if BLOCKED_EXTENSIONS and ext in BLOCKED_EXTENSIONS:
        return False
    
    if ALLOWED_EXTENSIONS is not None and ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True


# ============= Tools =============

@server.tool()
def list_directory(
    path: str = ".",
    show_hidden: bool = False,
    sort_by: str = "name"
) -> Dict[str, Any]:
    """
    List contents of a directory.
    
    Args:
        path: Directory path relative to base directory
        show_hidden: Include hidden files/directories
        sort_by: Sort by 'name', 'size', 'modified', or 'type'
    
    Returns:
        Directory listing with file information
    """
    dir_path = safe_path(path)
    if not dir_path or not dir_path.is_dir():
        return {"error": f"Invalid directory: {path}"}
    
    items = []
    
    try:
        for item in dir_path.iterdir():
            # Skip hidden files if requested
            if not show_hidden and item.name.startswith('.'):
                continue
            
            # Get file stats
            try:
                stats = item.stat()
                
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": stats.st_size if item.is_file() else None,
                    "size_formatted": format_size(stats.st_size) if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "permissions": oct(stats.st_mode)[-3:],
                    "path": str(item.relative_to(base_dir))
                })
            except (PermissionError, OSError):
                # Skip files we can't access
                continue
    
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    
    # Sort results
    if sort_by == "size":
        items.sort(key=lambda x: x.get("size", 0) or 0, reverse=True)
    elif sort_by == "modified":
        items.sort(key=lambda x: x["modified"], reverse=True)
    elif sort_by == "type":
        items.sort(key=lambda x: (x["type"], x["name"]))
    else:  # name
        items.sort(key=lambda x: x["name"].lower())
    
    return {
        "path": str(dir_path.relative_to(base_dir)),
        "absolute_path": str(dir_path),
        "item_count": len(items),
        "items": items
    }


@server.tool()
def read_file(
    path: str,
    encoding: str = "utf-8",
    lines: Optional[int] = None,
    start_line: int = 1
) -> Dict[str, Any]:
    """
    Read contents of a text file.
    
    Args:
        path: File path relative to base directory
        encoding: Text encoding (default: utf-8)
        lines: Number of lines to read (None for all)
        start_line: Starting line number (1-based)
    
    Returns:
        File contents and metadata
    """
    file_path = safe_path(path)
    if not file_path or not file_path.is_file():
        return {"error": f"Invalid file: {path}"}
    
    if not is_allowed_file(file_path):
        return {"error": f"File type not allowed: {path}"}
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        return {
            "error": f"File too large: {format_size(file_size)} (max: {format_size(MAX_FILE_SIZE)})"
        }
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            all_lines = f.readlines()
        
        # Handle line selection
        total_lines = len(all_lines)
        
        if lines is not None:
            end_line = min(start_line + lines - 1, total_lines)
            selected_lines = all_lines[start_line - 1:end_line]
            content = ''.join(selected_lines)
        else:
            content = ''.join(all_lines)
        
        return {
            "path": str(file_path.relative_to(base_dir)),
            "content": content,
            "encoding": encoding,
            "size": file_size,
            "size_formatted": format_size(file_size),
            "total_lines": total_lines,
            "lines_read": len(selected_lines) if lines else total_lines,
            "mime_type": mimetypes.guess_type(str(file_path))[0]
        }
    
    except UnicodeDecodeError:
        return {"error": f"Unable to decode file with {encoding} encoding"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


@server.tool()
def search_files(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    file_type: Optional[str] = None,
    content_search: Optional[str] = None,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Search for files matching a pattern.
    
    Args:
        pattern: File name pattern (supports wildcards: *, ?)
        path: Starting directory for search
        recursive: Search subdirectories
        file_type: Filter by file extension (e.g., '.py')
        content_search: Search for text within files
        case_sensitive: Case-sensitive search
    
    Returns:
        List of matching files with details
    """
    search_dir = safe_path(path)
    if not search_dir or not search_dir.is_dir():
        return {"error": f"Invalid directory: {path}"}
    
    matches = []
    search_count = 0
    
    # Prepare pattern matching
    if not case_sensitive:
        pattern = pattern.lower()
    
    def search_in_file(file_path: Path, search_text: str) -> bool:
        """Check if file contains search text."""
        if not is_allowed_file(file_path):
            return False
        
        try:
            # Only search in text files
            if file_path.stat().st_size > MAX_FILE_SIZE:
                return False
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if not case_sensitive:
                    content = content.lower()
                    search_text = search_text.lower()
                return search_text in content
        except:
            return False
    
    # Search for files
    try:
        if recursive:
            file_iterator = search_dir.rglob("*")
        else:
            file_iterator = search_dir.glob("*")
        
        for item in file_iterator:
            if len(matches) >= MAX_SEARCH_RESULTS:
                break
            
            if not item.is_file():
                continue
            
            search_count += 1
            
            # Check file type filter
            if file_type and item.suffix.lower() != file_type.lower():
                continue
            
            # Check name pattern
            name_to_match = item.name if case_sensitive else item.name.lower()
            if not fnmatch.fnmatch(name_to_match, pattern):
                continue
            
            # Check content search
            if content_search and not search_in_file(item, content_search):
                continue
            
            # Add to matches
            try:
                stats = item.stat()
                matches.append({
                    "name": item.name,
                    "path": str(item.relative_to(base_dir)),
                    "size": stats.st_size,
                    "size_formatted": format_size(stats.st_size),
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "mime_type": mimetypes.guess_type(str(item))[0]
                })
            except:
                continue
    
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}
    
    return {
        "pattern": pattern,
        "search_path": str(search_dir.relative_to(base_dir)),
        "files_searched": search_count,
        "matches_found": len(matches),
        "matches": matches,
        "truncated": len(matches) >= MAX_SEARCH_RESULTS
    }


@server.tool()
def file_info(path: str) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    Args:
        path: File or directory path
    
    Returns:
        Detailed file/directory metadata
    """
    item_path = safe_path(path)
    if not item_path or not item_path.exists():
        return {"error": f"Path does not exist: {path}"}
    
    try:
        stats = item_path.stat()
        
        info = {
            "name": item_path.name,
            "path": str(item_path.relative_to(base_dir)),
            "absolute_path": str(item_path),
            "type": "directory" if item_path.is_dir() else "file",
            "size": stats.st_size,
            "size_formatted": format_size(stats.st_size),
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
            "permissions": oct(stats.st_mode)[-3:],
            "owner_id": stats.st_uid,
            "group_id": stats.st_gid,
        }
        
        if item_path.is_file():
            info["mime_type"] = mimetypes.guess_type(str(item_path))[0]
            info["extension"] = item_path.suffix
            
            # Calculate file hash for small files
            if stats.st_size < 1024 * 1024:  # 1MB
                try:
                    with open(item_path, 'rb') as f:
                        info["md5"] = hashlib.md5(f.read()).hexdigest()
                except:
                    pass
        
        elif item_path.is_dir():
            # Count items in directory
            try:
                items = list(item_path.iterdir())
                info["item_count"] = len(items)
                info["file_count"] = sum(1 for i in items if i.is_file())
                info["dir_count"] = sum(1 for i in items if i.is_dir())
            except PermissionError:
                info["item_count"] = "Permission denied"
        
        return info
    
    except Exception as e:
        return {"error": f"Error getting file info: {str(e)}"}


@server.tool()
def get_tree(
    path: str = ".",
    max_depth: int = 3,
    show_hidden: bool = False,
    dirs_only: bool = False
) -> Dict[str, Any]:
    """
    Get directory tree structure.
    
    Args:
        path: Starting directory
        max_depth: Maximum depth to traverse
        show_hidden: Include hidden files/directories
        dirs_only: Show only directories
    
    Returns:
        Tree structure of directory
    """
    start_dir = safe_path(path)
    if not start_dir or not start_dir.is_dir():
        return {"error": f"Invalid directory: {path}"}
    
    def build_tree(dir_path: Path, current_depth: int) -> Dict[str, Any]:
        """Recursively build directory tree."""
        if current_depth > max_depth:
            return None
        
        tree = {
            "name": dir_path.name,
            "type": "directory",
            "children": []
        }
        
        try:
            for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                # Skip hidden if requested
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    subtree = build_tree(item, current_depth + 1)
                    if subtree:
                        tree["children"].append(subtree)
                elif not dirs_only:
                    tree["children"].append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size
                    })
        except PermissionError:
            tree["error"] = "Permission denied"
        
        return tree
    
    tree = build_tree(start_dir, 0)
    
    return {
        "path": str(start_dir.relative_to(base_dir)),
        "tree": tree
    }


# ============= Resources =============

@server.resource("file://{path}")
def file_resource(path: str) -> str:
    """
    Access file contents as a resource.
    
    Args:
        path: File path relative to base directory
    
    Returns:
        File contents
    """
    file_path = safe_path(path)
    if not file_path or not file_path.is_file():
        return f"Error: Invalid file path: {path}"
    
    if not is_allowed_file(file_path):
        return f"Error: File type not allowed: {path}"
    
    # Check file size
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return f"Error: File too large (max: {format_size(MAX_FILE_SIZE)})"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return f"Error: Unable to decode file as text: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@server.resource("directory://{path}")
def directory_resource(path: str) -> str:
    """
    Get directory listing as a resource.
    
    Args:
        path: Directory path relative to base directory
    
    Returns:
        JSON formatted directory listing
    """
    result = list_directory(path)
    return json.dumps(result, indent=2)


# ============= Prompts =============

@server.prompt()
def analyze_codebase(language: str = "python", path: str = ".") -> str:
    """
    Generate a prompt for analyzing a codebase.
    
    Args:
        language: Programming language
        path: Root directory of codebase
    
    Returns:
        Analysis prompt
    """
    # Get some stats about the codebase
    extensions = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "go": ".go",
        "rust": ".rs"
    }
    
    ext = extensions.get(language.lower(), ".*")
    search_result = search_files(f"*{ext}", path, recursive=True)
    
    return f"""Please analyze this {language} codebase:

Location: {path}
Files found: {search_result.get('matches_found', 0)} {language} files

Please provide:
1. Overall structure and organization
2. Main components and their responsibilities
3. Code quality observations
4. Potential improvements or issues
5. Documentation completeness
6. Testing coverage (if test files present)

Focus on architectural patterns, code style consistency, and best practices for {language}.
"""


@server.prompt()
def summarize_directory(path: str = ".") -> str:
    """
    Generate a prompt for summarizing directory contents.
    
    Args:
        path: Directory to summarize
    
    Returns:
        Summary prompt
    """
    listing = list_directory(path, show_hidden=False)
    
    return f"""Please provide a concise summary of this directory:

Path: {path}
Total items: {listing.get('item_count', 0)}

Contents:
{json.dumps(listing.get('items', [])[:20], indent=2)}

Please describe:
1. The apparent purpose of this directory
2. Types of files present
3. Organization structure
4. Any notable patterns or observations
"""


# ============= Main =============

def main():
    """Run the file server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="QuickMCP File Server")
    parser.add_argument(
        "--base-dir",
        default=DEFAULT_BASE_DIR,
        help=f"Base directory for file operations (default: {DEFAULT_BASE_DIR})"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=10 * 1024 * 1024,  # 10MB
        help="Maximum file size in bytes (default: 10MB)"
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)"
    )
    parser.add_argument(
        "--no-discovery",
        action="store_true",
        help="Disable autodiscovery"
    )
    
    args = parser.parse_args()
    
    # Update configuration
    global base_dir, MAX_FILE_SIZE
    base_dir = Path(args.base_dir).resolve()
    MAX_FILE_SIZE = args.max_size
    
    # Disable autodiscovery if requested
    if args.no_discovery:
        server.enable_autodiscovery = False
    
    # Run server - QuickMCP handles logging to stderr automatically
    if args.transport == "sse":
        server.run(transport="sse", port=args.port)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()