"""Get contents tool implementation for the Exa MCP server.

This module provides the exa_get_contents tool for extracting content from URLs.
"""

import json
from typing import Any

from mcp.server.fastmcp import Context

from ..constants import CHARACTER_LIMIT, ResponseFormat
from ..exceptions import format_error_for_llm
from ..models.contents import GetContentsInput
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
async def exa_get_contents(params: GetContentsInput, ctx: Context) -> str:
    """Extract full content from a list of URLs.

    Use this to get the complete text, highlights, or summary from web pages.
    This is useful for:
    - Reading full articles found via search
    - Extracting content for analysis
    - Getting summaries of multiple pages at once
    - Batch content extraction

    Args:
        params: GetContentsInput containing:
            - urls (list[str]): URLs to extract content from (required, max 100)
            - content (ContentOptions): What to extract (text/highlights/summary)
            - livecrawl (str): 'fallback', 'preferred', or 'always'
            - subpages (int): Number of subpages to crawl (0-5)
            - response_format (str): 'markdown' or 'json'
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
        # Build content options from params
        content_opts = params.content.to_api_params() if params.content else {"text": True}

        # Execute get contents
        data = await app_ctx.exa_client.get_contents(
            ids=params.urls,
            livecrawl=params.livecrawl.value if params.livecrawl else None,
            subpages=params.subpages,
            **content_opts,
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_contents_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
