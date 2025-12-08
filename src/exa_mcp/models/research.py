"""Pydantic models for the exa_research tools."""

from enum import Enum

from pydantic import BaseModel, Field

from ..constants import ResponseFormat
from .common import BaseInput


class ResearchTaskStatus(str, Enum):
    """Status of a research task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchOutputType(str, Enum):
    """Output type for research tasks."""

    REPORT = "report"
    SUMMARY = "summary"
    DETAILED = "detailed"


class CreateResearchInput(BaseInput):
    """Input parameters for creating a research task.

    Research tasks perform deep, multi-step research on a topic
    and return comprehensive results.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The research question or topic",
    )

    output_type: ResearchOutputType = Field(
        default=ResearchOutputType.REPORT,
        description="Type of output: 'report', 'summary', or 'detailed'",
    )

    include_domains: list[str] | None = Field(
        default=None,
        description="Only research from these domains",
    )

    exclude_domains: list[str] | None = Field(
        default=None,
        description="Exclude these domains from research",
    )


class GetResearchInput(BaseInput):
    """Input parameters for getting research task status/results."""

    task_id: str = Field(
        ...,
        min_length=1,
        description="The research task ID to check",
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Response format: 'markdown' or 'json'",
    )


class ListResearchInput(BaseInput):
    """Input parameters for listing research tasks."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of tasks to return",
    )

    status: ResearchTaskStatus | None = Field(
        default=None,
        description="Filter by task status",
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Response format: 'markdown' or 'json'",
    )


class ResearchTask(BaseModel):
    """A research task returned from the API."""

    id: str = Field(description="Task ID")
    status: ResearchTaskStatus = Field(description="Current status")
    query: str = Field(description="Original research query")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")
    result: str | None = Field(default=None, description="Research result (if completed)")
    error: str | None = Field(default=None, description="Error message (if failed)")
