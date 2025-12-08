"""Entry point for running exa_mcp as a module.

Usage:
    python -m exa_mcp

This avoids the double-module problem where tools register on
exa_mcp.server.mcp but __main__ has a different mcp instance.
"""

from exa_mcp.server import main

if __name__ == "__main__":
    main()
