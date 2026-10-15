# Overall Stats API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/overall-stats
> date: 2026-10-15

This endpoint can be used for retrieving dashboard statistics of given target domain.

The Overall Stats endpoint returns aggregate intelligence metrics for a target domain. It is the analytics counterpart to the leak-retrieval endpoints and is used to drive dashboards, executive reports, and posture monitoring rather than incident-level credential lookups.

A single request returns one named metric. To assemble a complete dashboard view, multiple calls are made in parallel — one per metric — using the same `query` value.

This endpoint supports thirteen metrics covering exposure counts, application breakdowns, incident timelines, recent activity, and country distribution.

---

## Endpoint

```
POST https://api.whiteintel.io/get_overall_stats.php
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

Default request throttle is `0.3 QPS` (1 request every ~3.3 seconds) per account/API key. Although dashboards may request multiple metrics, this conservative default avoids bursty parallel calls that can trigger upstream interception.

Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. Once the daily quota is exhausted, requests return a quota-exceeded message until the counter resets.

Each call consumes one daily quota credit, regardless of which metric is requested. Empty array results for list-style metrics (timelines, applications, recent events, country distribution) do not consume a credit. Empty count results for scalar metrics (consumer count, corporate count, etc.) do consume a credit because the response always contains zero-valued fields.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The target domain or subdomain (e.g. `example.com`). The endpoint will resolve the value to its registrable domain or full subdomain and use that as the lookup key. |
| `metric` | string | Yes | — | The metric to compute. See Available Metrics for the full list. |

### Notes on `query`

The `query` field accepts both registrable domains and subdomains. Invalid query formats return a validation error. The resolved domain is echoed back in the response under the `target_domain` field so clients can confirm how the value was interpreted.

---

## Available Metrics

| Metric | Returns | Purpose |
|---|---|---|
| `consumer_count` | object | Total credentials captured on the target domain's websites, broken down by source. |
| `corporate_count` | object | Total credentials whose username belongs to the target domain's email domain, broken down by source. |
| `computer_count` | object | Number of distinct infected machines that touched the target domain in any way. |
| `ip_address_count` | object | Number of unique IP addresses that touched the target domain in any way. |
| `application_count` | object | Number of distinct applications (subdomains) of the target domain that have been observed in leaks. |
| `third_party_application_count` | object | Number of distinct external applications that the target domain's users have logged into using corporate credentials. |
| `applications` | array | Top 10 applications hosted on the target domain ranked by leaked credential volume. |
| `third_party_applications` | array | Top 10 external applications used by the target domain's employees ranked by leaked credential volume. |
| `consumer_incident_timeline` | array | Monthly timeline of consumer-side credential exposures from 2017 onward. |
| `corporate_incident_timeline` | array | Monthly timeline of corporate-side credential exposures from 2017 onward. |
| `latest_consumer_events` | array | Most recent consumer-side leak events by application and date. |
| `latest_corporate_events` | array | Most recent corporate-side leak events by application and date. |
| `country_stats` | array | Distribution of consumer-side leaked credentials by country of the infected machine. |

### Consumer vs. Corporate

Several metrics come in matched consumer and corporate variants. The distinction is the same as in the Consumer Leaks and Corporate Leaks endpoints:

- **Consumer** metrics match on the **website** where the credential was captured — they describe exposure of accounts on the target domain.
- **Corporate** metrics match on the **email domain of the username** — they describe exposure of the target organization's employees regardless of where the credential was captured.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_overall_stats.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "metric": "consumer_count"
  }'
```

---

## Response Schema

### Common Envelope

Every successful response uses the same outer structure:

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `remaining_daily_calls` | integer | Remaining requests on the daily quota for the current API key. |
| `target_domain` | string | The resolved domain or subdomain used for the lookup. |
| `results` | object or array | The metric payload. Shape depends on the requested metric. |

The shape of `results` is documented per metric below.

---

### Metric: `consumer_count`

Returns the total number of credentials captured on the target domain's websites, broken out by source.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": {
    "combolist_consumer_count": 12450,
    "stealer_consumer_count": 84210
  }
}
```

| Field | Type | Description |
|---|---|---|
| `combolist_consumer_count` | integer | Records sourced from credential combolists. |
| `stealer_consumer_count` | integer | Records sourced from infostealer logs. |

---

### Metric: `corporate_count`

Returns the total number of credentials whose username belongs to the target domain's email domain, broken out by source.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": {
    "stealer_corporate_count": 6841,
    "combolist_corporate_count": 1932
  }
}
```

| Field | Type | Description |
|---|---|---|
| `stealer_corporate_count` | integer | Records sourced from infostealer logs. |
| `combolist_corporate_count` | integer | Records sourced from credential combolists. |

---

### Metric: `computer_count`

Returns the number of distinct infected machines that have produced credential records associated with the target domain, either through the website domain or the email domain.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": { "computer_count": 1843 }
}
```

---

### Metric: `ip_address_count`

Returns the number of unique IP addresses observed across all infected machines associated with the target domain.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": { "ip_address_count": 1620 }
}
```

---

### Metric: `application_count`

Returns the number of distinct applications (resolved as subdomains of the target domain) that appear in leak records.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": { "application_count": 47 }
}
```

---

### Metric: `third_party_application_count`

Returns the number of distinct external applications that employees of the target domain have logged into using corporate credentials.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": { "third_party_application_count": 312 }
}
```

---

### Metric: `applications`

Returns the top 10 applications hosted on the target domain, ranked by credential exposure volume.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": [
    { "application": "portal.example.com", "count": 24180 },
    { "application": "mail.example.com", "count": 18203 },
    { "application": "vpn.example.com", "count": 9412 }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `application` | string | The application identifier (subdomain). |
| `count` | integer | Total credentials captured for that application. |

---

### Metric: `third_party_applications`

Returns the top 10 external applications used by employees of the target domain, ranked by credential exposure volume.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": [
    { "application": "login.example.net", "count": 5120 },
    { "application": "accounts.example.org", "count": 2840 },
    { "application": "code.example.net", "count": 1502 }
  ]
}
```

Field structure is identical to the `applications` metric.

---

### Metric: `consumer_incident_timeline`

Returns a monthly time series of consumer-side credential exposures from 2017 onward, broken out by source. Each (year, month, source) tuple is a separate entry.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": [
    { "Year": 2024, "Month": 1, "Count": 412, "source": "stealer" },
    { "Year": 2024, "Month": 1, "Count": 88, "source": "combolist" },
    { "Year": 2024, "Month": 2, "Count": 539, "source": "stealer" }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `Year` | integer | Year of the bucket. |
| `Month` | integer | Month of the bucket (1–12). |
| `Count` | integer | Number of credentials in that bucket. |
| `source` | string | Either `stealer` or `combolist`. |

Results are sorted ascending by year, then month.

---

### Metric: `corporate_incident_timeline`

Same schema as `consumer_incident_timeline`, but matched on the email domain of the username instead of the website domain.

---

### Metric: `latest_consumer_events`

Returns the most recent consumer-side leak events grouped by application and date, sorted descending by date.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": [
    { "application": "portal.example.com", "records": 142, "type": "stealer", "date": "2025-11-14" },
    { "application": "mail.example.com", "records": 88, "type": "stealer", "date": "2025-11-13" },
    { "application": "example.com", "records": 211, "type": "combolist", "date": "2025-11-12" }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `application` | string | The application identifier (subdomain). |
| `records` | integer | Number of records in that application/date group. |
| `type` | string | Either `stealer` or `combolist`. |
| `date` | string (date) | Date of the records. |

---

### Metric: `latest_corporate_events`

Same schema as `latest_consumer_events`, but matched on the email domain of the username instead of the website domain.

---

### Metric: `country_stats`

Returns the distribution of consumer-side leaked credentials by country of the infected machine. Sorted descending by record count.

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "example.com",
  "results": [
    { "country": "United States", "total": 18420 },
    { "country": "Germany", "total": 9201 },
    { "country": "Brazil", "total": 5188 }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `country` | string | Country attribution as recorded in the underlying stealer log. |
| `total` | integer | Total number of records associated with that country. |

---

### Empty Result Set

When a list-style metric returns no records, the endpoint responds with an empty array:

```json
{
  "success": true,
  "results": []
}
```

For scalar metrics (`consumer_count`, `corporate_count`, `computer_count`, `ip_address_count`, `application_count`, `third_party_application_count`), the response always contains the metric fields with values of `0` rather than an empty array.

---

## Error Responses

All error responses return a JSON body with either an `error` or `message` field describing the failure.

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method or non-JSON content type. | `{"error": "Invalid request method or content type, expected POST with application/json."}` |
| `403` | Missing API key. | `{"error": "API Key is missing."}` |
| `403` | Invalid API key. | `{"error": "Invalid API Key."}` |
| `403` | Subscription tier does not permit API access. | `{"error": "API calls are only available for Enterprise and Higher tiers. Please upgrade your account."}` |
| `200` | Daily quota exhausted. | `{"success": false, "message": "Daily API request limit exceeded."}` |
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Query is not a valid domain or subdomain. | `{"success": false, "error": "Invalid query format. It should be a valid domain or subdomain."}` |
| `200` | Unrecognized `metric` value. | `{"success": false, "error": "Invalid metric parameter. Accepted values are: consumer_count, corporate_count, ..."}` |

> Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Best Practices

- **Dashboard composition:** Issue parallel calls — one per metric — to assemble a multi-panel dashboard view. Each call is independent and consumes one quota credit.
- **Quota planning:** Budget for the number of metrics you display, not the number of dashboards rendered. A 12-tile dashboard is 12 calls per render. Consider caching results client-side for short windows when the same domain is viewed repeatedly.
- **Consumer vs. corporate:** Choose the matched pair (`consumer_count` + `corporate_count`, `applications` + `third_party_applications`, etc.) when building a comparative dashboard. Mixing them is the most common analyst-facing view of organizational exposure.
- **Timeline range:** Both timeline metrics return data from January 2017 onward. Filter or truncate client-side if a narrower window is required.
- **Subdomain queries:** Submitting a subdomain (e.g. `mail.example.com`) restricts results to that subdomain rather than rolling up to the registrable domain. Use the registrable domain (e.g. `example.com`) for organization-wide views.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response to anticipate quota exhaustion before it occurs.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
