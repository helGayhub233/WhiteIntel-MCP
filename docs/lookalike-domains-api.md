# Lookalike Domains API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/lookalike-domains-api
> date: 2026-05-10

The Lookalike Domains endpoint returns typosquatting and brand-impersonation domains detected against the organization's watchlist. For each detected lookalike, the response includes the original watchlist domain it impersonates, the detected lookalike's WHOIS, hosting, nameserver, and registration metadata, and the date it was first observed.

This endpoint is the API counterpart to the Brand Protection page in the Whiteintel platform.

---

## Endpoint

```
POST https://api.whiteintel.io/get_lookalike_domains.php
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

> Each successful call consumes one daily quota credit, including calls that return an empty result set. Plan polling cadence accordingly.

---

## Query Modes

The endpoint supports two distinct query modes, selected by whether the `query` parameter is supplied:

- **Organization-wide mode** — Submit an empty `query` (or omit it entirely) to retrieve every lookalike domain detected across all of the organization's watchlist entries. Useful for populating a unified Brand Protection dashboard view.
- **Watchlist-scoped mode** — Submit a specific domain in `query` to retrieve only the lookalikes that target that particular watchlist entry. The submitted domain **must already exist in the organization's watchlist**. If it does not, the endpoint returns an error with the list of valid query values for the organization.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | No | empty | Either an empty value (organization-wide mode) or one of your watchlist domains (watchlist-scoped mode). The value is normalized to lowercase before lookup. |
| `limit` | integer | No | `500` | Maximum number of records to return. Allowed range: `1`–`5000`. |
| `page` | integer | No | `1` | Page number for pagination. |

### Notes on `query`

- The `query` value is matched exactly against your watchlist entries (case-insensitive). Wildcards, partial matches, and CIDR patterns are not supported.
- Queries targeting restricted domains will return a restricted-query error regardless of watchlist contents.
- If `query` is supplied but empty (`""`), the endpoint behaves as if it were omitted — organization-wide mode applies.

---

## Request Examples

### Organization-wide mode

```bash
curl -X POST https://api.whiteintel.io/get_lookalike_domains.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "limit": 100,
    "page": 1
  }'
```

### Watchlist-scoped mode

```bash
curl -X POST https://api.whiteintel.io/get_lookalike_domains.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "acme.com",
    "limit": 100,
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
| `results` | array | Array of lookalike domain records, sorted by `discovered_at` in descending order. |

### Result Object

| Field | Type | Description |
|---|---|---|
| `data_type` | string | Always `lookalike` for this endpoint. |
| `original_entry` | string | The watchlist domain that this lookalike impersonates. |
| `detected_domain` | string | The detected lookalike domain. |
| `detected_domain_ip` | string \| null | The IP address the lookalike currently resolves to, when available. |
| `detected_domain_ns` | string \| null | Nameservers configured for the lookalike, when available. |
| `whois_json` | string \| null | Raw WHOIS data for the lookalike, encoded as a JSON string. Parse client-side if structured access is required. |
| `creation_date_iso` | string \| null | Registration date of the lookalike in ISO 8601 format, when available. |
| `discovered_at` | string (datetime) | The date the lookalike was first observed by the platform. |

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "results": [
    {
      "data_type": "lookalike",
      "original_entry": "acme.com",
      "detected_domain": "acme-secure-login.com",
      "detected_domain_ip": "203.0.113.118",
      "detected_domain_ns": "ns1.suspicious-host.net,ns2.suspicious-host.net",
      "whois_json": "{\"registrar\": \"NameCheap, Inc.\", \"registrant_country\": \"PA\"}",
      "creation_date_iso": "2025-10-22T00:00:00Z",
      "discovered_at": "2025-10-23 11:42:08"
    },
    {
      "data_type": "lookalike",
      "original_entry": "acme.com",
      "detected_domain": "acme-portal-help.com",
      "detected_domain_ip": "198.51.100.42",
      "detected_domain_ns": "ns1.cloudflare.com,ns2.cloudflare.com",
      "whois_json": "{\"registrar\": \"GoDaddy.com, LLC\", \"registrant_country\": \"US\"}",
      "creation_date_iso": "2025-09-15T00:00:00Z",
      "discovered_at": "2025-09-16 04:18:27"
    }
  ]
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

## Watchlist Mismatch Error

When a non-empty `query` is supplied that does not match any of the organization's watchlist entries, the endpoint returns a structured error that includes the full list of valid query values:

```json
{
  "success": false,
  "error": "Query must be empty or one of your watchlist domains.",
  "allowed_queries": [
    "acme.com",
    "acme.io",
    "acmehealth.com"
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `false`. |
| `error` | string | Explanation of the mismatch. |
| `allowed_queries` | array of strings | All watchlist domains for the organization that can be supplied as `query`. |

---

## Error Responses

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `400` | Malformed JSON body. | `{"error": "Invalid JSON body."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit API access. | `{"error": "API calls are only available for Enterprise and Higher tiers. Please upgrade your account."}` |
| `403` | Daily quota exhausted. | `{"error": "Daily limit is reached."}` |
| `403` | Query is restricted. | `{"success": false, "error": "Query not allowed for restricted TLDs."}` |
| `429` | Request throttle hit. | `{"message": "Please wait 5 seconds between requests."}` |
| `200` | Validation error in request body. | `{"success": false, "error": "Limit must be an integer between 1 and 5000."}` |
| `200` | Daily quota exhausted between pre-check and increment. | `{"success": false, "message": "Daily API request limit exceeded."}` |
| `200` | Query supplied but not in watchlist. | See Watchlist Mismatch Error. |

---

## Best Practices

- **Dashboard composition:** For a complete Brand Protection view, use organization-wide mode (empty `query`) and paginate through results. Switch to watchlist-scoped mode when drilling into a specific brand.
- **Pagination:** Organizations with broad watchlist coverage may produce thousands of detected lookalikes. Paginate using `page` and `limit`. The maximum permitted `limit` is `5000`.
- **WHOIS payload:** The `whois_json` field is a string-encoded JSON document, not a structured object. Decode it client-side when structured access is required.
- **Self-correcting clients:** Use the `allowed_queries` field in mismatch responses to populate suggestions or correct typos.
- **Discovery cadence:** New lookalikes are added on a continuous basis. Use `discovered_at` to drive incremental ingestion.
- **Quota planning:** Every successful call consumes a daily quota credit, including calls that return empty arrays.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
