# Database Leaks API (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/database-leaks-api-sandbox
> date: 2026-10-15

Returns synthetic database leak records associated with a domain. Database leaks represent credentials exposed through third party database breaches rather than through stealer logs or combolists. Results are grouped by the source database in which the records were found.

This sandbox endpoint mirrors the production `get_third_party_db_leaks` endpoint in request format and response structure, and returns synthetic data only. In production this endpoint is restricted to Enterprise and Threat Intelligence licenses. In the sandbox this restriction is relaxed so that trial keys may be used for integration testing.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_third_party_db_leaks.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target domain.|
|`limit`|integer|No|`500`|Maximum number of account records returned across all databases. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination. Pagination spans databases in sequence.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Applied to the breach date. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Applied to the breach date. Must be supplied together with `start_date`.|

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_third_party_db_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "limit": 100
  }'
```

## Response

A successful response returns a list of source databases, each with the account records found within it.

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox. Omitted when the result set is empty.|
|`results`|array|List of source databases. Each entry contains its own account records.|

### Database Entry Fields

|Field|Type|Description|
|---|---|---|
|`database_name`|string|Name of the source database.|
|`breach_date`|string|Date associated with the breach.|
|`breach_description`|string|Description of the source database.|
|`data_fields`|string|Comma separated list of the fields present in the source database.|
|`total`|integer|Total number of account records available for this database.|
|`page`|integer|The requested page number.|
|`limit`|integer|The requested page size.|
|`accounts`|array|Account records for this database.|

### Account Record Fields

|Field|Type|Description|
|---|---|---|
|`id`|integer|Record identifier.|
|`email`|string|The exposed email address, on the queried domain.|
|`password`|string or null|The exposed password, or `null` when the source database does not provide it.|
|`hashed_password`|string or null|The exposed password hash, or `null` when the source database does not provide it.|

### Example Response

```json
{
  "success": true,
  "remaining_daily_calls": 4755,
  "results": [
    {
      "database_name": "ExampleShop 2023",
      "breach_date": "2024-11-03",
      "breach_description": "E-commerce platform breach exposing customer accounts.",
      "data_fields": "email, password, hashed_password",
      "total": 214,
      "page": 1,
      "limit": 100,
      "accounts": [
        {
          "id": 8419273,
          "email": "jsmith@example.com",
          "password": "Welcome2021",
          "hashed_password": "$2y$10$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2"
        }
      ]
    },
    {
      "database_name": "Forum Dump 2022",
      "breach_date": "2022-06-14",
      "breach_description": "Online forum database leak with salted password hashes.",
      "data_fields": "email, hashed_password",
      "total": 88,
      "page": 1,
      "limit": 100,
      "accounts": [
        {
          "id": 5120934,
          "email": "mdemir@example.com",
          "password": null,
          "hashed_password": "$2y$10$c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4"
        }
      ]
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
|429|Requests sent too quickly|`{"message": "Please wait 1 seconds between requests."}`|
|200|Empty query|`{"success": false, "error": "Query cannot be empty."}`|
|200|Only one date supplied|`{"success": false, "error": "Both start_date and end_date must be provided together."}`|
|200|Invalid date format|`{"success": false, "error": "Invalid date format. Use YYYY-MM-DD."}`|
|200|Invalid limit|`{"success": false, "error": "Limit must be an integer between 1 and 5000."}`|
|200|Restricted query|`{"success": false, "error": "This query is restricted."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

Results are grouped by source database. A given database may provide only one of the password or hashed password fields, in which case the other is returned as `null`. The `limit` parameter caps the total number of account records across all databases, and pagination advances through the databases in sequence. The same domain returns the same databases and records on every call. A domain with no database leaks returns an empty result set.
