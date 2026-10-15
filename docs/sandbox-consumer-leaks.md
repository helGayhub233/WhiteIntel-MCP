# Consumer Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/consumer-leaks-sandbox
> date: 2026-10-15

Returns synthetic consumer credential exposure associated with a domain or subdomain. Consumer exposure represents credentials where the affected service belongs to the queried domain, regardless of the account holder.

This sandbox endpoint mirrors the production `get_consumer_leaks` endpoint in request format and response structure, and returns synthetic data only.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_consumer_leaks.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target domain or subdomain.|
|`type`|string|No|`all`|Data source. One of `all`, `stealer`, `combolist`.|
|`include_system_info`|integer|No|`0`|When set to `1`, stealer records include machine fields. Applies to stealer records only.|
|`limit`|integer|No|`500`|Maximum records per source. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Must be supplied together with `start_date`.|
|`username`|string|No||Optional exact match filter on the username field.|
|`subdomain`|string|No||Optional exact match filter on the normalized subdomain.|
|`mask_password`|integer|No|`0`|When set to `1`, the password field is omitted from all records.|

When `type` is `all`, the endpoint returns up to `limit` records from each source and merges them into a single list ordered by date, newest first.

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_consumer_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "type": "all",
    "include_system_info": 1,
    "limit": 100,
    "page": 1
  }'
```

## Response

A successful response returns an object containing the result list and the current remaining daily call count.

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|List of exposure records.|

### Stealer Record Fields

|Field|Type|Description|
|---|---|---|
|`data_type`|string|Always `stealer`.|
|`url`|string|The affected service URL.|
|`log_id`|integer|Identifier of the source stealer log.|
|`username`|string|The exposed username.|
|`password`|string|The exposed password. Omitted when `mask_password` is `1`.|
|`log_date`|string|Date associated with the record.|
|`hostname`|string|Machine hostname. Present only when `include_system_info` is `1`.|
|`ip`|string|Machine IP address. Present only when `include_system_info` is `1`.|
|`malware_path`|string|Path of the infection artifact. Present only when `include_system_info` is `1`.|
|`anti_virus`|string|Antivirus product reported for the machine. Present only when `include_system_info` is `1`.|

### Combolist Record Fields

|Field|Type|Description|
|---|---|---|
|`data_type`|string|Always `combolist`.|
|`url`|string|The affected service URL.|
|`username`|string|The exposed username.|
|`password`|string|The exposed password. Omitted when `mask_password` is `1`.|
|`log_date`|string|Date associated with the record.|

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4821,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://portal.example.com/login",
      "log_id": 58302917,
      "username": "elena.kaya@gmail.com",
      "password": "Sunshine1987!",
      "log_date": "2026-09-27 14:03:51",
      "hostname": "DESKTOP-3F9A1C7",
      "ip": "198.51.100.42",
      "malware_path": "C:\\Users\\Elena\\AppData\\Local\\Temp\\b82e0d41.exe",
      "anti_virus": "Windows Defender"
    },
    {
      "data_type": "combolist",
      "url": "https://example.com/signin",
      "username": "kenji_sato57",
      "password": "Dragon412",
      "log_date": "2026-09-25 08:41:12"
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
|429|Requests sent too quickly|`{"message": "Please wait 5 seconds between requests."}`|
|200|Invalid `type` value|`{"success": false, "error": "Invalid type. Allowed values are: 'all', 'stealer', 'combolist'."}`|
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Only one date supplied|`{"success": false, "error": "Both start_date and end_date must be provided together."}`|
|200|Invalid date format|`{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

The sandbox returns deterministic synthetic records for each query. The same domain returns the same records on every call, which allows pagination and filtering to be validated consistently. A query that does not resolve to a valid domain returns an empty result set.
