"""Pytest configuration and fixtures for Exa MCP tests.

Following MCP testing best practices:
- Use in-memory Client(server) pattern
- Mock at httpx level, not mcp.get_context()
- Don't put clients in fixtures (event loop issues)
- Keep tests fast (< 1 second for unit tests)
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

# =============================================================================
# Mock Response Factory
# =============================================================================


def create_mock_response(
    data: dict,
    status_code: int = 200,
) -> MagicMock:
    """Create a mock httpx.Response.

    Args:
        data: JSON data to return.
        status_code: HTTP status code.

    Returns:
        Mock response that behaves like httpx.Response.
    """
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


def create_mock_http_client(default_response: dict | None = None) -> AsyncMock:
    """Create a mock httpx.AsyncClient.

    Args:
        default_response: Default response data for requests.

    Returns:
        Mock async client with request method.
    """
    client = AsyncMock(spec=httpx.AsyncClient)

    if default_response:
        mock_resp = create_mock_response(default_response)
        client.request.return_value = mock_resp

    return client


# =============================================================================
# Sample API Response Fixtures
# =============================================================================


@pytest.fixture
def search_response():
    """Sample search API response."""
    return {
        "results": [
            {
                "title": "Understanding Async Python",
                "url": "https://example.com/async-python",
                "publishedDate": "2024-01-15",
                "author": "Jane Developer",
                "score": 0.95,
                "text": "A comprehensive guide to async programming in Python...",
                "highlights": [
                    "async/await syntax makes concurrent code readable",
                    "asyncio is the standard library for async I/O",
                ],
                "summary": "This article covers async Python fundamentals.",
            },
            {
                "title": "FastAPI Best Practices",
                "url": "https://example.com/fastapi",
                "publishedDate": "2024-02-20",
                "score": 0.88,
                "text": "FastAPI is a modern web framework...",
            },
        ],
        "autopromptString": "best practices async python programming",
    }


@pytest.fixture
def similar_response():
    """Sample find_similar API response."""
    return {
        "results": [
            {
                "title": "Related Article 1",
                "url": "https://similar.com/article1",
                "publishedDate": "2024-03-01",
                "score": 0.92,
                "text": "Similar content here...",
            },
            {
                "title": "Related Article 2",
                "url": "https://similar.com/article2",
                "score": 0.85,
            },
        ]
    }


@pytest.fixture
def contents_response():
    """Sample get_contents API response."""
    return {
        "results": [
            {
                "title": "Full Article Content",
                "url": "https://example.com/article",
                "publishedDate": "2024-01-10",
                "author": "John Writer",
                "text": "This is the full article content extracted from the page...",
                "highlights": ["Key point 1", "Key point 2"],
                "summary": "Article summary here.",
            }
        ]
    }


@pytest.fixture
def answer_response():
    """Sample answer API response."""
    return {
        "answer": "Python async programming uses the async/await syntax to handle concurrent operations efficiently.",
        "citations": [
            {
                "title": "Python Async Guide",
                "url": "https://docs.python.org/3/library/asyncio.html",
                "publishedDate": "2024-01-01",
                "text": "asyncio is a library to write concurrent code...",
            },
            {
                "title": "Real Python Async Tutorial",
                "url": "https://realpython.com/async-io-python/",
                "text": "Async IO is a concurrent programming design...",
            },
        ],
    }


@pytest.fixture
def research_create_response():
    """Sample research task creation response."""
    return {
        "researchId": "task_abc123",
        "status": "pending",
        "instructions": "Latest breakthroughs in fusion energy",
        "model": "exa-research",
        "createdAt": "2024-12-08T10:00:00Z",
    }


@pytest.fixture
def research_completed_response():
    """Sample completed research task response."""
    return {
        "researchId": "task_abc123",
        "status": "completed",
        "instructions": "Latest breakthroughs in fusion energy",
        "model": "exa-research",
        "createdAt": "2024-12-08T10:00:00Z",
        "completedAt": "2024-12-08T10:05:00Z",
        "result": """# Fusion Energy Breakthroughs 2024

## Key Developments
1. NIF achieved ignition milestone
2. Private companies advancing tokamak designs
3. New superconducting magnet technologies

## Sources
- Nature Physics papers
- DOE announcements
""",
    }


@pytest.fixture
def research_list_response():
    """Sample research task list response."""
    return {
        "tasks": [
            {
                "researchId": "task_abc123",
                "status": "completed",
                "instructions": "Fusion energy breakthroughs",
                "model": "exa-research",
                "createdAt": "2024-12-08T10:00:00Z",
            },
            {
                "researchId": "task_def456",
                "status": "running",
                "instructions": "Quantum computing advances",
                "model": "exa-research",
                "createdAt": "2024-12-08T11:00:00Z",
            },
            {
                "researchId": "task_ghi789",
                "status": "pending",
                "instructions": "AI safety research",
                "model": "exa-research-pro",
                "createdAt": "2024-12-08T12:00:00Z",
            },
        ]
    }


@pytest.fixture
def empty_response():
    """Empty results response."""
    return {"results": []}


# =============================================================================
# Error Response Fixtures
# =============================================================================


@pytest.fixture
def rate_limit_error():
    """Rate limit error response."""
    return create_mock_response(
        {"error": "Rate limit exceeded"},
        status_code=429,
    )


@pytest.fixture
def auth_error():
    """Authentication error response."""
    return create_mock_response(
        {"error": "Invalid API key"},
        status_code=401,
    )


@pytest.fixture
def validation_error():
    """Validation error response."""
    return create_mock_response(
        {"error": "Query cannot be empty"},
        status_code=400,
    )
