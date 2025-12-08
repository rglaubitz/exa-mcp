# Exa Answer & Research API - Comprehensive Reference

> Official Docs: https://docs.exa.ai/reference/answer

## Overview

The Answer API provides direct answers with citations, reducing hallucinations. The Research API enables comprehensive async research tasks for complex queries.

---

## Answer Endpoint

**Endpoint:** `POST /answer`

### Purpose

Get direct answers to questions with source citations, combining Exa's search with LLM generation.

### Request Parameters

| Parameter            | Type     | Default  | Description                        |
| -------------------- | -------- | -------- | ---------------------------------- |
| `query`              | string   | required | The question to answer             |
| `text`               | bool     | false    | Include full text of citations     |
| `num_results`        | int      | 5        | Number of sources to use (1-10)    |
| `type`               | string   | "auto"   | Search type: auto, neural, keyword |
| `category`           | string   | null     | Category filter                    |
| `includeDomains`     | string[] | null     | Only search these domains          |
| `excludeDomains`     | string[] | null     | Exclude these domains              |
| `startPublishedDate` | string   | null     | Filter by publish date             |
| `endPublishedDate`   | string   | null     | Filter by publish date             |

### Example

```python
from exa_py import Exa

exa = Exa(api_key)

# Basic answer
response = exa.answer("What is the latest valuation of SpaceX?")
print(response.answer)

# With full citation text
response = exa.answer(
    "What are the key features of GPT-4o?",
    text=True,
    num_results=5
)

print(f"Answer: {response.answer}")
print(f"\nSources:")
for citation in response.citations:
    print(f"- {citation.title}: {citation.url}")
    if citation.text:
        print(f"  Excerpt: {citation.text[:200]}...")
```

### Response Format

```json
{
  "answer": "SpaceX was valued at $350 billion in December 2024...",
  "citations": [
    {
      "id": "https://ft.com/content/spacex-valuation",
      "url": "https://ft.com/content/spacex-valuation",
      "title": "SpaceX valued at $350bn in employee share sale",
      "publishedDate": "2024-12-01",
      "author": "Financial Times",
      "text": "Full text content if text=True..."
    }
  ]
}
```

### Citation Structure

Each citation includes:

- `id` - Unique identifier (typically URL)
- `url` - Source URL
- `title` - Page title
- `publishedDate` - Publication date
- `author` - Author if available
- `text` - Full text (only if `text=True`)

---

## Streaming Answer

For real-time streaming responses:

```python
stream = exa.stream_answer(
    "Explain the transformer architecture",
    text=True
)

for chunk in stream:
    if chunk.content:
        print(chunk.content, end="", flush=True)
    if chunk.citations:
        for citation in chunk.citations:
            print(f"\n[Source: {citation.url}]")
```

---

## Research API

### Overview

The Research API performs comprehensive, multi-step research tasks asynchronously. It's designed for complex queries requiring extensive analysis.

### Create Research Task

**Endpoint:** `POST /research/tasks`

#### Parameters

| Parameter       | Type   | Default        | Description                                 |
| --------------- | ------ | -------------- | ------------------------------------------- |
| `instructions`  | string | required       | Research instructions                       |
| `model`         | string | "exa-research" | Model: "exa-research" or "exa-research-pro" |
| `output_schema` | object | null           | JSON Schema for structured output           |
| `infer_schema`  | bool   | false          | Let LLM generate schema                     |

#### Models

| Model              | Speed    | Use Case                           |
| ------------------ | -------- | ---------------------------------- |
| `exa-research`     | 15-45s   | Most queries, faster turnaround    |
| `exa-research-pro` | 45s-2min | Complex topics, more comprehensive |

### Example: Basic Research

```python
# Create task
task = exa.research.create_task(
    instructions="What are the top 5 AI startups that raised Series B in 2024? Include funding amount and key investors.",
    model="exa-research"
)

print(f"Task ID: {task.id}")

# Poll for results
result = exa.research.poll_task(
    task.id,
    poll_interval=2,
    max_wait_time=120
)

print(f"Status: {result.status}")
print(f"Data: {result.data}")
print(f"Citations: {result.citations}")
```

### Example: Structured Output

```python
# Define output schema
schema = {
    "type": "object",
    "properties": {
        "companies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "funding_amount": {"type": "string"},
                    "investors": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": {"type": "string"}
                }
            }
        },
        "total_funding": {"type": "string"},
        "key_trends": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

task = exa.research.create_task(
    instructions="Research AI startups that raised Series B in 2024",
    output_schema=schema,
    model="exa-research-pro"
)

result = exa.research.poll_task(task.id)
print(result.data)  # Structured JSON matching schema
```

### Get Task Status

**Endpoint:** `GET /research/tasks/{id}`

```python
task = exa.research.get_task(task_id)

print(f"Status: {task.status}")  # "running", "completed", "failed"
print(f"Instructions: {task.instructions}")

if task.status == "completed":
    print(f"Results: {task.data}")
    print(f"Citations: {task.citations}")
```

### Response Format

```json
{
  "id": "task_abc123",
  "status": "completed",
  "instructions": "Research AI startups...",
  "schema": {...},
  "data": {
    "companies": [
      {
        "name": "Anthropic",
        "funding_amount": "$450M",
        "investors": ["Google", "Spark Capital"]
      }
    ]
  },
  "citations": {
    "companies": [
      {
        "id": "https://techcrunch.com/anthropic-series-b",
        "url": "https://techcrunch.com/anthropic-series-b",
        "title": "Anthropic raises $450M Series B",
        "snippet": "Anthropic announced today..."
      }
    ]
  }
}
```

### List Tasks

**Endpoint:** `GET /research/tasks`

```python
# List all tasks
response = exa.research.list_tasks(limit=20)

for task in response["data"]:
    print(f"{task['id']}: {task['status']} - {task['instructions'][:50]}...")

# Pagination
if response["hasMore"]:
    next_page = exa.research.list_tasks(cursor=response["nextCursor"])
```

---

## Citations in Research

Research results include citations grouped by output field:

```json
{
  "data": {
    "funding_amount": "$350B",
    "company_description": "..."
  },
  "citations": {
    "funding_amount": [{ "url": "...", "title": "...", "snippet": "..." }],
    "company_description": [{ "url": "...", "title": "...", "snippet": "..." }]
  }
}
```

Each citation maps to the field it supports, enabling verification.

---

## Error Handling

```python
try:
    task = exa.research.create_task(instructions="...")
    result = exa.research.poll_task(task.id, max_wait_time=120)

    if result.status == "failed":
        print(f"Research failed: {result.error}")

except Exception as e:
    print(f"Error: {e}")
```

### Common Errors

| Error          | Cause                                 | Solution                                 |
| -------------- | ------------------------------------- | ---------------------------------------- |
| Timeout        | Research took too long                | Increase max_wait_time or simplify query |
| Invalid schema | Schema doesn't match JSON Schema spec | Validate schema format                   |
| Rate limited   | Too many concurrent tasks             | Wait and retry                           |

---

## Best Practices

1. **Use structured schemas** for consistent output format
2. **Choose the right model**:
   - `exa-research` for most queries
   - `exa-research-pro` for comprehensive analysis
3. **Set reasonable timeouts** - Complex queries take longer
4. **Handle failures gracefully** - Research tasks can fail
5. **Use polling with backoff** - Don't hammer the API

---

## Cost

| Operation           | Credits    |
| ------------------- | ---------- |
| Answer (basic)      | 5 credits  |
| Answer (with text)  | 10 credits |
| Research (standard) | 20 credits |
| Research (pro)      | 50 credits |
