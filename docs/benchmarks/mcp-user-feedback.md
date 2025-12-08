# Exa MCP Server - User Feedback Analysis

> Research compiled: December 2025
> Source: GitHub Issues from exa-labs/exa-mcp-server

## Executive Summary

Active community demand for missing Exa API features in the MCP server. Key pain points validated by GitHub issues show users want domain filtering, date filtering, and the full API surface.

---

## Recent GitHub Issues (Dec 2025)

### Feature Requests

| Issue                                                       | Title                                           | Status      | Key Request                                     |
| ----------------------------------------------------------- | ----------------------------------------------- | ----------- | ----------------------------------------------- |
| [#94](https://github.com/exa-labs/exa-mcp-server/issues/94) | Add `includeDomains` and rest of API parameters | **Open**    | Domain filtering, date filtering                |
| [#96](https://github.com/exa-labs/exa-mcp-server/pull/96)   | Funnel through more search parameters           | **Open PR** | Adds userLocation, domains, dates, text filters |
| [#79](https://github.com/exa-labs/exa-mcp-server/pull/79)   | Expose advanced Exa API parameters              | Closed      | Requested highlights, dates, domains            |
| [#85](https://github.com/exa-labs/exa-mcp-server/issues/85) | Use HTTP headers instead of params              | Open        | Better API key handling                         |

### Validated User Pain Points

**From Issue #94:**

> "Is there a reason the search tool doesn't accept the same API parameters as listed in the docs? Specifically wanting `includeDomains`, `excludeDomains`, `startPublishedDate`, and `endPublishedDate`."
> — @aud

**From PR #79:**

> "The following Exa API parameters were not exposed by the MCP tool:
>
> - `useAutoprompt` - query optimization
> - `searchType` - neural/keyword/auto selection
> - `startPublishedDate`/`endPublishedDate` - date filtering
> - `includeDomains`/`excludeDomains` - domain filtering
> - `highlights` - extractive summaries"
>   — @kaminoguo

---

## Bug Reports

| Issue                                                       | Title                       | Status | Platform            |
| ----------------------------------------------------------- | --------------------------- | ------ | ------------------- |
| [#84](https://github.com/exa-labs/exa-mcp-server/issues/84) | NPX package broken on Linux | Open   | Linux               |
| [#82](https://github.com/exa-labs/exa-mcp-server/issues/82) | Unable to Connect           | Open   | Windows             |
| [#78](https://github.com/exa-labs/exa-mcp-server/issues/78) | Claude Code install broken  | Open   | -                   |
| [#86](https://github.com/exa-labs/exa-mcp-server/issues/86) | HTTP SSE returns 405        | Open   | Generic MCP clients |
| [#87](https://github.com/exa-labs/exa-mcp-server/issues/87) | Log spam "No stored tokens" | Open   | Cursor              |
| [#77](https://github.com/exa-labs/exa-mcp-server/issues/77) | Only 2 tools loaded (not 7) | Closed | Kiro IDE            |

---

## Current Tools Exposed

The official exa-mcp-server exposes only **2 tools by default**:

| Tool                    | Enabled by Default |
| ----------------------- | ------------------ |
| `web_search_exa`        | ✓                  |
| `get_code_context_exa`  | ✓                  |
| `deep_search_exa`       | ✗                  |
| `crawling_exa`          | ✗                  |
| `deep_researcher_start` | ✗                  |
| `deep_researcher_check` | ✗                  |
| `linkedin_search_exa`   | ✗                  |
| `company_research_exa`  | ✗                  |

---

## Missing Features (User Requested)

### Tier 1 - Critical (Most Requested)

1. **Domain Filtering** (`includeDomains`, `excludeDomains`)
   - Multiple issues and PRs requesting this
   - PR #96 addresses this

2. **Date Filtering** (`startPublishedDate`, `endPublishedDate`)
   - Essential for news and research use cases

3. **Category Filtering** (`category`)
   - Not exposed despite being a key differentiator

### Tier 2 - High Value

4. **find_similar Endpoint**
   - Unique Exa feature, completely missing from MCP

5. **get_contents Endpoint**
   - Full content extraction from URLs

6. **Highlights** (`highlights`)
   - Smart excerpt extraction

7. **Text Filtering** (`includeText`, `excludeText`)
   - PR #96 addresses this

### Tier 3 - Advanced

8. **Answer Endpoint**
   - Direct Q&A with citations

9. **Websets API**
   - Collections with enrichments

10. **Research API**
    - Async deep research workflows

---

## Community Sentiment

### Positive

- Search quality is highly regarded
- Neural search results praised
- Code search (`get_code_context_exa`) well-received

### Negative

- Frustration with limited MCP implementation
- "Exa is powerful but MCP is too basic"
- Users resorting to direct SDK instead of MCP
- Platform compatibility issues (Linux, generic MCP clients)

---

## Opportunity for exa-mcp-enhanced

| Gap                       | Impact | Priority |
| ------------------------- | ------ | -------- |
| Missing search parameters | High   | P1       |
| No find_similar           | High   | P1       |
| No get_contents           | Medium | P1       |
| No answer endpoint        | Medium | P2       |
| No websets                | Medium | P3       |
| Cross-platform issues     | High   | P1       |

---

## Sources

- [exa-labs/exa-mcp-server Issues](https://github.com/exa-labs/exa-mcp-server/issues)
- [PR #96 - More search parameters](https://github.com/exa-labs/exa-mcp-server/pull/96)
- [Issue #94 - Feature request](https://github.com/exa-labs/exa-mcp-server/issues/94)
