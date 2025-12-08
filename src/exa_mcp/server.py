"""Exa MCP Server - FastMCP server with lifespan-managed HTTP client.

This module provides the main MCP server implementation using FastMCP.
The server exposes tools for interacting with the Exa AI search API.

CRITICAL: Never write to stdout in STDIO-based servers - it corrupts JSON-RPC.
All logging must go to stderr.
"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastmcp import FastMCP

from .client import ExaClient
from .config import get_settings, validate_settings
from .constants import CONNECT_TIMEOUT, DEFAULT_TIMEOUT, EXA_API_BASE_URL

# Configure logging to stderr (CRITICAL for MCP servers)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("exa_mcp")


@dataclass
class AppContext:
    """Application context shared across all tool calls.

    This context is created once during server startup and provides
    access to the shared HTTP client and Exa client wrapper.

    Attributes:
        http_client: Lifespan-managed httpx.AsyncClient.
        exa_client: Exa API client wrapper.
    """

    http_client: httpx.AsyncClient
    exa_client: ExaClient


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle and shared resources.

    This context manager creates and manages the HTTP client that is
    shared across all tool calls. Using a single client provides:
    - Connection pooling for better performance
    - Proper resource cleanup on shutdown
    - Consistent configuration across all requests

    Args:
        server: The FastMCP server instance.

    Yields:
        AppContext with initialized HTTP and Exa clients.
    """
    settings = get_settings()
    logger.info("Starting Exa MCP server...")

    async with httpx.AsyncClient(
        base_url=EXA_API_BASE_URL,
        headers={
            "x-api-key": settings.exa_api_key,
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(DEFAULT_TIMEOUT, connect=CONNECT_TIMEOUT),
        follow_redirects=True,
    ) as http_client:
        exa_client = ExaClient(http_client)
        logger.info("Exa MCP server ready")
        yield AppContext(http_client=http_client, exa_client=exa_client)

    logger.info("Exa MCP server stopped")


# Create the FastMCP server instance
# Server name follows Python MCP convention: {service}_mcp
mcp = FastMCP(
    "exa_mcp",
    lifespan=app_lifespan,
)

# Import tools to register them with decorators
# NOTE: This must happen AFTER mcp is defined
from . import tools  # noqa: E402, F401


def main() -> None:
    """Main entry point for the Exa MCP server.

    Supports two transports:
    - STDIO (default): For Claude Desktop local usage
    - HTTP/SSE: For Cloud Run or remote hosting

    Set MCP_TRANSPORT=http to enable HTTP mode.
    """
    if not validate_settings():
        logger.error("Settings validation failed. Check EXA_API_KEY environment variable.")
        sys.exit(1)

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8080"))
        logger.info(f"Starting MCP server on HTTP transport ({host}:{port})...")
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting MCP server on STDIO transport...")
        mcp.run()


if __name__ == "__main__":
    main()
