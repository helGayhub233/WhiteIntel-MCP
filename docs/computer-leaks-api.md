# Computer Leaks API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/computer-leaks-api
> date: 2026-05-10

The Leaks by Computer Name endpoint returns infostealer credential records captured from machines with a specific hostname. It is intended for incident response and threat investigation workflows where an infected host's computer name is known and analysts need to enumerate every credential exfiltrated from that host.

Because hostname-based attribution is only available for infostealer-sourced records, this endpoint returns stealer logs exclusively and does not include combolist data.

---

## Endpoint

```
POST https://api.whiteintel.io/get_leaks_by_computer_name.php
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

This endpoint is restricted to the **Threat Intelligence** subscription tier. All other tiers, including Enterprise, will receive a `403 Forbidden` response indicating that the endpoint is not available on the current license.

To request access, contact `info@whiteintel.io`.

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
| `query` | string | Yes | — | The hostname of the target machine (e.g. `DESKTOP-K91PQ`). The match is exact and case-sensitive. |
| `mask_password` | integer | No | `0` | When set to `1`, the `password` field is omitted from results. |
| `limit` | integer | No | `500` | Maximum number of records to return. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |
| `start_date` | string | No | — | Lower bound of the log date range, format `YYYY-MM-DD`. Must be paired with `end_date`. |
| `end_date` | string | No | — | Upper bound of the log date range, format `YYYY-MM-DD`. Must be paired with `start_date`. |

### Notes on `query`

The `query` field expects a single hostname as it appears in the underlying stealer log metadata. Matching is exact; partial hostnames, wildcards, and domain-qualified hostnames (`HOST.DOMAIN.LOCAL`) are not normalized. Submit the hostname in the exact form you expect to find it.

### Notes on date filters

Both `start_date` and `end_date` must be supplied together. Supplying only one returns a validation error. Dates must conform to `YYYY-MM-DD` format.

### System Information

Records returned by this endpoint always include host-level system information (`hostname`, `ip`, `malware_path`, `anti_virus`) when available. This is enabled by default and is not configurable via request parameters.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_leaks_by_computer_name.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "DESKTOP-K91PQ",
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
| `results` | array | Array of stealer records, sorted by `log_date` in descending order. |

### Result Object

| Field | Type | Description |
|---|---|---|
| `data_type` | string | Always `stealer` for this endpoint. |
| `url` | string | The URL where the credential was captured. |
| `username` | string | The exposed username or email address. |
| `password` | string (when `mask_password=0`) | The exposed password in plaintext. Omitted entirely when `mask_password=1`. |
| `log_id` | integer | Internal identifier referencing the parent stealer log. |
| `log_date` | string (date) | The date associated with the leaked record. |
| `hostname` | string | Hostname of the infected machine. Will match the supplied `query`. |
| `ip` | string | IP address of the infected machine, when available. |
| `malware_path` | string | Filesystem path of the stealer binary on the infected machine, when available. |
| `anti_virus` | string | Antivirus product reported on the infected machine, if any. |

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://login.microsoftonline.com",
      "username": "j.smith@acme.com",
      "password": "REDACTED_FOR_DOC",
      "hostname": "DESKTOP-K91PQ",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender",
      "log_id": 184729302,
      "log_date": "2025-11-14"
    },
    {
      "data_type": "stealer",
      "url": "https://accounts.google.com",
      "username": "jsmith.personal@gmail.com",
      "password": "REDACTED_FOR_DOC",
      "hostname": "DESKTOP-K91PQ",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender",
      "log_id": 184729302,
      "log_date": "2025-11-14"
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

All error responses return a JSON body with either an `error` or `message` field describing the failure.

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit access (Threat Intelligence only). | `{"error": "This Endpoint only available for Threat Intel licenses."}` |
| `403` | Daily quota exhausted. | `{"error": "Daily limit is reached."}` |
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Date pairing error. | `{"success": false, "error": "Both start_date and end_date must be provided together."}` |

> **Important:** Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Best Practices

- **Hostname scope:** Each call queries a single hostname. For investigations spanning multiple machines, issue one call per hostname and aggregate results client-side.
- **Hostname uniqueness:** Default Windows hostnames (`DESKTOP-XXXXXXX`, `LAPTOP-XXXXXXX`) follow predictable patterns and may collide across different machines globally. Cross-reference results with other host-level fields (`ip`, `malware_path`, `log_date`) to confirm identity.
- **Date filtering:** Use `start_date` and `end_date` to narrow the lookup window when investigating a known infection timeframe.
- **Pagination:** Hosts with extensive credential capture histories may exceed the default `limit`. Paginate using `page` and `limit`. The maximum permitted `limit` is `5000`.
- **Password masking:** Use `mask_password=1` for compliance-sensitive integrations.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
