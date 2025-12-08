"""Pydantic models for the find_similar tool.

This module contains input validation models for the exa_find_similar tool.
"""

from pydantic import Field, HttpUrl, field_validator

from ..constants import DEFAULT_NUM_RESULTS, MAX_NUM_RESULTS
from .common import BaseInput, ContentOptions


class FindSimilarInput(BaseInput):
    """Input parameters for the exa_find_similar tool.

    Find pages similar to a given URL. This is useful for:
    - Finding related content to a specific article
    - Discovering competitors similar to a company page
    - Finding alternative sources on a topic

    Examples:
        Basic usage:
            {"url": "https://arxiv.org/abs/2301.00001"}

        With filters:
            {"url": "https://example.com", "num_results": 5,
             "exclude_source_domain": true}
    """

    url: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Source URL to find similar pages for. Must be a valid HTTP/HTTPS URL.",
    )
    num_results: int = Field(
        default=DEFAULT_NUM_RESULTS,
        ge=1,
        le=MAX_NUM_RESULTS,
        description="Number of similar results to return (1-100)",
    )
    include_domains: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Only include results from these domains",
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
    exclude_source_domain: bool = Field(
        default=True,
        description="Exclude results from the source URL's domain",
    )
    content: ContentOptions | None = Field(
        default=None,
        description="Content extraction options (text, highlights, summary)",
    )

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        # Use HttpUrl for validation but return string
        HttpUrl(v)
        return v

    @field_validator("include_domains", "exclude_domains", mode="before")
    @classmethod
    def validate_domains(cls, v: list[str] | None) -> list[str] | None:
        """Validate domain list - strip whitespace and filter empty."""
        if v is None:
            return None
        return [d.strip().lower() for d in v if d.strip()]
