# Exa MCP Enhanced - Project Context

## Project Overview

Custom MCP server to expose underutilized Exa API capabilities beyond the official `exa-mcp-server`. Goal is to maximize ROI from Exa API subscription.

## Tech Stack

- **Language**: Python 3.13+ (3.13.11 current stable)
- **Package Manager**: uv
- **MCP Framework**: FastMCP 2.13.3
- **HTTP Client**: httpx 0.28.1 (async)
- **Validation**: Pydantic 2.12.5
- **Testing**: pytest 9.0.2
- **Linting**: ruff 0.14.8
- **Exa SDK**: exa-py 1.16.1 (reference only, we use httpx directly)

## Project Structure

```
exa-mcp-enhanced/
├── src/
│   └── exa_mcp_enhanced/
│       ├── __init__.py
│       ├── server.py          # FastMCP server entry
│       ├── tools/             # Tool implementations
│       │   ├── search.py      # Enhanced search
│       │   ├── similar.py     # find_similar
│       │   ├── contents.py    # get_contents
│       │   ├── answer.py      # answer endpoint
│       │   ├── research.py    # research_start/check
│       │   └── websets.py     # webset_* tools
│       └── client.py          # Exa API client wrapper
├── tests/
├── pyproject.toml
└── research/
    └── planning.md            # Full planning doc
```

## Development Commands

```bash
# Setup
uv sync

# Run server (dev)
uv run python -m exa_mcp_enhanced.server

# Test
uv run pytest

# Lint
uv run ruff check --fix && uv run ruff format

# Type check
uv run mypy src/
```

## Environment Variables

```
EXA_API_KEY=xxx              # Required - from dashboard.exa.ai
```

## Tool Categories

### Core Search (3 tools)

- `search` - Enhanced with category, domain, date, phrase filters
- `find_similar` - Find pages similar to a URL
- `get_contents` - Full page content from URLs

### Answer/Research (3 tools)

- `answer` - Direct answers with citations
- `research_start` - Kick off deep research task
- `research_check` - Check status / get results

### Websets (4 tools)

- `webset_create` - Create new webset with query
- `webset_list` - List all websets
- `webset_items` - Get items from a webset
- `webset_enrich` - Add enrichments (emails, linkedin)

### Specialized (1 tool)

- `code_search` - Specialized code context search

## API Reference

- **Exa API Docs**: https://docs.exa.ai/reference/search
- **Exa OpenAPI Spec**: https://github.com/exa-labs/openapi-spec
- **Exa Python SDK**: https://github.com/exa-labs/exa-py
- **FastMCP Docs**: https://gofastmcp.com
- **Websets API**: https://docs.exa.ai/websets/overview

### Exa Search API Endpoints (api.exa.ai)

| Endpoint            | Method   | Description                            |
| ------------------- | -------- | -------------------------------------- |
| `/search`           | POST     | Neural/keyword search with full params |
| `/findSimilar`      | POST     | Find pages similar to URL              |
| `/contents`         | POST     | Extract content from URLs              |
| `/answer`           | POST     | Q&A with citations                     |
| `/research/v1`      | GET/POST | List/Create research tasks             |
| `/research/v1/{id}` | GET      | Get research results (SSE)             |

### Exa Websets API Endpoints (api.exa.ai/v0)

| Endpoint                    | Methods         | Description         |
| --------------------------- | --------------- | ------------------- |
| `/websets`                  | POST/GET        | Create/List websets |
| `/websets/{id}`             | GET/POST/DELETE | Manage webset       |
| `/websets/{id}/items`       | GET             | List items          |
| `/websets/{id}/enrichments` | POST            | Add enrichments     |
| `/websets/{id}/searches`    | POST            | Create search       |
| `/webhooks`                 | POST/GET        | Manage webhooks     |
| `/monitors`                 | POST/GET        | Automated monitors  |
| `/imports`                  | POST/GET        | Data imports        |

## Key Parameters (Missing from current MCP)

| Parameter            | Description                                                       |
| -------------------- | ----------------------------------------------------------------- |
| `category`           | Filter by type: company, news, research paper, pdf, github, tweet |
| `includeDomains`     | Only search these domains                                         |
| `excludeDomains`     | Skip these domains                                                |
| `startPublishedDate` | Filter by publish date (after)                                    |
| `endPublishedDate`   | Filter by publish date (before)                                   |
| `includeText`        | Must contain these phrases                                        |
| `excludeText`        | Must NOT contain these phrases                                    |
| `userLocation`       | Geographic relevance                                              |
| `highlights`         | Customizable excerpt extraction                                   |
| `summary`            | AI-generated summaries per result                                 |

## Coding Guidelines

- Follow PEP8 with black/ruff formatting
- Type hints on all functions
- Google-style docstrings
- Pydantic models for API request/response
- Async-first design (httpx.AsyncClient)
- Max 500 lines per file
- Tests in `/tests` mirroring src structure

## Testing Strategy

- Unit tests for each tool
- Mock Exa API responses
- Integration tests with real API (marked slow)
- Test all parameter combinations

## Current Phase

**Phase 1: Research & Validation**

- Verify API access for all endpoints
- Document rate limits
- Test find-similar endpoint manually

See `research/planning.md` for full task breakdown.
