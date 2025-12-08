# Exa find_similar & get_contents API - Comprehensive Reference

> Official Docs: https://docs.exa.ai/reference/find-similar

## Overview

- **find_similar**: Discover web pages semantically similar to a given URL
- **get_contents**: Extract full content from specific URLs

---

## find_similar Endpoint

**Endpoint:** `POST /findSimilar`

### Purpose

Find web pages that are semantically similar to a reference URL. Useful for:

- Competitive analysis (find similar companies)
- Content discovery (find related articles)
- Research expansion (find similar papers)

### Request Parameters

| Parameter             | Type     | Default  | Description                             |
| --------------------- | -------- | -------- | --------------------------------------- |
| `url`                 | string   | required | Reference URL to find similar pages for |
| `numResults`          | int      | 10       | Number of results (max 100)             |
| `category`            | string   | null     | Filter by category                      |
| `excludeSourceDomain` | bool     | false    | Exclude results from same domain        |
| `includeDomains`      | string[] | null     | Only include these domains              |
| `excludeDomains`      | string[] | null     | Exclude these domains                   |
| `startPublishedDate`  | string   | null     | Published after (ISO 8601)              |
| `endPublishedDate`    | string   | null     | Published before (ISO 8601)             |
| `startCrawlDate`      | string   | null     | Crawled after                           |
| `endCrawlDate`        | string   | null     | Crawled before                          |

### Basic Example

```python
from exa_py import Exa

exa = Exa(api_key)

# Find pages similar to a company website
similar = exa.find_similar(
    "https://anthropic.com",
    num_results=10,
    exclude_source_domain=True  # Don't return anthropic.com pages
)

for result in similar.results:
    print(f"{result.title}: {result.url}")
```

### With Content Extraction

```python
# Find similar with full content
similar = exa.find_similar_and_contents(
    "https://openai.com/research",
    text=True,
    highlights=True,
    num_results=5,
    category="research paper"
)

for result in similar.results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Highlights: {result.highlights}")
    print("---")
```

### Competitive Analysis Example

```python
# Find competitors to a SaaS company
competitors = exa.find_similar_and_contents(
    "https://notion.so",
    num_results=20,
    exclude_source_domain=True,
    category="company",
    text={"maxCharacters": 2000}
)

for result in competitors.results:
    print(f"Competitor: {result.title}")
    print(f"URL: {result.url}")
    print(f"Description: {result.text[:500]}...")
```

### Response Format

```json
{
  "requestId": "abc123",
  "results": [
    {
      "id": "https://similar-company.com",
      "url": "https://similar-company.com",
      "title": "Similar Company - AI Safety Research",
      "publishedDate": "2024-01-15",
      "author": null,
      "text": "Full text if requested...",
      "highlights": ["Key excerpt 1", "Key excerpt 2"],
      "highlightScores": [0.92, 0.87]
    }
  ]
}
```

---

## get_contents Endpoint

**Endpoint:** `POST /contents`

### Purpose

Extract full content from specific URLs. Useful for:

- Getting full article text from search results
- Extracting content from known URLs
- Batch content extraction

### Request Parameters

| Parameter    | Type        | Default    | Description                     |
| ------------ | ----------- | ---------- | ------------------------------- |
| `ids`        | string[]    | required   | Array of URLs (max 100)         |
| `text`       | bool/object | null       | Extract full text               |
| `highlights` | bool/object | null       | Extract smart excerpts          |
| `summary`    | bool/object | null       | Generate AI summary             |
| `livecrawl`  | string      | "fallback" | "fallback", "always", "never"   |
| `subpages`   | int         | 0          | Additional pages to crawl (0-5) |

### Basic Example

```python
# Get content from specific URLs
contents = exa.get_contents(
    ids=[
        "https://techcrunch.com/article-1",
        "https://wired.com/article-2",
        "https://arstechnica.com/article-3"
    ],
    text=True
)

for result in contents.results:
    print(f"Title: {result.title}")
    print(f"Text: {result.text[:1000]}...")
```

### With Highlights

```python
# Get content with focused highlights
contents = exa.get_contents(
    ids=["https://example.com/article"],
    highlights={
        "numSentences": 3,
        "highlightsPerUrl": 5,
        "query": "AI safety research"  # Focus highlights on this topic
    }
)

for result in contents.results:
    print(f"Title: {result.title}")
    for i, highlight in enumerate(result.highlights):
        score = result.highlight_scores[i]
        print(f"  [{score:.2f}] {highlight}")
```

### With Summary

```python
# Get content with AI-generated summary
contents = exa.get_contents(
    ids=["https://example.com/long-article"],
    summary=True,
    # Or with focused query:
    summary={"query": "What are the main findings?"}
)

for result in contents.results:
    print(f"Title: {result.title}")
    print(f"Summary: {result.summary}")
```

### Live Crawling Options

| Value        | Description                                       |
| ------------ | ------------------------------------------------- |
| `"fallback"` | Use cache first, crawl if not available (default) |
| `"always"`   | Always fetch fresh content (2x credits)           |
| `"never"`    | Only use cached content                           |

```python
# Force fresh content
contents = exa.get_contents(
    ids=["https://example.com/live-page"],
    text=True,
    livecrawl="always"
)
```

### Subpages Crawling

```python
# Get company page + about/pricing pages
contents = exa.get_contents(
    ids=["https://startup.com"],
    text=True,
    subpages=3  # Also crawl up to 3 linked pages
)

# Returns main page + discovered subpages
for result in contents.results:
    print(f"Page: {result.url}")
```

---

## Content Extraction Options

### Text Options

```python
# Full text with options
text_options = {
    "maxCharacters": 5000,      # Limit text length
    "includeHtmlTags": False    # Strip HTML (default)
}

result = exa.get_contents(
    ids=["https://example.com"],
    text=text_options
)
```

### Highlights Options

```python
# Customized highlights
highlights_options = {
    "numSentences": 3,        # Sentences per highlight
    "highlightsPerUrl": 5,    # Number of highlights
    "query": "specific topic" # Focus highlights on topic
}

result = exa.get_contents(
    ids=["https://example.com"],
    highlights=highlights_options
)
```

### Summary Options

```python
# Focused summary
summary_options = {
    "query": "What is the main argument?"
}

result = exa.get_contents(
    ids=["https://example.com"],
    summary=summary_options
)
```

---

## Combined Workflow Example

```python
# 1. Search for articles
search_results = exa.search(
    "transformer architecture improvements 2024",
    category="research paper",
    num_results=20
)

# 2. Get IDs of interesting results
urls = [r.url for r in search_results.results[:5]]

# 3. Get full content with highlights focused on implementation
contents = exa.get_contents(
    ids=urls,
    text={"maxCharacters": 10000},
    highlights={
        "numSentences": 3,
        "highlightsPerUrl": 3,
        "query": "implementation details"
    },
    summary={"query": "What are the key contributions?"}
)

for result in contents.results:
    print(f"\n=== {result.title} ===")
    print(f"Summary: {result.summary}")
    print(f"\nKey excerpts:")
    for h in result.highlights:
        print(f"  - {h}")
```

---

## Comparison: find_similar vs get_contents

| Feature         | find_similar   | get_contents    |
| --------------- | -------------- | --------------- |
| Input           | Single URL     | Multiple URLs   |
| Purpose         | Discovery      | Extraction      |
| Search          | Yes (semantic) | No              |
| Content         | Optional       | Primary purpose |
| Category filter | Yes            | No              |
| Domain filter   | Yes            | No              |
| Date filter     | Yes            | No              |
| Subpages        | No             | Yes             |

---

## Rate Limits & Credits

| Operation                         | Credits          |
| --------------------------------- | ---------------- |
| find_similar (basic)              | 1 credit         |
| find_similar + text               | 2 credits/result |
| get_contents (basic)              | 1 credit/URL     |
| get_contents + text               | 2 credits/URL    |
| get_contents + livecrawl="always" | 2x credits       |
| subpages                          | 1 credit/subpage |

---

## Error Handling

```python
try:
    contents = exa.get_contents(ids=urls, text=True)
except Exception as e:
    print(f"Error: {e}")

# Check for failed URLs in response
for result in contents.results:
    if hasattr(result, 'error'):
        print(f"Failed: {result.url} - {result.error}")
```

### Common Errors

| Error               | Cause                         | Solution              |
| ------------------- | ----------------------------- | --------------------- |
| URL not found       | Page doesn't exist or blocked | Check URL validity    |
| Rate limited        | Too many requests             | Implement backoff     |
| Content unavailable | Page behind paywall/login     | Try livecrawl or skip |
