"""Tests for the exa_answer tool.

Following MCP testing best practices:
- Test formatting functions directly (unit tests)
- Test tools via Client(server) pattern (integration tests)
- Mock at httpx level for external API calls
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from exa_mcp.tools.answer import (
    _format_answer_markdown,
    _format_citation_markdown,
    _truncate_response,
)

# =============================================================================
# Unit Tests: Formatting Functions
# =============================================================================


class TestFormatCitationMarkdown:
    """Tests for _format_citation_markdown helper."""

    def test_basic_citation(self):
        """Test formatting a basic citation."""
        citation = {
            "title": "Python Guide",
            "url": "https://docs.python.org",
        }
        output = _format_citation_markdown(citation, 1)

        assert "[1]" in output
        assert "[Python Guide]" in output
        assert "(https://docs.python.org)" in output

    def test_citation_with_date(self):
        """Test formatting citation with published date."""
        citation = {
            "title": "API Reference",
            "url": "https://api.example.com",
            "publishedDate": "2024-01-15",
        }
        output = _format_citation_markdown(citation, 2)

        assert "[2]" in output
        assert "(2024-01-15)" in output

    def test_citation_with_text(self):
        """Test formatting citation with excerpt text."""
        citation = {
            "title": "Test Article",
            "url": "https://example.com",
            "text": "This is an excerpt from the article explaining the topic.",
        }
        output = _format_citation_markdown(citation, 1)

        assert ">" in output  # Quote marker
        assert "excerpt from the article" in output

    def test_citation_text_truncation(self):
        """Test that long citation text is truncated."""
        long_text = "x" * 500
        citation = {
            "title": "Test",
            "url": "https://example.com",
            "text": long_text,
        }
        output = _format_citation_markdown(citation, 1)

        assert "..." in output

    def test_untitled_citation(self):
        """Test formatting citation without title."""
        citation = {"url": "https://example.com"}
        output = _format_citation_markdown(citation, 1)

        assert "[Untitled]" in output


class TestFormatAnswerMarkdown:
    """Tests for _format_answer_markdown helper."""

    def test_answer_only(self):
        """Test formatting answer without citations."""
        data = {
            "answer": "The answer is 42.",
            "citations": [],
        }
        output = _format_answer_markdown(data)

        assert "# Answer" in output
        assert "The answer is 42." in output
        assert "## Sources" not in output

    def test_answer_with_citations(self):
        """Test formatting answer with citations."""
        data = {
            "answer": "Python is a programming language.",
            "citations": [
                {"title": "Python Docs", "url": "https://python.org"},
                {"title": "Wiki", "url": "https://wikipedia.org"},
            ],
        }
        output = _format_answer_markdown(data)

        assert "# Answer" in output
        assert "Python is a programming language." in output
        assert "## Sources" in output
        assert "[1]" in output
        assert "[2]" in output

    def test_no_answer(self):
        """Test formatting when no answer generated."""
        data = {}
        output = _format_answer_markdown(data)

        assert "No answer generated." in output


class TestTruncateResponse:
    """Tests for _truncate_response helper."""

    def test_short_response_unchanged(self):
        """Test that short responses are not truncated."""
        text = "Short answer"
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


class TestExaAnswerTool:
    """Integration tests for exa_answer tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_answer_basic(self, answer_response):
        """Test basic answer returns formatted results."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(answer_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_answer", {"params": {"query": "What is async programming in Python?"}}
                )

                text = result.content[0].text
                assert "async/await syntax" in text
                assert "## Sources" in text or "Python Async Guide" in text

    @pytest.mark.asyncio
    async def test_answer_json_format(self, answer_response):
        """Test answer with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(answer_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_answer",
                    {
                        "params": {
                            "query": "What is async programming?",
                            "response_format": "json",
                        }
                    },
                )

                text = result.content[0].text
                data = json.loads(text)
                assert "answer" in data
                assert "citations" in data

    @pytest.mark.asyncio
    async def test_answer_with_no_citations(self):
        """Test answer response with no citations."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        no_citations_response = {
            "answer": "The answer is simple.",
            "citations": [],
        }
        mock_resp = create_mock_response(no_citations_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_answer", {"params": {"query": "Simple question"}}
                )

                text = result.content[0].text
                assert "The answer is simple." in text
