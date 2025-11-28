# Exa MCP Enhanced - Planning Document

> **Goal:** Maximize ROI from Exa API by exposing underutilized capabilities through a custom MCP server.

## Current State Analysis

### What We Have Access To (Current MCP)
- `web_search_exa` - Basic web search with type selection (auto/fast/deep)
- `get_code_context_exa` - Code-specific search with token limits

### What's Missing (Gap Analysis)

| API Endpoint | Description | Business Value |
|--------------|-------------|----------------|
| `/find-similar-links` | Find pages similar to a URL | Competitor research, vendor discovery |
| `/answer` | Direct answers with citations | Agent accuracy, reduced hallucinations |
| `/research` | Multi-agent deep research | Automated market analysis |
| `/contents` | Full page content retrieval | Complete data extraction |
| **Websets API** | Lead gen at scale | Sales prospecting |

### Missing Search Parameters
- `category` - Filter by type (company, news, research paper, pdf, github, tweet)
- `includeDomains` / `excludeDomains` - Domain filtering
- `startPublishedDate` / `endPublishedDate` - Date range filtering
- `includeText` / `excludeText` - Phrase filtering
- `userLocation` - Geographic relevance
- `highlights` - Customizable excerpt extraction
- `summary` - AI-generated summaries per result

---

## Dependencies

### Python Packages
```
fastmcp>=0.1.0          # MCP server framework
httpx>=0.27.0           # Async HTTP client (or requests)
pydantic>=2.0           # Data validation
python-dotenv>=1.0.0    # Environment management
exa-py>=1.0.0           # Official Exa Python SDK (optional - may use direct API)
```

### Environment Variables
```
EXA_API_KEY=xxx         # Required - from dashboard.exa.ai
```

### API Access Requirements
- Standard Exa API key covers: search, find-similar, contents, answer
- Research API: May require specific plan tier (verify)
- Websets API: Separate API surface (verify access)

---

## Tasks

### Phase 1: Research & Validation
- [ ] Verify Websets API access with current API key
- [ ] Verify Research API access with current API key  
- [ ] Review official exa-py SDK capabilities
- [ ] Document rate limits for each endpoint
- [ ] Test find-similar endpoint manually

### Phase 2: Core Implementation
- [ ] Set up project structure (pyproject.toml, src/, tests/)
- [ ] Implement enhanced search tool with all filters
- [ ] Implement find_similar tool
- [ ] Implement get_contents tool
- [ ] Implement answer tool

### Phase 3: Advanced Features
- [ ] Implement research_start tool
- [ ] Implement research_check tool
- [ ] Implement webset_create tool (if access confirmed)
- [ ] Implement webset_list tool
- [ ] Implement webset_items tool

### Phase 4: Testing & Documentation
- [ ] Write unit tests for each tool
- [ ] Create CLAUDE.md for project context
- [ ] Create tool usage guide
- [ ] Test integration with Claude Desktop

---

## Proposed Tool Set (~10-12 tools)

### Core Search (3)
1. `search` - Enhanced with category, domain, date, phrase filters
2. `find_similar` - Find pages similar to a URL
3. `get_contents` - Full page content from URLs

### Answer/Research (3)
4. `answer` - Direct answers with citations
5. `research_start` - Kick off deep research task
6. `research_check` - Check status / get results

### Websets (3-4)
7. `webset_create` - Create new webset with query
8. `webset_list` - List all websets
9. `webset_items` - Get items from a webset
10. `webset_enrich` - Add enrichments (emails, linkedin)

### Keep From Current (1)
11. `code_search` - Specialized code context search

---

## Reference Links

- **Exa API Docs:** https://docs.exa.ai/reference/search
- **Exa Python SDK:** https://github.com/exa-labs/exa-py
- **Official Exa MCP:** https://github.com/exa-labs/exa-mcp-server
- **FastMCP Framework:** https://github.com/jlowin/fastmcp
- **Websets API:** https://docs.exa.ai/websets/overview

---

## Use Cases for Origin/OpenHaul

| Use Case | Tool(s) | Expected ROI |
|----------|---------|--------------|
| Carrier competitor research | `find_similar` | 2-3 hrs saved/session |
| Vendor discovery for Oscar | `search` + filters | Faster development |
| Lead generation | `webset_create` + `webset_items` | New revenue potential |
| Market analysis reports | `research_start/check` | Hours → minutes |
| Tech documentation lookup | `code_search` + `answer` | Better agent accuracy |

---

*Created: 2025-11-28*
*Status: Planning*
