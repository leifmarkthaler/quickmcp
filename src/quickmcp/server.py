"""
QuickMCP Server - Simplified MCP server creation
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List, Union
from pathlib import Path
import sys
import json

from mcp import Server
from mcp.server.stdio import stdio_server
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class QuickMCPServer:
    """
    A simplified wrapper around the MCP Server class that makes it easy
    to create and run MCP servers with minimal boilerplate.
    
    Example:
        ```python
        server = QuickMCPServer("my-server")
        
        @server.tool()
        def add(a: int, b: int) -> int:
            return a + b
        
        @server.resource("data://{key}")
        def get_data(key: str) -> str:
            return f"Data for {key}"
        
        server.run()
        ```
    """
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None,
        log_level: str = "INFO",
    ):
        """
        Initialize a QuickMCP server.
        
        Args:
            name: The name of the server
            version: Server version
            description: Optional server description
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.name = name
        self.version = version
        self.description = description or f"{name} MCP Server"
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(name)
        
        # Create the underlying MCP server
        self._server = Server(name)
        
        # Track registered components
        self._tools: Dict[str, Callable] = {}
        self._resources: Dict[str, Callable] = {}
        self._prompts: Dict[str, Callable] = {}
        
        self.logger.info(f"Initialized QuickMCP server: {name} v{version}")
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Callable:
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            name: Optional tool name (defaults to function name)
            description: Optional tool description (defaults to docstring)
            schema: Optional JSON schema for parameters
        
        Example:
            ```python
            @server.tool()
            def calculate(operation: str, a: float, b: float) -> float:
                '''Perform a calculation'''
                if operation == "add":
                    return a + b
                elif operation == "multiply":
                    return a * b
            ```
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or (func.__doc__ or "").strip()
            
            # Register with the MCP server
            wrapped = self._server.tool(
                name=tool_name,
                description=tool_desc,
                schema=schema
            )(func)
            
            # Track in our registry
            self._tools[tool_name] = wrapped
            self.logger.debug(f"Registered tool: {tool_name}")
            
            return wrapped
        
        return decorator
    
    def resource(
        self,
        uri_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: str = "text/plain",
    ) -> Callable:
        """
        Decorator to register a function as an MCP resource.
        
        Args:
            uri_template: URI template for the resource (e.g., "file://{path}")
            name: Optional resource name
            description: Optional resource description
            mime_type: MIME type of the resource content
        
        Example:
            ```python
            @server.resource("config://{section}")
            def get_config(section: str) -> str:
                '''Get configuration section'''
                return read_config_file(section)
            ```
        """
        def decorator(func: Callable) -> Callable:
            resource_name = name or func.__name__
            resource_desc = description or (func.__doc__ or "").strip()
            
            # Register with the MCP server
            wrapped = self._server.resource(
                uri_template=uri_template,
                name=resource_name,
                description=resource_desc,
                mime_type=mime_type
            )(func)
            
            # Track in our registry
            self._resources[uri_template] = wrapped
            self.logger.debug(f"Registered resource: {uri_template}")
            
            return wrapped
        
        return decorator
    
    def prompt(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        arguments: Optional[List[Dict[str, Any]]] = None,
    ) -> Callable:
        """
        Decorator to register a function as an MCP prompt template.
        
        Args:
            name: Optional prompt name (defaults to function name)
            description: Optional prompt description
            arguments: Optional list of argument schemas
        
        Example:
            ```python
            @server.prompt()
            def analyze_code(language: str, code: str) -> str:
                '''Generate a code analysis prompt'''
                return f"Analyze this {language} code:\\n\\n{code}"
            ```
        """
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            prompt_desc = description or (func.__doc__ or "").strip()
            
            # Register with the MCP server
            wrapped = self._server.prompt(
                name=prompt_name,
                description=prompt_desc,
                arguments=arguments
            )(func)
            
            # Track in our registry
            self._prompts[prompt_name] = wrapped
            self.logger.debug(f"Registered prompt: {prompt_name}")
            
            return wrapped
        
        return decorator
    
    def add_tool_from_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a tool from an existing function.
        
        Args:
            func: The function to add as a tool
            name: Optional tool name
            description: Optional tool description
        """
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").strip()
        
        wrapped = self._server.tool(
            name=tool_name,
            description=tool_desc
        )(func)
        
        self._tools[tool_name] = wrapped
        self.logger.info(f"Added tool from function: {tool_name}")
    
    def list_tools(self) -> List[str]:
        """Get a list of registered tool names."""
        return list(self._tools.keys())
    
    def list_resources(self) -> List[str]:
        """Get a list of registered resource URIs."""
        return list(self._resources.keys())
    
    def list_prompts(self) -> List[str]:
        """Get a list of registered prompt names."""
        return list(self._prompts.keys())
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get server information including registered components.
        
        Returns:
            Dictionary with server info
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tools": self.list_tools(),
            "resources": self.list_resources(),
            "prompts": self.list_prompts(),
        }
    
    def run(
        self,
        transport: str = "stdio",
        host: str = "localhost",
        port: int = 8000,
        **kwargs
    ) -> None:
        """
        Run the MCP server.
        
        Args:
            transport: Transport type ("stdio", "sse", "http")
            host: Host for network transports
            port: Port for network transports
            **kwargs: Additional transport-specific arguments
        
        Example:
            ```python
            # Run as stdio server (default)
            server.run()
            
            # Run as SSE server
            server.run(transport="sse", port=8080)
            ```
        """
        self.logger.info(f"Starting {self.name} server with {transport} transport")
        self.logger.info(f"Registered {len(self._tools)} tools, "
                        f"{len(self._resources)} resources, "
                        f"{len(self._prompts)} prompts")
        
        if transport == "stdio":
            self.run_stdio()
        elif transport == "sse":
            self.run_sse(host=host, port=port, **kwargs)
        elif transport == "http":
            self.run_http(host=host, port=port, **kwargs)
        else:
            raise ValueError(f"Unknown transport: {transport}")
    
    def run_stdio(self) -> None:
        """Run the server with stdio transport."""
        self.logger.info("Running with stdio transport")
        asyncio.run(stdio_server(self._server).run())
    
    def run_sse(self, host: str = "localhost", port: int = 8000, **kwargs) -> None:
        """
        Run the server with SSE (Server-Sent Events) transport.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        try:
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.routing import Route
            import uvicorn
        except ImportError:
            self.logger.error("SSE transport requires 'http' extras: pip install quickmcp[http]")
            raise
        
        self.logger.info(f"Running SSE server on http://{host}:{port}/sse")
        
        # Create SSE transport
        transport = SseServerTransport(self._server)
        
        # Create Starlette app
        app = Starlette(
            routes=[
                Route("/sse", endpoint=transport.handle_sse, methods=["GET"]),
                Route("/", endpoint=self._health_check, methods=["GET"]),
            ]
        )
        
        # Run with uvicorn
        uvicorn.run(app, host=host, port=port, **kwargs)
    
    def run_http(self, host: str = "localhost", port: int = 8000, **kwargs) -> None:
        """
        Run the server with HTTP transport.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        # Similar to SSE but with regular HTTP endpoints
        raise NotImplementedError("HTTP transport not yet implemented")
    
    async def _health_check(self, request) -> Dict[str, Any]:
        """Health check endpoint for network transports."""
        from starlette.responses import JSONResponse
        return JSONResponse({
            "status": "healthy",
            "server": self.name,
            "version": self.version,
            "tools": len(self._tools),
            "resources": len(self._resources),
            "prompts": len(self._prompts),
        })
    
    def export_openapi(self) -> Dict[str, Any]:
        """
        Export server specification as OpenAPI schema.
        
        Returns:
            OpenAPI specification dictionary
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": self.name,
                "version": self.version,
                "description": self.description,
            },
            "paths": {
                "/tools": {
                    "get": {
                        "summary": "List available tools",
                        "responses": {
                            "200": {
                                "description": "List of tools",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                # Add more endpoints as needed
            }
        }
    
    def __repr__(self) -> str:
        return (f"QuickMCPServer(name='{self.name}', version='{self.version}', "
                f"tools={len(self._tools)}, resources={len(self._resources)}, "
                f"prompts={len(self._prompts)})")