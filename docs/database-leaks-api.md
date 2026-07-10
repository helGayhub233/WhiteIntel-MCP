# Database Leaks API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/database-leaks-api
> date: 2026-05-10

The Database Leaks endpoint returns corporate credentials exposed in third-party database breaches for a target domain. Unlike the infostealer-sourced leak endpoints, this dataset is sourced from publicly disclosed breach databases — for example, large platform breaches where account dumps included corporate email addresses.

Results are grouped by breach source, with each group carrying breach-level metadata (breach date, description, exposed data fields) alongside the affected account records (email, plaintext password where available, and hashed password where available).

This endpoint is intended for organizational exposure assessments, vendor risk reviews, and ongoing monitoring of credential leakage from breaches outside your own systems.

---

## Endpoint

```
POST https://api.whiteintel.io/get_third_party_db_leaks.php
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

This endpoint is available to **Enterprise** and **Threat Intelligence** subscription tiers. Lower tiers will receive a `403 Forbidden` response indicating the dataset is not available on the current license.

---

## Rate Limits and Quotas

| Limit Type | Description |
|---|---|
| Request throttle | Default `0.2 QPS` (1 request every 5 seconds) per account/API key. Exceeding this returns `429 Too Many Requests`. |
| Daily quota | Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. |

Once the daily quota is exhausted, requests return `403 Forbidden` with a quota-exceeded message until the counter resets.

Empty result responses do not consume a daily quota credit.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The target corporate domain (e.g. `acme.com`). The endpoint will return database breach records associated with this domain. |
| `limit` | integer | No | `500` | Maximum number of account records to return across all breach groups. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |
| `start_date` | string | No | — | Lower bound of the breach date range, format `YYYY-MM-DD`. Must be paired with `end_date`. |
| `end_date` | string | No | — | Upper bound of the breach date range, format `YYYY-MM-DD`. Must be paired with `start_date`. |

### Notes on `query`

Supply the registrable corporate domain (for example `acme.com`). Subdomains are normalized to their registrable domain before lookup.

### Notes on date filters

Both `start_date` and `end_date` must be supplied together. The date range is matched against the **breach date** (when the breach occurred), not when the records were ingested into the platform.

### Notes on `limit`

The `limit` parameter caps the total number of **account records** returned, summed across all breach groups in the response. Pagination flows across breach groups in a stable order.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_third_party_db_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "acme.com",
    "limit": 500,
    "page": 1,
    "start_date": "2010-01-01",
    "end_date": "2025-12-31"
  }'
```

---

## Response Schema

### Success Response

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `remaining_daily_calls` | integer | Remaining requests on the daily quota for the current API key. |
| `results` | array | Array of breach group objects. |

### Breach Group Object

| Field | Type | Description |
|---|---|---|
| `database_name` | string | The name of the breach source (e.g. the breached service or dataset name). |
| `breach_date` | string (date) \| null | The date the breach occurred, when known. |
| `breach_description` | string \| null | Description of the breach. |
| `data_fields` | string \| null | The categories of data exposed in the breach (e.g. emails, passwords, names). |
| `total` | integer | Total number of records in this breach group for the queried domain (across all pages). |
| `page` | integer | Echo of the requested `page` value. |
| `limit` | integer | Echo of the requested `limit` value. |
| `accounts` | array | Array of account record objects exposed in this breach. |

### Account Record Object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier for the record. |
| `email` | string | The exposed email address. |
| `password` | string \| null | Plaintext password, when available in the source breach. |
| `hashed_password` | string \| null | Hashed password, when available in the source breach. The hash format depends on the breach source. |

> Whether `password`, `hashed_password`, or both are populated depends entirely on what was exposed by the original breach.

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": [
    {
      "database_name": "ExampleBreach 2019",
      "breach_date": "2019-04-12",
      "breach_description": "Public disclosure of a 2019 breach affecting a major SaaS provider.",
      "data_fields": "emails, hashed passwords, IP addresses",
      "total": 84,
      "page": 1,
      "limit": 500,
      "accounts": [
        {
          "id": 1029384,
          "email": "j.smith@acme.com",
          "password": null,
          "hashed_password": "$2a$10$REDACTED_FOR_DOC"
        },
        {
          "id": 1029385,
          "email": "m.fields@acme.com",
          "password": null,
          "hashed_password": "$2a$10$REDACTED_FOR_DOC"
        }
      ]
    },
    {
      "database_name": "ForumLeak 2021",
      "breach_date": "2021-07-30",
      "breach_description": "Forum credential dump posted on dark-web aggregator sites.",
      "data_fields": "emails, plaintext passwords",
      "total": 12,
      "page": 1,
      "limit": 500,
      "accounts": [
        {
          "id": 2049182,
          "email": "user@acme.com",
          "password": "REDACTED_FOR_DOC",
          "hashed_password": null
        }
      ]
    }
  ]
}
```

### Empty Result Set

```json
{
  "success": true,
  "results": []
}
```

> Note: Empty result responses do not consume a daily quota credit.

---

## Error Responses

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit access. | `{"error": "Database leak API is only available for Enterprise and Threat Intelligence licenses."}` |
| `403` | Daily quota exhausted. | `{"error": "Daily limit is reached."}` |
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query cannot be empty."}` |
| `200` | Date pairing error. | `{"success": false, "error": "Both start_date and end_date must be provided together."}` |
| `200` | Invalid date format. | `{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}` |
| `200` | Query targets a restricted domain. | `{"success": false, "error": "This query is restricted."}` |
| `200` | Daily quota exhausted between pre-check and increment. | `{"success": false, "message": "Daily API request limit exceeded."}` |

---

## Best Practices

- **Pagination:** For organizations exposed across many breaches, paginate using `page` and `limit`. Pagination flows across breach groups. The maximum permitted `limit` is `5000`.
- **Date filtering:** Use `start_date` and `end_date` to scope to a specific era of breaches.
- **Hash handling:** When `hashed_password` is populated, the hash format varies by breach source (`bcrypt`, `MD5`, `SHA-1`, `SHA-256`, etc.). Inspect `data_fields` and `breach_description` for hints.
- **Aggregation by employee:** Group account records by `email` after retrieval to identify which employees appear in multiple breaches.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
