# Current exa-mcp-server Capabilities

> Analysis of the official Exa MCP server: https://github.com/exa-labs/exa-mcp-server

## Overview

The official `exa-mcp-server` (v3.1.3) is a TypeScript-based MCP server that exposes a subset of Exa's API capabilities. It uses the `@modelcontextprotocol/sdk` and Zod for schema validation.

---

## Available Tools

### Enabled by Default

| Tool                   | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `web_search_exa`       | Real-time web search with content scraping        |
| `get_code_context_exa` | Code snippets, examples, and documentation search |

### Disabled by Default (require `enabledTools` config)

| Tool                    | Description                                |
| ----------------------- | ------------------------------------------ |
| `deep_search_exa`       | Advanced web search with query expansion   |
| `crawling_exa`          | Extract content from specific URLs         |
| `deep_researcher_start` | Start comprehensive AI research task       |
| `deep_researcher_check` | Check status and retrieve research results |
| `linkedin_search_exa`   | Search LinkedIn profiles and companies     |
| `company_research_exa`  | Research companies and organizations       |

---

## Tool Details

### `web_search_exa`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | string | required | Websearch query |
| numResults | number | 8 | Number of search results |
| livecrawl | 'fallback' \| 'preferred' | 'fallback' | Live crawling mode |
| type | 'auto' \| 'fast' \| 'deep' | 'auto' | Search type |
| contextMaxCharacters | number | 10000 | Max characters for LLM context |

**What it does:**

- Calls `/search` endpoint with `contents.text=true` and `contents.context`
- Returns concatenated context string optimized for LLMs

**Missing parameters from full API:**

- `category` - No category filtering
- `includeDomains` / `excludeDomains` - No domain filtering
- `startPublishedDate` / `endPublishedDate` - No date filtering
- `includeText` / `excludeText` - No phrase filtering
- `highlights` - No highlight extraction
- `summary` - No AI summaries

---

### `get_code_context_exa`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | string | required | Search query for APIs/libraries |
| tokensNum | number | 5000 | Token count (1000-50000) |

**What it does:**

- Calls `/context` endpoint (specialized code search)
- Returns code snippets and documentation

---

### `deep_researcher_start`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| instructions | string | required | Research question/instructions |
| model | 'exa-research' \| 'exa-research-pro' | 'exa-research' | Research model |

**What it does:**

- Starts async research task via `/research/tasks`
- Returns task ID for polling

---

### `deep_researcher_check`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| taskId | string | required | Task ID from deep_researcher_start |

**What it does:**

- Polls `/research/tasks/{id}` for status
- Returns research results when completed

---

## What's MISSING from Current MCP

### Core Search Features Not Exposed

| Feature            | API Parameter                            | Value                                                   |
| ------------------ | ---------------------------------------- | ------------------------------------------------------- |
| Category filtering | `category`                               | company, news, research paper, github, tweet, pdf, etc. |
| Domain filtering   | `includeDomains`, `excludeDomains`       | Array of domains                                        |
| Date filtering     | `startPublishedDate`, `endPublishedDate` | ISO date strings                                        |
| Text filtering     | `includeText`, `excludeText`             | Phrase requirements                                     |
| Highlights         | `highlights`                             | Smart excerpt extraction                                |
| Summaries          | `summary`                                | AI-generated summaries per result                       |
| User location      | `userLocation`                           | Geographic relevance                                    |

### Entire Endpoints Not Implemented

| Endpoint       | Description                           |
| -------------- | ------------------------------------- |
| `find_similar` | Find pages similar to a URL           |
| `get_contents` | Get full content from URLs            |
| `answer`       | Direct answers with citations         |
| Websets API    | Create/manage curated web collections |
| Enrichments    | Email, LinkedIn profile extraction    |

---

## API Endpoints Used

```
POST /search          - web_search_exa, deep_search_exa
POST /context         - get_code_context_exa
POST /crawl           - crawling_exa
POST /research/tasks  - deep_researcher_start
GET  /research/tasks/{id} - deep_researcher_check
```

---

## Configuration

```json
{
  "exaApiKey": "xxx",
  "enabledTools": [
    "web_search_exa",
    "deep_search_exa",
    "deep_researcher_start"
  ],
  "debug": false
}
```

---

## Gap Analysis for exa-mcp-enhanced

### Priority 1: Add Missing Search Parameters

- Category filtering (huge for targeted searches)
- Domain include/exclude
- Date range filtering
- Text include/exclude

### Priority 2: New Endpoints

- `find_similar` - competitive analysis, related content
- `get_contents` - full page extraction
- `answer` - direct Q&A with citations

### Priority 3: Websets API

- Create persistent collections
- Enrichments (emails, LinkedIn)
- Automated monitoring

---

## Source Files Analyzed

- `src/index.ts` - Main server, tool registration
- `src/tools/webSearch.ts` - Web search implementation
- `src/tools/exaCode.ts` - Code context search
- `src/tools/deepResearchStart.ts` - Research task creation
- `src/tools/deepResearchCheck.ts` - Research task polling
- `src/tools/crawling.ts` - URL content extraction
- `src/tools/deepSearch.ts` - Advanced search
- `src/tools/linkedInSearch.ts` - LinkedIn search
- `src/tools/companyResearch.ts` - Company research
