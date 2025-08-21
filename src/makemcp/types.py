"""
MakeMCP Types - Type definitions for MakeMCP
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ToolResult(BaseModel):
    """
    Standard result format for MCP tools.
    """
    result: Any = Field(..., description="The tool execution result")
    success: bool = Field(default=True, description="Whether the tool executed successfully")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ResourceContent(BaseModel):
    """
    Content returned by MCP resources.
    """
    uri: str = Field(..., description="The resource URI")
    content: str = Field(..., description="The resource content")
    mime_type: str = Field(default="text/plain", description="MIME type of the content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class PromptMessage(BaseModel):
    """
    A message in a prompt template.
    """
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class Context(BaseModel):
    """
    Execution context passed to tools and resources.
    """
    request_id: Optional[str] = Field(default=None, description="Unique request ID")
    user: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class TransportType(str, Enum):
    """
    Supported transport types for MCP servers.
    """
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WEBSOCKET = "websocket"


class ServerConfig(BaseModel):
    """
    Configuration for a MakeMCP server.
    """
    name: str = Field(..., description="Server name")
    version: str = Field(default="1.0.0", description="Server version")
    description: Optional[str] = Field(default=None, description="Server description")
    transport: TransportType = Field(default=TransportType.STDIO, description="Transport type")
    host: str = Field(default="localhost", description="Host for network transports")
    port: int = Field(default=8000, description="Port for network transports")
    log_level: str = Field(default="INFO", description="Logging level")
    auto_reload: bool = Field(default=False, description="Auto-reload on code changes")


class ToolSchema(BaseModel):
    """
    Schema definition for a tool.
    """
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for parameters")
    returns: Dict[str, Any] = Field(..., description="JSON schema for return value")


class ResourceSchema(BaseModel):
    """
    Schema definition for a resource.
    """
    uri_template: str = Field(..., description="URI template")
    name: str = Field(..., description="Resource name")
    description: str = Field(..., description="Resource description")
    mime_type: str = Field(default="text/plain", description="MIME type")


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    """
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")