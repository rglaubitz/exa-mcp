"""Answer tool implementation for the Exa MCP server.

This module provides the exa_answer tool for getting direct answers with citations.
"""

import json
from typing import Any

from fastmcp import Context

from ..constants import CHARACTER_LIMIT
from ..exceptions import format_error_for_llm
from ..server import AppContext, mcp


def _get_app_context(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP Context."""
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _format_citation_markdown(citation: dict[str, Any], index: int) -> str:
    """Format a single citation as markdown.

    Args:
        citation: Citation data from Exa API.
        index: Citation index (1-based).

    Returns:
        Formatted markdown string.
    """
    lines = [f"**[{index}]** [{citation.get('title', 'Untitled')}]({citation.get('url', '#')})"]

    if citation.get("publishedDate"):
        lines[0] += f" ({citation['publishedDate']})"

    if citation.get("text"):
        # Show a brief excerpt
        text = citation["text"][:300] + "..." if len(citation["text"]) > 300 else citation["text"]
        lines.append(f"   > {text}")

    return "\n".join(lines)


def _format_answer_markdown(data: dict[str, Any]) -> str:
    """Format answer results as markdown.

    Args:
        data: API response data.

    Returns:
        Formatted markdown string.
    """
    answer = data.get("answer", "No answer generated.")
    citations = data.get("citations", [])

    lines = ["# Answer", "", answer, ""]

    if citations:
        lines.append("## Sources")
        lines.append("")
        for i, citation in enumerate(citations, 1):
            lines.append(_format_citation_markdown(citation, i))
            lines.append("")

    return "\n".join(lines)


def _truncate_response(text: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(text) <= CHARACTER_LIMIT:
        return text

    truncated = text[: CHARACTER_LIMIT - 200]
    truncated += (
        f"\n\n---\n[Response truncated from {len(text)} characters. "
        "Use more specific questions for shorter answers.]"
    )
    return truncated


@mcp.tool(
    name="exa_answer",
    annotations={
        "title": "Get Answer with Citations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def exa_answer(
    query: str,
    num_results: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    content: dict | None = None,
    response_format: str = "markdown",
    ctx: Context | None = None,
) -> str:
    """Get a direct answer to a question with web citations.

    This tool uses Exa to search the web and generate a comprehensive
    answer with cited sources. Use cases include:
    - Getting factual answers with source verification
    - Research questions needing multiple perspectives
    - Quick fact-checking with citations
    - Generating referenced explanations

    Note: Some parameters are accepted for schema compatibility but not
    currently supported by the Exa answer API endpoint.

    Args:
        query: Question to answer (required)
        num_results: Number of sources to cite (1-20, default 5) - not yet supported
        include_domains: Only search these domains - not yet supported
        exclude_domains: Exclude these domains - not yet supported
        start_published_date: After this date (YYYY-MM-DD) - not yet supported
        end_published_date: Before this date (YYYY-MM-DD) - not yet supported
        content: Content extraction options for sources - not yet supported
        response_format: 'markdown' or 'json'
        ctx: FastMCP request context (injected automatically).

    Returns:
        Answer with citations in requested format.

    Examples:
        Simple question:
            {"query": "What is the current state of quantum computing?"}

        Filtered sources:
            {"query": "Latest AI regulations",
             "include_domains": ["reuters.com", "nytimes.com"],
             "start_published_date": "2024-01-01"}

        JSON format:
            {"query": "How does photosynthesis work?",
             "response_format": "json"}
    """
    # Parameters accepted for schema compatibility but not used by API:
    # num_results, include_domains, exclude_domains, start_published_date,
    # end_published_date, content
    _ = (
        num_results,
        include_domains,
        exclude_domains,
        start_published_date,
        end_published_date,
        content,
    )

    app_ctx = _get_app_context(ctx)

    try:
        # Execute answer query
        data = await app_ctx.exa_client.answer(
            query=query,
            text=True,  # Always include source text for citations
        )

        # Format response
        if response_format == "json":
            response = json.dumps(data, indent=2)
        else:
            response = _format_answer_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
