"""
Tests for QuickMCP resources and prompts
"""

import pytest
from quickmcp import QuickMCPServer


class TestResourceRegistration:
    """Test resource registration and decoration."""
    
    def test_register_simple_resource(self, simple_server):
        """Test registering a simple resource."""
        @simple_server.resource("test://{id}")
        def test_resource(id: str) -> str:
            """Test resource."""
            return f"Resource {id}"
        
        resources = simple_server.list_resources()
        assert "test://{id}" in resources
        assert len(resources) == 1
    
    def test_register_resource_with_custom_name(self, simple_server):
        """Test registering a resource with custom name."""
        @simple_server.resource(
            "data://{key}",
            name="data_fetcher",
            description="Fetch data by key"
        )
        def get_data(key: str) -> str:
            """Get data."""
            return f"Data for {key}"
        
        resources = simple_server.list_resources()
        assert "data://{key}" in resources
    
    def test_register_resource_with_mime_type(self, simple_server):
        """Test registering a resource with custom MIME type."""
        @simple_server.resource(
            "json://{id}",
            mime_type="application/json"
        )
        def json_resource(id: str) -> str:
            """JSON resource."""
            import json
            return json.dumps({"id": id, "data": "test"})
        
        resources = simple_server.list_resources()
        assert "json://{id}" in resources
    
    def test_register_multiple_resources(self, simple_server):
        """Test registering multiple resources."""
        @simple_server.resource("file://{path}")
        def file_resource(path: str) -> str:
            return f"File at {path}"
        
        @simple_server.resource("config://{section}")
        def config_resource(section: str) -> str:
            return f"Config section {section}"
        
        @simple_server.resource("data://{id}")
        def data_resource(id: str) -> str:
            return f"Data {id}"
        
        resources = simple_server.list_resources()
        assert len(resources) == 3
        assert "file://{path}" in resources
        assert "config://{section}" in resources
        assert "data://{id}" in resources
    
    def test_resource_with_multiple_parameters(self, simple_server):
        """Test resource with multiple URI parameters."""
        @simple_server.resource("user://{org}/{user}")
        def user_resource(org: str, user: str) -> str:
            """User resource with multiple params."""
            return f"User {user} in org {org}"
        
        resources = simple_server.list_resources()
        assert "user://{org}/{user}" in resources
        
        # Test direct execution
        result = user_resource("myorg", "myuser")
        assert result == "User myuser in org myorg"


class TestResourceExecution:
    """Test resource execution."""
    
    def test_resource_in_registry(self, server_with_resources):
        """Test that resources are properly registered."""
        resources = server_with_resources._resources
        
        assert "test://{key}" in resources
        assert "info://server" in resources
        
        # Test that functions are callable
        test_func = resources["test://{key}"]
        assert callable(test_func)
    
    def test_resource_returns_string(self, simple_server):
        """Test that resources return strings."""
        test_data = {"a": 1, "b": 2}
        
        @simple_server.resource("data://{key}")
        def data_resource(key: str) -> str:
            """Return data as string."""
            import json
            return json.dumps(test_data.get(key, None))
        
        # Direct execution
        result = data_resource("a")
        assert result == "1"
        
        result = data_resource("c")
        assert result == "null"


class TestPromptRegistration:
    """Test prompt registration and decoration."""
    
    def test_register_simple_prompt(self, simple_server):
        """Test registering a simple prompt."""
        @simple_server.prompt()
        def test_prompt(topic: str) -> str:
            """Test prompt."""
            return f"Tell me about {topic}"
        
        prompts = simple_server.list_prompts()
        assert "test_prompt" in prompts
        assert len(prompts) == 1
    
    def test_register_prompt_with_custom_name(self, simple_server):
        """Test registering a prompt with custom name."""
        @simple_server.prompt(name="analysis_prompt")
        def analyze(data: str) -> str:
            """Analysis prompt."""
            return f"Analyze this data: {data}"
        
        prompts = simple_server.list_prompts()
        assert "analysis_prompt" in prompts
        assert "analyze" not in prompts
    
    def test_register_prompt_with_arguments(self, simple_server):
        """Test registering a prompt with argument schema."""
        arguments = [
            {"name": "topic", "type": "string", "required": True},
            {"name": "level", "type": "string", "required": False}
        ]
        
        @simple_server.prompt(
            name="educational_prompt",
            description="Generate educational content",
            arguments=arguments
        )
        def education_prompt(topic: str, level: str = "beginner") -> str:
            """Educational prompt."""
            return f"Explain {topic} at {level} level"
        
        prompts = simple_server.list_prompts()
        assert "educational_prompt" in prompts
    
    def test_register_multiple_prompts(self, simple_server):
        """Test registering multiple prompts."""
        @simple_server.prompt()
        def code_review(code: str) -> str:
            return f"Review this code: {code}"
        
        @simple_server.prompt()
        def explain_concept(concept: str) -> str:
            return f"Explain {concept}"
        
        @simple_server.prompt(name="debug")
        def debug_prompt(error: str) -> str:
            return f"Debug this error: {error}"
        
        prompts = simple_server.list_prompts()
        assert len(prompts) == 3
        assert "code_review" in prompts
        assert "explain_concept" in prompts
        assert "debug" in prompts


class TestPromptExecution:
    """Test prompt execution."""
    
    def test_prompt_in_registry(self, server_with_prompts):
        """Test that prompts are properly registered."""
        prompts = server_with_prompts._prompts
        
        assert "test_prompt" in prompts
        assert "custom_prompt" in prompts
        
        # Test that functions are callable
        test_func = prompts["test_prompt"]
        assert callable(test_func)
        
        # Direct execution
        result = test_func("Python")
        assert result == "Test prompt for Python"
    
    def test_prompt_with_default_arguments(self, simple_server):
        """Test prompt with default arguments."""
        @simple_server.prompt()
        def analysis_prompt(
            data: str,
            style: str = "detailed",
            format: str = "markdown"
        ) -> str:
            """Generate analysis prompt."""
            return f"Analyze {data} in {style} style using {format} format"
        
        # Test with all arguments
        result = analysis_prompt("test data", "brief", "json")
        assert "brief" in result
        assert "json" in result
        
        # Test with defaults
        result = analysis_prompt("test data")
        assert "detailed" in result
        assert "markdown" in result
    
    def test_prompt_returns_string(self, simple_server):
        """Test that prompts always return strings."""
        @simple_server.prompt()
        def template_prompt(items: list) -> str:
            """Generate prompt from list."""
            return f"Process these items: {', '.join(map(str, items))}"
        
        result = template_prompt([1, 2, 3])
        assert isinstance(result, str)
        assert result == "Process these items: 1, 2, 3"


class TestMixedComponents:
    """Test servers with mixed tools, resources, and prompts."""
    
    def test_server_with_all_components(self, simple_server):
        """Test server with tools, resources, and prompts."""
        # Add tool
        @simple_server.tool()
        def calculate(x: int, y: int) -> int:
            return x + y
        
        # Add resource
        @simple_server.resource("data://{id}")
        def get_data(id: str) -> str:
            return f"Data {id}"
        
        # Add prompt
        @simple_server.prompt()
        def analyze(text: str) -> str:
            return f"Analyze: {text}"
        
        # Check all are registered
        assert len(simple_server.list_tools()) == 1
        assert len(simple_server.list_resources()) == 1
        assert len(simple_server.list_prompts()) == 1
        
        # Check info
        info = simple_server.get_info()
        assert len(info["tools"]) == 1
        assert len(info["resources"]) == 1
        assert len(info["prompts"]) == 1