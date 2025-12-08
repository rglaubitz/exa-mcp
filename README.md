# Exa MCP Server

Enhanced MCP server for the [Exa AI](https://exa.ai) search API with full parameter support.

## Features

- **Full Exa API Coverage**: Access to search, find_similar, get_contents, answer, research, and websets endpoints
- **Rich Parameter Support**: Domain filtering, date filtering, category filtering, content extraction
- **MCP Best Practices**: Proper error handling, response formatting, truncation
- **Type Safety**: Full Pydantic validation with comprehensive input schemas

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Exa API key from [dashboard.exa.ai](https://dashboard.exa.ai)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/exa-mcp-enhanced.git
cd exa-mcp-enhanced

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env and add your EXA_API_KEY
```

## Usage

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "exa": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/exa-mcp-enhanced",
        "python",
        "-m",
        "exa_mcp.server"
      ],
      "env": {
        "EXA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Running Directly

```bash
# With uv
uv run python -m exa_mcp.server

# Or after installing
exa-mcp
```

## Available Tools

### P1 - Core Search

| Tool               | Description                                                        |
| ------------------ | ------------------------------------------------------------------ |
| `exa_search`       | Full-featured search with category, domain, date, and text filters |
| `exa_find_similar` | Find pages similar to a given URL                                  |
| `exa_get_contents` | Extract full content from URLs                                     |

### P2 - Answer & Research (Coming Soon)

| Tool                 | Description                     |
| -------------------- | ------------------------------- |
| `exa_answer`         | Direct Q&A with citations       |
| `exa_research_start` | Create async research task      |
| `exa_research_check` | Check research task status      |
| `exa_code_search`    | Specialized code context search |

### P3 - Websets (Coming Soon)

| Tool                | Description               |
| ------------------- | ------------------------- |
| `exa_webset_create` | Create a new webset       |
| `exa_webset_list`   | List all websets          |
| `exa_webset_items`  | Get webset items          |
| `exa_webset_enrich` | Add enrichments to webset |

## Development

```bash
# Run tests
uv run pytest

# Lint and format
uv run ruff check --fix && uv run ruff format

# Type check
uv run mypy src/
```

## License

MIT
