"""Async HTTP client for the Exa API.

This module provides a thin async wrapper around the Exa API endpoints.
All tools use this client for API communication.
"""

from typing import Any

import httpx

from .constants import (
    DEFAULT_TIMEOUT,
    EXA_API_BASE_URL,
    EXA_WEBSETS_BASE_URL,
)
from .exceptions import raise_for_status


class ExaClient:
    """Async client for Exa API operations.

    This client is designed to be used with a lifespan-managed httpx.AsyncClient
    for connection pooling and proper resource management.

    Attributes:
        http_client: The underlying httpx.AsyncClient instance.
    """

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        """Initialize the Exa client.

        Args:
            http_client: Pre-configured httpx.AsyncClient with API key headers.
        """
        self.http_client = http_client

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        base_url: str = EXA_API_BASE_URL,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/search")
            base_url: API base URL (defaults to main API)
            **kwargs: Additional arguments passed to httpx request.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            ExaError: On API errors with user-friendly messages.
        """
        url = f"{base_url}{endpoint}"
        response = await self.http_client.request(
            method,
            url,
            timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT),
            **kwargs,
        )
        raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]

    # ==========================================================================
    # Search API
    # ==========================================================================

    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        search_type: str = "auto",
        category: str | None = None,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        start_published_date: str | None = None,
        end_published_date: str | None = None,
        start_crawl_date: str | None = None,
        end_crawl_date: str | None = None,
        include_text: list[str] | None = None,
        exclude_text: list[str] | None = None,
        use_autoprompt: bool = True,
        livecrawl: str | None = None,
        # Content options
        text: dict[str, Any] | bool | None = None,
        highlights: dict[str, Any] | bool | None = None,
        summary: dict[str, Any] | bool | None = None,
    ) -> dict[str, Any]:
        """Execute a search query against the Exa API.

        Args:
            query: Search query string.
            num_results: Number of results to return (max 100).
            search_type: Search type (auto, neural, keyword).
            category: Content category filter.
            include_domains: Only include results from these domains.
            exclude_domains: Exclude results from these domains.
            start_published_date: Filter by publish date (ISO format).
            end_published_date: Filter by publish date (ISO format).
            start_crawl_date: Filter by crawl date (ISO format).
            end_crawl_date: Filter by crawl date (ISO format).
            include_text: Results must contain these phrases.
            exclude_text: Results must NOT contain these phrases.
            use_autoprompt: Enable query optimization.
            livecrawl: Live crawl mode (fallback, preferred, always).
            text: Text content extraction options.
            highlights: Highlight extraction options.
            summary: Summary generation options.

        Returns:
            Search results with optional content.
        """
        payload: dict[str, Any] = {
            "query": query,
            "numResults": num_results,
            "type": search_type,
            "useAutoprompt": use_autoprompt,
        }

        # Optional filters
        if category:
            payload["category"] = category
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains
        if start_published_date:
            payload["startPublishedDate"] = start_published_date
        if end_published_date:
            payload["endPublishedDate"] = end_published_date
        if start_crawl_date:
            payload["startCrawlDate"] = start_crawl_date
        if end_crawl_date:
            payload["endCrawlDate"] = end_crawl_date
        if include_text:
            payload["includeText"] = include_text
        if exclude_text:
            payload["excludeText"] = exclude_text
        if livecrawl:
            payload["livecrawl"] = livecrawl

        # Content options
        if text is not None:
            payload["text"] = text if isinstance(text, dict) else {}
        if highlights is not None:
            payload["highlights"] = highlights if isinstance(highlights, dict) else {}
        if summary is not None:
            payload["summary"] = summary if isinstance(summary, dict) else {}

        return await self._request("POST", "/search", json=payload)

    async def find_similar(
        self,
        url: str,
        *,
        num_results: int = 10,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        start_published_date: str | None = None,
        end_published_date: str | None = None,
        exclude_source_domain: bool = True,
        # Content options
        text: dict[str, Any] | bool | None = None,
        highlights: dict[str, Any] | bool | None = None,
        summary: dict[str, Any] | bool | None = None,
    ) -> dict[str, Any]:
        """Find pages similar to a given URL.

        Args:
            url: Source URL to find similar pages for.
            num_results: Number of results to return.
            include_domains: Only include results from these domains.
            exclude_domains: Exclude results from these domains.
            start_published_date: Filter by publish date (ISO format).
            end_published_date: Filter by publish date (ISO format).
            exclude_source_domain: Exclude results from source URL domain.
            text: Text content extraction options.
            highlights: Highlight extraction options.
            summary: Summary generation options.

        Returns:
            Similar pages with optional content.
        """
        payload: dict[str, Any] = {
            "url": url,
            "numResults": num_results,
            "excludeSourceDomain": exclude_source_domain,
        }

        # Optional filters
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains
        if start_published_date:
            payload["startPublishedDate"] = start_published_date
        if end_published_date:
            payload["endPublishedDate"] = end_published_date

        # Content options
        if text is not None:
            payload["text"] = text if isinstance(text, dict) else {}
        if highlights is not None:
            payload["highlights"] = highlights if isinstance(highlights, dict) else {}
        if summary is not None:
            payload["summary"] = summary if isinstance(summary, dict) else {}

        return await self._request("POST", "/findSimilar", json=payload)

    async def get_contents(
        self,
        ids: list[str],
        *,
        text: dict[str, Any] | bool | None = None,
        highlights: dict[str, Any] | bool | None = None,
        summary: dict[str, Any] | bool | None = None,
        livecrawl: str | None = None,
        subpages: int | None = None,
    ) -> dict[str, Any]:
        """Get full content for a list of URLs or document IDs.

        Args:
            ids: List of URLs or document IDs to fetch content for.
            text: Text content extraction options.
            highlights: Highlight extraction options.
            summary: Summary generation options.
            livecrawl: Live crawl mode (fallback, preferred, always).
            subpages: Number of subpages to crawl (0-5).

        Returns:
            Content for each requested URL/ID.
        """
        payload: dict[str, Any] = {"ids": ids}

        # Content options
        if text is not None:
            payload["text"] = text if isinstance(text, dict) else {}
        if highlights is not None:
            payload["highlights"] = highlights if isinstance(highlights, dict) else {}
        if summary is not None:
            payload["summary"] = summary if isinstance(summary, dict) else {}
        if livecrawl:
            payload["livecrawl"] = livecrawl
        if subpages is not None:
            payload["subpages"] = subpages

        return await self._request("POST", "/contents", json=payload)

    # ==========================================================================
    # Answer API
    # ==========================================================================

    async def answer(
        self,
        query: str,
        *,
        text: bool = True,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Get a direct answer to a question with citations.

        Args:
            query: Question to answer.
            text: Include source text in response.
            model: Model to use for answer generation.
            system_prompt: Custom system prompt for answer generation.

        Returns:
            Answer with citations and optional source text.
        """
        payload: dict[str, Any] = {"query": query, "text": text}

        if model:
            payload["model"] = model
        if system_prompt:
            payload["systemPrompt"] = system_prompt

        return await self._request("POST", "/answer", json=payload)

    # ==========================================================================
    # Research API (v1)
    # ==========================================================================

    async def research_create(
        self,
        instructions: str,
        *,
        model: str = "exa-research",
        output_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new async research task.

        Args:
            instructions: Natural language instructions for the research task.
            model: Model to use ('exa-research' or 'exa-research-pro').
            output_schema: Optional JSON schema for structured output.

        Returns:
            Research task metadata including researchId.
        """
        payload: dict[str, Any] = {
            "instructions": instructions,
            "model": model,
        }
        if output_schema:
            payload["outputSchema"] = output_schema
        return await self._request("POST", "/research/v1", json=payload)

    async def research_get(self, research_id: str) -> dict[str, Any]:
        """Get the status and results of a research task.

        Args:
            research_id: ID of the research task.

        Returns:
            Research task status and results (if completed).
        """
        return await self._request("GET", f"/research/v1/{research_id}")

    async def research_list(self) -> dict[str, Any]:
        """List all research tasks.

        Returns:
            List of research tasks with their statuses.
        """
        return await self._request("GET", "/research/v1")

    # ==========================================================================
    # Websets API (v0)
    # ==========================================================================

    async def webset_create(
        self,
        query: str,
        *,
        count: int = 100,
        criteria: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new webset from a search query.

        Args:
            query: Search query to populate the webset.
            count: Number of items to include (default 100).
            criteria: Additional filtering criteria.

        Returns:
            Created webset metadata.
        """
        search_payload: dict[str, Any] = {
            "query": query,
            "count": count,
        }
        if criteria:
            search_payload["criteria"] = criteria

        payload: dict[str, Any] = {"search": search_payload}
        return await self._request("POST", "/websets", base_url=EXA_WEBSETS_BASE_URL, json=payload)

    async def webset_get(self, webset_id: str) -> dict[str, Any]:
        """Get webset details.

        Args:
            webset_id: ID of the webset.

        Returns:
            Webset metadata and status.
        """
        return await self._request("GET", f"/websets/{webset_id}", base_url=EXA_WEBSETS_BASE_URL)

    async def webset_list(
        self,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List all websets.

        Args:
            limit: Maximum number of websets to return.
            cursor: Pagination cursor.

        Returns:
            List of websets with pagination info.
        """
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/websets", base_url=EXA_WEBSETS_BASE_URL, params=params)

    async def webset_delete(self, webset_id: str) -> dict[str, Any]:
        """Delete a webset.

        Args:
            webset_id: ID of the webset to delete.

        Returns:
            Deletion confirmation.
        """
        return await self._request("DELETE", f"/websets/{webset_id}", base_url=EXA_WEBSETS_BASE_URL)

    async def webset_items(
        self,
        webset_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Get items from a webset.

        Args:
            webset_id: ID of the webset.
            limit: Maximum number of items to return.
            cursor: Pagination cursor.

        Returns:
            Webset items with pagination info.
        """
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        return await self._request(
            "GET",
            f"/websets/{webset_id}/items",
            base_url=EXA_WEBSETS_BASE_URL,
            params=params,
        )

    async def webset_enrich(
        self,
        webset_id: str,
        *,
        enrichment_type: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add an enrichment to a webset.

        Args:
            webset_id: ID of the webset.
            enrichment_type: Type of enrichment (e.g., "findEmail", "findLinkedIn").
            config: Enrichment-specific configuration.

        Returns:
            Enrichment task metadata.
        """
        payload: dict[str, Any] = {"type": enrichment_type}
        if config:
            payload["config"] = config

        return await self._request(
            "POST",
            f"/websets/{webset_id}/enrichments",
            base_url=EXA_WEBSETS_BASE_URL,
            json=payload,
        )
