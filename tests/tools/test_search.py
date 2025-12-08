"""Tests for the exa_search and exa_code_search tools.

Following MCP testing best practices:
- Test formatting functions directly (unit tests)
- Test tools via Client(server) pattern (integration tests)
- Mock at httpx level for external API calls
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from exa_mcp.tools.search import (
    _format_code_results_markdown,
    _format_result_markdown,
    _format_results_markdown,
    _truncate_response,
)

# =============================================================================
# Unit Tests: Formatting Functions
# =============================================================================


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

    def test_result_with_all_fields(self):
        """Test formatting a result with all optional fields."""
        result = {
            "title": "Full Article",
            "url": "https://example.com/full",
            "publishedDate": "2024-01-15",
            "author": "Jane Doe",
            "score": 0.95,
            "highlights": ["Key point 1", "Key point 2"],
            "summary": "Article summary here.",
            "text": "Full article text content...",
        }
        output = _format_result_markdown(result, 1)

        assert "### 1. Full Article" in output
        assert "**Published:** 2024-01-15" in output
        assert "**Author:** Jane Doe" in output
        assert "**Relevance:** 0.95" in output
        assert "**Highlights:**" in output
        assert "> Key point 1" in output
        assert "**Summary:** Article summary here." in output
        assert "**Content Preview:**" in output

    def test_untitled_result(self):
        """Test formatting a result without title."""
        result = {"url": "https://example.com"}
        output = _format_result_markdown(result, 1)

        assert "### 1. Untitled" in output

    def test_text_truncation(self):
        """Test that long text is truncated at 500 chars."""
        long_text = "x" * 600
        result = {"title": "Test", "url": "https://example.com", "text": long_text}
        output = _format_result_markdown(result, 1)

        assert "..." in output
        assert len(output) < len(long_text) + 200


class TestFormatResultsMarkdown:
    """Tests for _format_results_markdown helper."""

    def test_empty_results(self):
        """Test formatting empty results."""
        data = {"results": []}
        output = _format_results_markdown(data, "test query")

        assert "No results found for: 'test query'" in output

    def test_multiple_results(self):
        """Test formatting multiple results."""
        data = {
            "results": [
                {"title": "Result 1", "url": "https://example.com/1"},
                {"title": "Result 2", "url": "https://example.com/2"},
            ]
        }
        output = _format_results_markdown(data, "test query")

        assert "# Search Results for: 'test query'" in output
        assert "Found **2** results" in output
        assert "### 1. Result 1" in output
        assert "### 2. Result 2" in output

    def test_autoprompt_string(self):
        """Test that autoprompt string is displayed."""
        data = {
            "results": [{"title": "Test", "url": "https://example.com"}],
            "autopromptString": "optimized query here",
        }
        output = _format_results_markdown(data, "original query")

        assert 'Query optimized to: "optimized query here"' in output


class TestFormatCodeResultsMarkdown:
    """Tests for _format_code_results_markdown helper."""

    def test_empty_code_results(self):
        """Test formatting empty code results."""
        data = {"results": []}
        output = _format_code_results_markdown(data, "react hooks")

        assert "No code results found for: 'react hooks'" in output

    def test_code_results_with_highlights(self):
        """Test formatting code results with code snippets."""
        data = {
            "results": [
                {
                    "title": "React useState Example",
                    "url": "https://github.com/example/repo",
                    "score": 0.95,
                    "highlights": ["const [count, setCount] = useState(0);"],
                    "text": "Example of useState hook usage...",
                },
            ]
        }
        output = _format_code_results_markdown(data, "react useState")

        assert "# Code Search Results: 'react useState'" in output
        assert "Found **1** code-related results" in output
        assert "**Code Snippets:**" in output
        assert "```" in output  # Code block
        assert "useState(0)" in output


class TestTruncateResponse:
    """Tests for _truncate_response helper."""

    def test_short_response_unchanged(self):
        """Test that short responses are not truncated."""
        text = "Short response"
        output = _truncate_response(text)
        assert output == text

    def test_long_response_truncation(self):
        """Test that long responses are truncated."""
        long_text = "x" * 30000
        output = _truncate_response(long_text)

        assert len(output) < len(long_text)
        assert "[Response truncated" in output
        assert "30000 characters" in output


# =============================================================================
# Integration Tests: Tool Functions via MCP Protocol
# =============================================================================


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

        # Mock the Exa API response
        httpx_mock.add_response(json=search_response)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "exa_search", {"params": {"query": "python async programming"}}
            )

            # Verify response content
            text = result.content[0].text
            assert "Understanding Async Python" in text
            assert "FastAPI Best Practices" in text

    @pytest.mark.asyncio
    async def test_search_json_format(self, search_response):
        """Test search with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(search_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_search",
                    {"params": {"query": "test", "response_format": "json"}},
                )

                # Verify JSON response
                text = result.content[0].text
                data = json.loads(text)
                assert "results" in data
                assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_search_empty_results(self, empty_response):
        """Test search with no results."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(empty_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_search", {"params": {"query": "nonexistent topic xyz"}}
                )

                text = result.content[0].text
                assert "No results found" in text


class TestExaCodeSearchTool:
    """Integration tests for exa_code_search tool."""

    @pytest.mark.asyncio
    async def test_code_search_basic(self, search_response):
        """Test code search returns formatted results."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(search_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_code_search", {"params": {"query": "React useState examples"}}
                )

                text = result.content[0].text
                assert "Code Search Results" in text or "results" in text.lower()
