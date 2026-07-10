# Threat Feed API (Darkweb Chatters)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/threat-discovery/threat-feed-api-darkweb-chatters
> date: 2025-12-10

The Threat Feed (Darkweb Chatters) endpoint provides access to curated threat intelligence posts from dark web sources, ransomware claims, and data leak announcements. This endpoint is an **add-on package** for Threat Intelligence license holders and is governed by a separate daily quota.

---

## Endpoint

```
POST https://api.whiteintel.io/get_threat_feeds.php
```

### Headers

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |

---

## Access & Quotas

| Limit Type | Description |
|---|---|
| Auth | API key via JSON body `{ "apikey": "..." }`. |
| Plan requirement | Add-on for yearly Threat Intel license holders (3000 USD/year). |
| Daily quota | 20 calls per day. |
| Burst rate limit | Default `0.2 QPS` (1 request every 5 seconds) per account/API key; `429` on violation. |
| Method | `POST` only. |

---

## Modes

This endpoint supports **2 modes**:

1. **Posts mode** (default) — returns threat intelligence posts with filters.
2. **Taxonomy mode** — set `"taxonomy": "categories" | "industries" | "networks"` to get distinct values **with counts**, optionally filtered by date.

---

## Request Parameters

### Posts Mode Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your WhiteIntel API key. |
| `page` | integer | No | `1` | Page number for pagination (1-based). |
| `limit` | integer | No | `100` | Maximum records per page. Range: `1`–`100`. |
| `start_date` | string | No | — | Lower bound of the publication date range, format `YYYY-MM-DD` (inclusive). |
| `end_date` | string | No | — | Upper bound of the publication date range, format `YYYY-MM-DD` (inclusive). |
| `category` | string or array | No | — | Filter by post category. String or array, max 2 values. |
| `industry` | string or array | No | — | Filter by victim industry. String or array, max 2 values. |
| `network` | string or array | No | — | Filter by network of origin. String or array, no explicit cap. |
| `search` | string | No | — | Keyword or domain to search for. Min 4 characters. |

**Filter rules:**
- Dates: `start_date` and `end_date` are **inclusive** at the day level.
- Category / Industry: Exact match strings. Arrays allowed but **max 2 values** each (more than 2 returns `400`).
- Network: Exact match, array allowed (no explicit cap).
- Search: Keyword or domain. Can be empty or min 4 characters long.

### Taxonomy Mode Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your WhiteIntel API key. |
| `taxonomy` | string | Yes | — | One of `categories`, `industries`, or `networks`. |
| `start_date` | string | No | — | Optional date filter, format `YYYY-MM-DD`. |
| `end_date` | string | No | — | Optional date filter, format `YYYY-MM-DD`. |
| `limit` | integer | No | `100` | Range: `1`–`100`. |

---

## Request Examples

### Posts Mode — Domain Search

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "page": 1,
    "limit": 50,
    "search": "tesla"
  }'
```

### Posts Mode — Industry Filter

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "page": 1,
    "limit": 50,
    "industry": "Government Administration"
  }'
```

### Posts Mode — Date Range with Multiple Industries

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "page": 1,
    "limit": 100,
    "start_date": "2025-08-08",
    "end_date": "2025-09-07",
    "industry": ["Government Administration", "Education"]
  }'
```

### Posts Mode — Category + Network

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "page": 1,
    "limit": 100,
    "category": "ransomware",
    "network": ["darkweb"]
  }'
```

### Taxonomy Mode — Categories

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "taxonomy": "categories",
    "start_date": "2025-08-08",
    "end_date": "2025-09-07",
    "limit": 100
  }'
```

### Taxonomy Mode — Networks

```bash
curl -L 'https://api.whiteintel.io/get_threat_feeds.php' \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "taxonomy": "networks",
    "limit": 100
  }'
```

---

## Response Schema

### Posts Mode Response

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `mode` | string | Always `"posts"` for posts mode. |
| `remaining_threat_feed_calls` | integer | Remaining calls on the Threat Feed daily quota. |
| `results` | array | Array of post objects, sorted by `published_at DESC, id DESC`. |

#### Post Result Object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier. |
| `uuid` | string | Stable UUID. Use this for cross-referencing. |
| `published_url` | string | The original source URL where the post was observed. |
| `title` | string | Post title. |
| `category` | string | Post category (e.g. `ransomware`). |
| `network` | string | Network of origin (e.g. `darkweb`, `telegram`). |
| `published_at` | string (datetime) | Publication date in UTC. |
| `victim_organization` | string \| null | Named victim organization, when known. |
| `victim_site` | string \| null | Victim website, when known. |
| `victim_domain` | string \| null | Victim domain, when known. |
| `victim_industry` | string \| null | Victim industry classification. |
| `victim_country` | string \| null | Victim country. |
| `threat_actor_names_cached` | string \| null | Comma-separated threat actor names. |
| `tags_csv` | string \| null | Comma-separated tags. |
| `tags_norm_json` | array \| null | Normalized tags as a parsed JSON array. |
| `threat_actors_norm_json` | array \| null | Normalized threat actors as a parsed JSON array. |
| `screenshots_json` | array \| null | Screenshot URLs as a parsed JSON array. |

### Taxonomy Mode Response

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `mode` | string | Always `"taxonomy"`. |
| `taxonomy` | string | Echoes the requested taxonomy type. |
| `remaining_threat_feed_calls` | integer | Remaining calls on the Threat Feed daily quota. |
| `results` | array | Array of `{ value, cnt }` objects, sorted by count descending. |

---

## Response Examples

### Posts Mode

```json
{
  "success": true,
  "mode": "posts",
  "remaining_threat_feed_calls": 42,
  "results": [
    {
      "id": 12345,
      "uuid": "e7f23a1b-...",
      "published_url": "https://example-leak-site.onion/post/12345",
      "title": "Acme Corp — Data Leak Announcement",
      "category": "ransomware",
      "network": "darkweb",
      "published_at": "2025-09-06 12:34:56",
      "victim_organization": "Acme Corp",
      "victim_site": "acme.example",
      "victim_domain": "acme.com",
      "victim_industry": "Manufacturing",
      "victim_country": "US",
      "threat_actor_names_cached": "ActorX",
      "tags_csv": "lockbit,leak",
      "tags_norm_json": ["lockbit", "leak"],
      "threat_actors_norm_json": ["ActorX"],
      "screenshots_json": [{"url": "https://cdn.whiteintel.io/screenshots/1.png"}]
    }
  ]
}
```

### Taxonomy Mode

```json
{
  "success": true,
  "mode": "taxonomy",
  "taxonomy": "industries",
  "remaining_threat_feed_calls": 43,
  "results": [
    {"value": "Government Administration", "cnt": 2809},
    {"value": "Education", "cnt": 1835},
    {"value": "Healthcare", "cnt": 1542}
  ]
}
```

---

## Error Responses

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Malformed JSON. | `{"error": "Invalid JSON body."}` |
| `400` | `limit` out of range. | `{"success": false, "error": "Limit must be between 1 and 100."}` |
| `400` | More than 2 categories. | `{"success": false, "error": "category accepts at most 2 values."}` |
| `400` | More than 2 industries. | `{"success": false, "error": "industry accepts at most 2 values."}` |
| `400` | Invalid taxonomy value. | `{"success": false, "error": "Invalid taxonomy. Use 'categories', 'industries', or 'networks'."}` |
| `403` | Missing or invalid API key. | `{"error": "API Key is missing."}` / `{"error": "Invalid API Key."}` |
| `403` | Threat Feed add-on not enabled. | `{"error": "Threat Feed add-on is required to use this API."}` |
| `403` | Daily quota exhausted. | `{"error": "Threat Feed daily limit is reached."}` |
| `403` | Base plan not entitled. | `{"error": "API calls are only available for Enterprise and Higher tiers."}` |
| `429` | Rate limit exceeded. | `{"message": "Please wait 5 seconds between requests."}` |
| `500` | Internal server error. | `{"error": "Internal error."}` |

---

## Best Practices

- **Exact matches:** Category, industry, and network filters are exact. Use taxonomy mode first to fetch valid values.
- **Date windows:** Supplying only `start_date` returns everything from that day forward; only `end_date` returns everything up to that day.
- **Sorting:** Results are ordered by `published_at DESC, id DESC`.
- **Quota monitoring:** Track the `remaining_threat_feed_calls` field after each successful response.
- **Pagination:** Use `page` and `limit` for large result sets. Consider smaller `limit` with multiple pages for heavy consumers.

---

## Support

For technical questions, integration assistance, add-on activation, or quota increase requests, contact `info@whiteintel.io`.
