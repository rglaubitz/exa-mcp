"""Get contents tool implementation for the Exa MCP server.

This module provides the exa_get_contents tool for extracting content from URLs.
"""

import json
from typing import Any

from fastmcp import Context

from ..constants import CHARACTER_LIMIT
from ..exceptions import format_error_for_llm
from ..models.common import ContentOptions
from ..server import AppContext, mcp


def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context."""
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _format_content_markdown(result: dict[str, Any], index: int) -> str:
    """Format a single content result as markdown.

    Args:
        result: Content result from Exa API.
        index: Result index (1-based).

    Returns:
        Formatted markdown string.
    """
    lines = [f"## {index}. {result.get('title', 'Untitled')}"]
    lines.append(f"**URL:** {result.get('url', 'N/A')}")

    if result.get("publishedDate"):
        lines.append(f"**Published:** {result['publishedDate']}")

    if result.get("author"):
        lines.append(f"**Author:** {result['author']}")

    # Add highlights if available
    if result.get("highlights"):
        lines.append("\n### Highlights")
        for highlight in result["highlights"]:
            lines.append(f"> {highlight}")
        lines.append("")

    # Add summary if available
    if result.get("summary"):
        lines.append(f"### Summary\n{result['summary']}")
        lines.append("")

    # Add full text if available
    if result.get("text"):
        lines.append("### Full Content")
        lines.append(result["text"])
        lines.append("")

    return "\n".join(lines)


def _format_contents_markdown(data: dict[str, Any]) -> str:
    """Format contents results as markdown.

    Args:
        data: API response data.

    Returns:
        Formatted markdown string.
    """
    results = data.get("results", [])

    if not results:
        return "No content extracted from the provided URLs."

    lines = ["# Extracted Content", ""]
    lines.append(f"Successfully extracted content from **{len(results)}** URLs")
    lines.append("")

    for i, result in enumerate(results, 1):
        lines.append(_format_content_markdown(result, i))
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _truncate_response(text: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(text) <= CHARACTER_LIMIT:
        return text

    truncated = text[: CHARACTER_LIMIT - 200]
    truncated += (
        f"\n\n---\n[Response truncated from {len(text)} characters. "
        "Request fewer URLs or use more specific content options.]"
    )
    return truncated


@mcp.tool(
    name="exa_get_contents",
    annotations={
        "title": "Get Page Contents",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_get_contents(
    urls: list[str],
    content: dict | None = None,
    livecrawl: str | None = None,
    subpages: int | None = None,
    response_format: str = "markdown",
    ctx: Context | None = None,
) -> str:
    """Extract full content from a list of URLs.

    Use this to get the complete text, highlights, or summary from web pages.
    This is useful for:
    - Reading full articles found via search
    - Extracting content for analysis
    - Getting summaries of multiple pages at once
    - Batch content extraction

    Args:
        urls: URLs to extract content from (required, max 100)
        content: Content extraction options (text, highlights, summary)
        livecrawl: Live crawl mode ('fallback', 'preferred', or 'always')
        subpages: Number of subpages to crawl (0-5)
        response_format: 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Extracted content in requested format (markdown or JSON).

    Examples:
        Get full text:
            {"urls": ["https://example.com/article"],
             "content": {"include_text": true}}

        Get summaries for multiple URLs:
            {"urls": ["https://example.com/1", "https://example.com/2"],
             "content": {"include_summary": true}}

        Force live crawl:
            {"urls": ["https://example.com"], "livecrawl": "always"}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Build content options
        content_opts: dict[str, Any] = {"text": True}  # Default: extract text
        if content:
            content_model = ContentOptions(**content)
            content_opts = content_model.to_api_params() or {"text": True}

        # Execute get contents
        data = await app_ctx.exa_client.get_contents(
            ids=urls,
            livecrawl=livecrawl,
            subpages=subpages,
            **content_opts,
        )

        # Format response
        if response_format == "json":
            response = json.dumps(data, indent=2)
        else:
            response = _format_contents_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
