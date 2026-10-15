# IP Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/ip-leaks-sandbox
> date: 2026-10-15

Returns synthetic stealer exposure associated with a specific IP address. This endpoint is used to retrieve the credentials harvested from hosts observed at a given IP address.

This sandbox endpoint mirrors the production `get_leaks_by_ip` endpoint in request format and response structure, and returns synthetic data only. In production this endpoint is restricted to Threat Intelligence licenses. In the sandbox this restriction is relaxed so that trial keys may be used for integration testing.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_leaks_by_ip.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target IP address. Both IPv4 and IPv6 are accepted.|
|`limit`|integer|No|`500`|Maximum records. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Must be supplied together with `start_date`.|
|`mask_password`|integer|No|`0`|When set to `1`, the password field is omitted from all records.|

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_leaks_by_ip.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "198.51.100.42",
    "limit": 100
  }'
```

## Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|List of stealer records associated with the queried IP address.|

All records are of type `stealer` and always include the machine fields. Every record carries the IP address supplied in the query. The record fields are identical to those documented in the Computer Name Leaks endpoint.

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4788,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://www.paypal.com/signin",
      "username": "maria.garcia@outlook.com",
      "password": "Galaxy808#",
      "hostname": "DESKTOP-A04E9B2",
      "ip": "198.51.100.42",
      "malware_path": "C:\\Users\\Maria\\Downloads\\9c1f7a30.exe",
      "anti_virus": "ESET NOD32",
      "log_id": 71640385,
      "log_date": "2026-07-19"
    }
  ]
}
```

### Empty Result

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
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Invalid IP address|`{"success": false, "error": "Invalid IP address."}`|
|200|Only one date supplied|`{"success": false, "error": "Both start_date and end_date must be provided together."}`|
|200|Invalid date format|`{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

A single IP address may be associated with more than one host. The sandbox models each queried IP address as one or more machines sharing that address, each with its own hostname, owner, and infection artifact. The queried IP address is returned on every record. The same IP address returns the same records on every call. This endpoint does not apply a per request rate limit.
