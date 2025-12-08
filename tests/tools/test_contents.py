"""Tests for the exa_get_contents tool.

Following MCP testing best practices:
- Test formatting functions directly (unit tests)
- Test tools via Client(server) pattern (integration tests)
- Mock at httpx level for external API calls
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from exa_mcp.tools.contents import (
    _format_content_markdown,
    _format_contents_markdown,
    _truncate_response,
)

# =============================================================================
# Unit Tests: Formatting Functions
# =============================================================================


class TestFormatContentMarkdown:
    """Tests for _format_content_markdown helper."""

    def test_basic_content(self):
        """Test formatting basic content with title and URL."""
        result = {
            "title": "Article Title",
            "url": "https://example.com/article",
        }
        output = _format_content_markdown(result, 1)

        assert "## 1. Article Title" in output
        assert "**URL:** https://example.com/article" in output

    def test_content_with_all_fields(self):
        """Test formatting content with all optional fields."""
        result = {
            "title": "Full Article",
            "url": "https://example.com/full",
            "publishedDate": "2024-03-15",
            "author": "Content Author",
            "highlights": ["Key insight 1", "Key insight 2"],
            "summary": "Article summary text.",
            "text": "Full article content goes here...",
        }
        output = _format_content_markdown(result, 1)

        assert "## 1. Full Article" in output
        assert "**Published:** 2024-03-15" in output
        assert "**Author:** Content Author" in output
        assert "### Highlights" in output
        assert "> Key insight 1" in output
        assert "> Key insight 2" in output
        assert "### Summary" in output
        assert "Article summary text." in output
        assert "### Full Content" in output
        assert "Full article content goes here..." in output

    def test_untitled_content(self):
        """Test formatting content without title."""
        result = {"url": "https://example.com"}
        output = _format_content_markdown(result, 1)

        assert "## 1. Untitled" in output


class TestFormatContentsMarkdown:
    """Tests for _format_contents_markdown helper."""

    def test_empty_results(self):
        """Test formatting empty results."""
        data = {"results": []}
        output = _format_contents_markdown(data)

        assert "No content extracted from the provided URLs." in output

    def test_single_result(self):
        """Test formatting a single content result."""
        data = {
            "results": [
                {
                    "title": "Extracted Content",
                    "url": "https://example.com/page",
                    "text": "Page content here...",
                }
            ]
        }
        output = _format_contents_markdown(data)

        assert "# Extracted Content" in output
        assert "Successfully extracted content from **1** URLs" in output
        assert "## 1. Extracted Content" in output

    def test_multiple_results(self):
        """Test formatting multiple content results."""
        data = {
            "results": [
                {"title": "Page 1", "url": "https://example.com/1"},
                {"title": "Page 2", "url": "https://example.com/2"},
                {"title": "Page 3", "url": "https://example.com/3"},
            ]
        }
        output = _format_contents_markdown(data)

        assert "Successfully extracted content from **3** URLs" in output
        assert "## 1. Page 1" in output
        assert "## 2. Page 2" in output
        assert "## 3. Page 3" in output
        # Check separator between results
        assert "---" in output


class TestTruncateResponse:
    """Tests for _truncate_response helper."""

    def test_short_response(self):
        """Test that short responses are not truncated."""
        text = "Short content"
        output = _truncate_response(text)
        assert output == text

    def test_long_response_truncation(self):
        """Test that long responses are truncated."""
        long_text = "x" * 30000
        output = _truncate_response(long_text)

        assert len(output) < len(long_text)
        assert "[Response truncated" in output
        assert "fewer URLs" in output


# =============================================================================
# Integration Tests: Tool Functions via MCP Protocol
# =============================================================================


class TestExaGetContentsTool:
    """Integration tests for exa_get_contents tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_get_contents_basic(self, contents_response):
        """Test basic get contents returns formatted results."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(contents_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_get_contents", {"params": {"urls": ["https://example.com/article"]}}
                )

                text = result.content[0].text
                assert "Full Article Content" in text
                assert "John Writer" in text

    @pytest.mark.asyncio
    async def test_get_contents_json_format(self, contents_response):
        """Test get contents with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(contents_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_get_contents",
                    {
                        "params": {
                            "urls": ["https://example.com/article"],
                            "response_format": "json",
                        }
                    },
                )

                text = result.content[0].text
                data = json.loads(text)
                assert "results" in data
                assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_contents_multiple_urls(self):
        """Test get contents with multiple URLs."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        multi_response = {
            "results": [
                {"title": "Article 1", "url": "https://example.com/1", "text": "Content 1"},
                {"title": "Article 2", "url": "https://example.com/2", "text": "Content 2"},
            ]
        }
        mock_resp = create_mock_response(multi_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_get_contents",
                    {"params": {"urls": ["https://example.com/1", "https://example.com/2"]}},
                )

                text = result.content[0].text
                assert "Article 1" in text
                assert "Article 2" in text
                assert "Successfully extracted content from **2** URLs" in text

    @pytest.mark.asyncio
    async def test_get_contents_empty_results(self, empty_response):
        """Test get contents with no results."""
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
                    "exa_get_contents", {"params": {"urls": ["https://invalid-url.com"]}}
                )

                text = result.content[0].text
                assert "No content extracted" in text
