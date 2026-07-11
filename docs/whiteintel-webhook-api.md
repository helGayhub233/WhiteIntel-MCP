# WhiteIntel Webhook API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/webhooks/whiteintel-webhook-api
> date: 2025-07-10

WhiteIntel webhooks allow your organization to receive **real-time alerts** when your **watchlist items** (such as domains, IPs, hostnames, or emails) are detected in leaked stealer logs.

---

## Setup

To configure a webhook:

1. Go to your **WhiteIntel dashboard**.
2. Set your receiving **HTTPS endpoint**.
3. A secure **HMAC secret** will be auto-generated.

> **⚠️ Note:** Configuring a webhook will override any existing configuration.

### Endpoint Requirements

- Must use `https://` (or `http://` in dev/test).
- Must not point to internal/private addresses (e.g. `localhost`, `.local`, `127.0.0.1`).
- Must not target WhiteIntel-owned domains.

---

## Security & Signature

Every webhook POST is signed with an **HMAC SHA256** signature.

> **⚠️ NEVER PROCESS THE REQUEST BEFORE VERIFYING THE SIGNATURE.**

### Request Headers

| Header | Description |
|---|---|
| `X-Signature` | Base64-encoded HMAC signature. |
| `X-Signature-Version` | Currently always `v1`. |
| `X-Timestamp` | ISO 8601 UTC timestamp. |
| `User-Agent` | Always `WhiteIntel-Webhook`. |

### Signature Generation

```
signature = base64(HMAC_SHA256(timestamp, secret_key))
```

The signature is computed over the timestamp value using your HMAC secret key. You must verify this signature on your end before processing any webhook payload.

See [Signature Validation](/docs/signature-validation-api.md) for implementation examples across multiple languages.

---

## Events & Payload Structure

Webhook notifications are triggered for the following watchlist match types:

| Type | Description |
|---|---|
| `consumer` | Consumer credentials found for a watched domain. |
| `corporate` | Corporate credentials found for a watched domain. |
| `email` | Credentials found for a watched email address. |
| `ip` | Infected machine found for a watched IP address. |
| `hostname` | Infected machine found for a watched hostname. |

### Common Payload Fields

| Field | Type | Description |
|---|---|---|
| `type` | string | The match type (`consumer`, `corporate`, `email`, `ip`, `hostname`). |
| `value` | string | The watchlist entry that triggered the alert. |
| `description` | string | Human-readable description of the alert. |
| `count` | integer | Number of credentials or events detected. |
| `event_date` | string (datetime) | The date the event was recorded. |
| `source` | string | Always `watchlist_monitor`. |
| `usernames` | array | Pairs of `[username, count]` showing affected accounts (present for `consumer`, `corporate`, and `email` types). |

### Consumer Event

```json
{
  "type": "consumer",
  "value": "example.com",
  "description": "As part of WhiteIntel's dark web surveillance, the specified consumer accounts have been found exposed in stolen credentials.",
  "count": 8,
  "usernames": [
    ["user2@gmail.com", 5],
    ["user1@gmail.com", 3]
  ],
  "event_date": "2025-04-10 12:00:00",
  "source": "watchlist_monitor"
}
```

### Corporate Event

```json
{
  "type": "corporate",
  "value": "internal.corp.com",
  "description": "As part of WhiteIntel's dark web surveillance, the specified corporate accounts have been found exposed in stolen credentials.",
  "count": 5,
  "usernames": [
    ["ceo@corp.com", 2],
    ["it@corp.com", 1]
  ],
  "event_date": "2025-04-10 12:00:00",
  "source": "watchlist_monitor"
}
```

### Email Event

```json
{
  "type": "email",
  "value": "staff@example.com",
  "description": "As part of WhiteIntel's dark web surveillance, the specified email address has been found exposed in stolen credentials.",
  "count": 2,
  "usernames": [
    ["staff@example.com", 2]
  ],
  "event_date": "2025-04-10 06:00:00",
  "source": "watchlist_monitor"
}
```

### IP Event

```json
{
  "type": "ip",
  "value": "192.0.2.1",
  "description": "As part of WhiteIntel's dark web monitoring, the following IP addresses have been identified as compromised by stealer malware.",
  "count": 1,
  "event_date": "2025-04-10 08:00:00",
  "source": "watchlist_monitor"
}
```

### Hostname Event

```json
{
  "type": "hostname",
  "value": "DESKTOP-HACKED01",
  "description": "As part of WhiteIntel's dark web monitoring, the specified Computer name have been identified as compromised by stealer malware.",
  "count": 1,
  "event_date": "2025-04-10 07:00:00",
  "source": "watchlist_monitor"
}
```

---

## Webhook Simulation

To simulate webhook calls before deploying to production, visit your Webhook page on the WhiteIntel platform. The simulation tool sends test payloads to your configured endpoint so you can validate your receiving logic and signature verification.

---

## Support

For technical questions or integration assistance, contact `info@whiteintel.io`.
