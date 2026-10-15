# Open API Spec

> Source: https://docs.whiteintel.io/whiteintel-api-doc/overview/open-api-spec
> date: 2026-10-15

The official Open API specification (`whiteintel-openapi-spec.yaml`, OpenAPI 3.0.3, spec version 1.0.0) is published on the Whiteintel docs site and can be downloaded here:

```text
https://538104496-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FtCYnCt8eu1iosE17eQn0%2Fuploads%2FwhTRLthdRS08H15mPG2i%2Fwhiteintel-openapi-spec.yaml?alt=media&token=17260781-5cce-432d-b320-f494ca00185e
```

If the download link stops working, fetch the latest file from the official page above.

## Coverage Notes

The spec currently documents the eleven core retrieval and analytics endpoints:

- `get_consumer_leaks.php`, `get_corporate_leaks.php`
- `get_last_leaks.php`, `get_leaks_by_username.php`, `get_leaks_by_ip.php`, `get_leaks_by_computer_name.php`, `get_leaks_by_id.php`
- `get_third_party_db_leaks.php`, `get_overall_stats.php`, `get_lookalike_domains.php`, `get_threat_feeds.php`

The following endpoints are not yet included in the spec; use the per-endpoint pages in this directory as the authoritative reference for them:

- `watchlist_manage.php`, `supplier_api.php`, `get_audit_logs.php`, `card_check.php`
- All `/sandbox/` endpoints

Two spec-level gaps relative to the current per-endpoint documentation: the `sortBy` parameter on last leaks and the `database` source type on username leaks are not yet reflected in the spec.
