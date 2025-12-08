# Exa Python SDK Specification

> Source: https://docs.exa.ai/sdks/python-sdk-specification

## Getting Started

```bash
pip install exa_py
```

```python
from exa_py import Exa
import os

exa = Exa(os.getenv('EXA_API_KEY'))
```

---

## Core Methods

### `search` Method

Perform an Exa search given an input query and retrieve a list of relevant results as links.

#### Input Example

```python
# Basic search
result = exa.search(
  "hottest AI startups",
  num_results=2
)

# Deep search with query variations
deep_result = exa.search(
  "blog post about AI",
  type="deep",
  additional_queries=["AI blogpost", "machine learning blogs"],
  num_results=5
)
```

#### Input Parameters

| Parameter            | Type                                         | Description                                                                                                                       | Default  |
| -------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------- |
| query                | str                                          | The input query string.                                                                                                           | Required |
| additional_queries   | Optional[List[str]]                          | Additional query variations for deep search. Only works with type="deep".                                                         | None     |
| num_results          | Optional[int]                                | Number of search results to return. Max 100 for "neural".                                                                         | 10       |
| include_domains      | Optional[List[str]]                          | List of domains to include in the search.                                                                                         | None     |
| exclude_domains      | Optional[List[str]]                          | List of domains to exclude in the search.                                                                                         | None     |
| start_crawl_date     | Optional[str]                                | Results only include links **crawled** after this date.                                                                           | None     |
| end_crawl_date       | Optional[str]                                | Results only include links **crawled** before this date.                                                                          | None     |
| start_published_date | Optional[str]                                | Results only include links with **published** date after this date.                                                               | None     |
| end_published_date   | Optional[str]                                | Results only include links with **published** date before this date.                                                              | None     |
| type                 | Optional[str]                                | The type of search: "auto", "neural", "fast", or "deep".                                                                          | "auto"   |
| category             | Optional[str]                                | Data category: company, research paper, news, linkedin profile, github, tweet, movie, song, personal site, pdf, financial report. | None     |
| include_text         | Optional[List[str]]                          | Strings that must be present in webpage text. Max 1 string, up to 5 words.                                                        | None     |
| exclude_text         | Optional[List[str]]                          | Strings that must NOT be present in webpage text. Max 1 string, up to 5 words.                                                    | None     |
| context              | Union[ContextContentsOptions, Literal[True]] | If true, concatenates results into a context string.                                                                              | None     |

---

### `search_and_contents` Method

Perform search and retrieve results with full text and/or highlights.

#### Input Example

```python
# Search with full text content
result_with_text = exa.search_and_contents(
    "AI in healthcare",
    text=True,
    num_results=2
)

# Search with highlights
result_with_highlights = exa.search_and_contents(
    "AI in healthcare",
    highlights=True,
    num_results=2
)

# Search with structured summary schema
company_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Company Information",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "industry": {"type": "string"},
        "foundedYear": {"type": "number"},
        "keyProducts": {"type": "array", "items": {"type": "string"}},
        "competitors": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["name", "industry"]
}

result_with_structured_summary = exa.search_and_contents(
    "OpenAI company information",
    summary={"schema": company_schema},
    category="company",
    num_results=3
)
```

#### Additional Parameters (beyond search)

| Parameter  | Type                                            | Description                               | Default |
| ---------- | ----------------------------------------------- | ----------------------------------------- | ------- |
| text       | Union[TextContentsOptions, Literal[True]]       | Include full text of content in results.  | None    |
| highlights | Union[HighlightsContentsOptions, Literal[True]] | Include highlights of content in results. | None    |
| summary    | Dict with schema                                | Extract structured data per JSON schema   | None    |

---

### `find_similar` Method

Find pages similar to a given URL.

#### Input Example

```python
similar_results = exa.find_similar(
    "miniclip.com",
    num_results=2,
    exclude_source_domain=True
)
```

#### Input Parameters

| Parameter             | Type                | Description                                     | Default  |
| --------------------- | ------------------- | ----------------------------------------------- | -------- |
| url                   | str                 | URL of the webpage to find similar results for. | Required |
| num_results           | Optional[int]       | Number of similar results to return.            | None     |
| include_domains       | Optional[List[str]] | Domains to include in the search.               | None     |
| exclude_domains       | Optional[List[str]] | Domains to exclude from the search.             | None     |
| start_crawl_date      | Optional[str]       | Only links crawled after this date.             | None     |
| end_crawl_date        | Optional[str]       | Only links crawled before this date.            | None     |
| start_published_date  | Optional[str]       | Only links published after this date.           | None     |
| end_published_date    | Optional[str]       | Only links published before this date.          | None     |
| exclude_source_domain | Optional[bool]      | If true, excludes results from the same domain. | None     |
| category              | Optional[str]       | Data category to focus on.                      | None     |

---

### `find_similar_and_contents` Method

Find similar pages with full text/highlights.

```python
similar_with_text = exa.find_similar_and_contents(
    "https://example.com/article",
    text=True,
    highlights=True,
    num_results=2
)
```

---

### `answer` Method

Generate an answer to a query using Exa's search and LLM capabilities.

#### Input Example

```python
response = exa.answer("What is the capital of France?")
print(response.answer)       # "Paris"
print(response.citations)    # list of citations

# With full text of citations
response_with_text = exa.answer(
    "What is the capital of France?",
    text=True
)
print(response_with_text.citations[0].text)
```

#### Parameters

| Parameter | Type           | Description                         | Default  |
| --------- | -------------- | ----------------------------------- | -------- |
| query     | str            | The question to answer.             | Required |
| text      | Optional[bool] | Include full text of each citation. | False    |

#### Response

| Field     | Type               | Description                           |
| --------- | ------------------ | ------------------------------------- |
| answer    | str                | The generated answer text             |
| citations | List[AnswerResult] | Citations used to generate the answer |

---

### `stream_answer` Method

Streaming answer generation.

```python
stream = exa.stream_answer("What is the capital of France?", text=True)

for chunk in stream:
    if chunk.content:
        print("Partial answer:", chunk.content)
    if chunk.citations:
        for citation in chunk.citations:
            print("Citation found:", citation.url)
```

---

## Research API

### `research.create_task` Method

Create an asynchronous research task.

```python
instructions = "What is the latest valuation of SpaceX?"
schema = {
    "type": "object",
    "properties": {
        "valuation": {"type": "string"},
        "date": {"type": "string"},
        "source": {"type": "string"}
    }
}

task = exa.research.create_task(
    instructions=instructions,
    output_schema=schema
)

# Or let model infer schema
simple_task = exa.research.create_task(
    instructions="What are the main benefits of meditation?",
    infer_schema=True
)
```

#### Parameters

| Parameter     | Type           | Description                          | Default        |
| ------------- | -------------- | ------------------------------------ | -------------- |
| instructions  | str            | Natural language instructions.       | Required       |
| model         | Optional[str]  | "exa-research" or "exa-research-pro" | "exa-research" |
| output_schema | Optional[Dict] | JSON Schema for output structure.    | None           |
| infer_schema  | Optional[bool] | Let LLM generate output schema.      | None           |

---

### `research.get_task` Method

Get status and results of a research task.

```python
task = exa.research.get_task(task_id)
print(f"Status: {task.status}")  # "running", "completed", "failed"

if task.status == "completed":
    print(f"Results: {task.data}")
    print(f"Citations: {task.citations}")
```

---

### `research.poll_task` Method

Poll until task completes.

```python
result = exa.research.poll_task(
    task.id,
    poll_interval=2,      # seconds between polls
    max_wait_time=300     # max seconds to wait
)
```

---

### `research.list_tasks` Method

List all research tasks with pagination.

```python
response = exa.research.list_tasks(limit=10)
if response['hasMore']:
    next_page = exa.research.list_tasks(cursor=response['nextCursor'])
```

---

## Available Categories

- company
- research paper
- news
- linkedin profile
- github
- tweet
- movie
- song
- personal site
- pdf
- financial report

---

## Search Types

| Type   | Description                               |
| ------ | ----------------------------------------- |
| auto   | Balanced search (default)                 |
| neural | Semantic search, max 100 results          |
| fast   | Quick results                             |
| deep   | Comprehensive search with query expansion |
