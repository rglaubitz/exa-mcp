"""Research tools implementation for the Exa MCP server.

This module provides tools for creating and managing async research tasks.
"""

import json
from typing import Any

from fastmcp import Context

from ..constants import CHARACTER_LIMIT, ResponseFormat
from ..exceptions import format_error_for_llm
from ..models.research import CreateResearchInput, GetResearchInput, ListResearchInput
from ..server import AppContext, mcp


def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context."""
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _format_task_markdown(task: dict[str, Any]) -> str:
    """Format a single research task as markdown.

    Args:
        task: Research task data.

    Returns:
        Formatted markdown string.
    """
    status = task.get("status", "unknown")
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
    }.get(status, "❓")

    research_id = task.get("researchId", task.get("id", "unknown"))
    lines = [
        f"### {status_emoji} Task: {research_id}",
        f"**Status:** {status}",
        f"**Instructions:** {task.get('instructions', 'N/A')}",
        f"**Model:** {task.get('model', 'N/A')}",
    ]

    if task.get("createdAt") or task.get("created_at"):
        created = task.get("createdAt") or task.get("created_at")
        lines.append(f"**Created:** {created}")

    if task.get("completedAt") or task.get("completed_at"):
        completed = task.get("completedAt") or task.get("completed_at")
        lines.append(f"**Completed:** {completed}")

    if task.get("error"):
        lines.append(f"**Error:** {task['error']}")

    return "\n".join(lines)


def _format_result_markdown(data: dict[str, Any]) -> str:
    """Format research results as markdown.

    Args:
        data: API response data.

    Returns:
        Formatted markdown string.
    """
    research_id = data.get("researchId", data.get("id", "unknown"))
    status = data.get("status", "unknown")
    instructions = data.get("instructions", "N/A")
    result = data.get("result", data.get("output", ""))

    lines = [
        f"# Research Results: {research_id}",
        "",
        f"**Status:** {status}",
        f"**Instructions:** {instructions}",
        "",
    ]

    if result:
        lines.append("## Report")
        lines.append("")
        # Result might be a string or an object (for structured output)
        if isinstance(result, dict):
            lines.append(json.dumps(result, indent=2))
        else:
            lines.append(str(result))
    elif status == "running":
        lines.append("*Research is still in progress. Check back later.*")
    elif status == "pending":
        lines.append("*Research task is queued and will start soon.*")
    elif data.get("error"):
        lines.append(f"**Error:** {data['error']}")

    return "\n".join(lines)


def _format_task_list_markdown(data: dict[str, Any]) -> str:
    """Format task list as markdown.

    Args:
        data: API response data with tasks list.

    Returns:
        Formatted markdown string.
    """
    tasks = data.get("tasks", data.get("data", []))

    if not tasks:
        return "No research tasks found."

    lines = ["# Research Tasks", "", f"Found **{len(tasks)}** tasks", ""]

    for task in tasks:
        lines.append(_format_task_markdown(task))
        lines.append("")

    return "\n".join(lines)


def _truncate_response(text: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(text) <= CHARACTER_LIMIT:
        return text

    truncated = text[: CHARACTER_LIMIT - 200]
    truncated += (
        f"\n\n---\n[Response truncated from {len(text)} characters. "
        "Research results may be large; consider using filters.]"
    )
    return truncated


@mcp.tool(
    name="exa_research_start",
    annotations={
        "title": "Start Research Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def exa_research_start(params: CreateResearchInput, ctx: Context) -> str:
    """Start an async deep research task on a topic.

    This creates a long-running research task that performs comprehensive
    research on your query. The task runs asynchronously - use
    exa_research_check to poll for results.

    Use cases:
    - Deep research on complex topics
    - Comprehensive market analysis
    - Literature reviews
    - Multi-source fact gathering

    Args:
        params: CreateResearchInput containing:
            - instructions (str): Natural language instructions for the research (required)
            - model (str): 'exa-research' (default) or 'exa-research-pro' (higher quality)
        ctx: FastMCP request context (injected automatically).

    Returns:
        Task ID and initial status. Use this ID to check results.

    Examples:
        Start research:
            {"instructions": "What are the latest breakthroughs in fusion energy?"}

        Detailed research:
            {"instructions": "Compare cloud providers for ML workloads",
             "model": "exa-research-pro"}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Create research task
        # Handle both enum objects (with .value) and raw strings from HTTP transport
        model = getattr(params.model, "value", params.model) if params.model else "exa-research"
        data = await app_ctx.exa_client.research_create(
            instructions=params.instructions,
            model=model,
        )

        # Format response with research ID prominently
        research_id = data.get("researchId", data.get("id", "unknown"))
        status = data.get("status", "pending")

        response = (
            f"# Research Task Created\n\n"
            f"**Research ID:** `{research_id}`\n"
            f"**Status:** {status}\n"
            f"**Model:** {model}\n"
            f"**Instructions:** {params.instructions}\n\n"
            f"Use `exa_research_check` with research_id='{research_id}' to get results.\n"
            f"Note: Research typically takes 20-90 seconds to complete."
        )

        return response

    except Exception as e:
        return format_error_for_llm(e)


@mcp.tool(
    name="exa_research_check",
    annotations={
        "title": "Check Research Task",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_research_check(params: GetResearchInput, ctx: Context) -> str:
    """Check the status and get results of a research task.

    Poll this endpoint to get research results after starting a task
    with exa_research_start.

    Args:
        params: GetResearchInput containing:
            - research_id (str): The research task ID (required)
            - response_format (str): 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Task status and results (if completed).

    Examples:
        Check task:
            {"research_id": "task_abc123"}

        Get JSON:
            {"research_id": "task_abc123", "response_format": "json"}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Get research task status/results
        data = await app_ctx.exa_client.research_get(params.research_id)

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_result_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)


@mcp.tool(
    name="exa_research_list",
    annotations={
        "title": "List Research Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_research_list(params: ListResearchInput, ctx: Context) -> str:
    """List all research tasks.

    Get an overview of all your research tasks and their statuses.

    Args:
        params: ListResearchInput containing:
            - limit (int): Maximum tasks to return (1-100, default 10)
            - status (str): Filter by status (pending/running/completed/failed)
            - response_format (str): 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        List of research tasks with their statuses.

    Examples:
        List all:
            {}

        Filter completed:
            {"status": "completed", "limit": 20}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # List research tasks
        data = await app_ctx.exa_client.research_list()

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_task_list_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
