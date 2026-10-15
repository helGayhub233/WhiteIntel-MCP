# Corporate Leaks (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/corporate-leaks-sandbox
> date: 2026-10-15

<!-- TODO(sync-with-official): the production corporate leaks page
(corporate-leaks-api.md), the OpenAPI spec, and the MCP request model do not
yet document this page's `type: "database"` value, `include_database_leaks`
parameter, or `database_leaks` response object. Align the production page and
the model when the official production documentation catches up. -->

Returns synthetic corporate credential exposure associated with a domain. Corporate exposure represents credentials belonging to accounts on the queried domain, across any affected service. This endpoint also supports database leak records.

This sandbox endpoint mirrors the production `get_corporate_leaks` endpoint in request format and response structure, and returns synthetic data only.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_corporate_leaks.php
Content-Type: application/json
```

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`query`|string|Yes||Target domain.|
|`type`|string|No|`all`|Data source. One of `all`, `stealer`, `combolist`, `database`. The alias `data_type` is also accepted.|
|`include_system_info`|integer|No|`0`|When set to `1`, stealer records include machine fields.|
|`include_database_leaks`|integer|No|`0`|When set to `1` and `type` is `all`, database leaks are included under a separate `database_leaks` object.|
|`limit`|integer|No|`500`|Maximum records. Range 1 to 5000. Trial keys are capped at 20.|
|`page`|integer|No|`1`|Page number for pagination.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format. Must be supplied together with `end_date`.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format. Must be supplied together with `start_date`.|
|`mask_password`|integer|No|`0`|When set to `1`, password fields are omitted. For database records this omits both the password and the hashed password.|

## Response Structure by Type

The response shape depends on the requested `type`.

For `type` values `all`, `stealer`, and `combolist`, the `results` field is a flat array of records. For `type` value `database`, the `results` field is an object grouped by source database. When `type` is `all` and `include_database_leaks` is `1`, database leaks are returned under a separate top level `database_leaks` object, because their structure differs from the flat record array.

## Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_corporate_leaks.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "query": "example.com",
    "type": "all",
    "include_system_info": 1,
    "include_database_leaks": 1,
    "limit": 100
  }'
```

## Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`remaining_daily_calls`|integer|Remaining daily calls for the account. Reported for parity and not decremented in the sandbox.|
|`results`|array or object|Record list for stealer and combolist sources, or a grouped object for the database source.|
|`database_leaks`|object|Present only when `type` is `all` and `include_database_leaks` is `1`.|

### Stealer and Combolist Record Fields

Stealer and combolist records follow the same field structure as the Consumer Leaks endpoint. Stealer records include machine fields when `include_system_info` is `1`.

### Database Leak Structure

|Field|Type|Description|
|---|---|---|
|`database_results`|array|List of source databases, each with its own account list.|
|`total_databases`|integer|Number of source databases returned.|

Each entry in `database_results` contains the following fields.

|Field|Type|Description|
|---|---|---|
|`database_name`|string|Name of the source database.|
|`breach_date`|string|Date associated with the breach.|
|`breach_description`|string|Description of the source database.|
|`data_fields`|string|Comma separated list of the fields present in the source database.|
|`total`|integer|Total number of accounts available for this database.|
|`page`|integer|The requested page number.|
|`limit`|integer|The requested page size.|
|`accounts`|array|Account records for this database.|

Each account record contains an `id`, an `email`, and, unless masked, a `password` and a `hashed_password`. A given database may provide only one of these two credential fields, in which case the other is returned as `null`.

### Example Response for a Database Query

```json
{
  "success": true,
  "remaining_daily_calls": 4820,
  "results": {
    "database_results": [
      {
        "database_name": "ExampleShop 2023",
        "breach_date": "2024-11-03",
        "breach_description": "E-commerce platform breach exposing customer accounts.",
        "data_fields": "email, password, hashed_password",
        "total": 214,
        "page": 1,
        "limit": 50,
        "accounts": [
          {
            "id": 8419273,
            "email": "schen@example.com",
            "password": "Welcome2021",
            "hashed_password": "$2y$10$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2"
          }
        ]
      }
    ],
    "total_databases": 1
  }
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

Synthetic usernames for corporate records are always addresses on the queried domain. Database leak results are grouped by source database, and pagination spans databases in sequence. The same query returns the same records on every call.
