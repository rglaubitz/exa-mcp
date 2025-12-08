"""Test helper functions for Exa MCP tests.

These are utility functions that can be imported across test files.
"""

from unittest.mock import MagicMock

import httpx


def create_mock_response(
    data: dict,
    status_code: int = 200,
) -> MagicMock:
    """Create a mock httpx.Response.

    Args:
        data: JSON data to return.
        status_code: HTTP status code.

    Returns:
        Mock response that behaves like httpx.Response.
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = data
    response.raise_for_status = MagicMock()

    if status_code >= 400:
        error = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response,
        )
        response.raise_for_status.side_effect = error

    return response
