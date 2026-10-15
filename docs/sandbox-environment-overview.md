# Sandbox Environment Overview

> Source: https://docs.whiteintel.io/whiteintel-api-doc/api-sandbox/sandbox-environment-overview
> date: 2026-10-15

The WhiteIntel Sandbox provides a dedicated set of API endpoints that mirror the production API in request format, validation rules, and response structure, while returning synthetic sample data only. It is intended for trial customers and for integration development, allowing teams to validate API keys, build automations, and test client-side parsing without consuming production data or quota.

## Base URL

All sandbox endpoints are served under the `/sandbox/` path:

```
https://api.whiteintel.io/sandbox/<endpoint>.php
```

Every sandbox response includes the following HTTP header, which can be used by integrations to confirm that they are communicating with the sandbox rather than production:

```
X-WhiteIntel-Sandbox: 1
```

## Key Principles

The sandbox is designed to behave identically to production at the interface level while remaining fully isolated at the data level.

1. Request contracts are identical. Parameter names, accepted values, validation order, and error messages match the corresponding production endpoints.
2. Response structures are identical. Field names, nesting, and data types match production, so a client written against the sandbox will parse production responses without modification.
3. All returned records are synthetic. No production credential, breach, host, or threat intelligence data is ever returned.
4. Data is deterministic. For a given input, a sandbox endpoint returns the same synthetic records on every call. This allows pagination, filtering, and date windows to be tested reliably.
5. No production quota is consumed. Sandbox calls do not decrement the daily API call counter. The `remaining_daily_calls` value is reported for interface parity and reflects the current account value in read-only form.

## Authentication

Sandbox endpoints accept the same API keys as production. The key is supplied in the JSON request body as the `apikey` field and is validated against the account system. Subscription tier restrictions that apply in production are relaxed in the sandbox so that trial and lower tier keys may be used for integration testing.

```json
{
  "apikey": "YOUR_API_KEY",
  "query": "example.com"
}
```

## Request Format

All sandbox endpoints accept HTTP `POST` requests with a JSON request body and the following header:

```
Content-Type: application/json
```

Requests that do not use the `POST` method or do not declare a JSON content type receive an HTTP 400 response.

## Trial Key Behavior

Keys provisioned with a trial API version are subject to a maximum page size of 20 records. If a larger `limit` is requested, it is silently reduced to 20. This mirrors production behavior.

## Synthetic Data Notes

All synthetic records are generated using documentation safe values. Email addresses, hostnames, and organizations are fictional. IP addresses are drawn from the reserved documentation ranges defined in RFC 5737 (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`). No synthetic value is intended to correspond to a real individual, host, or organization.

## Available Sandbox Endpoints

|Endpoint|Description|
|---|---|
|`get_consumer_leaks.php`|Consumer credential exposure for a domain or subdomain|
|`get_corporate_leaks.php`|Corporate credential exposure for a domain, including database leaks|
|`get_last_leaks.php`|Recent exposure within a rolling day window, consumer and corporate|
|`get_leaks_by_computer_name.php`|Stealer exposure associated with a specific machine hostname|
|`get_leaks_by_ip.php`|Stealer exposure associated with a specific IP address|
|`get_leaks_by_username.php`|Exposure associated with a specific username or email address|
|`overall_stats.php`|Aggregated exposure statistics and timelines for a domain|
|`get_threat_feeds.php`|Threat feed posts, public news, and taxonomy listings|
|`get_third_party_db_leaks.php`|Database leak records grouped by the source database|
