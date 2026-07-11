# Last Leaks API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/last-leaks-api
> date: 2026-05-10

The Last Leaks endpoint returns the most recent credential exposures for a target domain across both consumer and corporate breach categories within a configurable look-back window. It is designed for incremental ingestion and continuous monitoring workflows where only newly observed leaks are required.

In a single call, this endpoint can surface:

- **Consumer leaks** — credentials captured on the queried website or its subdomains.
- **Corporate leaks** — credentials whose username belongs to the queried organization's email domain, regardless of which third-party service they were used on.

Results are sourced from infostealer logs and combolists and can be filtered by both source type and breach category.

---

## Endpoint

```
POST https://api.whiteintel.io/get_last_leaks.php
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

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. This conservative default keeps sequential page fetches and concurrent MCP tool calls below common upstream burst-interception thresholds.

Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. Once the daily quota is exhausted, requests return a quota-exceeded message until the counter resets.

Empty result responses do not consume a daily quota credit.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The target domain or subdomain. The endpoint will detect whether the value is a subdomain and adjust the lookup accordingly. |
| `days` | integer | Yes | — | Look-back window in days. Allowed range: `1`–`30`. Records added to the platform within this window are returned. |
| `data_type` | string | No | `all` | Source type filter. One of `all`, `stealer`, `combolist`. |
| `breach_type` | string | No | `all` | Breach category filter. One of `all`, `consumer`, `corporate`. |
| `mask_password` | integer | No | `0` | When set to `1`, the `password` field is omitted from results. |
| `limit` | integer | No | `500` | Maximum number of records to return. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |

### Notes on `data_type` and `breach_type`

The two filters are orthogonal and can be combined freely:

- `data_type` — The **source** of the credential record (`stealer` or `combolist`).
- `breach_type` — The **subject** of the credential record (`consumer` or `corporate`).

Setting either filter to `all` removes that dimension from the filter. Using `data_type=all` and `breach_type=all` returns the broadest possible result set.

### Notes on `query`

Supply either a registrable domain (e.g. `acme.com`) or a specific subdomain (e.g. `mail.acme.com`). The endpoint will route the lookup automatically.

### System Information

Stealer records returned by this endpoint always include host-level system information (`hostname`, `ip`, `malware_path`, `anti_virus`) when available. This is enabled by default and is not configurable via request parameters.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_last_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "acme.com",
    "days": 7,
    "data_type": "all",
    "breach_type": "all",
    "limit": 500,
    "page": 1
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
| `breach_type` | string | All | Either `consumer` or `corporate`. |
| `url` | string | All | The URL where the credential was captured. |
| `username` | string | All | The exposed username or email address. |
| `password` | string | All (when `mask_password=0`) | The exposed password in plaintext. Omitted entirely when `mask_password=1`. |
| `log_date` | string (datetime) | All | The date the record was added to the platform. |
| `log_id` | integer | `stealer` only | Internal identifier referencing the parent stealer log. |
| `hostname` | string | `stealer` only | Hostname of the infected machine, when available. |
| `ip` | string | `stealer` only | IP address of the infected machine, when available. |
| `malware_path` | string | `stealer` only | Filesystem path of the stealer binary on the infected machine, when available. |
| `anti_virus` | string | `stealer` only | Antivirus product reported on the infected machine, when available. |

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": [
    {
      "data_type": "stealer",
      "breach_type": "consumer",
      "url": "https://portal.acme.com/login",
      "log_id": 184729302,
      "username": "customer@acme.com",
      "password": "REDACTED_FOR_DOC",
      "log_date": "2025-11-14 08:23:11",
      "hostname": "DESKTOP-K91PQ",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\customer\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender"
    },
    {
      "data_type": "stealer",
      "breach_type": "corporate",
      "url": "https://login.microsoftonline.com",
      "log_id": 184729188,
      "username": "j.smith@acme.com",
      "password": "REDACTED_FOR_DOC",
      "log_date": "2025-11-13 16:02:44",
      "hostname": "ACME-LAPTOP-219",
      "ip": "198.51.100.12",
      "malware_path": "C:\\Users\\jsmith\\Downloads\\setup.exe",
      "anti_virus": "CrowdStrike Falcon"
    },
    {
      "data_type": "combolist",
      "breach_type": "corporate",
      "url": "https://accounts.google.com",
      "username": "m.fields@acme.com",
      "password": "REDACTED_FOR_DOC",
      "log_date": "2025-11-12 09:41:00"
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

---

## Error Responses

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit API access. | `{"error": "API calls are only available for Enterprise and Higher tiers. Please upgrade your account."}` |
| `200` | Daily quota exhausted. | `{"success": false, "message": "Daily API request limit exceeded."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Missing or out-of-range `days`. | `{"success": false, "error": "The days parameter must be an integer between 1 and 30."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Invalid `data_type` value. | `{"success": false, "error": "Invalid data type. Allowed values are: 'all', 'stealer', 'combolist'."}` |
| `200` | Invalid `breach_type` value. | `{"success": false, "error": "Invalid breach type. Allowed values are: 'all', 'consumer', 'corporate'."}` |
| `200` | Query targets a restricted domain. | `{"success": false, "error": "This query is restricted."}` |

---

## Best Practices

- **Incremental ingestion:** Use a fixed `days` value aligned with your polling cadence (e.g. `days=1` for hourly polling, `days=7` for weekly digests).
- **Filter selection:** Combine `data_type` and `breach_type` filters to scope responses to the exact slice you need.
- **Pagination:** For high-exposure organizations, paginate using `page` and `limit`. The maximum permitted `limit` is `5000`.
- **Password masking:** Use `mask_password=1` for compliance-sensitive integrations.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
