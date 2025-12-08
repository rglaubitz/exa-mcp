# MCP Server Testing Best Practices (2024-2025)

**Research Date:** December 8, 2025
**Agent:** deep_researcher
**Sources:** 15+ verified sources including official MCP/FastMCP documentation

---

## Executive Summary

Testing Model Context Protocol (MCP) servers requires a specialized approach that balances protocol compliance, asynchronous operations, and real-world integration patterns. The community has converged on **in-memory testing** as the gold standard for unit tests, with clear patterns for integration testing and mocking external dependencies.

**Key Findings:**

- Use in-memory client-server binding for deterministic unit tests (avoid subprocess spawning)
- FastMCP provides native testing support via `Client(server)` pattern
- Async testing with pytest-asyncio is standard
- Mock external dependencies using `unittest.mock.AsyncMock`
- Integration tests should validate tool chaining and context preservation
- Official MCP documentation is sparse; community resources (MCPcat, FastMCP docs) fill the gap

---

## 1. Core Testing Philosophy: In-Memory Testing

### The Problem with Traditional Approaches

Early MCP testing often involved spawning subprocess servers and connecting over stdio/HTTP, leading to:

- Race conditions and connection failures
- Slow test execution (seconds vs milliseconds)
- Difficult debugging (cross-process breakpoints)
- Flaky CI/CD pipelines

### The Solution: Direct Client-Server Binding

**Source:** [MCPcat Unit Testing Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers)

```python
import pytest
from fastmcp import FastMCP, Client

async def test_tool_execution():
    """Test MCP tool directly in-memory without subprocess overhead."""
    server = FastMCP("TestServer")

    @server.tool
    def calculate(x: int, y: int) -> int:
        """Simple calculation tool for testing."""
        return x + y

    async with Client(server) as client:
        result = await client.call_tool("calculate", {"x": 5, "y": 3})
        assert result[0].text == "8"
```

**Why This Works:**

- Eliminates network/IPC overhead
- Deterministic execution (no timing issues)
- Full debugger support (single process)
- Protocol-compliant (actual MCP messages)
- Fast (milliseconds per test)

**Source:** [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)

> "FastMCP uses in-memory transport for testing, where servers and clients communicate directly. This runs the actual MCP protocol without network overhead, providing deterministic execution and full debugger support."

---

## 2. Project Setup and Configuration

### Required Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "fastmcp>=2.13.3",
    "httpx>=0.28.0",  # For external API calls
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
]
```

### Pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Enable automatic async test detection
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "integration: marks tests as integration (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "client_process: marks tests that spawn separate processes",
]
```

### Running Tests

```bash
# All tests
uv run pytest

# Skip integration tests
uv run pytest -m "not integration"

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific file
uv run pytest tests/test_tools.py

# Single test
uv run pytest tests/test_tools.py::test_search_tool
```

**Performance Expectation:** Tests should complete in under 1 second unless marked as integration tests.

---

## 3. Unit Testing Patterns

### 3.1 Testing Tools with Parameters

**Source:** [MCPcat Unit Testing Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers)

```python
import pytest
from fastmcp import FastMCP, Client
import json
from typing import List, Dict

@pytest.fixture
def mcp_server():
    """Reusable server fixture with search tool."""
    server = FastMCP("TestServer")

    @server.tool
    def search_items(query: str, limit: int = 10) -> List[Dict]:
        """Search for items matching query."""
        if not query:
            raise ValueError("Query cannot be empty")
        return [
            {"name": f"Item {i}", "score": i * 10}
            for i in range(limit)
        ]

    return server

@pytest.mark.asyncio
async def test_tool_with_default_parameters(mcp_server):
    """Test tool with default limit parameter."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("search_items", {"query": "test"})
        items = json.loads(result[0].text)
        assert len(items) == 10

@pytest.mark.asyncio
async def test_tool_with_custom_parameters(mcp_server):
    """Test tool with custom limit parameter."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("search_items", {
            "query": "python",
            "limit": 5
        })
        items = json.loads(result[0].text)
        assert len(items) == 5
        assert items[0]["name"] == "Item 0"

@pytest.mark.asyncio
async def test_tool_validation_error(mcp_server):
    """Test tool raises error on empty query."""
    async with Client(mcp_server) as client:
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("search_items", {"query": ""})
        assert "Query cannot be empty" in str(exc_info.value)
```

### 3.2 Parametrized Testing

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("query,limit,expected_count", [
    ("test", 5, 5),
    ("python", 10, 10),
    ("data", 1, 1),
    ("empty", 0, 0),
])
async def test_search_variations(mcp_server, query, limit, expected_count):
    """Test multiple query/limit combinations."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("search_items", {
            "query": query,
            "limit": limit
        })
        items = json.loads(result[0].text)
        assert len(items) == expected_count
```

### 3.3 Testing Resources

```python
@pytest.fixture
def server_with_resources():
    """Server with resource handlers."""
    server = FastMCP("ResourceServer")

    @server.resource("config://settings")
    async def get_settings():
        return {"theme": "dark", "language": "en"}

    @server.resource("data://stats")
    async def get_stats():
        return {"users": 1000, "active": 250}

    return server

@pytest.mark.asyncio
async def test_resource_listing(server_with_resources):
    """Test listing available resources."""
    async with Client(server_with_resources) as client:
        resources = await client.list_resources()
        uris = [r.uri for r in resources]
        assert "config://settings" in uris
        assert "data://stats" in uris

@pytest.mark.asyncio
async def test_resource_content(server_with_resources):
    """Test reading resource content."""
    async with Client(server_with_resources) as client:
        content = await client.read_resource("config://settings")
        settings = json.loads(content.text)
        assert settings["theme"] == "dark"
        assert settings["language"] == "en"
```

### 3.4 Testing Prompts

```python
@pytest.fixture
def server_with_prompts():
    """Server with prompt templates."""
    server = FastMCP("PromptServer")

    @server.prompt()
    def analyze_code(language: str = "python") -> str:
        return f"Analyze this {language} code for best practices and suggest improvements."

    return server

@pytest.mark.asyncio
async def test_prompt_listing(server_with_prompts):
    """Test listing available prompts."""
    async with Client(server_with_prompts) as client:
        prompts = await client.list_prompts()
        names = [p.name for p in prompts]
        assert "analyze_code" in names

@pytest.mark.asyncio
async def test_prompt_with_parameters(server_with_prompts):
    """Test prompt with custom parameters."""
    async with Client(server_with_prompts) as client:
        prompt = await client.get_prompt("analyze_code", {"language": "rust"})
        assert "rust" in prompt.messages[0].content.text.lower()
```

---

## 4. Mocking External Dependencies

### 4.1 Mocking HTTP APIs

**Source:** [MCPcat Unit Testing Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers)

```python
from unittest.mock import AsyncMock, patch
import httpx

@pytest.fixture
def weather_server():
    """Server with external API dependency."""
    server = FastMCP("WeatherServer")

    @server.tool
    async def fetch_weather(city: str) -> Dict:
        """Fetch weather data from external API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.weather.com/v1/current",
                params={"city": city}
            )
            return response.json()

    return server

@pytest.mark.asyncio
async def test_weather_with_mocked_api(weather_server):
    """Test weather tool with mocked HTTP client."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "city": "NYC",
        "temp": 72,
        "condition": "sunny"
    })

    with patch('httpx.AsyncClient.get', return_value=mock_response):
        async with Client(weather_server) as client:
            result = await client.call_tool("fetch_weather", {"city": "NYC"})
            weather = json.loads(result[0].text)
            assert weather["temp"] == 72
            assert weather["condition"] == "sunny"
```

### 4.2 Mocking Database Operations

```python
from unittest.mock import MagicMock, AsyncMock
import pytest

@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.fetch_users = AsyncMock(return_value=[
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ])
    db.create_user = AsyncMock(return_value={"id": 3, "name": "Charlie"})
    return db

@pytest.fixture
def db_server(mock_db):
    """Server with database dependency (injected)."""
    server = FastMCP("DatabaseServer")

    @server.tool
    async def get_users() -> List[Dict]:
        """Fetch all users from database."""
        return await mock_db.fetch_users()

    @server.tool
    async def create_user(name: str, email: str) -> Dict:
        """Create new user in database."""
        return await mock_db.create_user(name=name, email=email)

    return server

@pytest.mark.asyncio
async def test_get_users(db_server, mock_db):
    """Test fetching users with mocked database."""
    async with Client(db_server) as client:
        result = await client.call_tool("get_users", {})
        users = json.loads(result[0].text)
        assert len(users) == 2
        assert users[0]["name"] == "Alice"

    # Verify mock was called
    mock_db.fetch_users.assert_called_once()

@pytest.mark.asyncio
async def test_create_user(db_server, mock_db):
    """Test creating user with mocked database."""
    async with Client(db_server) as client:
        result = await client.call_tool("create_user", {
            "name": "Charlie",
            "email": "charlie@example.com"
        })
        user = json.loads(result[0].text)
        assert user["id"] == 3
        assert user["name"] == "Charlie"

    # Verify mock was called with correct args
    mock_db.create_user.assert_called_once_with(
        name="Charlie",
        email="charlie@example.com"
    )
```

### 4.3 Dependency Injection Pattern

**Best Practice:** Design tools to accept dependencies as parameters for easier testing.

```python
# Bad: Hard-coded dependency
@server.tool
async def fetch_data(query: str) -> Dict:
    client = ExternalAPIClient()  # Hard to mock
    return await client.search(query)

# Good: Dependency injection
class MCPServer:
    def __init__(self, api_client=None):
        self.server = FastMCP("MyServer")
        self.api_client = api_client or ExternalAPIClient()

        @self.server.tool
        async def fetch_data(query: str) -> Dict:
            return await self.api_client.search(query)

# Easy to test
@pytest.fixture
def server_with_mock_api():
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value={"results": []})
    return MCPServer(api_client=mock_client).server
```

---

## 5. Integration Testing

### 5.1 Multi-Tool Workflow Testing

**Source:** [MCPcat Integration Testing Guide](https://mcpcat.io/guides/integration-tests-mcp-flows)

```python
@pytest.fixture
def workflow_server():
    """Server with multiple interdependent tools."""
    server = FastMCP("WorkflowServer")

    # Shared state for workflow
    data_store = {}

    @server.tool
    async def fetch_data(source: str) -> Dict:
        """Step 1: Fetch data from source."""
        data_id = f"data_{len(data_store)}"
        data_store[data_id] = {
            "source": source,
            "raw": f"Raw data from {source}",
            "status": "fetched"
        }
        return {"data_id": data_id}

    @server.tool
    async def process_data(data_id: str, operation: str) -> Dict:
        """Step 2: Process fetched data."""
        if data_id not in data_store:
            raise ValueError(f"Data {data_id} not found")

        data_store[data_id]["processed"] = f"Processed: {operation}"
        data_store[data_id]["status"] = "processed"
        return {"data_id": data_id, "operation": operation}

    @server.tool
    async def validate_data(data_id: str) -> Dict:
        """Step 3: Validate processed data."""
        if data_id not in data_store:
            raise ValueError(f"Data {data_id} not found")

        data = data_store[data_id]
        is_valid = data.get("status") == "processed"
        return {"data_id": data_id, "valid": is_valid}

    return server

@pytest.mark.asyncio
async def test_complete_workflow(workflow_server):
    """Test complete data processing workflow."""
    async with Client(workflow_server) as client:
        # Step 1: Fetch data
        fetch_result = await client.call_tool("fetch_data", {"source": "database"})
        fetch_data = json.loads(fetch_result[0].text)
        data_id = fetch_data["data_id"]
        assert data_id.startswith("data_")

        # Step 2: Process data
        process_result = await client.call_tool("process_data", {
            "data_id": data_id,
            "operation": "transform"
        })
        process_data = json.loads(process_result[0].text)
        assert process_data["operation"] == "transform"

        # Step 3: Validate processed data
        validate_result = await client.call_tool("validate_data", {
            "data_id": data_id
        })
        validate_data = json.loads(validate_result[0].text)
        assert validate_data["valid"] is True

@pytest.mark.asyncio
async def test_workflow_error_handling(workflow_server):
    """Test workflow error handling for missing data."""
    async with Client(workflow_server) as client:
        # Try to process non-existent data
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("process_data", {
                "data_id": "nonexistent",
                "operation": "transform"
            })
        assert "not found" in str(exc_info.value).lower()
```

### 5.2 Concurrent Request Testing

```python
import asyncio

@pytest.mark.asyncio
async def test_concurrent_operations(workflow_server):
    """Test server handles concurrent requests correctly."""
    async with Client(workflow_server) as client:
        # Create 10 concurrent fetch operations
        tasks = [
            client.call_tool("fetch_data", {"source": f"source_{i}"})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 10

        # Extract data IDs and verify uniqueness
        data_ids = [
            json.loads(r[0].text)["data_id"]
            for r in results
        ]
        assert len(set(data_ids)) == 10  # All unique
```

### 5.3 Context Preservation Testing

```python
@pytest.mark.asyncio
async def test_session_context_preservation(workflow_server):
    """Test that context is preserved across multiple tool calls."""
    async with Client(workflow_server) as client:
        # Perform operations in same session
        fetch1 = await client.call_tool("fetch_data", {"source": "A"})
        fetch2 = await client.call_tool("fetch_data", {"source": "B"})

        data_id_1 = json.loads(fetch1[0].text)["data_id"]
        data_id_2 = json.loads(fetch2[0].text)["data_id"]

        # Both data items should be accessible
        validate1 = await client.call_tool("validate_data", {"data_id": data_id_1})
        validate2 = await client.call_tool("validate_data", {"data_id": data_id_2})

        # Context was preserved - both are accessible
        assert json.loads(validate1[0].text)
        assert json.loads(validate2[0].text)
```

---

## 6. Error Handling and Validation Testing

### 6.1 Testing Error Responses

**Source:** [MCPcat Error Handling Guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers)

```python
from fastmcp import FastMCP, Client
from mcp.types import CallToolResult, TextContent

@pytest.fixture
def error_handling_server():
    """Server with comprehensive error handling."""
    server = FastMCP("ErrorServer")

    @server.tool
    async def risky_operation(action: str) -> str:
        """Tool that may fail based on action."""
        if action == "fail":
            raise RuntimeError("Operation failed intentionally")
        elif action == "invalid":
            raise ValueError("Invalid action parameter")
        elif action == "timeout":
            raise TimeoutError("Operation timed out")
        return f"Success: {action}"

    return server

@pytest.mark.asyncio
async def test_runtime_error_handling(error_handling_server):
    """Test server handles RuntimeError correctly."""
    async with Client(error_handling_server) as client:
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("risky_operation", {"action": "fail"})
        assert "Operation failed intentionally" in str(exc_info.value)

@pytest.mark.asyncio
async def test_validation_error_handling(error_handling_server):
    """Test server handles ValueError correctly."""
    async with Client(error_handling_server) as client:
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("risky_operation", {"action": "invalid"})
        assert "Invalid action parameter" in str(exc_info.value)

@pytest.mark.asyncio
async def test_success_path(error_handling_server):
    """Test successful operation returns expected result."""
    async with Client(error_handling_server) as client:
        result = await client.call_tool("risky_operation", {"action": "process"})
        assert "Success: process" in result[0].text
```

### 6.2 Input Validation Testing

**Source:** [MCPcat Validation Testing Guide](https://mcpcat.io/guides/validation-tests-tool-inputs)

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class SearchParams(BaseModel):
    """Validated search parameters."""
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=10, ge=1, le=100)
    category: Optional[str] = Field(None, pattern="^[a-z_]+$")

@pytest.fixture
def validated_server():
    """Server with Pydantic validation."""
    server = FastMCP("ValidatedServer")

    @server.tool
    async def validated_search(query: str, limit: int = 10, category: str = None) -> Dict:
        """Search with validated parameters."""
        # Validate using Pydantic
        params = SearchParams(query=query, limit=limit, category=category)
        return {
            "query": params.query,
            "limit": params.limit,
            "category": params.category
        }

    return server

@pytest.mark.asyncio
@pytest.mark.parametrize("query,limit,should_fail", [
    ("valid query", 10, False),
    ("", 10, True),  # Empty query
    ("valid", 0, True),  # Limit too low
    ("valid", 101, True),  # Limit too high
    ("x" * 201, 10, True),  # Query too long
])
async def test_input_validation(validated_server, query, limit, should_fail):
    """Test input validation with various parameter combinations."""
    async with Client(validated_server) as client:
        if should_fail:
            with pytest.raises(Exception):
                await client.call_tool("validated_search", {
                    "query": query,
                    "limit": limit
                })
        else:
            result = await client.call_tool("validated_search", {
                "query": query,
                "limit": limit
            })
            assert result[0].text  # Should succeed

@pytest.mark.asyncio
async def test_category_pattern_validation(validated_server):
    """Test category parameter pattern validation."""
    async with Client(validated_server) as client:
        # Valid category
        result = await client.call_tool("validated_search", {
            "query": "test",
            "category": "tech_news"
        })
        assert result[0].text

        # Invalid category (uppercase not allowed)
        with pytest.raises(Exception):
            await client.call_tool("validated_search", {
                "query": "test",
                "category": "TechNews"
            })
```

---

## 7. FastMCP-Specific Testing Patterns

### 7.1 Testing with FastMCP Test Client

**Source:** [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)

```python
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_with_test_client():
    """Use FastMCP's built-in test_client() method."""
    server = FastMCP("TestServer")

    @server.tool()
    async def echo(message: str) -> str:
        return f"Echo: {message}"

    # Use test_client() context manager
    async with server.test_client() as client:
        # List tools
        tools = await client.list_tools()
        assert len(tools.tools) == 1
        assert tools.tools[0].name == "echo"

        # Call tool
        result = await client.call_tool("echo", message="Hello")
        assert result.content[0].text == "Echo: Hello"
```

### 7.2 Fixture-Based Server Configuration

```python
@pytest.fixture
def base_server():
    """Base server configuration for reuse."""
    return FastMCP("TestServer")

@pytest.fixture
def server_with_tools(base_server):
    """Server with standard tools."""
    @base_server.tool
    def add(a: int, b: int) -> int:
        return a + b

    @base_server.tool
    def multiply(a: int, b: int) -> int:
        return a * b

    return base_server

@pytest.mark.asyncio
async def test_math_operations(server_with_tools):
    """Test multiple math tools."""
    async with Client(server_with_tools) as client:
        add_result = await client.call_tool("add", {"a": 5, "b": 3})
        assert add_result[0].text == "8"

        mult_result = await client.call_tool("multiply", {"a": 5, "b": 3})
        assert mult_result[0].text == "15"
```

### 7.3 Testing with In-Process Server (Advanced)

**Source:** [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)

For cases where you need more control:

```python
from fastmcp import FastMCP
from fastmcp.testing import run_server_async
import asyncio

@pytest.mark.asyncio
async def test_with_in_process_server():
    """Test using in-process server for advanced scenarios."""
    server = FastMCP("TestServer")

    @server.tool
    async def slow_operation(seconds: int) -> str:
        await asyncio.sleep(seconds)
        return f"Completed after {seconds}s"

    # Run server as async task
    async with run_server_async(server) as client:
        result = await client.call_tool("slow_operation", {"seconds": 1})
        assert "Completed after 1s" in result[0].text
```

---

## 8. Real-World Testing Patterns

### 8.1 Testing Exa API Integration (Your Use Case)

```python
from unittest.mock import AsyncMock, patch
import httpx

@pytest.fixture
def exa_server():
    """MCP server wrapping Exa API."""
    server = FastMCP("ExaServer")

    @server.tool
    async def search(
        query: str,
        num_results: int = 10,
        category: str = None
    ) -> Dict:
        """Search using Exa API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.exa.ai/search",
                json={
                    "query": query,
                    "numResults": num_results,
                    "category": category
                },
                headers={"Authorization": f"Bearer {os.getenv('EXA_API_KEY')}"}
            )
            return response.json()

    return server

@pytest.mark.asyncio
async def test_exa_search_with_mock(exa_server):
    """Test Exa search with mocked API response."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "results": [
            {"url": "https://example.com", "title": "Example", "score": 0.95}
        ],
        "autopromptString": "improved query"
    })

    with patch('httpx.AsyncClient.post', return_value=mock_response):
        async with Client(exa_server) as client:
            result = await client.call_tool("search", {
                "query": "python testing",
                "num_results": 10
            })

            data = json.loads(result[0].text)
            assert len(data["results"]) == 1
            assert data["results"][0]["title"] == "Example"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_exa_search_real_api(exa_server):
    """Integration test with real Exa API (marked as integration)."""
    if not os.getenv("EXA_API_KEY"):
        pytest.skip("EXA_API_KEY not set")

    async with Client(exa_server) as client:
        result = await client.call_tool("search", {
            "query": "fastmcp testing",
            "num_results": 5
        })

        data = json.loads(result[0].text)
        assert "results" in data
        assert len(data["results"]) <= 5
```

### 8.2 Testing with Fixtures for Test Data

```python
@pytest.fixture
def sample_search_response():
    """Sample Exa API response for testing."""
    return {
        "results": [
            {
                "url": "https://docs.exa.ai/search",
                "title": "Exa Search API Documentation",
                "publishedDate": "2024-01-15",
                "score": 0.98,
                "text": "Complete guide to Exa search..."
            },
            {
                "url": "https://github.com/exa-labs/exa-py",
                "title": "Exa Python SDK",
                "score": 0.92,
                "text": "Official Python SDK for Exa API"
            }
        ],
        "autopromptString": "exa api search documentation"
    }

@pytest.mark.asyncio
async def test_search_result_parsing(exa_server, sample_search_response):
    """Test parsing of Exa search results."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=sample_search_response)
        mock_post.return_value = mock_response

        async with Client(exa_server) as client:
            result = await client.call_tool("search", {"query": "test"})
            data = json.loads(result[0].text)

            assert len(data["results"]) == 2
            assert data["results"][0]["score"] == 0.98
            assert "Documentation" in data["results"][0]["title"]
```

---

## 9. Test Organization and Structure

### 9.1 Recommended Directory Structure

```
exa-mcp-enhanced/
├── src/
│   └── exa_mcp_enhanced/
│       ├── __init__.py
│       ├── server.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py
│       │   ├── similar.py
│       │   └── answer.py
│       └── client.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_server.py           # Server initialization tests
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── test_search.py       # Unit tests for search tool
│   │   ├── test_similar.py      # Unit tests for similar tool
│   │   └── test_answer.py       # Unit tests for answer tool
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_workflows.py    # Multi-tool workflows
│   │   └── test_real_api.py     # Real API integration tests
│   └── fixtures/
│       ├── __init__.py
│       └── sample_responses.py  # Mock response data
└── pyproject.toml
```

### 9.2 Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from fastmcp import FastMCP, Client
from unittest.mock import AsyncMock
import os

@pytest.fixture
def base_server():
    """Base MCP server for testing."""
    return FastMCP("TestServer")

@pytest.fixture
def mock_exa_client():
    """Mock Exa API client."""
    client = AsyncMock()
    client.search = AsyncMock(return_value={
        "results": [],
        "autopromptString": "test query"
    })
    return client

@pytest.fixture
def skip_if_no_api_key():
    """Skip test if API key not available."""
    if not os.getenv("EXA_API_KEY"):
        pytest.skip("EXA_API_KEY not set - skipping integration test")

@pytest.fixture(scope="session")
def sample_data():
    """Load sample test data once per session."""
    return {
        "valid_queries": ["python", "javascript", "rust"],
        "invalid_queries": ["", None, " " * 300],
    }
```

### 9.3 Test Markers for Organization

```python
# Mark integration tests
@pytest.mark.integration
async def test_real_api_call():
    pass

# Mark slow tests
@pytest.mark.slow
async def test_large_dataset_processing():
    pass

# Mark tests requiring network
@pytest.mark.network
async def test_external_service():
    pass

# Custom marker for API tests
pytestmark = pytest.mark.api_tests  # Mark entire module
```

---

## 10. Testing Best Practices Summary

### 10.1 Do's

**Source:** [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)

1. **Use in-memory testing** - Fastest and most reliable
2. **Test single behavior per test** - Easier debugging
3. **Mock external dependencies** - Faster tests, no API costs
4. **Use pytest fixtures** - Reusable test setup
5. **Test error scenarios** - Not just happy paths
6. **Parametrize tests** - Test multiple inputs efficiently
7. **Use async/await properly** - Avoid blocking operations
8. **Keep tests fast** - Unit tests < 1 second
9. **Use descriptive test names** - `test_search_with_empty_query_raises_error`
10. **Separate unit and integration tests** - Use markers

### 10.2 Don'ts

1. **Don't spawn subprocesses for unit tests** - Slow and flaky
2. **Don't test multiple behaviors in one test** - Hard to debug
3. **Don't use fixtures for FastMCP clients** - Event loop issues
4. **Don't skip error testing** - Errors are critical to test
5. **Don't hardcode test data in tests** - Use fixtures
6. **Don't test implementation details** - Test behavior
7. **Don't forget to clean up resources** - Use context managers
8. **Don't write slow unit tests** - Mark as integration instead
9. **Don't test external APIs without mocks** - Too slow/flaky
10. **Don't ignore async warnings** - Fix them immediately

### 10.3 Performance Guidelines

**Source:** [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)

> "Tests should complete in under 1 second unless marked as integration tests."

| Test Type         | Target Speed | Acceptable Range |
| ----------------- | ------------ | ---------------- |
| Unit tests        | < 100ms      | < 1 second       |
| Integration tests | < 5 seconds  | < 30 seconds     |
| E2E tests         | < 30 seconds | < 2 minutes      |

---

## 11. Advanced Patterns

### 11.1 Testing with Inline Snapshots

For complex response validation:

```python
from inline_snapshot import snapshot

@pytest.mark.asyncio
async def test_search_response_structure(exa_server, sample_search_response):
    """Test response matches expected structure using snapshots."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=sample_search_response)
        mock_post.return_value = mock_response

        async with Client(exa_server) as client:
            result = await client.call_tool("search", {"query": "test"})
            data = json.loads(result[0].text)

            # Use snapshot for complex structure validation
            assert data == snapshot({
                "results": [
                    {
                        "url": "https://docs.exa.ai/search",
                        "title": "Exa Search API Documentation",
                        "score": 0.98,
                    }
                ],
                "autopromptString": "exa api search documentation"
            })
```

Run `pytest --inline-snapshot=create` to generate snapshots initially, then `pytest --inline-snapshot=fix` to update them.

### 11.2 Property-Based Testing with Hypothesis

```python
from hypothesis import given, strategies as st

@given(
    query=st.text(min_size=1, max_size=200),
    limit=st.integers(min_value=1, max_value=100)
)
@pytest.mark.asyncio
async def test_search_with_random_inputs(exa_server, query, limit):
    """Test search handles arbitrary valid inputs."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"results": []})
        mock_post.return_value = mock_response

        async with Client(exa_server) as client:
            result = await client.call_tool("search", {
                "query": query,
                "num_results": limit
            })
            assert result  # Should not raise exception
```

### 11.3 Testing Resource Cleanup

```python
import weakref

@pytest.mark.asyncio
async def test_client_cleanup(exa_server):
    """Test that client resources are properly cleaned up."""
    client_refs = []

    for _ in range(5):
        async with Client(exa_server) as client:
            # Create weak reference to track cleanup
            client_refs.append(weakref.ref(client))
            await client.call_tool("search", {"query": "test"})

    # Force garbage collection
    import gc
    gc.collect()

    # Verify all clients were cleaned up
    assert all(ref() is None for ref in client_refs)
```

---

## 12. CI/CD Integration

### 12.1 GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run unit tests
        run: uv run pytest -m "not integration" --cov=src --cov-report=xml

      - name: Run integration tests
        run: uv run pytest -m integration
        env:
          EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 12.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (fast tests only)
        entry: uv run pytest -m "not integration and not slow"
        language: system
        pass_filenames: false
        always_run: true
```

---

## 13. Tools and Resources

### 13.1 Essential Tools

| Tool            | Purpose              | Installation                  |
| --------------- | -------------------- | ----------------------------- |
| pytest          | Test framework       | `pip install pytest`          |
| pytest-asyncio  | Async test support   | `pip install pytest-asyncio`  |
| pytest-cov      | Coverage reports     | `pip install pytest-cov`      |
| pytest-mock     | Enhanced mocking     | `pip install pytest-mock`     |
| inline-snapshot | Snapshot testing     | `pip install inline-snapshot` |
| hypothesis      | Property-based tests | `pip install hypothesis`      |

### 13.2 MCP-Specific Tools

| Tool          | Purpose               | Link                                             |
| ------------- | --------------------- | ------------------------------------------------ |
| MCP Inspector | Interactive testing   | `npm install -g @modelcontextprotocol/inspector` |
| FastMCP       | Python MCP framework  | https://gofastmcp.com                            |
| mcp-eval      | MCP testing framework | https://mcp-eval.ai                              |
| mcp-validator | Protocol validation   | https://github.com/Janix-ai/mcp-validator        |

### 13.3 Documentation Sources

1. **MCPcat Testing Guides** - https://mcpcat.io/guides/topic/mcp-testing
   - Most comprehensive community resource
   - Python and TypeScript examples
   - Unit, integration, and validation testing

2. **FastMCP Documentation** - https://gofastmcp.com/development/tests
   - Official FastMCP testing guide
   - In-memory testing patterns
   - Network transport testing

3. **MCP Official Docs** - https://modelcontextprotocol.io
   - Protocol specification
   - SDK documentation (limited testing guidance)

4. **Real Python Tutorial** - https://realpython.com/python-mcp/
   - Beginner-friendly MCP introduction
   - Basic testing examples

---

## 14. Common Issues and Solutions

### 14.1 Async Event Loop Issues

**Problem:** "RuntimeError: Event loop is closed"

```python
# Bad
@pytest.fixture
async def client(server):
    async with Client(server) as c:
        yield c  # Event loop closed after fixture

# Good
@pytest.fixture
def server():
    return FastMCP("TestServer")

@pytest.mark.asyncio
async def test_tool(server):
    async with Client(server) as client:  # Event loop managed in test
        result = await client.call_tool("tool", {})
```

### 14.2 Mock Not Being Called

**Problem:** Mock not intercepting calls

```python
# Bad - Mock applied too late
async with Client(server) as client:
    with patch('httpx.AsyncClient.get'):
        await client.call_tool("fetch")  # Already initialized

# Good - Mock applied before client creation
with patch('httpx.AsyncClient.get'):
    async with Client(server) as client:
        await client.call_tool("fetch")  # Mock active
```

### 14.3 Test Timeout Issues

**Problem:** Tests hang indefinitely

```python
# Configure pytest timeout
# pyproject.toml
[tool.pytest.ini_options]
timeout = 10  # 10 seconds per test

# Or per-test
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_slow_operation():
    pass
```

---

## 15. Key Takeaways

1. **In-Memory Testing is King** - Use `Client(server)` pattern for deterministic, fast tests

2. **Mock External Dependencies** - Use `AsyncMock` for APIs, databases, and services

3. **Separate Unit and Integration Tests** - Use pytest markers to organize tests

4. **Test Error Paths** - Don't just test happy paths; errors are critical

5. **Use Fixtures Wisely** - Share setup code but avoid event loop issues

6. **Keep Tests Fast** - Unit tests < 1s, integration tests < 30s

7. **Test Tool Chaining** - Integration tests should validate workflows

8. **Validate Inputs** - Use Pydantic for schema validation and test edge cases

9. **Follow FastMCP Patterns** - Use official testing utilities and conventions

10. **Official Docs Are Limited** - Community resources (MCPcat, blogs) are more comprehensive

---

## Sources

1. [MCPcat Unit Testing Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers) - Comprehensive Python/TypeScript testing patterns
2. [MCPcat Integration Testing Guide](https://mcpcat.io/guides/integration-tests-mcp-flows) - Multi-tool workflow testing
3. [FastMCP Testing Documentation](https://gofastmcp.com/development/tests) - Official FastMCP testing guide
4. [MCPcat Error Handling Guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers) - Error testing patterns
5. [MCPcat Validation Testing Guide](https://mcpcat.io/guides/validation-tests-tool-inputs) - Input validation with Pydantic
6. [Jeremiah Lowin - Stop Vibe-Testing](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers) - Testing philosophy
7. [DataCamp FastMCP Tutorial](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp) - Complete examples
8. [Real Python MCP Tutorial](https://realpython.com/python-mcp/) - Beginner guide with testing section
9. [Firecrawl FastMCP Tutorial](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python) - Testing and debugging
10. [mcp-python-sdk-inmemory-server-tests](https://github.com/junkmd/mcp-python-sdk-inmemory-server-tests) - In-memory testing examples
11. [Model Context Protocol Docs](https://modelcontextprotocol.io) - Official MCP specification
12. [mcp-eval Documentation](https://mcp-eval.ai) - MCP testing framework
13. [pytest-mcp-server GitHub](https://github.com/kieranlal/mcp_pytest_service) - Pytest integration service
14. [Composio MCP Guide](https://composio.dev/blog/how-to-effectively-use-prompts-resources-and-tools-in-mcp) - Prompts, resources, tools
15. [Medium - Testing MCP Servers](https://medium.com/@varun.singh9786/testing-mcp-servers-mcp-eval-f357a899002b) - mcp-eval overview

---

**Report Generated:** December 8, 2025
**Research Agent:** deep_researcher
**Total Sources Reviewed:** 15 primary sources, 20+ supplementary sources
**Confidence Level:** High (cross-validated across multiple authoritative sources)
