# Card Check API

> Source: https://docs.whiteintel.io/whiteintel-api-doc/payment-fraud-intelligence/card-check-api
> date: 2026-06-13

The Card Check endpoint provides programmatic access to WhiteIntel's exposed payment card intelligence. It allows authorized clients to query compromised card records that have been identified across infostealer logs and dark web sources, filtered by issuer identification number (BIN), issuing institution, country, and a range of card attributes.

This endpoint is part of the Payment Fraud Intelligence module and requires a license with payment fraud access enabled.

---

## Endpoint

```
POST https://api.whiteintel.io/card_check.php
```

### Headers

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |

---

## Authentication

Authentication is performed using your API key, supplied in the request body. The API key must belong to an account with the Payment Fraud Intelligence module enabled.

```json
{
  "apikey": "YOUR_API_KEY",
  "bin": "424242"
}
```

Requests that omit the API key, supply an invalid key, or originate from an account without payment fraud access will be rejected with an appropriate error response.

---

## Privacy and Data Handling

This endpoint never returns cardholder names. Card records are returned with partial card identifiers (BIN and last four digits only) alongside non-sensitive metadata such as issuer, country, network, and card classification. Full primary account numbers (PAN), security codes, and cardholder names are not exposed through this API under any circumstance.

---

## Access Requirements

Access is governed by a daily call quota associated with your API key. Each request to this endpoint consumes one call from your daily allowance, regardless of the number of records returned. The `remaining_daily_calls` field reports your remaining quota after the current request.

When the daily limit is reached, further requests are rejected until the quota resets. To request a higher limit, contact your account representative.

Default request throttle is `0.2 QPS` (1 request every 5 seconds) per account/API key. The fixed 20-record page size can encourage repeated pagination, so clients should keep this default unless the upstream account explicitly allows a higher burst rate.

---

## Request Parameters

### Primary Selector (exactly one required)

Exactly one primary selector must be supplied per request. Supplying zero or more than one will result in a validation error.

| Parameter | Type | Description |
|---|---|---|
| `bin` | string | A 6-digit or 8-digit Bank Identification Number. Non-digit characters are stripped automatically. A 6-digit value matches against the card BIN; an 8-digit value matches against the extended BIN. |
| `issuer` | string | The name of the issuing institution. Matching is case-insensitive and partial. Must be between 3 and 100 characters. |
| `country` | string | The issuing country. A 2-character value is treated as an ISO 3166-1 alpha-2 country code and matched exactly. A longer value is treated as a country name and matched partially. |

### Optional Filters

Any combination of the following filters may be applied in addition to the primary selector. Filters are combined using logical AND semantics.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `networks` | array | — | Restrict results to the specified card networks, e.g. `["VISA", "MASTERCARD"]`. Case-insensitive. Maximum 10 values. |
| `types` | array | — | Restrict results to the specified card types, e.g. `["credit", "debit"]`. Case-insensitive. Maximum 10 values. |
| `brands` | array | — | Restrict results to the specified card brands or product tiers, e.g. `["VISA SIGNATURE", "WORLD ELITE"]`. Case-insensitive. Maximum 10 values. |
| `countries` | array | — | Restrict results to one or more ISO 3166-1 alpha-2 country codes. Applied in addition to the primary selector. Maximum 20 values. |
| `valid_only` | boolean | — | When `true`, only cards whose expiration date has not yet passed are returned. |
| `exposed_after` | string | — | Only return cards first exposed on or after this date. Format: `YYYY-MM-DD`. |
| `exposed_before` | string | — | Only return cards first exposed on or before this date. Format: `YYYY-MM-DD`. |

### Sorting

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sort_by` | string | `exposed_date` | The field to sort by. Accepted values: `exposed_date`, `expiry`. |
| `sort_dir` | string | `desc` | The sort direction. Accepted values: `asc`, `desc`. |

### Pagination

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | The page number to retrieve, using 1-based indexing. |

Each response returns a maximum of **20 records**. This limit is fixed and cannot be increased. The `has_more` field in the response indicates whether additional pages are available.

---

## Request Examples

### Query by BIN

```bash
curl -X POST https://api.whiteintel.io/card_check.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "bin": "424242"
  }'
```

### Query by Issuer with Filters

```bash
curl -X POST https://api.whiteintel.io/card_check.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "issuer": "Example Bank",
    "networks": ["VISA"],
    "types": ["credit"],
    "valid_only": true
  }'
```

### Query by Country with Date Range

```bash
curl -X POST https://api.whiteintel.io/card_check.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "country": "US",
    "exposed_after": "2026-01-01",
    "exposed_before": "2026-06-30",
    "sort_by": "expiry",
    "sort_dir": "asc"
  }'
```

### Paginate to Page 2

```bash
curl -X POST https://api.whiteintel.io/card_check.php \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "YOUR_API_KEY",
    "issuer": "Example Bank",
    "page": 2
  }'
```

---

## Response Schema

### Outer Structure

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` when the request completed successfully. |
| `remaining_daily_calls` | integer | The number of payment fraud API calls remaining for the current day. |
| `query` | object | An echo of the interpreted query, including the primary selector, applied filters, and sort configuration. |
| `page` | integer | The page number returned. |
| `page_size` | integer | The maximum number of records per page. Always `20`. |
| `count` | integer | The number of records returned in this response. |
| `has_more` | boolean | Indicates whether additional pages of results are available. |
| `results` | array | The array of matching card records. |

### Card Record Object

| Field | Type | Description |
|---|---|---|
| `bin6` | string | The 6-digit Bank Identification Number. |
| `bin8` | string \| null | The 8-digit extended Bank Identification Number, where available. |
| `last_four` | string | The last four digits of the card number. |
| `expiry_month` | integer \| null | The card expiration month, where available. |
| `expiry_year` | integer \| null | The card expiration year, where available. |
| `is_valid_expiry` | boolean | Indicates whether the card's expiration date is still in the future. |
| `card_network` | string \| null | The card network, such as VISA, MASTERCARD, or AMEX. |
| `issuer_bank` | string \| null | The name of the issuing institution. |
| `issuer_country` | string \| null | The ISO 3166-1 alpha-2 country code of the issuing institution. |
| `card_type` | string \| null | The card type, such as credit or debit. |
| `card_brand` | string \| null | The card brand or product tier, such as VISA SIGNATURE or WORLD ELITE. |
| `exposed_date` | string | The timestamp at which the card record was added to the platform. |

---

## Response Example

```json
{
  "success": true,
  "remaining_daily_calls": 487,
  "query": {
    "primary": { "type": "bin", "value": "424242" },
    "filters": {
      "networks": ["VISA"],
      "valid_only": true
    },
    "sort": { "by": "exposed_date", "dir": "desc" }
  },
  "page": 1,
  "page_size": 20,
  "count": 20,
  "has_more": true,
  "results": [
    {
      "bin6": "424242",
      "bin8": "42424200",
      "last_four": "1234",
      "expiry_month": 11,
      "expiry_year": 2027,
      "is_valid_expiry": true,
      "card_network": "VISA",
      "issuer_bank": "Example Bank N.A.",
      "issuer_country": "US",
      "card_type": "credit",
      "card_brand": "VISA SIGNATURE",
      "exposed_date": "2026-06-09 14:22:01"
    }
  ]
}
```

---

## Error Responses

Errors are returned as a JSON object with `success` set to `false` and a descriptive message.

| HTTP Status | Condition | Example Response |
|---|---|---|
| `400` | Invalid request method, content type, or malformed JSON. | `{"success": false, "message": "Invalid request."}` |
| `403` | Missing or invalid API key, or payment fraud module not enabled. | `{"success": false, "error": "The Payment Fraud module is an add-on and is currently not available for your account."}` |
| `200` | Missing primary selector. | `{"success": false, "message": "Provide exactly one primary selector: bin, issuer, or country."}` |
| `200` | Invalid BIN. | `{"success": false, "message": "bin must be exactly 6 or 8 digits."}` |
| `200` | Daily limit exceeded. | `{"success": false, "message": "Daily payment fraud API request limit exceeded."}` |

> Validation errors are returned with HTTP `200` and `success: false`. Clients should always inspect the `success` field in addition to the HTTP status code.

---

## Pagination Strategy

To retrieve a complete result set, begin with `page` set to 1 and continue incrementing the page number while the `has_more` field is `true`. Because each call consumes one unit of your daily quota, paginate only as deeply as required for your use case. The fixed page size of 20 records is a deliberate control to discourage bulk extraction.

---

## Best Practices

- **Selector precision:** Choose the most specific primary selector available. A BIN lookup is the most targeted; country queries may produce large result sets.
- **Filter layering:** Combine optional filters (`networks`, `types`, `brands`, `valid_only`) to narrow results before paginating.
- **Date scoping:** Use `exposed_after` and `exposed_before` for incremental ingestion or to limit historical depth.
- **Quota monitoring:** Track the `remaining_daily_calls` field after each successful response to anticipate quota exhaustion.

---

## Support

For technical questions, integration assistance, or to request a quota increase, contact `info@whiteintel.io`.
