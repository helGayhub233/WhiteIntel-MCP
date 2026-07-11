# Threat Feed API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/threat-discovery/threat-feed-api
> date: 2026-05-10

The Threat Feeds endpoint provides programmatic access to the Whiteintel threat intelligence feed — curated dark web posts, ransomware claims, data leak announcements, and a parallel public news stream covering the broader threat landscape.

This endpoint operates in three modes selected via request parameters:

- **Posts mode** — returns curated intelligence posts with structured metadata (category, industry, victim, threat actors, screenshots).
- **Public news mode** — returns public-source news articles with summaries.
- **Taxonomy mode** — returns the available filter values (categories, industries, networks) and their record counts, useful for populating filter UIs.

This endpoint is governed by a separate **Threat Feed add-on** entitlement and a dedicated daily quota counter that is independent from the standard API daily quota.

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

## Authentication

Authentication is performed via an API key passed in the request body. Your API key can be retrieved from either the **Organizations** page or the **Profile** page on the Whiteintel platform.

```json
{
  "apikey": "YOUR_API_KEY"
}
```

Requests without a valid API key return `403 Forbidden`.

---

## Access Requirements

Access to this endpoint requires the **Threat Feed add-on** to be enabled on the API key. This add-on is provisioned separately from the standard subscription tier. API keys without the add-on receive a `403 Forbidden` response.

To enable the Threat Feed add-on on your account, contact `info@whiteintel.io`.

---

## Rate Limits and Quotas

| Limit Type | Description |
|---|---|
| Request throttle | Default `0.2 QPS` (1 request every 5 seconds) per account/API key. Exceeding this returns `429 Too Many Requests`. |
| Threat Feed daily quota | A dedicated daily quota gates access to this endpoint, tracked separately from the standard API daily quota. Remaining quota is returned in every successful response under `remaining_threat_feed_calls`. |

Each successful call consumes one Threat Feed quota credit, regardless of mode. Once the daily quota is exhausted, requests return a quota-exceeded message until the counter resets.

---

## Modes

The endpoint selects between modes based on which parameters are present:

| Mode | Condition | Description |
|---|---|---|
| Taxonomy | `taxonomy` parameter is supplied (`categories`, `industries`, or `networks`). | Distinct values with record counts. |
| Public news | `mode` parameter is set to `public_news`. | Public-source news articles. |
| Posts | Default. Used when neither of the above is set. | Curated intelligence posts. |

If both `taxonomy` and `mode` are supplied, taxonomy mode takes precedence.

---

## Request Parameters

### Common Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `limit` | integer | No | `100` | Maximum number of records to return. Allowed range: `1`–`100`. |
| `page` | integer | No | `1` | Page number for pagination (Posts and Public News modes only; ignored for Taxonomy). |
| `start_date` | string | No | — | Lower bound of the publication date range, format `YYYY-MM-DD` (inclusive). |
| `end_date` | string | No | — | Upper bound of the publication date range, format `YYYY-MM-DD` (inclusive). |

### Posts Mode Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | string | No | — | Free-text search across title, content, and victim domain. Minimum 4 characters when supplied. |
| `category` | string or array | No | — | Filter by post category. Up to 2 values supported. |
| `industry` | string or array | No | — | Filter by victim industry. Up to 2 values supported. |
| `network` | string or array | No | — | Filter by network of origin. Multiple values supported. |

### Public News Mode Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `mode` | string | Yes | — | Must be set to `public_news`. |
| `search` | string | No | — | Free-text search across title, summary, and AI summary. Minimum 4 characters when supplied. |

### Taxonomy Mode Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `taxonomy` | string | Yes | — | One of `categories`, `industries`, or `networks`. |

### Notes

- `category` / `industry` accept either a single string or an array. When multiple values are supplied, results match any of them (logical OR). The maximum of 2 values per filter prevents excessively broad queries.
- `network` has no explicit cap on values.
- `search` requires a minimum of 4 characters when supplied.
- **Date filters** are independent of one another — either may be supplied alone.

---

## Request Examples

### Posts mode (default)

```bash
curl -X POST https://api.whiteintel.io/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "page": 1,
    "limit": 50
  }'
```

### Posts mode with filters

```bash
curl -X POST https://api.whiteintel.io/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "category": ["ransomware", "data-leak"],
    "industry": "Manufacturing",
    "network": ["darkweb", "telegram"],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "limit": 100
  }'
```

### Public news mode

```bash
curl -X POST https://api.whiteintel.io/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "mode": "public_news",
    "search": "ransomware healthcare",
    "limit": 50
  }'
```

### Taxonomy mode

```bash
curl -X POST https://api.whiteintel.io/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "taxonomy": "categories"
  }'
```

---

## Response Schema

### Outer Structure

Every successful response uses the same outer structure:

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `mode` | string | The mode that produced this response (`posts`, `public_news`, or `taxonomy`). |
| `taxonomy` | string | Present only in taxonomy mode. Echoes the requested taxonomy. |
| `remaining_threat_feed_calls` | integer | Remaining requests on the Threat Feed daily quota. |
| `results` | array | The mode-specific result payload. |

### Posts Mode Result Object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier of the post. |
| `uuid` | string | Stable UUID for the post. Use this for cross-referencing rather than `id`. |
| `published_url` | string | The original URL where the post was observed. |
| `title` | string | Post title. |
| `category` | string | Post category (e.g. `ransomware`, `data-leak`). |
| `network` | string | Network of origin (e.g. `darkweb`, `telegram`). |
| `published_at` | string (datetime) | Publication date of the post. |
| `description` | string | Full text content of the post. |
| `victim_organization` | string \| null | Named victim organization, when known. |
| `victim_site` | string \| null | Victim website, when known. |
| `victim_domain` | string \| null | Victim domain, when known. |
| `victim_industry` | string \| null | Victim industry classification, when known. |
| `victim_country` | string \| null | Victim country, when known. |
| `threat_actor_names_cached` | string \| null | Comma-separated string of associated threat actor names. |
| `tags_csv` | string \| null | Comma-separated string of tags. |
| `tags_norm_json` | array \| string \| null | Normalized tags as a parsed JSON array. |
| `threat_actors_norm_json` | array \| string \| null | Normalized threat actors as a parsed JSON array. |
| `screenshots_json` | array \| string \| null | Screenshot URLs as a parsed JSON array. |

### Public News Result Object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier of the news article. |
| `source` | string | The publication or source name. |
| `title` | string | Article title. |
| `summary` | string | Original article summary. |
| `ai_summary` | string \| null | AI-generated summary, when available. |
| `link` | string | URL to the original article. |
| `published_at` | string (datetime) | Publication date. |
| `tags` | string \| null | Comma-separated tags, when available. |

### Taxonomy Mode Result Object

| Field | Type | Description |
|---|---|---|
| `value` | string | The taxonomy value (category name, industry name, or network name). |
| `cnt` | integer | Number of posts associated with this value within the optional date range. |

Results are sorted by count descending, then alphabetically.

---

## Response Examples

### Posts mode

```json
{
  "success": true,
  "mode": "posts",
  "remaining_threat_feed_calls": 982,
  "results": [
    {
      "id": 184729,
      "uuid": "8c4b1a2e-7f3d-4e5a-9b1c-0d2e3f4a5b6c",
      "published_url": "https://example-leak-site.onion/post/12345",
      "title": "Acme Industries — 240GB data dump",
      "category": "data-leak",
      "network": "darkweb",
      "published_at": "2025-11-14 08:23:11",
      "description": "Full text of the leak announcement...",
      "victim_organization": "Acme Industries",
      "victim_site": "https://acme.com",
      "victim_domain": "acme.com",
      "victim_industry": "Manufacturing",
      "victim_country": "United States",
      "threat_actor_names_cached": "RansomGroup1, AffiliateAlpha",
      "tags_csv": "240gb, sql, financial",
      "tags_norm_json": ["240gb", "sql", "financial"],
      "threat_actors_norm_json": ["RansomGroup1", "AffiliateAlpha"],
      "screenshots_json": [
        "https://cdn.whiteintel.io/screenshots/abc123.png",
        "https://cdn.whiteintel.io/screenshots/def456.png"
      ]
    }
  ]
}
```

### Public news mode

```json
{
  "success": true,
  "mode": "public_news",
  "remaining_threat_feed_calls": 981,
  "results": [
    {
      "id": 50182,
      "source": "Example Security News",
      "title": "Healthcare provider confirms ransomware incident",
      "summary": "A regional healthcare provider disclosed a ransomware incident affecting patient records...",
      "ai_summary": "Healthcare provider hit by ransomware; patient data potentially exposed; investigation ongoing.",
      "link": "https://example-news.com/articles/healthcare-ransomware-2025-11",
      "published_at": "2025-11-13 14:00:00",
      "tags": "ransomware, healthcare, breach"
    }
  ]
}
```

### Taxonomy mode

```json
{
  "success": true,
  "mode": "taxonomy",
  "taxonomy": "categories",
  "remaining_threat_feed_calls": 980,
  "results": [
    { "value": "ransomware", "cnt": 8412 },
    { "value": "data-leak", "cnt": 5219 },
    { "value": "initial-access", "cnt": 1843 }
  ]
}
```

---

## Error Responses

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `400` | Malformed JSON body. | `{"error": "Invalid JSON body."}` |
| `400` | Invalid type for `category`, `industry`, or `network`. | `{"success": false, "error": "category must be a string or array of strings."}` |
| `400` | Too many values for `category` or `industry`. | `{"success": false, "error": "category accepts at most 2 values."}` |
| `400` | Search string shorter than 4 characters. | `{"success": false, "error": "Search must be at least 4 characters long."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Threat Feed add-on not enabled. | `{"error": "Threat Feed add-on is required to use this API."}` |
| `403` | Threat Feed daily quota exhausted. | `{"error": "Threat Feed daily limit is reached."}` |
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be between 1 and 100."}` |
| `200` | Invalid taxonomy value. | `{"success": false, "error": "Invalid taxonomy. Use 'categories', 'industries', or 'networks'."}` |
| `200` | Threat Feed quota exhausted between pre-check and increment. | `{"success": false, "message": "Daily Threat Feed API request limit exceeded."}` |

---

## Best Practices

- **Filter discovery:** Use taxonomy mode to populate dropdowns and filter UIs with actual values present in the dataset.
- **Incremental ingestion:** Combine date filters with pagination for incremental sync.
- **Search behavior:** The `search` field performs a multi-word match across searchable fields. For exact domain match, supply a single domain targeting `victim_domain`.
- **Mode separation:** Posts and public news are distinct datasets. A workflow needing both should issue two calls.
- **JSON sub-fields:** `tags_norm_json`, `threat_actors_norm_json`, and `screenshots_json` are returned as parsed JSON arrays when valid.
- **Quota separation:** The Threat Feed quota is independent from the standard API daily quota.
- **Quota monitoring:** Track the `remaining_threat_feed_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, Threat Feed add-on activation, or quota increase requests, contact `info@whiteintel.io`.
