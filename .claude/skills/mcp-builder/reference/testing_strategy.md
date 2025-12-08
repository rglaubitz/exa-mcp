# MCP Server Testing Strategy

## Overview

Testing MCP servers requires a specific approach because they are long-running processes that communicate via protocols (stdio/HTTP/SSE). This guide covers best practices for writing effective tests that catch real bugs.

---

## Quick Reference

### Test Pyramid for MCP Servers

```
                    /\
                   /  \
                  / E2E \        <- Evaluation harness (Phase 4)
                 /--------\
                /          \
               / Integration \   <- Client(server) pattern
              /--------------\
             /                \
            /    Unit Tests    \ <- Formatting functions, models
           /--------------------\
```

### Key Patterns

| Pattern           | Use Case                             | Mock Level      |
| ----------------- | ------------------------------------ | --------------- |
| Unit tests        | Formatting helpers, model validation | None            |
| Integration tests | Tool execution via MCP protocol      | HTTP (httpx)    |
| E2E tests         | Full workflows with real API         | None (real API) |

---

## The Critical Bug: Context Access

### The Problem

FastMCP tools with lifespan-managed resources have a common pitfall that unit tests won't catch:

```python
# This looks correct but FAILS at runtime
@mcp.tool(name="my_tool")
async def my_tool(params: MyInput) -> str:
    ctx = mcp.get_context()  # Returns FastMCP Context, not AppContext!
    data = await ctx.my_client.fetch()  # AttributeError: 'Context' has no attribute 'my_client'
```

### The Solution

Accept `Context` as a parameter and access lifespan context explicitly:

```python
from mcp.server.fastmcp import Context

def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context."""
    return ctx.request_context.lifespan_context  # type: ignore[return-value]

@mcp.tool(name="my_tool")
async def my_tool(params: MyInput, ctx: Context) -> str:
    app_ctx = _get_app_context(ctx)
    data = await app_ctx.my_client.fetch()  # Works!
```

### Why Unit Tests Miss This

Unit tests that call tool functions directly with mock contexts will pass because you control what the mock returns. Only integration tests through the MCP protocol exercise the real context injection path.

---

## Testing Levels

### Level 1: Unit Tests (Formatting Functions)

Test pure functions directly without any MCP machinery:

```python
# tests/tools/test_search.py

from exa_mcp.tools.search import (
    _format_result_markdown,
    _format_results_markdown,
    _truncate_response,
)

class TestFormatResultMarkdown:
    """Tests for _format_result_markdown helper."""

    def test_basic_result(self):
        """Test formatting a basic result with title and URL."""
        result = {
            "title": "Test Article",
            "url": "https://example.com/test",
        }
        output = _format_result_markdown(result, 1)

        assert "### 1. Test Article" in output
        assert "**URL:** https://example.com/test" in output

    def test_text_truncation(self):
        """Test that long text is truncated at 500 chars."""
        long_text = "x" * 600
        result = {"title": "Test", "url": "https://example.com", "text": long_text}
        output = _format_result_markdown(result, 1)

        assert "..." in output
        assert len(output) < len(long_text) + 200
```

### Level 2: Integration Tests (Client(server) Pattern)

Test tools through the MCP protocol using `Client(server)`:

```python
# tests/tools/test_search.py

import pytest
from unittest.mock import AsyncMock, patch

class TestExaSearchTool:
    """Integration tests for exa_search tool via MCP protocol."""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        """Set required environment variable for tests."""
        monkeypatch.setenv("EXA_API_KEY", "test_api_key")

    @pytest.mark.asyncio
    async def test_search_basic_query(self, search_response, httpx_mock):
        """Test basic search returns formatted results."""
        from fastmcp import Client
        from exa_mcp.server import mcp

        # Mock the HTTP response (NOT the context)
        httpx_mock.add_response(json=search_response)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "exa_search",
                {"params": {"query": "python async programming"}}
            )

            text = result.content[0].text
            assert "Understanding Async Python" in text
```

### Why Mock at httpx Level

```
                 Test                MCP Server              External API
                  |                      |                        |
                  |--- call_tool() ----->|                        |
                  |                      |--- httpx.request() --->|
                  |                      |<-- Mock Response -------|
                  |<-- Tool Result ------|                        |
```

Mocking at httpx level means:

- Full tool logic executes (validation, formatting, error handling)
- Context injection works correctly (catches the bug above!)
- Only external HTTP calls are mocked

### Level 3: E2E Tests (Evaluation Harness)

Use the evaluation harness from Phase 4 for full end-to-end testing with real APIs.

---

## Test Structure

### Recommended Directory Layout

```
tests/
├── conftest.py              # Shared fixtures
├── helpers.py               # Test utilities (can't import conftest)
├── test_client.py           # API client unit tests
├── test_config.py           # Settings tests
├── tools/
│   ├── test_search.py       # Unit + integration tests
│   ├── test_similar.py
│   ├── test_contents.py
│   └── ...
└── integration/
    └── test_live_api.py     # @pytest.mark.integration (real API)
```

### conftest.py Fixtures

```python
# tests/conftest.py

import pytest

@pytest.fixture
def search_response():
    """Standard search response for mocking."""
    return {
        "results": [
            {
                "title": "Understanding Async Python",
                "url": "https://example.com/async",
                "score": 0.95,
                "publishedDate": "2024-01-15",
            },
            {
                "title": "FastAPI Best Practices",
                "url": "https://example.com/fastapi",
                "score": 0.89,
            },
        ],
        "autopromptString": "async python programming best practices",
    }

@pytest.fixture
def empty_response():
    """Empty response for no results scenarios."""
    return {"results": []}
```

### helpers.py Utilities

```python
# tests/helpers.py
# Note: conftest.py cannot be imported, so shared utilities go here

from unittest.mock import MagicMock
import httpx

def create_mock_response(
    data: dict,
    status_code: int = 200,
) -> MagicMock:
    """Create a mock httpx.Response for patching."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = data
    response.raise_for_status = MagicMock()

    if status_code >= 400:
        error = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response,
        )
        response.raise_for_status.side_effect = error

    return response
```

---

## Dependencies

### pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=0.25.0",
    "pytest-httpx>=0.35.0",    # For httpx_mock fixture
    "ruff>=0.14.8",
    "mypy>=1.0.0",
]

[dependency-groups]
dev = [
    "fastmcp>=2.13.2",         # For Client(server) pattern
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
]
```

---

## Common Pitfalls

### 1. Wrong Tool Argument Structure

FastMCP tools with Pydantic models expect arguments wrapped in `{"params": {...}}`:

```python
# Wrong - causes "Field required" error
result = await client.call_tool("exa_search", {"query": "test"})

# Correct
result = await client.call_tool("exa_search", {"params": {"query": "test"}})
```

### 2. Missing Environment Variables

Tools may fail during lifespan setup if required env vars are missing:

```python
@pytest.fixture(autouse=True)
def set_env(self, monkeypatch):
    """Set required environment variables for all tests in this class."""
    monkeypatch.setenv("MY_API_KEY", "test_key")
```

### 3. Mocking at Wrong Level

```python
# Wrong - mocks context, misses the real bug
with patch.object(mcp, 'get_context', return_value=mock_ctx):
    result = await exa_search(params)

# Correct - mocks HTTP, exercises full code path
httpx_mock.add_response(json=api_response)
async with Client(mcp) as client:
    result = await client.call_tool("exa_search", {"params": {...}})
```

### 4. Using httpx_mock with patch

If `httpx_mock` fixture doesn't work with your lifespan client, fall back to patching:

```python
from unittest.mock import AsyncMock, patch
from tests.helpers import create_mock_response

async def test_with_patch(self, search_response):
    mock_resp = create_mock_response(search_response)

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.request.return_value = mock_resp
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClient.return_value = mock_instance

        async with Client(mcp) as client:
            result = await client.call_tool(...)
```

---

## Quality Checklist

### Unit Tests

- [ ] All formatting functions have direct tests
- [ ] Edge cases covered (empty results, truncation, missing fields)
- [ ] Pydantic model validation tested

### Integration Tests

- [ ] Each tool tested via `Client(server)` pattern
- [ ] Success scenarios covered
- [ ] Error scenarios return user-friendly messages
- [ ] JSON and Markdown response formats tested

### Test Infrastructure

- [ ] `pytest-httpx` or patch helpers configured
- [ ] `fastmcp` in dev dependencies for `Client`
- [ ] Environment variables set in fixtures
- [ ] `asyncio_mode = "auto"` in pytest config

### Coverage Targets

- Unit tests (formatting): 95%+
- Integration tests (tools): 80%+
- Models (Pydantic): 95%+

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/tools/test_search.py

# Run only unit tests (fast)
uv run pytest tests/tools/ -k "not Tool"

# Run only integration tests
uv run pytest tests/tools/ -k "Tool"

# Skip real API tests
uv run pytest -m "not integration"

# Run with coverage
uv run pytest --cov=src/exa_mcp --cov-report=term-missing
```
