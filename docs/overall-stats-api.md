# Overall Stats API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/leak-discovery/overall-stats-api
> date: 2026-03-10

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

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. Although dashboards may request multiple metrics, this conservative default avoids bursty parallel calls that can trigger upstream interception.

Each API key is provisioned with a daily request quota. Remaining quota is returned in every successful response under `remaining_daily_calls`. Once the daily quota is exhausted, requests return a quota-exceeded message until the counter resets.

Each call consumes one daily quota credit, regardless of which metric is requested. Empty array results for list-style metrics (timelines, applications, recent events, country distribution) do not consume a credit. Empty count results for scalar metrics do consume a credit.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `apikey` | string | Yes | — | Your Whiteintel API key. |
| `query` | string | Yes | — | The target domain or subdomain (e.g. `acme.com`). The endpoint will resolve the value to its registrable domain or full subdomain and use that as the lookup key. |
| `metric` | string | Yes | — | The metric to compute. See Available Metrics for the full list. |

### Notes on `query`

The `query` field accepts both registrable domains and subdomains. Invalid query formats return a validation error. The resolved domain is echoed back in the response under the `target_domain` field so clients can confirm how the value was interpreted.

---

## Available Metrics

### Scalar Metrics (object response)

| Metric | Response Type | Description |
|---|---|---|
| `consumer_count` | object | Total credentials captured on the target domain's websites, broken down by source. |
| `corporate_count` | object | Total credentials whose username belongs to the target domain's email domain, broken down by source. |
| `computer_count` | object | Number of distinct infected machines that touched the target domain in any way. |
| `ip_address_count` | object | Number of unique IP addresses that touched the target domain in any way. |
| `application_count` | object | Number of distinct applications (subdomains) of the target domain that have been observed in leaks. |
| `third_party_application_count` | object | Number of distinct external applications that the target domain's users have logged into using corporate credentials. |

### List Metrics (array response)

| Metric | Response Type | Description |
|---|---|---|
| `applications` | array | Top 10 applications hosted on the target domain ranked by leaked credential volume. |
| `third_party_applications` | array | Top 10 external applications used by the target domain's employees ranked by leaked credential volume. |
| `consumer_incident_timeline` | array | Monthly timeline of consumer-side credential exposures from 2017 onward. |
| `corporate_incident_timeline` | array | Monthly timeline of corporate-side credential exposures from 2017 onward. |
| `latest_consumer_events` | array | Most recent consumer-side leak events by application and date. |
| `latest_corporate_events` | array | Most recent corporate-side leak events by application and date. |
| `country_stats` | array | Distribution of consumer-side leaked credentials by country of the infected machine. |

### Consumer vs. Corporate

- **Consumer** metrics match on the **website** where the credential was captured — they describe exposure of accounts on the target domain.
- **Corporate** metrics match on the **email domain of the username** — they describe exposure of the target organization's employees regardless of where the credential was captured.

---

## Request Example

```bash
curl -X POST https://api.whiteintel.io/get_overall_stats.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "acme.com",
    "metric": "consumer_count"
  }'
```

---

## Response Schema

### Outer Structure

Every successful response uses the same outer structure:

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `remaining_daily_calls` | integer | Remaining requests on the daily quota for the current API key. |
| `target_domain` | string | The resolved domain or subdomain used for the lookup. |
| `results` | object or array | The metric payload. Shape depends on the requested metric. |

### Metric-Specific Response Examples

#### `consumer_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": {
    "combolist_consumer_count": 12450,
    "stealer_consumer_count": 84210
  }
}
```

#### `corporate_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": {
    "stealer_corporate_count": 6841,
    "combolist_corporate_count": 1932
  }
}
```

#### `computer_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": { "computer_count": 1843 }
}
```

#### `ip_address_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": { "ip_address_count": 1620 }
}
```

#### `application_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": { "application_count": 47 }
}
```

#### `third_party_application_count`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": { "third_party_application_count": 312 }
}
```

#### `applications`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": [
    { "application": "portal.acme.com", "count": 24180 },
    { "application": "mail.acme.com", "count": 18203 },
    { "application": "vpn.acme.com", "count": 9412 }
  ]
}
```

#### `consumer_incident_timeline`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": [
    { "Year": 2024, "Month": 1, "Count": 412, "source": "stealer" },
    { "Year": 2024, "Month": 1, "Count": 88, "source": "combolist" },
    { "Year": 2024, "Month": 2, "Count": 539, "source": "stealer" }
  ]
}
```

#### `latest_consumer_events`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": [
    { "application": "portal.acme.com", "records": 142, "type": "stealer", "date": "2025-11-14" },
    { "application": "mail.acme.com", "records": 88, "type": "stealer", "date": "2025-11-13" }
  ]
}
```

#### `country_stats`

```json
{
  "success": true,
  "remaining_daily_calls": 4983,
  "target_domain": "acme.com",
  "results": [
    { "country": "United States", "total": 18420 },
    { "country": "Germany", "total": 9201 },
    { "country": "Brazil", "total": 5188 }
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
| `200` | Empty or missing `query`. | `{"success": false, "error": "Query can not be empty."}` |
| `200` | Query is not a valid domain or subdomain. | `{"success": false, "error": "Invalid query format. It should be a valid domain or subdomain."}` |
| `200` | Unrecognized `metric` value. | `{"success": false, "error": "Invalid metric parameter. Accepted values are: consumer_count, corporate_count, ..."}` |

---

## Best Practices

- **Dashboard composition:** Issue parallel calls — one per metric — to assemble a multi-panel dashboard view. Each call is independent and consumes one quota credit.
- **Quota planning:** A 12-tile dashboard is 12 calls per render. Consider caching results client-side for short windows when the same domain is viewed repeatedly.
- **Consumer vs. corporate:** Choose the matched pair when building a comparative dashboard.
- **Timeline range:** Both timeline metrics return data from January 2017 onward.
- **Subdomain queries:** Submitting a subdomain (e.g. `mail.acme.com`) restricts results to that subdomain. Use the registrable domain for organization-wide views.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
