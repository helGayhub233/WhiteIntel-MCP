# Supplier API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/supplier-security-api/supplier-api
> date: 2026-06-26

The Supplier Security API manages an organization's tracked supplier list. It supports listing tracked suppliers with their latest risk snapshot, adding or reactivating a supplier, and permanently removing a supplier.

## Endpoint

```text
POST https://api.whiteintel.io/supplier_api.php
```

## Request Headers

| Header | Value |
| --- | --- |
| `Content-Type` | `application/json` |

## Authentication

Authentication is performed via an API key in the JSON request body:

```json
{
  "apikey": "YOUR_API_KEY"
}
```

The API key must be valid and attached to an organization.

## Rate Limits and Quotas

| Limit Type | Description |
| --- | --- |
| Request throttle | Default `0.2 QPS` (1 request every 5 seconds) per account/API key. This conservative default is used when the upstream wait time is not specified; clients should still honor `429`/`Retry-After` responses. |
| Daily quota | Remaining quota is returned as `remaining_daily_calls`. |
| Supplier slots | Active suppliers are capped by the organization's supplier credit allowance. |

A well-formed authenticated call consumes one daily quota credit even when it is a no-op, such as adding an already tracked supplier or listing zero rows.

## Actions

| Action | Description |
| --- | --- |
| `list` | Return tracked suppliers with filtering, sorting, and pagination. |
| `add` | Add a new tracked supplier or reactivate an archived supplier. |
| `remove` | Permanently remove a tracked supplier. |

The value `delete` is accepted as an alias for `remove`.

## Action: list

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `apikey` | string | Yes | - | WhiteIntel API key. |
| `action` | string | Yes | - | Must be `list`. |
| `status` | string | No | `active` | One of `active`, `paused`, `archived`, or `all`. |
| `tier` | string | No | - | One of `critical`, `high`, `medium`, or `low`. |
| `search` | string | No | - | Case-insensitive substring match against `domain` and `display_name`; max 253 characters. |
| `sort` | string | No | `score` | One of `score`, `recent`, `scanned`, `name`, `added`, or `updated`. |
| `order` | string | No | `desc` | One of `asc` or `desc`. |
| `limit` | integer | No | `50` | Page size, clamped 1-200. |
| `offset` | integer | No | `0` | Row offset for pagination. |

## Action: add

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `apikey` | string | Yes | - | WhiteIntel API key. |
| `action` | string | Yes | - | Must be `add`. |
| `domain` | string | Yes | - | Supplier domain, resolved to its registrable root. |
| `display_name` | string | No | - | Human-readable supplier name; max 255 characters. |
| `size` | string | No | - | Free-form organization size label; max 32 characters. |
| `country` | string | No | - | Country label; max 64 characters. |
| `industry` | string | No | - | Industry label; max 96 characters. |
| `category` | string | No | - | Free-form category label; max 64 characters. |
| `supplier_tier` | string | No | - | One of `critical`, `high`, `medium`, or `low`. |
| `notes` | string | No | - | Free-form notes; max 5000 characters. |

## Action: remove

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `apikey` | string | Yes | - | WhiteIntel API key. |
| `action` | string | Yes | - | Must be `remove` or `delete`. |
| `id` | integer | Conditional | - | Supplier identifier. Required if `domain` is not provided. |
| `domain` | string | Conditional | - | Supplier domain. Required if `id` is not provided. |

## Error Responses

| Status | Condition |
| --- | --- |
| `400 Bad Request` | Invalid JSON body, missing or invalid action, missing or unresolvable domain, invalid filters, or remove without `id` or `domain`. |
| `403 Forbidden` | Missing/invalid API key, API key without organization, supplier credit allowance reached, blocked domain, or daily quota exhausted. |
| `404 Not Found` | Supplier or organization not found. |
| `405 Method Not Allowed` | Request was not `POST` with `application/json`. |
| `409 Conflict` | Supplier is already actively tracked. |
| `429 Too Many Requests` | Per-account request throttle exceeded. |
| `500 Internal Server Error` | Unexpected server error. |

---

## Request Examples

### List Suppliers

```bash
curl --location 'https://api.whiteintel.io/supplier_api.php' \
  --header 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "action": "list",
    "status": "active",
    "sort": "score",
    "order": "desc",
    "limit": 10,
    "offset": 0
  }'
```

### Add Supplier

```bash
curl --location 'https://api.whiteintel.io/supplier_api.php' \
  --header 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "action": "add",
    "domain": "acme.com",
    "display_name": "Acme Corporation",
    "industry": "SaaS",
    "country": "US",
    "supplier_tier": "high",
    "notes": "Primary billing vendor"
  }'
```

### Remove Supplier by ID

```bash
curl --location 'https://api.whiteintel.io/supplier_api.php' \
  --header 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "action": "remove",
    "id": 4413
  }'
```

### Remove Supplier by Domain

```bash
curl --location 'https://api.whiteintel.io/supplier_api.php' \
  --header 'Content-Type: application/json' \
  --data '{
    "apikey": "YOUR_API_KEY",
    "action": "remove",
    "domain": "acme.com"
  }'
```

---

## Response Examples

### List Response

```json
{
  "success": true,
  "total": 128,
  "count": 50,
  "limit": 50,
  "offset": 0,
  "suppliers": [
    {
      "id": 4412,
      "domain": "acme.com",
      "display_name": "Acme Corporation",
      "size": "200-500",
      "country": "US",
      "industry": "SaaS",
      "supplier_tier": "high",
      "category": "vendor",
      "status": "active",
      "last_score": 72.5,
      "last_grade": "C",
      "last_score_delta": -3.1,
      "last_scored_at": "2026-06-24 03:15:00",
      "last_event_at": "2026-06-23 18:42:10",
      "last_event_type": "credential_exposure",
      "last_event_summary": "New corporate credentials observed",
      "created_at": "2026-01-10 09:00:00",
      "updated_at": "2026-06-24 03:15:00"
    }
  ],
  "remaining_daily_calls": 487
}
```

### Add Response (New Supplier)

```json
{
  "success": true,
  "action": "added",
  "supplier_id": 4413,
  "domain": "acme.com",
  "used": 41,
  "limit": 100,
  "remaining": 59,
  "remaining_daily_calls": 486
}
```

### Remove Response

```json
{
  "success": true,
  "action": "deleted",
  "supplier_id": 4413,
  "used": 40,
  "limit": 100,
  "remaining": 60,
  "remaining_daily_calls": 485
}
```

### Error Responses (Selected)

```json
{ "success": false, "error": "Invalid or missing action.", "allowed": ["list", "add", "remove"] }
```

```json
{ "success": false, "error": "Supplier tracking limit reached for your plan.", "used": 100, "limit": 100, "remaining": 0 }
```

```json
{ "success": false, "error": "This supplier is already being tracked.", "supplier_id": 4413 }
```

```json
{ "success": false, "error": "Daily API request limit exceeded." }
```
