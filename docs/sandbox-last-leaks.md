# Get Last Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/get-last-leaks-sandbox
> date: 2026-10-15

Returns synthetic credential exposure for a domain within a rolling recent time window, covering both consumer and corporate exposure and both the stealer and combolist sources. This endpoint is intended for monitoring recent activity.

This sandbox endpoint mirrors the production `get_last_leaks` endpoint in request format and response structure, and returns synthetic data only.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_last_leaks.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target domain or subdomain.|
|`days`|integer|Yes||Size of the recent window in days. Range 1 to 30.|
|`data_type`|string|No|`all`|Data source. One of `all`, `stealer`, `combolist`.|
|`breach_type`|string|No|`all`|Exposure class. One of `all`, `consumer`, `corporate`.|
|`limit`|integer|No|`500`|Maximum records per source. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`sortBy`|string|No|`index_date`|Controls the stealer date column used for filtering and ordering. One of `index_date` or `log_date`. This affects stealer records only. Combolist records always use their log date.|
|`mask_password`|integer|No|`0`|When set to `1`, the password field is omitted from all records.|

System information fields are always included on stealer records for this endpoint.

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_last_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "days": 7,
    "data_type": "all",
    "breach_type": "all",
    "limit": 100
  }'
```

## Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|List of exposure records, ordered by date, newest first.|

Each record carries both a `data_type` field (`stealer` or `combolist`) and a `breach_type` field (`consumer` or `corporate`), in addition to the standard record fields documented in the Consumer Leaks endpoint. Stealer records always include the machine fields `hostname`, `ip`, `malware_path`, and `anti_virus`.

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4810,
  "results": [
    {
      "data_type": "stealer",
      "breach_type": "corporate",
      "url": "https://vpn.example.com/",
      "log_id": 40918273,
      "username": "mdemir@example.com",
      "password": "Istanbul1453.",
      "log_date": "2026-09-28 19:05:13",
      "hostname": "DESKTOP-7B2E04F",
      "ip": "192.0.2.87",
      "malware_path": "C:\\Users\\Mehmet\\AppData\\Roaming\\e41a9c07.exe",
      "anti_virus": "Windows Defender"
    },
    {
      "data_type": "combolist",
      "breach_type": "consumer",
      "url": "https://example.com/login",
      "username": "sarah.chen@gmail.com",
      "password": "Welcome2023!",
      "log_date": "2026-09-27 11:22:47"
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
|200|Invalid `data_type` value|`{"success": false, "error": "Invalid data type. Allowed values are: 'all', 'stealer', 'combolist'."}`|
|200|Invalid `breach_type` value|`{"success": false, "error": "Invalid breach type. Allowed values are: 'all', 'consumer', 'corporate'."}`|
|200|Invalid or missing `days`|`{"success": false, "error": "The days parameter must be an integer between 1 and 30."}`|
|200|Invalid `sortBy` value|`{"success": false, "error": "Invalid sortBy value. sortBy can only be index_date or log_date."}`|
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

The `days` window is observable in the sandbox. Synthetic records are distributed across the recent period, so a smaller window returns fewer records than a larger one. The `sortBy` value changes both which stealer records fall inside the window and their ordering, because stealer records carry an index date that can differ from their log date. This endpoint does not apply a per request rate limit.
