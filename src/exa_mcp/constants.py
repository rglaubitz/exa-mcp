"""Constants and enums for the Exa MCP server.

This module defines all constants, enums, and configuration values
used throughout the server implementation.
"""

from enum import Enum

# MCP Response Limits
CHARACTER_LIMIT = 25000  # Maximum response size in characters (MCP best practice)
DEFAULT_NUM_RESULTS = 10
MAX_NUM_RESULTS = 100

# API Configuration
EXA_API_BASE_URL = "https://api.exa.ai"
EXA_WEBSETS_BASE_URL = "https://api.exa.ai/v0"
DEFAULT_TIMEOUT = 30.0
CONNECT_TIMEOUT = 10.0


class ResponseFormat(str, Enum):
    """Output format for tool responses.

    MARKDOWN: Human-readable formatted text (default)
    JSON: Machine-readable structured data
    """

    MARKDOWN = "markdown"
    JSON = "json"


class SearchType(str, Enum):
    """Search type for Exa queries.

    AUTO: Let Exa decide the best search type
    NEURAL: Semantic/neural search
    KEYWORD: Traditional keyword search
    """

    AUTO = "auto"
    NEURAL = "neural"
    KEYWORD = "keyword"


class Category(str, Enum):
    """Content category filter for search results.

    These categories help narrow results to specific content types.
    """

    COMPANY = "company"
    NEWS = "news"
    RESEARCH_PAPER = "research paper"
    GITHUB = "github"
    TWEET = "tweet"
    PDF = "pdf"
    PERSONAL_SITE = "personal site"
    LINKEDIN_PROFILE = "linkedin profile"


class LivecrawlMode(str, Enum):
    """Live crawling mode for content extraction.

    FALLBACK: Use cached content, fallback to live crawl if unavailable
    PREFERRED: Prefer live crawl over cached content
    ALWAYS: Always perform live crawl
    """

    FALLBACK = "fallback"
    PREFERRED = "preferred"
    ALWAYS = "always"


class WebsetStatus(str, Enum):
    """Status of a webset."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStatus(str, Enum):
    """Status of a research task."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
