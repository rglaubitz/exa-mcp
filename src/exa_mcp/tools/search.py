"""Search tool implementation for the Exa MCP server.

This module provides the exa_search tool with full parameter support.
"""

import json
from typing import Any

from fastmcp import Context

from ..constants import CHARACTER_LIMIT, DEFAULT_NUM_RESULTS
from ..exceptions import format_error_for_llm
from ..models.common import ContentOptions
from ..server import AppContext, mcp


def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context.

    Args:
        ctx: FastMCP request context.

    Returns:
        Application context with Exa client.
    """
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _format_result_markdown(result: dict[str, Any], index: int) -> str:
    """Format a single search result as markdown.

    Args:
        result: Search result from Exa API.
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
        lines.append(f"**Relevance:** {result['score']:.2f}")

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


def _format_results_markdown(data: dict[str, Any], query: str) -> str:
    """Format search results as markdown.

    Args:
        data: API response data.
        query: Original search query.

    Returns:
        Formatted markdown string.
    """
    results = data.get("results", [])

    if not results:
        return f"No results found for: '{query}'"

    lines = [f"# Search Results for: '{query}'", ""]
    lines.append(f"Found **{len(results)}** results")

    if data.get("autopromptString"):
        lines.append(f'\n*Query optimized to: "{data["autopromptString"]}"*')

    lines.append("")

    for i, result in enumerate(results, 1):
        lines.append(_format_result_markdown(result, i))
        lines.append("")

    return "\n".join(lines)


def _truncate_response(text: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT.

    Args:
        text: Response text to potentially truncate.

    Returns:
        Original or truncated text with message.
    """
    if len(text) <= CHARACTER_LIMIT:
        return text

    truncated = text[: CHARACTER_LIMIT - 200]
    truncated += (
        f"\n\n---\n[Response truncated from {len(text)} characters. "
        "Use more specific filters or reduce num_results.]"
    )
    return truncated


@mcp.tool(
    name="exa_search",
    annotations={
        "title": "Exa Web Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_search(
    query: str,
    num_results: int = DEFAULT_NUM_RESULTS,
    search_type: str = "auto",
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    include_text: list[str] | None = None,
    exclude_text: list[str] | None = None,
    use_autoprompt: bool = True,
    livecrawl: str | None = None,
    content: dict | None = None,
    response_format: str = "markdown",
    ctx: Context | None = None,
) -> str:
    """Search the web using Exa's neural search engine.

    Exa provides high-quality semantic search results with optional content extraction.
    Use this for research, finding documentation, news, papers, and more.

    The search supports filtering by:
    - **Category**: company, news, research paper, github, tweet, pdf
    - **Domains**: Include or exclude specific domains
    - **Dates**: Filter by publish date or crawl date
    - **Text**: Require or exclude specific phrases

    Args:
        query: Search query (required)
        num_results: Number of results (1-100, default 10)
        search_type: 'auto' (recommended), 'neural' for semantic, 'keyword' for exact
        category: Content type filter (company, news, research paper, github, tweet, pdf)
        include_domains: Only these domains (e.g., ['arxiv.org', 'github.com'])
        exclude_domains: Skip these domains
        start_published_date: After this date (YYYY-MM-DD)
        end_published_date: Before this date (YYYY-MM-DD)
        start_crawl_date: After this crawl date (YYYY-MM-DD)
        end_crawl_date: Before this crawl date (YYYY-MM-DD)
        include_text: Results must contain ALL of these phrases
        exclude_text: Results must NOT contain any of these phrases
        use_autoprompt: Let Exa optimize the query for better results
        livecrawl: Live crawl mode ('fallback', 'preferred', or 'always')
        content: Content extraction options (text, highlights, summary)
        response_format: 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Search results in requested format (markdown or JSON).

    Examples:
        Simple search:
            {"query": "best practices for Python async programming"}

        Filtered search:
            {"query": "transformer architecture", "category": "research paper",
             "include_domains": ["arxiv.org"], "num_results": 5}

        With content extraction:
            {"query": "FastAPI tutorial", "content": {"include_text": true, "include_highlights": true}}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Build content options
        content_opts: dict[str, Any] = {}
        if content:
            content_model = ContentOptions(**content)
            content_opts = content_model.to_api_params()

        # Execute search
        data = await app_ctx.exa_client.search(
            query=query,
            num_results=num_results,
            search_type=search_type or "auto",
            category=category,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            start_published_date=start_published_date,
            end_published_date=end_published_date,
            start_crawl_date=start_crawl_date,
            end_crawl_date=end_crawl_date,
            include_text=include_text,
            exclude_text=exclude_text,
            use_autoprompt=use_autoprompt,
            livecrawl=livecrawl,
            **content_opts,
        )

        # Format response
        if response_format == "json":
            response = json.dumps(data, indent=2)
        else:
            response = _format_results_markdown(data, query)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
