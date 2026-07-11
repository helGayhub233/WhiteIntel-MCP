# Consumer Leaks API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/consumer-leaks-api
> date: 2026-05-10

The Consumer Leaks endpoint returns credential records exposed in infostealer logs and combolists for a given domain or subdomain. Results include the source URL, username, password (or masked password), and timestamp, with optional host-level system information for stealer-sourced records.

This endpoint supports filtering by date range, username, subdomain, source type, and pagination.

---

## Endpoint

```
POST https://api.whiteintel.io/get_consumer_leaks.php
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

This endpoint is available to **Enterprise** and **Threat Intelligence** subscription tiers. Lower tiers will receive a `403 Forbidden` response with an upgrade message.

---

## Rate Limits and Quotas

| Limit Type | Description |
|---|---|
| Request throttle | Default `0.2 QPS` (1 request every 5 seconds) per account/API key. Exceeding this returns `429 Too Many Requests`. |
| Daily quota | Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. |

Once the daily quota is exhausted, requests return `403 Forbidden` with a quota-exceeded message until the counter resets.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The target domain (e.g. `example.com`). |
| `type` | string | No | `all` | Result source type. One of `all`, `stealer`, `combolist`. |
| `include_system_info` | integer | No | `0` | When set to `1`, stealer records include host-level system information. |
| `mask_password` | integer | No | `0` | When set to `1`, the `password` field is omitted from results. |
| `limit` | integer | No | `500` | Maximum number of records to return. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |
| `start_date` | string | No | — | Lower bound of the log date range, format `YYYY-MM-DD`. Must be paired with `end_date`. |
| `end_date` | string | No | — | Upper bound of the log date range, format `YYYY-MM-DD`. Must be paired with `start_date`. |
| `username` | string | No | — | Exact-match filter on the leaked username field. |
| `subdomain` | string | No | — | When the target is a specific subdomain, supply the registrable domain in `query` and the full subdomain here. |

### Notes on `query` and `subdomain`

The `query` field accepts both registrable domains and subdomains. When targeting a specific subdomain, the recommended pattern is to supply the **registrable domain** in `query` and the **full subdomain** in the `subdomain` field.

Example:

```json
{
  "query": "acme.com",
  "subdomain": "admin.acme.com"
}
```

### Notes on date filters

Both `start_date` and `end_date` must be supplied together. Supplying only one returns a validation error. Dates must conform to `YYYY-MM-DD` format.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_consumer_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "type": "all",
    "include_system_info": 1,
    "limit": 100,
    "page": 1,
    "start_date": "2025-01-01",
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
| `results` | array | Array of leak records, sorted by `log_date` in descending order. |

### Result Object

| Field | Type | Applies To | Description |
|---|---|---|---|
| `data_type` | string | All | Either `stealer` or `combolist`. |
| `url` | string | All | The URL where the credential was captured. |
| `username` | string | All | The exposed username or email address. |
| `password` | string | All (when `mask_password=0`) | The exposed password in plaintext. Omitted entirely when `mask_password=1`. |
| `log_date` | string (datetime) | All | The date the record was added to the platform. |
| `log_id` | integer | `stealer` only | Internal identifier referencing the parent stealer log. |
| `hostname` | string | `stealer` with `include_system_info=1` | Hostname of the infected machine. |
| `ip` | string | `stealer` with `include_system_info=1` | IP address of the infected machine. |
| `malware_path` | string | `stealer` with `include_system_info=1` | Filesystem path of the stealer binary on the infected machine. |
| `anti_virus` | string | `stealer` with `include_system_info=1` | Antivirus product reported on the infected machine, if any. |

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://portal.example.com/login",
      "log_id": 184729302,
      "username": "victim@example.com",
      "password": "REDACTED_FOR_DOC",
      "log_date": "2025-11-14 08:23:11",
      "hostname": "DESKTOP-K91PQ",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender"
    },
    {
      "data_type": "combolist",
      "url": "example.com",
      "username": "user@example.com",
      "password": "REDACTED_FOR_DOC",
      "log_date": "2025-09-02 12:00:00"
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

All error responses return a JSON body with either an `error` or `message` field describing the failure.

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit API access. | `{"error": "API calls are only available for Enterprise and Higher tiers. Please upgrade your account."}` |
| `403` | Daily quota exhausted. | `{"error": "Daily limit is reached."}` |
| `403` | Query targets a restricted domain. | `{"success": false, "error": "This query is restricted."}` |
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Invalid `type` value. | `{"success": false, "error": "Invalid type. Allowed values are: 'all', 'stealer', 'combolist'."}` |
| `200` | Date pairing error. | `{"success": false, "error": "Both start_date and end_date must be provided together."}` |
| `200` | Invalid date format. | `{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}` |

> **Important:** Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Best Practices

- **Pagination:** For domains with large exposure footprints, paginate using `page` and `limit` rather than requesting a single oversized result set. The maximum permitted `limit` is `5000`.
- **Result type:** When monitoring a specific data source, use `type=stealer` or `type=combolist` to reduce payload size and response latency. Use `type=all` for unified views.
- **System information:** Set `include_system_info=1` only when host-level context is required for triage. Omit otherwise to reduce response size.
- **Password masking:** Use `mask_password=1` for compliance-sensitive integrations where credential material should not transit downstream systems.
- **Date filtering:** When ingesting incrementally, use `start_date` and `end_date` to retrieve only newly exposed records since the last sync.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response to anticipate quota exhaustion before it occurs.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
