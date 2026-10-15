# Threat Feed API (Sandbox)

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/threat-feed-api-sandbox
> date: 2026-10-15

Returns synthetic threat intelligence content. The endpoint supports three modes: dark web and telegram posts, public news, and taxonomy listings. The mode is selected through the `mode` and `taxonomy` parameters.

This sandbox endpoint mirrors the production `get_threat_feeds` endpoint in request format and response structure, and returns synthetic data only. In production this endpoint requires the Threat Feed add on. In the sandbox this requirement is relaxed so that trial keys may be used for integration testing.

## Endpoint

```
POST https://api.whiteintel.io/sandbox/get_threat_feeds.php
Content-Type: application/json
```

## Modes

|Mode|Selection|Description|
|---|---|---|
|Posts|Default, or any `mode` other than `public_news` when `taxonomy` is not set|Threat intelligence posts with optional filters.|
|Public News|`mode` set to `public_news`|Public security news items.|
|Taxonomy|`taxonomy` set to `categories`, `industries`, or `networks`|Distinct taxonomy values with counts. Takes precedence over `mode`.|

## Request Parameters

|Parameter|Type|Required|Default|Description|
|---|---|---|---|---|
|`apikey`|string|Yes||Your API key.|
|`mode`|string|No|posts|Selects the content mode. Set to `public_news` for the news feed.|
|`taxonomy`|string|No||When set, selects taxonomy mode. One of `categories`, `industries`, `networks`.|
|`page`|integer|No|`1`|Page number for pagination.|
|`limit`|integer|No|`100`|Page size. Range 1 to 100. Trial keys are capped at 20.|
|`start_date`|string|No||Inclusive start date in `YYYY-MM-DD` format.|
|`end_date`|string|No||Inclusive end date in `YYYY-MM-DD` format.|
|`search`|string|No||Free text search term. Minimum length 4 characters. Applies to posts and public news modes.|
|`category`|string or array|No||Filter by category. Accepts at most 2 values. Posts mode only.|
|`industry`|string or array|No||Filter by victim industry. Accepts at most 2 values. Posts mode only.|
|`network`|string or array|No||Filter by network. Multiple values are allowed. Posts mode only.|

## Posts Mode

### Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "category": ["ransomware", "data-leak"],
    "industry": "Manufacturing",
    "network": ["darkweb", "telegram"],
    "limit": 50
  }'
```

### Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`mode`|string|Always `posts` in this mode.|
|`remaining_threat_feed_calls`|integer|Remaining Threat Feed calls for the account. Reported for parity and not decremented in the sandbox.|
|`results`|array|List of post records, ordered by publication date, newest first.|

Each post record contains the following fields.

|Field|Type|Description|
|---|---|---|
|`id`|integer|Record identifier.|
|`uuid`|string|Record UUID.|
|`published_url`|string|Canonical URL of the post.|
|`title`|string|Post title.|
|`category`|string|Post category.|
|`network`|string|Source network.|
|`published_at`|string|Publication timestamp.|
|`description`|string|Post content.|
|`victim_organization`|string|Affected organization.|
|`victim_site`|string|Affected organization site.|
|`victim_domain`|string|Affected organization domain.|
|`victim_industry`|string|Affected organization industry.|
|`victim_country`|string|Affected organization country.|
|`threat_actor_names_cached`|string|Comma separated list of associated threat actors.|
|`tags_csv`|string|Comma separated list of tags.|
|`tags_norm_json`|array|Normalized tag list.|
|`threat_actors_norm_json`|array|Normalized threat actor list.|
|`screenshots_json`|array|Associated screenshot references.|

### Example Response

```json
{
  "success": true,
  "mode": "posts",
  "remaining_threat_feed_calls": 950,
  "results": [
    {
      "id": 142,
      "uuid": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
      "published_url": "https://sandbox.whiteintel.io/intel/142",
      "title": "Ransomware incident: Acme Corp (US)",
      "category": "ransomware",
      "network": "darkweb",
      "published_at": "2026-09-12 08:30:00",
      "description": "Synthetic threat intel record for sandbox testing.",
      "victim_organization": "Acme Corp",
      "victim_site": "https://www.acmecorp142.example",
      "victim_domain": "acmecorp142.example",
      "victim_industry": "Manufacturing",
      "victim_country": "US",
      "threat_actor_names_cached": "LockBit",
      "tags_csv": "ransomware,darkweb,manufacturing",
      "tags_norm_json": ["ransomware", "darkweb", "manufacturing"],
      "threat_actors_norm_json": ["LockBit"],
      "screenshots_json": []
    }
  ]
}
```

## Public News Mode

### Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "mode": "public_news",
    "limit": 50
  }'
```

### News Record Fields

|Field|Type|Description|
|---|---|---|
|`id`|integer|Record identifier.|
|`source`|string|Publication source.|
|`title`|string|Article title.|
|`summary`|string|Article summary.|
|`ai_summary`|string|Generated article summary.|
|`link`|string|Article link.|
|`published_at`|string|Publication timestamp.|
|`tags`|string|Comma separated tag list.|

### Example Response

```json
{
  "success": true,
  "mode": "public_news",
  "remaining_threat_feed_calls": 949,
  "results": [
    {
      "id": 57,
      "source": "Sandbox Threat Daily",
      "title": "Sandbox report: Ransomware campaign observed in demo telemetry #57",
      "summary": "Synthetic news summary about a ransomware campaign.",
      "ai_summary": "AI-generated demo summary for API testing only.",
      "link": "https://sandbox.whiteintel.io/news/57",
      "published_at": "2026-09-01 10:15:00",
      "tags": "ransomware,sandbox"
    }
  ]
}
```

## Taxonomy Mode

### Example Request

```bash
curl -X POST https://api.whiteintel.io/sandbox/get_threat_feeds.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "taxonomy": "categories"
  }'
```

### Response

|Field|Type|Description|
|---|---|---|
|`success`|boolean|Indicates whether the request was processed successfully.|
|`mode`|string|Always `taxonomy` in this mode.|
|`taxonomy`|string|The requested taxonomy.|
|`remaining_threat_feed_calls`|integer|Remaining Threat Feed calls for the account. Reported for parity and not decremented in the sandbox.|
|`results`|array|Distinct taxonomy values with counts, ordered by count descending then value ascending.|

Each taxonomy entry contains a `value` field and a `cnt` field, where `cnt` is returned as a string.

### Example Response

```json
{
  "success": true,
  "mode": "taxonomy",
  "taxonomy": "categories",
  "remaining_threat_feed_calls": 948,
  "results": [
    { "value": "ransomware", "cnt": "64" },
    { "value": "data-leak", "cnt": "41" }
  ]
}
```

## Error Responses

|HTTP Status|Condition|Body|
|---|---|---|
|400|Invalid JSON body|`{"error": "Invalid JSON body."}`|
|403|API key missing|`{"error": "API Key is missing."}`|
|403|API key invalid|`{"error": "Invalid API Key."}`|
|429|Requests sent too quickly|`{"message": "Please wait 5 seconds between requests."}`|
|200|Limit out of range|`{"success": false, "error": "Limit must be between 1 and 100."}`|
|400|More than two category values|`{"success": false, "error": "category accepts at most 2 values."}`|
|400|More than two industry values|`{"success": false, "error": "industry accepts at most 2 values."}`|
|400|Search term too short|`{"success": false, "error": "Search must be at least 4 characters long."}`|
|200|Invalid taxonomy value|`{"success": false, "error": "Invalid taxonomy. Use 'categories', 'industries', or 'networks'."}`|
|400|Non JSON or non POST request|`{"error": "Invalid request method or content type, expected POST with application/json."}`|

## Notes

All modes are served from a single consistent synthetic data set, so taxonomy counts agree with the number of posts that can be retrieved for each category, industry, and network. Date filters reduce taxonomy counts and post results together. Affected organizations and domains are fictional and use the reserved `.example` suffix. The same request returns the same records on every call.
