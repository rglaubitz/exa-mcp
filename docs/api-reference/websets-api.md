# Exa Websets API - Comprehensive Reference

> Official Docs: https://docs.exa.ai/websets/overview

## Overview

Websets are persistent, queryable collections of web pages with enrichment capabilities. They enable batch operations for lead generation, competitive analysis, and content monitoring at scale.

---

## What Are Websets?

- **Persistent Collections**: Store search results for later access
- **Enrichments**: Add emails, LinkedIn profiles, company data to results
- **Batch Processing**: Handle thousands of results efficiently
- **Status Tracking**: Monitor collection progress

---

## Create Webset

**Endpoint:** `POST /websets`

### Request Parameters

| Parameter            | Type     | Description                        |
| -------------------- | -------- | ---------------------------------- |
| `query`              | string   | Natural language search query      |
| `num_results`        | int      | Number of results (max 10,000)     |
| `type`               | string   | Search type: auto, neural, keyword |
| `category`           | string   | Filter by category                 |
| `includeDomains`     | string[] | Only include these domains         |
| `excludeDomains`     | string[] | Exclude these domains              |
| `startPublishedDate` | string   | Published after (ISO 8601)         |
| `endPublishedDate`   | string   | Published before (ISO 8601)        |
| `includeText`        | string[] | Must contain phrases               |
| `excludeText`        | string[] | Must NOT contain phrases           |
| `contents`           | object   | Content extraction options         |

### Example

```python
import httpx

response = httpx.post(
    "https://api.exa.ai/websets",
    headers={"x-api-key": API_KEY},
    json={
        "query": "AI startups founded in 2024",
        "num_results": 500,
        "category": "company",
        "contents": {
            "text": {"maxCharacters": 3000}
        }
    }
)

webset = response.json()
print(f"Webset ID: {webset['id']}")
print(f"Status: {webset['status']}")  # "processing" or "completed"
```

### Response

```json
{
  "id": "ws_abc123",
  "status": "processing",
  "query": "AI startups founded in 2024",
  "numResults": 500,
  "createdAt": "2024-12-07T10:00:00Z"
}
```

---

## List Websets

**Endpoint:** `GET /websets`

### Parameters

| Parameter | Type   | Description                           |
| --------- | ------ | ------------------------------------- |
| `limit`   | int    | Results per page (max 100)            |
| `cursor`  | string | Pagination cursor                     |
| `status`  | string | Filter: processing, completed, failed |

### Example

```python
response = httpx.get(
    "https://api.exa.ai/websets",
    headers={"x-api-key": API_KEY},
    params={"limit": 20, "status": "completed"}
)

websets = response.json()
for ws in websets["data"]:
    print(f"{ws['id']}: {ws['query']} ({ws['itemCount']} items)")
```

---

## Get Webset Details

**Endpoint:** `GET /websets/{id}`

```python
response = httpx.get(
    f"https://api.exa.ai/websets/{webset_id}",
    headers={"x-api-key": API_KEY}
)

webset = response.json()
print(f"Status: {webset['status']}")
print(f"Items: {webset['itemCount']}")
print(f"Enrichments: {webset.get('enrichments', [])}")
```

---

## Get Webset Items

**Endpoint:** `GET /websets/{id}/items`

### Parameters

| Parameter         | Type   | Description                |
| ----------------- | ------ | -------------------------- |
| `limit`           | int    | Items per page (max 1,000) |
| `cursor`          | string | Pagination cursor          |
| `includeContents` | bool   | Include full content       |

### Example

```python
response = httpx.get(
    f"https://api.exa.ai/websets/{webset_id}/items",
    headers={"x-api-key": API_KEY},
    params={"limit": 100, "includeContents": True}
)

items = response.json()
for item in items["data"]:
    print(f"URL: {item['url']}")
    print(f"Title: {item['title']}")
    print(f"Emails: {item.get('enrichments', {}).get('emails', [])}")
```

### Response

```json
{
  "data": [
    {
      "id": "item_123",
      "url": "https://example-startup.com",
      "title": "Example AI Startup",
      "publishedDate": "2024-06-15",
      "text": "Full page content...",
      "enrichments": {
        "emails": [
          { "email": "contact@example-startup.com", "confidence": 0.95 }
        ],
        "linkedin": {
          "companyUrl": "https://linkedin.com/company/example-startup",
          "employeeCount": "50-100"
        }
      }
    }
  ],
  "hasMore": true,
  "nextCursor": "eyJjdXJzb3IiOiJhYmMxMjMifQ=="
}
```

---

## Delete Webset

**Endpoint:** `DELETE /websets/{id}`

```python
response = httpx.delete(
    f"https://api.exa.ai/websets/{webset_id}",
    headers={"x-api-key": API_KEY}
)
```

---

## Enrichments

### Add Enrichment

**Endpoint:** `POST /websets/{id}/enrichments`

### Email Enrichment

```python
response = httpx.post(
    f"https://api.exa.ai/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY},
    json={
        "type": "email",
        "options": {
            "includePersonal": False,  # Company emails only
            "verifyDeliverability": True
        }
    }
)
```

**Response includes:**

- `email` - The email address
- `type` - "company" or "personal"
- `confidence` - Score 0-1
- `source` - Where it was found

**Cost:** 1 credit per item

### LinkedIn Enrichment

```python
response = httpx.post(
    f"https://api.exa.ai/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY},
    json={
        "type": "linkedin",
        "options": {
            "includeCompany": True,
            "includeEmployees": True,
            "employeeRoles": ["CEO", "CTO", "Founder"]
        }
    }
)
```

**Response includes:**

- `companyUrl` - LinkedIn company page
- `employeeCount` - Size range
- `industry` - Industry classification
- `headquarters` - Location
- `employees` - List of matching profiles (if requested)

**Cost:** 2 credits for company, 5 credits with employees

### Company Data Enrichment

```python
response = httpx.post(
    f"https://api.exa.ai/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY},
    json={
        "type": "company_data",
        "options": {
            "includeFunding": True,
            "includeMetrics": True
        }
    }
)
```

**Response includes:**

- `totalFunding` - Amount raised
- `lastRound` - Most recent funding round
- `investors` - List of investors
- `foundedYear` - Year founded
- `revenueEstimate` - Revenue range
- `growthRate` - Growth metrics

**Cost:** 3 credits per item

---

## Check Enrichment Status

**Endpoint:** `GET /websets/{id}/enrichments`

```python
response = httpx.get(
    f"https://api.exa.ai/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY}
)

enrichments = response.json()
for enrich in enrichments["data"]:
    print(f"Type: {enrich['type']}")
    print(f"Status: {enrich['status']}")
    print(f"Progress: {enrich['processedCount']}/{enrich['totalCount']}")
```

---

## Complete Lead Gen Workflow

```python
import httpx
import time

API_KEY = "your_api_key"
BASE_URL = "https://api.exa.ai"

# 1. Create webset
webset_response = httpx.post(
    f"{BASE_URL}/websets",
    headers={"x-api-key": API_KEY},
    json={
        "query": "B2B SaaS companies using AI for customer support",
        "num_results": 200,
        "category": "company",
        "contents": {"text": {"maxCharacters": 2000}}
    }
)
webset_id = webset_response.json()["id"]

# 2. Wait for completion
while True:
    status_response = httpx.get(
        f"{BASE_URL}/websets/{webset_id}",
        headers={"x-api-key": API_KEY}
    )
    if status_response.json()["status"] == "completed":
        break
    time.sleep(5)

# 3. Add email enrichment
httpx.post(
    f"{BASE_URL}/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY},
    json={"type": "email", "options": {"includePersonal": False}}
)

# 4. Add LinkedIn enrichment
httpx.post(
    f"{BASE_URL}/websets/{webset_id}/enrichments",
    headers={"x-api-key": API_KEY},
    json={
        "type": "linkedin",
        "options": {
            "includeCompany": True,
            "includeEmployees": True,
            "employeeRoles": ["CEO", "VP Sales", "Head of Customer Success"]
        }
    }
)

# 5. Wait for enrichments
time.sleep(30)

# 6. Get enriched results
items_response = httpx.get(
    f"{BASE_URL}/websets/{webset_id}/items",
    headers={"x-api-key": API_KEY},
    params={"limit": 200, "includeContents": True}
)

leads = items_response.json()["data"]
for lead in leads:
    print(f"Company: {lead['title']}")
    print(f"URL: {lead['url']}")
    if "enrichments" in lead:
        emails = lead["enrichments"].get("emails", [])
        linkedin = lead["enrichments"].get("linkedin", {})
        print(f"Emails: {[e['email'] for e in emails]}")
        print(f"LinkedIn: {linkedin.get('companyUrl')}")
    print("---")
```

---

## Rate Limits

| Operation      | Limit        |
| -------------- | ------------ |
| Create Webset  | 100/hour     |
| Get Items      | 1,000/minute |
| Add Enrichment | 50/hour      |

---

## Error Handling

| Status Code | Description         |
| ----------- | ------------------- |
| 400         | Invalid parameters  |
| 401         | Invalid API key     |
| 404         | Webset not found    |
| 429         | Rate limit exceeded |
| 500         | Server error        |

```python
try:
    response = httpx.post(...)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # Rate limited, wait and retry
        time.sleep(60)
    elif e.response.status_code == 404:
        # Webset not found
        print("Webset does not exist")
```
