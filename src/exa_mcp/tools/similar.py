"""Find similar tool implementation for the Exa MCP server.

This module provides the exa_find_similar tool.
"""

import json
from typing import Any

from fastmcp import Context

from ..constants import CHARACTER_LIMIT, ResponseFormat
from ..exceptions import format_error_for_llm
from ..models.similar import FindSimilarInput
from ..server import AppContext, mcp


def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context."""
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _format_result_markdown(result: dict[str, Any], index: int) -> str:
    """Format a single similar result as markdown.

    Args:
        result: Similar result from Exa API.
        index: Result index (1-based).

    Returns:
        Formatted markdown string.
    """
    lines = [f"### {index}. {result.get('title', 'Untitled')}"]
    lines.append(f"**URL:** {result.get('url', 'N/A')}")

    if result.get("publishedDate"):
        lines.append(f"**Published:** {result['publishedDate']}")

    if result.get("author"):
        lines.append(f"**Author:** {result['author']}")

    if result.get("score"):
        lines.append(f"**Similarity:** {result['score']:.2f}")

    # Add highlights if available
    if result.get("highlights"):
        lines.append("\n**Highlights:**")
        for highlight in result["highlights"][:3]:
            lines.append(f"> {highlight}")

    # Add summary if available
    if result.get("summary"):
        lines.append(f"\n**Summary:** {result['summary']}")

    # Add text excerpt if available
    if result.get("text"):
        text = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
        lines.append(f"\n**Content Preview:**\n{text}")

    return "\n".join(lines)


def _format_results_markdown(data: dict[str, Any], source_url: str) -> str:
    """Format similar results as markdown.

    Args:
        data: API response data.
        source_url: Original source URL.

    Returns:
        Formatted markdown string.
    """
    results = data.get("results", [])

    if not results:
        return f"No similar pages found for: {source_url}"

    lines = [f"# Pages Similar to: {source_url}", ""]
    lines.append(f"Found **{len(results)}** similar pages")
    lines.append("")

    for i, result in enumerate(results, 1):
        lines.append(_format_result_markdown(result, i))
        lines.append("")

    return "\n".join(lines)


def _truncate_response(text: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(text) <= CHARACTER_LIMIT:
        return text

    truncated = text[: CHARACTER_LIMIT - 200]
    truncated += (
        f"\n\n---\n[Response truncated from {len(text)} characters. "
        "Use more specific filters or reduce num_results.]"
    )
    return truncated


@mcp.tool(
    name="exa_find_similar",
    annotations={
        "title": "Find Similar Pages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_find_similar(params: FindSimilarInput, ctx: Context) -> str:
    """Find web pages similar to a given URL.

    This is a unique Exa capability that finds semantically similar content
    to any webpage. Use cases include:
    - Finding related articles on a topic
    - Discovering competitor websites
    - Finding alternative sources for research
    - Expanding a reading list with similar content

    Args:
        params: FindSimilarInput containing:
            - url (str): Source URL to find similar pages for (required)
            - num_results (int): Number of results (1-100, default 10)
            - include_domains (list[str]): Only these domains
            - exclude_domains (list[str]): Skip these domains
            - start_published_date (str): After this date (YYYY-MM-DD)
            - end_published_date (str): Before this date (YYYY-MM-DD)
            - exclude_source_domain (bool): Exclude source URL's domain (default true)
            - content (ContentOptions): Text/highlights/summary options
            - response_format (str): 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Similar pages in requested format (markdown or JSON).

    Examples:
        Find similar to an article:
            {"url": "https://arxiv.org/abs/2301.00001"}

        Find competitors:
            {"url": "https://stripe.com", "exclude_source_domain": true,
             "num_results": 10}

        With content:
            {"url": "https://example.com/blog/post",
             "content": {"include_summary": true}}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Build content options from params
        content_opts = params.content.to_api_params() if params.content else {}

        # Execute find similar
        data = await app_ctx.exa_client.find_similar(
            url=params.url,
            num_results=params.num_results,
            include_domains=params.include_domains,
            exclude_domains=params.exclude_domains,
            start_published_date=params.start_published_date,
            end_published_date=params.end_published_date,
            exclude_source_domain=params.exclude_source_domain,
            **content_opts,
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_results_markdown(data, params.url)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
