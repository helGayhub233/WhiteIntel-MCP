# Overall Stats (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/overall-stats-sandbox
> date: 2026-10-15

Returns synthetic aggregated exposure statistics for a domain. The endpoint is metric driven. A single metric is requested per call, and the response structure depends on the metric.

This sandbox endpoint mirrors the production `get_overall_stats` endpoint in request format and response structure, and returns synthetic data only.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_overall_stats.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target domain or subdomain.|
|`metric`|string|Yes||The metric to retrieve. See the list below.|

## Available Metrics

|Metric|Result Shape|Description|
|---|---|---|
|`consumer_count`|object|Consumer exposure counts for the stealer and combolist sources.|
|`corporate_count`|object|Corporate exposure counts for the stealer and combolist sources.|
|`computer_count`|object|Number of distinct machines associated with the domain.|
|`ip_address_count`|object|Number of distinct IP addresses associated with the domain.|
|`application_count`|object|Number of distinct applications associated with the domain.|
|`third_party_application_count`|object|Number of distinct third party applications associated with the domain.|
|`consumer_incident_timeline`|array|Monthly consumer exposure counts by source.|
|`corporate_incident_timeline`|array|Monthly corporate exposure counts by source.|
|`applications`|array|Top applications by exposure count.|
|`third_party_applications`|array|Top third party applications by exposure count.|
|`latest_consumer_events`|array|Most recent consumer exposure events.|
|`latest_corporate_events`|array|Most recent corporate exposure events.|
|`country_stats`|array|Exposure counts grouped by country.|

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_overall_stats.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "metric": "consumer_count"
  }'
```

## Response

A successful response contains the requested metric result together with the resolved target domain.

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox.|
|`target_domain`|string|The resolved registrable domain or subdomain.|
|`results`|object or array|The metric result. The shape depends on the requested metric.|

### Example Response for a Count Metric

```json
{
  "success": true,
  "remaining_daily_calls": 4766,
  "target_domain": "example.com",
  "results": {
    "combolist_consumer_count": 183402,
    "stealer_consumer_count": 29517
  }
}
```

### Example Response for an Incident Timeline Metric

```json
{
  "success": true,
  "remaining_daily_calls": 4765,
  "target_domain": "example.com",
  "results": [
    {
      "Year": "2025",
      "Month": "11",
      "Count": "812",
      "source": "stealer"
    },
    {
      "Year": "2025",
      "Month": "11",
      "Count": "2043",
      "source": "combolist"
    }
  ]
}
```

### Example Response for an Applications Metric

```json
{
  "success": true,
  "remaining_daily_calls": 4764,
  "target_domain": "example.com",
  "results": [
    { "application": "mail.example.com", "count": 3821 },
    { "application": "vpn.example.com", "count": 1944 }
  ]
}
```

### Example Response for the Country Statistics Metric

```json
{
  "success": true,
  "remaining_daily_calls": 4763,
  "target_domain": "example.com",
  "results": [
    { "country": "United States", "total": "4120" },
    { "country": "Brazil", "total": "2875" }
  ]
}
```

### Empty Result

Array based metrics may return an empty list. Count based metrics always return their full object, including when all values are zero.

```json
{
  "success": true,
  "results": []
}
```

## Error Responses

|HTTP Status|Condition|Body|
|---|---|---|
|403|API key missing|`{"error": "API Key is missing."}`|
|403|API key invalid|`{"error": "Invalid API Key."}`|
|200|Invalid JSON body|`{"success": false, "error": "Invalid JSON payload."}`|
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Empty metric|`{"success": false, "error": "Metric can not be empty."}`|
|200|Invalid query format|`{"success": false, "error": "Invalid query format. It should be a valid domain or subdomain."}`|
|200|Unrecognized metric|`{"success": false, "error": "Invalid metric parameter. Accepted values are: ..."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

All metrics for a given domain are generated from a single consistent synthetic profile. The application count agrees with the number of applications returned by the applications metric, events reference only applications that exist in that profile, and date filtered results scale together. The same domain returns the same statistics on every call. Responses are pretty printed to match production.
