# Get Leaks By ID API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/get-leaks-by-id-api
> date: 2026-05-10

The Get Leaks By ID API endpoint returns the complete contents of one or more stealer infection records, identified by their internal log ID. For each requested ID, the response includes the full host-level device profile and every credential captured during that infection event.

The accepted ID corresponds directly to the `log_id` field returned by the Consumer Leaks, Corporate Leaks, Last Leaks, Leaks by Username, Leaks by IP, and Leaks by Computer Name endpoints. This makes the endpoint the standard way to drill down from a single credential hit into the full infection record it came from.

This endpoint supports both single-ID lookups and batched lookups of up to 5 IDs in a single call.

---

## Endpoint

```
POST https://api.whiteintel.io/get_leaks_by_id.php
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

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. This conservative default keeps batched investigations and concurrent MCP tool calls below common upstream burst-interception thresholds.

Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. Once the daily quota is exhausted, requests return a quota-exceeded message until the counter resets.

A batched request that includes multiple IDs consumes a **single** daily quota credit, regardless of how many IDs are submitted in the `query` array.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | integer or array of integers | Yes | — | Either a single log ID or an array of log IDs. When an array is supplied, it must contain between 1 and 5 elements. Each ID must be a positive integer. |
| `mask_password` | integer | No | `0` | When set to `1`, the `password` field is omitted from the credentials in the response. |

### Notes on `query`

The `query` parameter accepts two formats:

**Single ID** — pass an integer (or numeric string):

```json
{ "query": 184729302 }
```

**Batch of IDs** — pass an array of 1 to 5 integers:

```json
{ "query": [184729302, 184729303, 184729304] }
```

The response shape differs between the two modes. See Response Schema for details.

---

## Request Example — Single ID

```bash
curl -X POST https://api.whiteintel.io/get_leaks_by_id.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": 184729302
  }'
```

## Request Example — Batched IDs

```bash
curl -X POST https://api.whiteintel.io/get_leaks_by_id.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": [184729302, 184729303, 184729304],
    "mask_password": 0
  }'
```

---

## Response Schema

### Success Response

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `remaining_daily_calls` | integer | Remaining requests on the daily quota for the current API key. |
| `results` | object or empty array | The shape depends on whether a single ID or an array was supplied. |

### Single ID Response

When `query` is a single integer, `results` is an object containing two fields:

| Field | Type | Description |
|---|---|---|
| `compromised_device_information` | object \| null | The host-level profile of the infected machine. `null` if no device record exists for the supplied ID. |
| `compromised_credentials` | array | All credentials captured during the infection event. Each element is a credential object. |

If both fields are empty (no device info and no credentials match the supplied ID), `results` is returned as an empty array (`[]`).

### Batched IDs Response

When `query` is an array of integers, `results` is an object keyed by ID (as a string). Each value has the same structure as the single-ID lookup response.

IDs that return no device information and no credentials are omitted from the response object entirely. Submitting five IDs may therefore yield fewer than five entries in the response.

### Compromised Device Information

| Field | Type | Description |
|---|---|---|
| `hostname` | string \| null | Hostname of the infected machine. |
| `username` | string \| null | Operating system username at the time of capture. |
| `ip` | string \| null | IP address of the infected machine. |
| `malware_path` | string \| null | Filesystem path of the stealer binary on the infected machine. |
| `anti_virus` | string \| null | Antivirus product reported on the infected machine, if any. |
| `country` | string \| null | Country attribution of the infected machine. |
| `log_date` | string (datetime) \| null | The date associated with the infection record. |

### Compromised Credential Object

| Field | Type | Description |
|---|---|---|
| `url` | string | The URL where the credential was captured. |
| `username` | string | The exposed username or email address. |
| `password` | string (when `mask_password=0`) | The exposed password in plaintext. Omitted entirely when `mask_password=1`. |

---

## Response Example — Single ID

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": {
    "compromised_device_information": {
      "hostname": "DESKTOP-K91PQ",
      "username": "jsmith",
      "ip": "203.0.113.42",
      "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
      "anti_virus": "Windows Defender",
      "country": "United States",
      "log_date": "2025-11-14 08:23:11"
    },
    "compromised_credentials": [
      {
        "url": "https://login.microsoftonline.com",
        "username": "j.smith@acme.com",
        "password": "REDACTED_FOR_DOC"
      },
      {
        "url": "https://accounts.google.com",
        "username": "jsmith.personal@gmail.com",
        "password": "REDACTED_FOR_DOC"
      },
      {
        "url": "https://github.com/login",
        "username": "jsmith-acme",
        "password": "REDACTED_FOR_DOC"
      }
    ]
  }
}
```

## Response Example — Batched IDs

```json
{
  "success": true,
  "remaining_daily_calls": 4982,
  "results": {
    "184729302": {
      "compromised_device_information": {
        "hostname": "DESKTOP-K91PQ",
        "username": "jsmith",
        "ip": "203.0.113.42",
        "malware_path": "C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost.exe",
        "anti_virus": "Windows Defender",
        "country": "United States",
        "log_date": "2025-11-14 08:23:11"
      },
      "compromised_credentials": [
        {
          "url": "https://login.microsoftonline.com",
          "username": "j.smith@acme.com",
          "password": "REDACTED_FOR_DOC"
        }
      ]
    },
    "184729303": {
      "compromised_device_information": {
        "hostname": "ACME-LAPTOP-219",
        "username": "mfields",
        "ip": "198.51.100.12",
        "malware_path": "C:\\Users\\mfields\\Downloads\\setup.exe",
        "anti_virus": "CrowdStrike Falcon",
        "country": "Germany",
        "log_date": "2025-11-13 16:02:44"
      },
      "compromised_credentials": [
        {
          "url": "https://accounts.google.com",
          "username": "m.fields@acme.com",
          "password": "REDACTED_FOR_DOC"
        }
      ]
    }
  }
}
```

### Empty Result Set

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
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
| `403` | Subscription tier does not permit access. | `{"error": "This endpoint is only available for Threat Intelligence licenses."}` |
| `200` | Daily quota exhausted. | `{"success": false, "message": "Daily API request limit exceeded."}` |
| `200` | Malformed JSON body. | `{"success": false, "message": "Invalid JSON payload."}` |
| `200` | `query` is not an integer or array of integers. | `{"success": false, "message": "Invalid query format. Expected an integer or an array of integers."}` |
| `200` | `query` is a single value less than 1. | `{"success": false, "message": "Query must be an integer greater than or equal to 1."}` |
| `200` | `query` array is empty or has more than 5 entries. | `{"success": false, "message": "You may request between 1 and 5 IDs per request."}` |
| `200` | `query` array contains non-integer values. | `{"success": false, "message": "Query array must contain only integer values."}` |
| `200` | An ID in the `query` array is less than 1. | `{"success": false, "message": "Each ID in query array must be greater than or equal to 1."}` |

> **Important:** Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Best Practices

- **Drilling down from list endpoints:** Use this endpoint to expand the full infection profile behind a single credential hit returned by the list-based endpoints. Pass the `log_id` field from those responses directly as the `query` here.
- **Batch efficiency:** When investigating multiple suspect infections, batch up to 5 IDs into a single call. Batched requests consume only one daily quota credit while returning all results.
- **Response shape:** Always inspect the type of `results` before iterating. Single-ID and empty-result responses return different shapes (object vs empty array). Batched responses return an object keyed by string IDs.
- **Missing IDs in batched mode:** Do not assume one entry per submitted ID. IDs that return no records are omitted from the response object. Reconcile against your input list.
- **Password masking:** Use `mask_password=1` for compliance-sensitive integrations.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
