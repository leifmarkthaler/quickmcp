"""
QuickMCP Server - Simplified MCP server creation
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List, Union
from pathlib import Path
import sys
import json
import inspect

from mcp.server import Server, InitializationOptions
from mcp.server.stdio import stdio_server
from pydantic import BaseModel
from mcp.types import Tool, Resource, Prompt, TextContent, ServerCapabilities

from .autodiscovery import AutoDiscovery

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
        enable_autodiscovery: bool = True,
        discovery_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a QuickMCP server.
        
        Args:
            name: The name of the server
            version: Server version
            description: Optional server description
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            enable_autodiscovery: Enable network autodiscovery
            discovery_metadata: Additional metadata for discovery
        """
        self.name = name
        self.version = version
        self.description = description or f"{name} MCP Server"
        
        # Set up logging - always use stderr to avoid interfering with stdio transport
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr
        )
        self.logger = logging.getLogger(name)
        
        # Create the underlying MCP server
        self._server = Server(name, version=version)
        
        # Track registered components
        self._tools: Dict[str, Callable] = {}
        self._resources: Dict[str, Callable] = {}
        self._prompts: Dict[str, Callable] = {}
        
        # Store metadata
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._resource_metadata: Dict[str, Dict[str, Any]] = {}
        self._prompt_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Register handlers with the MCP server
        self._register_handlers()
        
        # Autodiscovery setup
        self.enable_autodiscovery = enable_autodiscovery
        self.discovery_metadata = discovery_metadata or {}
        self._autodiscovery: Optional[AutoDiscovery] = None
        
        self.logger.info(f"Initialized QuickMCP server: {name} v{version}")
    
    def _register_handlers(self):
        """Register the request handlers with the MCP server."""
        
        @self._server.list_tools()
        async def list_tools():
            """List available tools."""
            tools = []
            for tool_name, func in self._tools.items():
                metadata = self._tool_metadata.get(tool_name, {})
                tools.append(Tool(
                    name=tool_name,
                    description=metadata.get("description", ""),
                    inputSchema=metadata.get("schema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                ))
            return tools
        
        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Execute a tool."""
            if name not in self._tools:
                raise ValueError(f"Tool {name} not found")
            
            func = self._tools[name]
            
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
            
            # Return as TextContent
            return [TextContent(
                type="text",
                text=json.dumps(result) if not isinstance(result, str) else result
            )]
        
        @self._server.list_resources()
        async def list_resources():
            """List available resources."""
            resources = []
            for uri_template, func in self._resources.items():
                metadata = self._resource_metadata.get(uri_template, {})
                resources.append(Resource(
                    uri=uri_template,
                    name=metadata.get("name", func.__name__),
                    description=metadata.get("description", ""),
                    mimeType=metadata.get("mime_type", "text/plain")
                ))
            return resources
        
        @self._server.read_resource()
        async def read_resource(uri: str):
            """Read a resource."""
            # Find matching resource
            for uri_template, func in self._resources.items():
                # Simple template matching (replace {param} with actual values)
                # This is a simplified version - production code would need proper URI template matching
                if self._uri_matches(uri, uri_template):
                    params = self._extract_params(uri, uri_template)
                    
                    if asyncio.iscoroutinefunction(func):
                        content = await func(**params)
                    else:
                        content = func(**params)
                    
                    metadata = self._resource_metadata.get(uri_template, {})
                    return TextContent(
                        type="text",
                        text=content,
                        mimeType=metadata.get("mime_type", "text/plain")
                    )
            
            raise ValueError(f"Resource {uri} not found")
        
        @self._server.list_prompts()
        async def list_prompts():
            """List available prompts."""
            prompts = []
            for prompt_name, func in self._prompts.items():
                metadata = self._prompt_metadata.get(prompt_name, {})
                prompts.append(Prompt(
                    name=prompt_name,
                    description=metadata.get("description", ""),
                    arguments=metadata.get("arguments", [])
                ))
            return prompts
        
        @self._server.get_prompt()
        async def get_prompt(name: str, arguments: dict):
            """Get a prompt."""
            if name not in self._prompts:
                raise ValueError(f"Prompt {name} not found")
            
            func = self._prompts[name]
            
            if asyncio.iscoroutinefunction(func):
                content = await func(**arguments)
            else:
                content = func(**arguments)
            
            return TextContent(
                type="text",
                text=content
            )
    
    def _uri_matches(self, uri: str, template: str) -> bool:
        """Check if a URI matches a template pattern."""
        # Simple implementation - just check if the base matches
        # A full implementation would parse the template properly
        import re
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', template)
        return bool(re.match(f"^{pattern}$", uri))
    
    def _extract_params(self, uri: str, template: str) -> Dict[str, str]:
        """Extract parameters from a URI based on a template."""
        # Simple implementation
        import re
        
        # Find parameter names in template
        param_names = re.findall(r'\{([^}]+)\}', template)
        
        # Create regex pattern from template
        pattern = template
        for param_name in param_names:
            pattern = pattern.replace(f"{{{param_name}}}", r'([^/]+)')
        
        # Extract values
        match = re.match(f"^{pattern}$", uri)
        if match:
            return dict(zip(param_names, match.groups()))
        return {}
    
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
            
            # Generate schema from function signature if not provided
            tool_schema = schema
            if tool_schema is None:
                tool_schema = self._generate_schema_from_function(func)
            
            # Track in our registry
            self._tools[tool_name] = func
            self._tool_metadata[tool_name] = {
                "description": tool_desc,
                "schema": tool_schema
            }
            self.logger.debug(f"Registered tool: {tool_name}")
            
            return func
        
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
            
            # Track in our registry
            self._resources[uri_template] = func
            self._resource_metadata[uri_template] = {
                "name": resource_name,
                "description": resource_desc,
                "mime_type": mime_type
            }
            self.logger.debug(f"Registered resource: {uri_template}")
            
            return func
        
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
            
            # Generate arguments from function signature if not provided
            prompt_arguments = arguments
            if prompt_arguments is None:
                prompt_arguments = self._generate_arguments_from_function(func)
            
            # Track in our registry
            self._prompts[prompt_name] = func
            self._prompt_metadata[prompt_name] = {
                "description": prompt_desc,
                "arguments": prompt_arguments
            }
            self.logger.debug(f"Registered prompt: {prompt_name}")
            
            return func
        
        return decorator
    
    def _generate_schema_from_function(self, func: Callable) -> Dict[str, Any]:
        """Generate JSON schema from function signature."""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            # Basic type mapping
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
            
            properties[param_name] = {"type": param_type}
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _generate_arguments_from_function(self, func: Callable) -> List[Dict[str, Any]]:
        """Generate argument list from function signature."""
        sig = inspect.signature(func)
        arguments = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            arg = {
                "name": param_name,
                "required": param.default == inspect.Parameter.empty
            }
            arguments.append(arg)
        
        return arguments
    
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
        
        self._tools[tool_name] = func
        self._tool_metadata[tool_name] = {
            "description": tool_desc,
            "schema": self._generate_schema_from_function(func)
        }
        
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
    
    def start_autodiscovery(self, transport: str = "stdio", host: str = "localhost", port: int = 8000) -> None:
        """
        Start autodiscovery broadcasting.
        
        Args:
            transport: Transport type
            host: Host for network transports
            port: Port for network transports
        """
        if not self.enable_autodiscovery:
            return
        
        if self._autodiscovery:
            self.logger.warning("Autodiscovery already started")
            return
        
        # Create autodiscovery instance
        self._autodiscovery = AutoDiscovery(
            server_name=self.name,
            server_version=self.version,
            server_description=self.description,
            transport=transport,
            host=host,
            port=port,
            metadata=self.discovery_metadata
        )
        
        # Update capabilities
        self._autodiscovery.update_capabilities(
            tools=self.list_tools(),
            resources=self.list_resources(),
            prompts=self.list_prompts()
        )
        
        # Start broadcasting
        self._autodiscovery.start()
        self.logger.info("Autodiscovery broadcasting started")
    
    def stop_autodiscovery(self) -> None:
        """Stop autodiscovery broadcasting."""
        if self._autodiscovery:
            self._autodiscovery.stop()
            self._autodiscovery = None
            self.logger.info("Autodiscovery broadcasting stopped")
    
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
        # Check for --info flag (for discovery)
        if "--info" in sys.argv:
            info = {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "capabilities": {
                    "tools": self.list_tools(),
                    "resources": self.list_resources(),
                    "prompts": self.list_prompts()
                },
                "metadata": self.discovery_metadata
            }
            print(json.dumps(info))
            sys.exit(0)
        
        self.logger.info(f"Starting {self.name} server with {transport} transport")
        self.logger.info(f"Registered {len(self._tools)} tools, "
                        f"{len(self._resources)} resources, "
                        f"{len(self._prompts)} prompts")
        
        # Start autodiscovery if enabled (but not for stdio transport)
        if transport != "stdio":
            self.start_autodiscovery(transport=transport, host=host, port=port)
        
        try:
            if transport == "stdio":
                self.run_stdio()
            elif transport == "sse":
                self.run_sse(host=host, port=port, **kwargs)
            elif transport == "http":
                self.run_http(host=host, port=port, **kwargs)
            else:
                raise ValueError(f"Unknown transport: {transport}")
        finally:
            # Stop autodiscovery when server stops
            self.stop_autodiscovery()
    
    def run_stdio(self) -> None:
        """Run the server with stdio transport."""
        # Disable logging for stdio transport to avoid interfering with JSON-RPC
        logging.getLogger().setLevel(logging.CRITICAL)
        
        async def run_async():
            # Create initialization options
            init_options = InitializationOptions(
                server_name=self.name,
                server_version=self.version,
                capabilities=ServerCapabilities(
                    tools={"listTools": True, "callTool": True} if self._tools else {},
                    resources={"listResources": True, "readResource": True} if self._resources else {},
                    prompts={"listPrompts": True, "getPrompt": True} if self._prompts else {}
                ),
                instructions=self.description
            )
            
            async with stdio_server() as (read_stream, write_stream):
                await self._server.run(
                    read_stream=read_stream,
                    write_stream=write_stream,
                    initialization_options=init_options
                )
        
        asyncio.run(run_async())
    
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