# Exa AI Search API - Comprehensive Reference

> Official Docs: https://docs.exa.ai/reference/search

## Overview

The Exa Search API provides semantic and keyword-based web search with advanced filtering, content extraction, and AI-powered features.

---

## Search Types

| Type      | Description                     | Use Case                             |
| --------- | ------------------------------- | ------------------------------------ |
| `auto`    | Automatically selects best type | General queries (default)            |
| `neural`  | Semantic/embedding search       | Finding conceptually related content |
| `keyword` | Traditional text matching       | Exact phrase matching                |

---

## Core Parameters

| Parameter       | Type   | Default  | Description                            |
| --------------- | ------ | -------- | -------------------------------------- |
| `query`         | string | required | The search query                       |
| `numResults`    | int    | 10       | Results to return (max 100 for neural) |
| `type`          | string | "auto"   | Search type: auto, neural, keyword     |
| `useAutoprompt` | bool   | false    | Enhance query with Exa's autoprompt    |

---

## Filtering Parameters

### Category Filtering

| Parameter  | Type   | Description                           |
| ---------- | ------ | ------------------------------------- |
| `category` | string | Focus search on specific content type |

**Available Categories:**

- `company` - Company websites and pages
- `research paper` - Academic papers
- `news` - News articles
- `pdf` - PDF documents
- `github` - GitHub repositories and code
- `tweet` - Twitter/X posts
- `personal site` - Personal blogs and portfolios
- `linkedin profile` - LinkedIn profiles
- `movie` - Movie information
- `song` - Music/song information
- `financial report` - Financial documents

### Domain Filtering

| Parameter        | Type     | Description                             |
| ---------------- | -------- | --------------------------------------- |
| `includeDomains` | string[] | Only include results from these domains |
| `excludeDomains` | string[] | Exclude results from these domains      |

```python
# Example: Only search tech news sites
exa.search(
    "AI startups funding",
    include_domains=["techcrunch.com", "venturebeat.com", "theverge.com"]
)
```

### Date Filtering

| Parameter            | Type   | Description                              |
| -------------------- | ------ | ---------------------------------------- |
| `startPublishedDate` | string | Only results published after (ISO 8601)  |
| `endPublishedDate`   | string | Only results published before (ISO 8601) |
| `startCrawlDate`     | string | Only results crawled after               |
| `endCrawlDate`       | string | Only results crawled before              |

```python
# Example: Last 30 days of news
from datetime import datetime, timedelta

exa.search(
    "OpenAI announcements",
    category="news",
    start_published_date=(datetime.now() - timedelta(days=30)).isoformat()
)
```

### Text Filtering

| Parameter     | Type     | Description                                                      |
| ------------- | -------- | ---------------------------------------------------------------- |
| `includeText` | string[] | Results must contain these phrases (1 string, up to 5 words)     |
| `excludeText` | string[] | Results must NOT contain these phrases (1 string, up to 5 words) |

```python
# Example: Find ML papers that mention transformers but not GPT
exa.search(
    "machine learning research",
    category="research paper",
    include_text=["transformer architecture"],
    exclude_text=["GPT"]
)
```

### Other Filters

| Parameter      | Type   | Description                                                    |
| -------------- | ------ | -------------------------------------------------------------- |
| `livecrawl`    | string | 'fallback' (use cache first) or 'preferred' (prioritize fresh) |
| `userLocation` | string | Geographic location for relevance                              |

---

## Content Options

### Text Extraction

```python
result = exa.search_and_contents(
    "AI startups",
    text=True,  # Get full text
    # Or with options:
    text={"maxCharacters": 5000}
)
```

| Option            | Type | Description              |
| ----------------- | ---- | ------------------------ |
| `maxCharacters`   | int  | Limit text length        |
| `includeHtmlTags` | bool | Preserve HTML formatting |

### Highlights (Smart Excerpts)

```python
result = exa.search_and_contents(
    "AI startups",
    highlights=True,
    # Or with options:
    highlights={
        "numSentences": 3,
        "highlightsPerUrl": 2,
        "query": "funding rounds"  # Focus highlights on this topic
    }
)
```

| Option             | Type   | Description                          |
| ------------------ | ------ | ------------------------------------ |
| `numSentences`     | int    | Sentences per highlight (default: 3) |
| `highlightsPerUrl` | int    | Number of highlights per result      |
| `query`            | string | Focus highlights on specific topic   |

### Summary (AI-Generated)

```python
result = exa.search_and_contents(
    "AI startups",
    summary=True,
    # Or with structured schema:
    summary={
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "industry": {"type": "string"},
                "funding": {"type": "string"}
            }
        }
    }
)
```

### Context String (LLM-Optimized)

```python
result = exa.search_and_contents(
    "AI startups",
    context=True,
    # Or with options:
    context={"maxCharacters": 10000}
)

# Access concatenated context
print(result.context)  # All results in one string
```

---

## Response Format

```json
{
  "requestId": "abc123",
  "autopromptString": "Enhanced query...",
  "results": [
    {
      "id": "https://example.com/article",
      "url": "https://example.com/article",
      "title": "Article Title",
      "publishedDate": "2024-01-15",
      "author": "John Doe",
      "text": "Full text content...",
      "highlights": ["Key excerpt 1", "Key excerpt 2"],
      "highlightScores": [0.95, 0.87],
      "summary": "AI-generated summary..."
    }
  ],
  "context": "Concatenated context string..."
}
```

---

## Rate Limits & Credits

| Plan | Requests/Month | Rate Limit |
| ---- | -------------- | ---------- |
| Free | 1,000          | 10/minute  |
| Pro  | 10,000+        | 100/minute |

**Credit Consumption:**

- Basic search: 1 credit
- With text: +1 credit per result
- With highlights: +0.5 credit per result
- With summary: +1 credit per result
- Livecrawl preferred: 2x credits

---

## Examples

### Basic Search

```python
result = exa.search("best Python libraries for data science")
```

### Research Papers with Date Filter

```python
result = exa.search_and_contents(
    "transformer architecture improvements",
    category="research paper",
    start_published_date="2024-01-01",
    highlights=True,
    num_results=20
)
```

### Company Research with Summaries

```python
result = exa.search_and_contents(
    "AI companies Series A funding",
    category="company",
    summary={
        "schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "funding_amount": {"type": "string"},
                "investors": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    num_results=10
)
```

### News Search with Domain Filter

```python
result = exa.search_and_contents(
    "OpenAI GPT-5",
    category="news",
    include_domains=["techcrunch.com", "wired.com", "arstechnica.com"],
    start_published_date="2024-06-01",
    text={"maxCharacters": 2000}
)
```

### GitHub Code Search

```python
result = exa.search_and_contents(
    "FastAPI authentication middleware",
    category="github",
    text=True,
    num_results=15
)
```

---

## Best Practices

1. **Use category filtering** - Dramatically improves result quality
2. **Combine date + domain filters** - For targeted news monitoring
3. **Use highlights with query** - Get topic-focused excerpts
4. **Start with fewer results** - Increase numResults only if needed
5. **Use context for RAG** - More efficient than individual texts
6. **Prefer cached content** - Use livecrawl='preferred' only when freshness is critical
