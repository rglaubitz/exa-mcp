"""Pydantic models for the search tool.

This module contains input validation models for the exa_search tool.
"""

from pydantic import Field, field_validator

from ..constants import (
    DEFAULT_NUM_RESULTS,
    MAX_NUM_RESULTS,
    Category,
    LivecrawlMode,
    SearchType,
)
from .common import BaseInput, ContentOptions


class SearchInput(BaseInput):
    """Input parameters for the exa_search tool.

    Provides full access to Exa's search API parameters including
    domain filtering, date filtering, category filtering, and content extraction.

    Examples:
        Basic search:
            {"query": "AI safety research"}

        With filters:
            {"query": "machine learning", "category": "research paper",
             "include_domains": ["arxiv.org"], "num_results": 5}

        With content:
            {"query": "Python best practices", "content": {"include_text": true}}
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Search query string. Can be a question, topic, or keywords.",
    )
    num_results: int = Field(
        default=DEFAULT_NUM_RESULTS,
        ge=1,
        le=MAX_NUM_RESULTS,
        description="Number of search results to return (1-100)",
    )
    search_type: SearchType = Field(
        default=SearchType.AUTO,
        description="Search type: 'auto' (recommended), 'neural' for semantic, 'keyword' for exact",
    )
    category: Category | None = Field(
        default=None,
        description="Filter by content type: company, news, research paper, github, tweet, pdf",
    )
    include_domains: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Only include results from these domains (e.g., ['arxiv.org', 'github.com'])",
    )
    exclude_domains: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Exclude results from these domains",
    )
    start_published_date: str | None = Field(
        default=None,
        description="Only include results published after this date (ISO format: YYYY-MM-DD)",
    )
    end_published_date: str | None = Field(
        default=None,
        description="Only include results published before this date (ISO format: YYYY-MM-DD)",
    )
    start_crawl_date: str | None = Field(
        default=None,
        description="Only include results crawled after this date (ISO format: YYYY-MM-DD)",
    )
    end_crawl_date: str | None = Field(
        default=None,
        description="Only include results crawled before this date (ISO format: YYYY-MM-DD)",
    )
    include_text: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Results must contain ALL of these phrases",
    )
    exclude_text: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Results must NOT contain any of these phrases",
    )
    use_autoprompt: bool = Field(
        default=True,
        description="Let Exa optimize the query for better results",
    )
    livecrawl: LivecrawlMode | None = Field(
        default=None,
        description="Live crawl mode: 'fallback', 'preferred', or 'always'",
    )
    content: ContentOptions | None = Field(
        default=None,
        description="Content extraction options (text, highlights, summary)",
    )

    @field_validator("include_domains", "exclude_domains", mode="before")
    @classmethod
    def validate_domains(cls, v: list[str] | None) -> list[str] | None:
        """Validate domain list - strip whitespace and filter empty."""
        if v is None:
            return None
        return [d.strip().lower() for d in v if d.strip()]

    @field_validator("include_text", "exclude_text", mode="before")
    @classmethod
    def validate_text_filters(cls, v: list[str] | None) -> list[str] | None:
        """Validate text filter list - strip whitespace and filter empty."""
        if v is None:
            return None
        return [t.strip() for t in v if t.strip()]
