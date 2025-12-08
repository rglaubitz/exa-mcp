"""Answer tool implementation for the Exa MCP server.

This module provides the exa_answer tool for getting direct answers with citations.
"""

import json
from typing import Any

from mcp.server.fastmcp import Context

from ..constants import CHARACTER_LIMIT, ResponseFormat
from ..exceptions import format_error_for_llm
from ..models.answer import AnswerInput
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
async def exa_answer(params: AnswerInput, ctx: Context) -> str:
    """Get a direct answer to a question with web citations.

    This tool uses Exa to search the web and generate a comprehensive
    answer with cited sources. Use cases include:
    - Getting factual answers with source verification
    - Research questions needing multiple perspectives
    - Quick fact-checking with citations
    - Generating referenced explanations

    Args:
        params: AnswerInput containing:
            - query (str): Question to answer (required)
            - num_results (int): Number of sources to cite (1-20, default 5)
            - include_domains (list[str]): Only search these domains
            - exclude_domains (list[str]): Exclude these domains
            - start_published_date (str): After this date (YYYY-MM-DD)
            - end_published_date (str): Before this date (YYYY-MM-DD)
            - response_format (str): 'markdown' or 'json'
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
    app_ctx = _get_app_context(ctx)

    try:
        # Execute answer query
        data = await app_ctx.exa_client.answer(
            query=params.query,
            text=True,  # Always include source text for citations
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps(data, indent=2)
        else:
            response = _format_answer_markdown(data)

        # Truncate if needed
        return _truncate_response(response)

    except Exception as e:
        return format_error_for_llm(e)
