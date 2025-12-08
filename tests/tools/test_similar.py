"""Tests for the exa_find_similar tool.

Following MCP testing best practices:
- Test formatting functions directly (unit tests)
- Test tools via Client(server) pattern (integration tests)
- Mock at httpx level for external API calls
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from exa_mcp.tools.similar import (
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
        """Test formatting a basic result."""
        result = {
            "title": "Similar Article",
            "url": "https://example.com/similar",
        }
        output = _format_result_markdown(result, 1)

        assert "### 1. Similar Article" in output
        assert "**URL:** https://example.com/similar" in output

    def test_result_with_similarity_score(self):
        """Test formatting a result with similarity score."""
        result = {
            "title": "Related Content",
            "url": "https://example.com/related",
            "score": 0.92,
        }
        output = _format_result_markdown(result, 1)

        assert "**Similarity:** 0.92" in output

    def test_result_with_all_fields(self):
        """Test formatting a result with all optional fields."""
        result = {
            "title": "Full Result",
            "url": "https://example.com/full",
            "publishedDate": "2024-02-01",
            "author": "Test Author",
            "score": 0.88,
            "highlights": ["Highlight 1", "Highlight 2", "Highlight 3", "Highlight 4"],
            "summary": "Test summary.",
            "text": "Full text content here...",
        }
        output = _format_result_markdown(result, 1)

        assert "**Published:** 2024-02-01" in output
        assert "**Author:** Test Author" in output
        assert "**Similarity:** 0.88" in output
        assert "**Highlights:**" in output
        # Should only show first 3 highlights
        assert "> Highlight 1" in output
        assert "> Highlight 3" in output
        assert "**Summary:** Test summary." in output
        assert "**Content Preview:**" in output

    def test_text_truncation(self):
        """Test that long text is truncated at 500 chars."""
        long_text = "x" * 600
        result = {"title": "Test", "url": "https://example.com", "text": long_text}
        output = _format_result_markdown(result, 1)

        assert "..." in output


class TestFormatResultsMarkdown:
    """Tests for _format_results_markdown helper."""

    def test_empty_results(self):
        """Test formatting empty results."""
        data = {"results": []}
        output = _format_results_markdown(data, "https://example.com/source")

        assert "No similar pages found for: https://example.com/source" in output

    def test_multiple_results(self):
        """Test formatting multiple results."""
        data = {
            "results": [
                {"title": "Similar 1", "url": "https://similar.com/1"},
                {"title": "Similar 2", "url": "https://similar.com/2"},
                {"title": "Similar 3", "url": "https://similar.com/3"},
            ]
        }
        output = _format_results_markdown(data, "https://source.com/page")

        assert "# Pages Similar to: https://source.com/page" in output
        assert "Found **3** similar pages" in output
        assert "### 1. Similar 1" in output
        assert "### 2. Similar 2" in output
        assert "### 3. Similar 3" in output


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


# =============================================================================
# Integration Tests: Tool Functions via MCP Protocol
# =============================================================================


class TestExaFindSimilarTool:
    """Integration tests for exa_find_similar tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_find_similar_basic(self, similar_response):
        """Test basic find similar returns formatted results."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(similar_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_find_similar", {"params": {"url": "https://example.com/article"}}
                )

                text = result.content[0].text
                assert "Related Article 1" in text
                assert "Related Article 2" in text

    @pytest.mark.asyncio
    async def test_find_similar_json_format(self, similar_response):
        """Test find similar with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(similar_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_find_similar",
                    {
                        "params": {
                            "url": "https://example.com/article",
                            "response_format": "json",
                        }
                    },
                )

                text = result.content[0].text
                data = json.loads(text)
                assert "results" in data
                assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_find_similar_empty_results(self, empty_response):
        """Test find similar with no results."""
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
                    "exa_find_similar",
                    {"params": {"url": "https://obscure-site.com/page"}},
                )

                text = result.content[0].text
                assert "No similar pages found" in text
