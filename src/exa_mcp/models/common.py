"""Common Pydantic models shared across tools.

This module contains base classes and shared models used by multiple tools.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..constants import DEFAULT_NUM_RESULTS, MAX_NUM_RESULTS, ResponseFormat


class BaseInput(BaseModel):
    """Base input model with common configuration.

    All input models should inherit from this class to ensure
    consistent validation behavior.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list operations."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    limit: int = Field(
        default=DEFAULT_NUM_RESULTS,
        ge=1,
        le=MAX_NUM_RESULTS,
        description="Maximum number of results to return (1-100)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination",
    )


class ContentOptions(BaseModel):
    """Options for content extraction from search results.

    These options control what content is extracted and returned
    with search results.
    """

    model_config = ConfigDict(extra="forbid")

    include_text: bool = Field(
        default=False,
        description="Include full text content from pages",
    )
    max_characters: int | None = Field(
        default=None,
        ge=100,
        le=50000,
        description="Maximum characters of text to extract per result",
    )
    include_highlights: bool = Field(
        default=False,
        description="Include relevant text excerpts/highlights",
    )
    num_sentences: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Number of highlight sentences per result",
    )
    include_summary: bool = Field(
        default=False,
        description="Include AI-generated summary per result",
    )

    def to_api_params(self) -> dict[str, Any]:
        """Convert to Exa API parameter format.

        Returns:
            Dictionary with text, highlights, and summary options.
        """
        params: dict[str, Any] = {}

        if self.include_text:
            text_opts: dict[str, Any] = {}
            if self.max_characters:
                text_opts["maxCharacters"] = self.max_characters
            params["text"] = text_opts if text_opts else True

        if self.include_highlights:
            highlight_opts: dict[str, Any] = {}
            if self.num_sentences:
                highlight_opts["numSentences"] = self.num_sentences
            params["highlights"] = highlight_opts if highlight_opts else True

        if self.include_summary:
            params["summary"] = True

        return params
