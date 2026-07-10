# Username Leaks API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/username-leaks-api
> date: 2026-05-10

This endpoint can be used for retrieving leaks related to the given email address or username.

The Username Leaks API endpoint returns credential records where the leaked username exactly matches the supplied query. It is intended for targeted lookups against a specific email address or account identifier rather than broad domain or organization sweeps.

Results are sourced from infostealer logs and combolists, and include the captured login URL, password (or masked password), and timestamp, with optional host-level system information for stealer-sourced records.

This endpoint maintains a dedicated quota counter that is independent from the daily quota used by the domain-scoped endpoints.

---

## Endpoint

```
POST https://api.whiteintel.io/get_leaks_by_username.php
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
| Daily quota | A daily request quota gates access to all API endpoints. |
| Username search quota | This endpoint additionally consumes a **dedicated username search quota** that is tracked separately from the daily quota. The remaining balance is returned in every successful response under `remaining_username_calls`. |

When the username search quota is exhausted, the endpoint returns a quota-exhaustion message until the counter resets or the quota is increased.

Empty result responses do not consume a quota credit on either counter.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The exact username or email address to search for (e.g. `j.smith@acme.com`). Matching is performed on the full username field; partial matches are not supported. |
| `type` | string | No | `all` | Result source type. One of `all`, `stealer`, `combolist`. The parameter name `data_type` is accepted as an alias, and the value `both` is accepted as a legacy alias for `all`. |
| `include_system_info` | integer | No | `0` | When set to `1`, stealer records include host-level system information. |
| `mask_password` | integer | No | `0` | When set to `1`, the `password` field is omitted from results. |
| `limit` | integer | No | `500` | Maximum number of records to return. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |
| `start_date` | string | No | — | Lower bound of the log date range, format `YYYY-MM-DD`. Must be paired with `end_date`. |
| `end_date` | string | No | — | Upper bound of the log date range, format `YYYY-MM-DD`. Must be paired with `start_date`. |

### Notes on `query`

The `query` field requires an exact match against the username as it appears in the underlying record. For email-based identifiers, supply the full email address. The match is case-sensitive at the database level, so account for casing variations in your client logic if needed.

### Notes on date filters

Both `start_date` and `end_date` must be supplied together. Supplying only one returns a validation error. Dates must conform to `YYYY-MM-DD` format.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_leaks_by_username.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "j.smith@acme.com",
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
| `remaining_username_calls` | integer | Remaining requests on the username search quota for the current API key. |
| `results` | array | Array of leak records, sorted by `log_date` in descending order. |

### Result Object

| Field | Type | Applies To | Description |
|---|---|---|---|
| `data_type` | string | All | Either `stealer` or `combolist`. |
| `url` | string | All | The URL where the credential was captured. |
| `username` | string | All | The exposed username or email address. Will match the supplied `query`. |
| `password` | string | All (when `mask_password=0`) | The exposed password in plaintext. Omitted entirely when `mask_password=1`. |
| `log_date` | string (datetime) | All | The date associated with the leaked record. |
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
  "remaining_username_calls": 982,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://login.microsoftonline.com",
      "username": "j.smith@acme.com",
      "password": "REDACTED_FOR_DOC",
      "log_id": 184729302,
      "log_date": "2025-11-14",
      "hostname": "DESKTOP-K91PQ",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender"
    },
    {
      "data_type": "combolist",
      "url": "https://accounts.google.com",
      "username": "j.smith@acme.com",
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

> Note: Empty result responses do not consume a username search quota credit.

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
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Username search quota exhausted. | `{"success": false, "message": "Username API call limit exhausted. Wait until reload or increase your API calls."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Date pairing error. | `{"success": false, "error": "Both start_date and end_date must be provided together."}` |

> **Important:** Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Best Practices

- **Targeted lookups:** This endpoint is designed for one-username-per-call lookups. For broad domain or organization searches, use the Consumer Leaks or Corporate Leaks endpoints.
- **Quota separation:** Username search quota is tracked separately from the daily request quota. Plan integrations around both counters when mixing endpoint types.
- **System information:** Set `include_system_info=1` only when host-level context is required for triage.
- **Password masking:** Use `mask_password=1` for compliance-sensitive integrations.
- **Date filtering:** When ingesting incrementally, use `start_date` and `end_date` to retrieve only newly exposed records since the last sync.
- **Quota monitoring:** Track the `remaining_username_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
