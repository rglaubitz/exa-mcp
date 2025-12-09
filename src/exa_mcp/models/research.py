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


class ResearchModel(str, Enum):
    """Model to use for research tasks."""

    EXA_RESEARCH = "exa-research"
    EXA_RESEARCH_PRO = "exa-research-pro"


class CreateResearchInput(BaseInput):
    """Input parameters for creating a research task.

    Research tasks perform deep, multi-step research on a topic
    and return comprehensive results.
    """

    instructions: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Natural language instructions for the research task",
    )

    model: ResearchModel = Field(
        default=ResearchModel.EXA_RESEARCH,
        description="Model to use: 'exa-research' (default) or 'exa-research-pro' (higher quality)",
    )


class GetResearchInput(BaseInput):
    """Input parameters for getting research task status/results."""

    research_id: str = Field(
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

    research_id: str = Field(alias="researchId", description="Research task ID")
    status: ResearchTaskStatus = Field(description="Current status")
    instructions: str = Field(description="Original research instructions")
    model: str = Field(description="Model used for research")
    created_at: str | None = Field(
        default=None, alias="createdAt", description="Creation timestamp"
    )
    completed_at: str | None = Field(
        default=None, alias="completedAt", description="Completion timestamp"
    )
    result: str | None = Field(default=None, description="Research result (if completed)")
    error: str | None = Field(default=None, description="Error message (if failed)")
