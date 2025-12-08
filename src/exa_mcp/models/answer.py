"""Pydantic models for the exa_answer tool."""

from typing import Any

from pydantic import BaseModel, Field

from ..constants import ResponseFormat
from .common import BaseInput, ContentOptions


class AnswerInput(BaseInput):
    """Input parameters for the exa_answer tool.

    This tool provides direct answers to questions with citations
    from web sources.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to answer",
    )

    num_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of sources to cite (1-20)",
    )

    include_domains: list[str] | None = Field(
        default=None,
        description="Only search these domains for answers",
    )

    exclude_domains: list[str] | None = Field(
        default=None,
        description="Exclude these domains from search",
    )

    start_published_date: str | None = Field(
        default=None,
        description="Only include sources published after this date (YYYY-MM-DD)",
    )

    end_published_date: str | None = Field(
        default=None,
        description="Only include sources published before this date (YYYY-MM-DD)",
    )

    content: ContentOptions | None = Field(
        default=None,
        description="Content extraction options for sources",
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Response format: 'markdown' or 'json'",
    )


class AnswerResponse(BaseModel):
    """Response from the answer endpoint."""

    answer: str = Field(description="The generated answer")
    citations: list[dict[str, Any]] = Field(default_factory=list, description="Source citations")
