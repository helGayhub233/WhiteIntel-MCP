# Audit Logs API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/miscellaneous/audit-logs-api
> date: 2026-06-10

Retrieves paginated audit logs for a given API key, excluding sensitive query content. Logs include metadata such as IP address, HTTP method, query type, and timestamp, enabling traceability and usage analysis for security and debugging purposes.

---

## Endpoint

```
POST https://api.whiteintel.io/get_audit_logs.php
```

---

## Rate Limits and Quotas

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. Audit log reads are often used for troubleshooting after other API calls, so this conservative default avoids compounding burst traffic during investigations.

---

## Request Body (JSON)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your API key |
| `page` | int | No | `1` | Pagination |

---

## Example Request

```bash
curl -X POST https://api.whiteintel.io/get_audit_logs.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey":"YOUR API KEY",
    "page": 1
  }'
```

---

## Example Response

```json
{
  "success": true,
  "page": 1,
  "count": 11,
  "logs": [
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 18:15:58",
      "http_method": "POST",
      "query_type": "audit_logs"
    },
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 18:15:34",
      "http_method": "POST",
      "query_type": "audit_logs"
    },
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 18:15:19",
      "http_method": "POST",
      "query_type": "audit_logs"
    },
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 17:16:42",
      "http_method": "POST",
      "query_type": "leaksby_id"
    },
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 17:06:07",
      "http_method": "POST",
      "query_type": "corporate_leaks"
    },
    {
      "ip": "10.0.0.5",
      "call_date": "2025-07-30 17:03:31",
      "http_method": "POST",
      "query_type": "consumer_leaks"
    }
  ]
}
```

---

## Error Responses

```json
{"success":false,"error":"Invalid page number. Must be a positive integer."}
```
