"""Pydantic models for the get_contents tool.

This module contains input validation models for the exa_get_contents tool.
"""

from pydantic import Field, HttpUrl, field_validator

from ..constants import LivecrawlMode
from .common import BaseInput, ContentOptions


class GetContentsInput(BaseInput):
    """Input parameters for the exa_get_contents tool.

    Extract full content from a list of URLs or document IDs.
    This is useful for:
    - Getting the full text of articles found via search
    - Extracting content from specific pages
    - Batch content extraction

    Examples:
        Basic usage:
            {"urls": ["https://example.com/article"]}

        With options:
            {"urls": ["https://example.com"], "content": {"include_text": true},
             "livecrawl": "preferred"}
    """

    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of URLs or document IDs to extract content from (max 100)",
    )
    content: ContentOptions | None = Field(
        default=None,
        description="Content extraction options (text, highlights, summary)",
    )
    livecrawl: LivecrawlMode | None = Field(
        default=None,
        description="Live crawl mode: 'fallback' (default), 'preferred', or 'always'",
    )
    subpages: int | None = Field(
        default=None,
        ge=0,
        le=5,
        description="Number of subpages to crawl from each URL (0-5)",
    )

    @field_validator("urls", mode="before")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Validate and normalize URLs."""
        validated = []
        for url in v:
            url = url.strip()
            if not url:
                continue
            # Add https:// if no protocol specified and it looks like a URL
            if not url.startswith(("http://", "https://")) and "." in url:
                url = "https://" + url
            # Validate URL format (but allow document IDs that don't look like URLs)
            if url.startswith(("http://", "https://")):
                HttpUrl(url)
            validated.append(url)

        if not validated:
            raise ValueError("At least one valid URL is required")
        return validated
