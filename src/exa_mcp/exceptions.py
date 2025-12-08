"""Custom exceptions and error handling for the Exa MCP server.

This module defines exception classes and provides user-friendly error
message formatting for LLM consumption.
"""

from typing import Any

import httpx


class ExaError(Exception):
    """Base exception for all Exa-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ExaAuthenticationError(ExaError):
    """Raised when API authentication fails."""

    pass


class ExaRateLimitError(ExaError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class ExaValidationError(ExaError):
    """Raised when input validation fails."""

    pass


class ExaNotFoundError(ExaError):
    """Raised when a requested resource is not found."""

    pass


class ExaServerError(ExaError):
    """Raised when Exa API returns a server error."""

    pass


def format_error_for_llm(e: Exception) -> str:
    """Format an exception into a user-friendly, actionable error message.

    MCP best practice: Return errors in results, NOT as protocol errors.
    Error messages should guide agents toward correct usage.

    Args:
        e: The exception to format.

    Returns:
        A clear, actionable error message string.

    Examples:
        >>> format_error_for_llm(ExaRateLimitError())
        'Error: Rate limit exceeded. Please wait before making more requests.'
    """
    if isinstance(e, ExaAuthenticationError):
        return (
            "Error: Authentication failed. Please verify your EXA_API_KEY "
            "environment variable is set correctly. Get your key at dashboard.exa.ai"
        )

    if isinstance(e, ExaRateLimitError):
        msg = "Error: Rate limit exceeded. Please wait before making more requests."
        if e.retry_after:
            msg += f" Retry after {e.retry_after} seconds."
        return msg

    if isinstance(e, ExaValidationError):
        return f"Error: Invalid input - {e.message}. Please check your parameters."

    if isinstance(e, ExaNotFoundError):
        return f"Error: Resource not found - {e.message}. Please verify the ID is correct."

    if isinstance(e, ExaServerError):
        return (
            "Error: Exa API server error. This is temporary - please try again. "
            f"Details: {e.message}"
        )

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return (
                "Error: Invalid API key. Check your EXA_API_KEY environment variable. "
                "Get your key at dashboard.exa.ai"
            )
        if status == 403:
            return "Error: Access forbidden. You may not have permission for this endpoint."
        if status == 404:
            return "Error: Resource not found. Please check the ID or URL is correct."
        if status == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        if status >= 500:
            return f"Error: Exa API server error ({status}). Please try again later."
        return f"Error: API request failed with status {status}."

    if isinstance(e, httpx.TimeoutException):
        return (
            "Error: Request timed out. The Exa API took too long to respond. "
            "Try reducing the number of results or simplifying your query."
        )

    if isinstance(e, httpx.ConnectError):
        return "Error: Could not connect to Exa API. Please check your internet connection."

    # Generic fallback
    return f"Error: {type(e).__name__} - {str(e)}"


def raise_for_status(response: httpx.Response) -> None:
    """Check response status and raise appropriate ExaError.

    Args:
        response: The HTTP response to check.

    Raises:
        ExaAuthenticationError: For 401 responses.
        ExaRateLimitError: For 429 responses.
        ExaNotFoundError: For 404 responses.
        ExaServerError: For 5xx responses.
        ExaError: For other error responses.
    """
    if response.is_success:
        return

    status = response.status_code
    try:
        detail = response.json().get("error", response.text)
    except Exception:
        detail = response.text

    if status == 401:
        raise ExaAuthenticationError(f"Authentication failed: {detail}")
    if status == 404:
        raise ExaNotFoundError(f"Not found: {detail}")
    if status == 429:
        retry_after = response.headers.get("Retry-After")
        raise ExaRateLimitError(
            f"Rate limit exceeded: {detail}",
            retry_after=int(retry_after) if retry_after else None,
        )
    if status >= 500:
        raise ExaServerError(f"Server error ({status}): {detail}")

    raise ExaError(f"API error ({status}): {detail}")
