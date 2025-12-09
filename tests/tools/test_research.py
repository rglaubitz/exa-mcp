"""Tests for the exa_research tools.

Following MCP testing best practices:
- Test formatting functions directly (unit tests)
- Test tools via Client(server) pattern (integration tests)
- Mock at httpx level for external API calls
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from exa_mcp.tools.research import (
    _format_result_markdown,
    _format_task_list_markdown,
    _format_task_markdown,
    _truncate_response,
)

# =============================================================================
# Unit Tests: Formatting Functions
# =============================================================================


class TestFormatTaskMarkdown:
    """Tests for _format_task_markdown helper."""

    def test_pending_task(self):
        """Test formatting a pending task."""
        task = {
            "researchId": "task_123",
            "status": "pending",
            "instructions": "Test research instructions",
            "model": "exa-research",
            "createdAt": "2024-12-08T10:00:00Z",
        }
        output = _format_task_markdown(task)

        assert "task_123" in output
        assert "pending" in output
        assert "Test research instructions" in output
        assert "2024-12-08T10:00:00Z" in output

    def test_running_task(self):
        """Test formatting a running task."""
        task = {
            "researchId": "task_456",
            "status": "running",
            "instructions": "Running research",
            "model": "exa-research",
        }
        output = _format_task_markdown(task)

        assert "running" in output

    def test_completed_task(self):
        """Test formatting a completed task."""
        task = {
            "researchId": "task_789",
            "status": "completed",
            "instructions": "Completed research",
            "model": "exa-research",
            "createdAt": "2024-12-08T10:00:00Z",
            "completedAt": "2024-12-08T10:05:00Z",
        }
        output = _format_task_markdown(task)

        assert "completed" in output
        assert "10:05:00Z" in output

    def test_failed_task(self):
        """Test formatting a failed task with error."""
        task = {
            "researchId": "task_err",
            "status": "failed",
            "instructions": "Failed research",
            "model": "exa-research",
            "error": "API rate limit exceeded",
        }
        output = _format_task_markdown(task)

        assert "failed" in output
        assert "API rate limit exceeded" in output


class TestFormatResultMarkdown:
    """Tests for _format_result_markdown helper."""

    def test_completed_result(self):
        """Test formatting completed research results."""
        data = {
            "researchId": "task_abc123",
            "status": "completed",
            "instructions": "Fusion energy research",
            "model": "exa-research",
            "result": "# Fusion Energy Report\n\nKey findings here...",
        }
        output = _format_result_markdown(data)

        assert "Research Results: task_abc123" in output
        assert "completed" in output
        assert "## Report" in output
        assert "Fusion Energy Report" in output

    def test_running_result(self):
        """Test formatting running task (no results yet)."""
        data = {
            "researchId": "task_xyz",
            "status": "running",
            "instructions": "Ongoing research",
            "model": "exa-research",
        }
        output = _format_result_markdown(data)

        assert "running" in output
        assert "still in progress" in output

    def test_pending_result(self):
        """Test formatting pending task."""
        data = {
            "researchId": "task_queue",
            "status": "pending",
            "instructions": "Queued research",
            "model": "exa-research",
        }
        output = _format_result_markdown(data)

        assert "pending" in output
        assert "queued" in output


class TestFormatTaskListMarkdown:
    """Tests for _format_task_list_markdown helper."""

    def test_empty_task_list(self):
        """Test formatting empty task list."""
        data = {"tasks": []}
        output = _format_task_list_markdown(data)

        assert "No research tasks found" in output

    def test_multiple_tasks(self):
        """Test formatting multiple tasks."""
        data = {
            "tasks": [
                {
                    "researchId": "task_1",
                    "status": "completed",
                    "instructions": "Query 1",
                    "model": "exa-research",
                },
                {
                    "researchId": "task_2",
                    "status": "running",
                    "instructions": "Query 2",
                    "model": "exa-research",
                },
                {
                    "researchId": "task_3",
                    "status": "pending",
                    "instructions": "Query 3",
                    "model": "exa-research-pro",
                },
            ]
        }
        output = _format_task_list_markdown(data)

        assert "# Research Tasks" in output
        assert "Found **3** tasks" in output
        assert "task_1" in output
        assert "task_2" in output
        assert "task_3" in output


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


class TestExaResearchStartTool:
    """Integration tests for exa_research_start tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_research_start_basic(self, research_create_response):
        """Test basic research task creation."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(research_create_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_research_start",
                    {"params": {"instructions": "Latest breakthroughs in fusion energy"}},
                )

                text = result.content[0].text
                assert "Research Task Created" in text
                assert "task_abc123" in text
                assert "exa_research_check" in text


class TestExaResearchCheckTool:
    """Integration tests for exa_research_check tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_research_check_completed(self, research_completed_response):
        """Test checking a completed research task."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(research_completed_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_research_check", {"params": {"research_id": "task_abc123"}}
                )

                text = result.content[0].text
                assert "Research Results" in text
                assert "completed" in text
                assert "Fusion Energy Breakthroughs" in text

    @pytest.mark.asyncio
    async def test_research_check_json_format(self, research_completed_response):
        """Test research check with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(research_completed_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_research_check",
                    {"params": {"research_id": "task_abc123", "response_format": "json"}},
                )

                text = result.content[0].text
                data = json.loads(text)
                assert data["researchId"] == "task_abc123"
                assert data["status"] == "completed"


class TestExaResearchListTool:
    """Integration tests for exa_research_list tool via MCP protocol."""

    @pytest.mark.asyncio
    async def test_research_list_basic(self, research_list_response):
        """Test listing research tasks."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(research_list_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool("exa_research_list", {"params": {}})

                text = result.content[0].text
                assert "Research Tasks" in text
                assert "3" in text  # 3 tasks in fixture
                assert "Fusion energy" in text or "task_abc123" in text

    @pytest.mark.asyncio
    async def test_research_list_json_format(self, research_list_response):
        """Test research list with JSON response format."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        mock_resp = create_mock_response(research_list_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "exa_research_list", {"params": {"response_format": "json"}}
                )

                text = result.content[0].text
                data = json.loads(text)
                assert "tasks" in data
                assert len(data["tasks"]) == 3

    @pytest.mark.asyncio
    async def test_research_list_empty(self):
        """Test listing when no research tasks exist."""
        from fastmcp import Client

        from exa_mcp.server import mcp
        from tests.helpers import create_mock_response

        empty_list = {"tasks": []}
        mock_resp = create_mock_response(empty_list)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            async with Client(mcp) as client:
                result = await client.call_tool("exa_research_list", {"params": {}})

                text = result.content[0].text
                assert "No research tasks found" in text
