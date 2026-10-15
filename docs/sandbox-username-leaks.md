# Username Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/username-leaks-sandbox
> date: 2026-10-15

<!-- TODO(sync-with-official): this page names the database record field
`database_description`, while the production page (username-leaks-api.md)
uses `description` for the same record type. Align both mirrors and the tool
documentation once the official pages settle on one field name. -->

Returns synthetic exposure associated with a specific username or email address, across the stealer, combolist, and database leak sources.

This sandbox endpoint mirrors the production `get_leaks_by_username` endpoint in request format and response structure, and returns synthetic data only.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_leaks_by_username.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target username or email address.|
|`type`|string|No|`all`|Data source. One of `all`, `stealer`, `combolist`, `database`. The alias `data_type` is also accepted. The legacy value `both` is treated as `all`, and the legacy value `db` is treated as `database`.|
|`include_system_info`|integer|No|`0`|When set to `1`, stealer records include machine fields.|
|`limit`|integer|No|`500`|Maximum records. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Must be supplied together with `start_date`.|
|`mask_password`|integer|No|`0`|When set to `1`, password fields are omitted. For database records this omits both the password and the hashed password.|

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_leaks_by_username.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "james.smith@example.com",
    "type": "all",
    "limit": 100
  }'
```

## Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|Flat list of exposure records across all requested sources, ordered by date, newest first.|

The `results` array may contain records of three types. All records carry the queried username in the `username` field.

### Stealer and Combolist Record Fields

Stealer and combolist records follow the field structure documented in the Consumer Leaks endpoint. Stealer records include machine fields when `include_system_info` is `1`.

### Database Record Fields

|Field|Type|Description|
|---|---|---|
|`data_type`|string|Always `database`.|
|`username`|string|The queried username.|
|`password`|string or null|The exposed password, or `null` when the source database does not provide it. Omitted entirely when `mask_password` is `1`.|
|`hashed_password`|string or null|The exposed password hash, or `null` when the source database does not provide it. Omitted entirely when `mask_password` is `1`.|
|`database_name`|string|Name of the source database.|
|`database_description`|string|Description of the source database.|
|`log_date`|string|Breach date associated with the record.|

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4777,
  "results": [
    {
      "data_type": "stealer",
      "url": "https://github.com/login",
      "username": "james.smith@example.com",
      "password": "Welcome2024.",
      "log_id": 83561024,
      "log_date": "2026-08-02"
    },
    {
      "data_type": "database",
      "username": "james.smith@example.com",
      "password": "Dragon412",
      "hashed_password": null,
      "database_name": "Collection #1",
      "database_description": "Large aggregated credential collection circulated on hacking forums.",
      "log_date": "2025-03-18"
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
|200|Invalid `type` value|`{"success": false, "error": "Invalid type. Allowed values are: 'all', 'stealer', 'combolist', 'database'."}`|
|200|Empty query|`{"success": false, "error": "Query can not be empty."}`|
|200|Only one date supplied|`{"success": false, "error": "Both start_date and end_date must be provided together."}`|
|200|Invalid date format|`{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

The sandbox generates an independent synthetic record set for each source, so a given username may be present in one source and absent from another. The same username returns the same records on every call. Database records are returned as flat entries within the combined result list.
