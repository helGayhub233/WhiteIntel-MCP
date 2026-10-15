# Computer Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/computer-leaks-sandbox
> date: 2026-10-15

Returns synthetic stealer exposure associated with a specific machine hostname. This endpoint is used to retrieve the credentials harvested from a single infected host.

This sandbox endpoint mirrors the production `get_leaks_by_computer_name` endpoint in request format and response structure, and returns synthetic data only. In production this endpoint is restricted to Threat Intelligence licenses. In the sandbox this restriction is relaxed so that trial keys may be used for integration testing.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_leaks_by_computer_name.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target machine hostname.|
|`limit`|integer|No|`500`|Maximum records. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Must be supplied together with `start_date`.|
|`mask_password`|integer|No|`0`|When set to `1`, the password field is omitted from all records.|

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_leaks_by_computer_name.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "DESKTOP-3F9A1C7",
    "limit": 100
  }'
```

## Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|List of stealer records associated with the queried hostname.|

All records are of type `stealer` and always include the machine fields. Every record carries the hostname supplied in the query.

|Field|Type|Description|
|---|---|---|
|`data_type`|string|Always `stealer`.|
|`url`|string|The affected service URL.|
|`username`|string|The exposed username.|
|`password`|string|The exposed password. Omitted when `mask_password` is `1`.|
|`hostname`|string|The machine hostname. Matches the query.|
|`ip`|string|The machine IP address.|
|`malware_path`|string|Path of the infection artifact.|
|`anti_virus`|string|Antivirus product reported for the machine.|
|`log_id`|integer|Identifier of the source stealer log.|
|`log_date`|string|Effective date associated with the record.|

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4799,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://accounts.google.com/signin",
      "username": "james.smith@gmail.com",
      "password": "Freedom2020!",
      "hostname": "DESKTOP-3F9A1C7",
      "ip": "198.51.100.42",
      "malware_path": "C:\\Users\\James\\AppData\\Local\\Temp\\b82e0d41.exe",
      "anti_virus": "Windows Defender",
      "log_id": 58302917,
      "log_date": "2026-05-14"
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
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Only one date supplied|`{"success": false, "error": "Both start_date and end_date must be provided together."}`|
|200|Invalid date format|`{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

A hostname represents a single machine. The sandbox models each queried hostname as one host with a fixed owner, IP address, and antivirus product across one or more infection events, each of which harvested a set of credentials. The same hostname returns the same records on every call.
