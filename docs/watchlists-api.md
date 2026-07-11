# Watchlists API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/miscellaneous/watchlists-api
> date: 2025-12-10

## Base Information

- **Method:** `POST`
- **Endpoint:** `https://api.whiteintel.io/watchlist_manage.php`
- **Content-Type:** `application/json`
- **Auth:** API key in the request body (`apikey`)

```json
{
  "apikey": "YOUR_API_KEY",
  "action": "list"
}
```

---

## Rate Limits and Quotas

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. Watchlist add/remove operations mutate account state, so keeping the same conservative default as read-only endpoints avoids accidental bursts from MCP client concurrency.

---

## Supported Actions

The endpoint is action-based. Send an `action` field with one of:

- `list`
- `add`
- `remove`
- `enable`
- `disable`

---

## Entry Types & Access

Allowed `entry_type` values:

- `domain`
- `email`
- `computername` *(requires TIFirm plan)*
- `ip` *(requires TIFirm plan)*
- `keyword`
- `github_repo`

> Access to specific types depends on your subscription. If your plan doesn't include a type (e.g., TIFirm-only), the API returns a **403 Forbidden**.

---

## Integrations (Slack and Jira)

To enable Slack notification push:
```json
"push_to_slack": 1
```

To enable Jira push:
```json
"push_to_jira": 1
```

In order to set integrations, initial configuration must be completed via Web-ui under the Organizations page.

---

## Credits (Per Type)

- Adding a new watchlist item **consumes 1 credit** for that item's type.
- Removing an item **refunds 1 credit** for that type.
- Enabling/disabling **does not** change credits.

If no credits remain for a type, the API returns **402** with a generic balance-exhausted message.

---

## Request Schema

Every request must include your API key:

```json
{
  "apikey": "YOUR_API_KEY",
  "action": "list"
}
```

---

## Examples

### List watchlist items

```bash
curl -sL https://api.whiteintel.io/watchlist_manage.php \
  -H 'Content-Type: application/json' \
  --data '{"apikey":"YOUR_API_KEY","action":"list","type":"domain","status":"enabled","page":1,"limit":50}'
```

Response:
```json
{
  "success": true,
  "page": 1,
  "limit": 50,
  "total": 2,
  "results": [
    {
      "id": 987,
      "organizationid": 1337,
      "entry_type": "domain",
      "entry": "example.com",
      "added_by": "api:42",
      "added_at": "2025-09-07 03:21:45",
      "include_usernames": 0,
      "consumer_alerts": 1,
      "corporate_alerts": 1,
      "status": "enabled",
      "notify_email": "alerts@example.com",
      "updated_by": "api:42",
      "updated_at": "2025-09-07 03:21:45"
    },
    {
      "id": 988,
      "organizationid": 1337,
      "entry_type": "domain",
      "entry": "contoso.com",
      "added_by": "api:42",
      "added_at": "2025-09-07 04:10:02",
      "include_usernames": 0,
      "include_passwords": 0,
      "consumer_alerts": 1,
      "corporate_alerts": 1,
      "status": "enabled",
      "notify_email": "alerts@example.com",
      "updated_by": "api:42",
      "updated_at": "2025-09-07 04:10:02"
    }
  ]
}
```

### Add a watchlist item

```bash
curl -sL https://api.whiteintel.io/watchlist_manage.php \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey":"YOUR_API_KEY",
    "action":"add",
    "entry_type":"domain",
    "entry":"example.com",
    "notify_email":"alerts@example.com"
  }'
```

Response:
```json
{
  "success": true,
  "id": 1001,
  "entry_type": "domain",
  "entry": "example.com",
  "remaining_type_balance": 14
}
```

### Remove a watchlist item

```bash
curl -sL https://api.whiteintel.io/watchlist_manage.php \
  -H 'Content-Type: application/json' \
  --data '{
    "apikey":"YOUR_API_KEY",
    "action":"remove",
    "id":1001
  }'
```

Response:
```json
{
  "success": true,
  "id": 1001,
  "entry_type": "domain",
  "remaining_type_balance": 15,
  "message": "Removed."
}
```

---

## Error Examples

### Invalid / missing API key (403)

```json
{ "success": false, "error": "Unauthorized." }
```

### Invalid Request (400)

```json
{ "success": false, "error": "Invalid request." }
```

### Quota exceeded

```json
{ "success": false, "error": "Quota exceeded." }
```
