"""Search tool implementation for the Exa MCP server.

This module provides the exa_search tool with full parameter support.
"""

import json
from typing import Any

from mcp.server.fastmcp import Context

from ..constants import CHARACTER_LIMIT, ResponseFormat
from ..exceptions import format_error_for_llm
from ..models.search import SearchInput
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
async def exa_search(params: SearchInput, ctx: Context) -> str:
    """Search the web using Exa's neural search engine.

    Exa provides high-quality semantic search results with optional content extraction.
    Use this for research, finding documentation, news, papers, and more.

    The search supports filtering by:
    - **Category**: company, news, research paper, github, tweet, pdf
    - **Domains**: Include or exclude specific domains
    - **Dates**: Filter by publish date or crawl date
    - **Text**: Require or exclude specific phrases

    Args:
        params: SearchInput containing:
            - query (str): Search query (required)
            - num_results (int): Number of results (1-100, default 10)
            - search_type (str): 'auto', 'neural', or 'keyword'
            - category (str): Content type filter
            - include_domains (list[str]): Only these domains
            - exclude_domains (list[str]): Skip these domains
            - start_published_date (str): After this date (YYYY-MM-DD)
            - end_published_date (str): Before this date (YYYY-MM-DD)
            - include_text (list[str]): Must contain phrases
            - exclude_text (list[str]): Must NOT contain phrases
            - content (ContentOptions): Text/highlights/summary options
            - response_format (str): 'markdown' or 'json'
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
        # Build content options from params
        content_opts = params.content.to_api_params() if params.content else {}

        # Execute search
        data = await app_ctx.exa_client.search(
            query=params.query,
            num_results=params.num_results,
            search_type=params.search_type.value if params.search_type else "auto",
            category=params.category.value if params.category else None,
            include_domains=params.include_domains,
            exclude_domains=params.exclude_domains,
            start_published_date=params.start_published_date,
            end_published_date=params.end_published_date,
            start_crawl_date=params.start_crawl_date,
            end_crawl_date=params.end_crawl_date,
            include_text=params.include_text,
            exclude_text=params.exclude_text,
            use_autoprompt=params.use_autoprompt,
            livecrawl=params.livecrawl.value if params.livecrawl else None,
            **content_opts,
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_results_markdown(data, params.query)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)


def _format_code_results_markdown(data: dict[str, Any], query: str) -> str:
    """Format code search results as markdown.

    Args:
        data: API response data.
        query: Original search query.

    Returns:
        Formatted markdown string.
    """
    results = data.get("results", [])

    if not results:
        return f"No code results found for: '{query}'"

    lines = [f"# Code Search Results: '{query}'", ""]
    lines.append(f"Found **{len(results)}** code-related results")
    lines.append("")

    for i, result in enumerate(results, 1):
        lines.append(f"### {i}. {result.get('title', 'Untitled')}")
        lines.append(f"**URL:** {result.get('url', 'N/A')}")

        if result.get("publishedDate"):
            lines.append(f"**Updated:** {result['publishedDate']}")

        if result.get("score"):
            lines.append(f"**Relevance:** {result['score']:.2f}")

        # Add code highlights if available
        if result.get("highlights"):
            lines.append("\n**Code Snippets:**")
            for highlight in result["highlights"][:3]:
                lines.append(f"```\n{highlight}\n```")

        # Add text excerpt if available
        if result.get("text"):
            text = result["text"][:800] + "..." if len(result["text"]) > 800 else result["text"]
            lines.append(f"\n**Content:**\n{text}")

        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="exa_code_search",
    annotations={
        "title": "Code Context Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_code_search(params: SearchInput, ctx: Context) -> str:
    """Search for code examples, documentation, and GitHub repositories.

    This is a specialized search optimized for finding code-related content.
    It automatically filters to GitHub and code-related sources.

    Use cases:
    - Finding code examples and implementations
    - Searching for library documentation
    - Discovering GitHub repositories
    - Finding API usage examples

    Args:
        params: SearchInput containing:
            - query (str): Code-related search query (required)
            - num_results (int): Number of results (1-100, default 10)
            - include_domains (list[str]): Additional domains to include
            - exclude_domains (list[str]): Domains to exclude
            - content (ContentOptions): Text/highlights options
            - response_format (str): 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Code search results in requested format.

    Examples:
        Find examples:
            {"query": "React useState hook examples"}

        Library docs:
            {"query": "FastAPI dependency injection",
             "content": {"include_text": true}}

        Specific repo:
            {"query": "authentication middleware",
             "include_domains": ["github.com/expressjs"]}
    """
    app_ctx = _get_app_context(ctx)

    try:
        # Build content options from params
        content_opts = params.content.to_api_params() if params.content else {"text": True}

        # Code search uses github category and specific domains
        code_domains = ["github.com", "stackoverflow.com", "dev.to", "medium.com"]
        if params.include_domains:
            code_domains.extend(params.include_domains)

        # Execute search with github category
        data = await app_ctx.exa_client.search(
            query=params.query,
            num_results=params.num_results,
            search_type="auto",
            category="github",  # Focus on GitHub content
            include_domains=code_domains,
            exclude_domains=params.exclude_domains,
            use_autoprompt=True,
            **content_opts,
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_code_results_markdown(data, params.query)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
