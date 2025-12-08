# Exa MCP Enhanced - Implementation Plan

## Phase 1: Documentation & Research (COMPLETED)

### Created Documentation Structure

```
docs/
├── api-reference/
│   ├── search-api.md          # Full search parameters
│   ├── websets-api.md         # Websets + enrichments
│   ├── answer-research-api.md # Answer + async research
│   └── similar-contents-api.md # find_similar + get_contents
├── current-mcp/
│   └── exa-mcp-server-capabilities.md  # Gap analysis
├── sdk/
│   └── python-sdk-specification.md     # Python SDK reference
└── benchmarks/                 # TO BE CREATED
    └── (pending research agent results)
```

### Key Gaps Identified in Current exa-mcp-server

**Missing Search Parameters:**

- `category` (company, news, research paper, github, tweet, pdf...)
- `includeDomains` / `excludeDomains`
- `startPublishedDate` / `endPublishedDate`
- `includeText` / `excludeText`
- `highlights`, `summary`

**Missing Endpoints:**

- `find_similar` - Find pages similar to a URL
- `get_contents` - Full content extraction
- `answer` - Direct Q&A with citations
- **Websets API** - Collections + enrichments

---

## Phase 2: Benchmarks Research (PENDING EXECUTION)

Research agents prepared plans for:

1. **Exa vs Competitors** - Google, Bing, Tavily, Serper, Perplexity
   - Search quality, latency, coverage, RAG performance, cost

2. **Exa in Agent Frameworks** - LangChain, LlamaIndex, CrewAI, AutoGPT
   - Integration patterns, performance comparisons, case studies

3. **Exa MCP User Feedback** - GitHub issues, Reddit, HN, Twitter
   - User satisfaction, feature requests, competitive positioning

**Files to Create:**

```
docs/benchmarks/
├── exa-vs-competitors.md       # Competitive analysis
├── agent-framework-usage.md    # Framework integrations
└── mcp-user-feedback.md        # Community feedback
```

---

## Phase 3: Implementation Plan

### Tool Categories for exa-mcp-enhanced

| Priority | Tool                 | Endpoint                  | Value Add              |
| -------- | -------------------- | ------------------------- | ---------------------- |
| P1       | `exa_search`         | /search                   | Full parameter support |
| P1       | `exa_find_similar`   | /findSimilar              | Competitive analysis   |
| P1       | `exa_get_contents`   | /contents                 | Content extraction     |
| P2       | `exa_answer`         | /answer                   | Direct Q&A + citations |
| P2       | `exa_research_start` | /research/tasks           | Async deep research    |
| P2       | `exa_research_check` | /research/tasks/{id}      | Poll research status   |
| P3       | `exa_webset_create`  | /websets                  | Create collections     |
| P3       | `exa_webset_list`    | /websets                  | List collections       |
| P3       | `exa_webset_items`   | /websets/{id}/items       | Get items              |
| P3       | `exa_webset_enrich`  | /websets/{id}/enrichments | Add emails/LinkedIn    |

### Tech Stack (Updated Dec 2025)

- **Language:** Python 3.13+ (3.13.11 stable)
- **MCP Framework:** FastMCP 2.13.3
- **HTTP Client:** httpx 0.28.1 (async)
- **Validation:** Pydantic 2.12.5
- **Testing:** pytest 9.0.2
- **Linting:** ruff 0.14.8
- **Reference SDK:** exa-py 1.16.1

### Project Structure

```
src/exa_mcp_enhanced/
├── __init__.py
├── server.py              # FastMCP entry point
├── client.py              # Exa API client wrapper
└── tools/
    ├── __init__.py
    ├── search.py          # exa_search with full params
    ├── similar.py         # exa_find_similar
    ├── contents.py        # exa_get_contents
    ├── answer.py          # exa_answer
    ├── research.py        # research_start/check
    └── websets.py         # webset_* tools
```

---

## Next Steps

1. Complete benchmark research
2. Create `docs/benchmarks/` folder with findings
3. Finalize implementation plan
4. Begin Phase 3 implementation
