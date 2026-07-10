import pytest
from pydantic import ValidationError

from whiteintel_mcp.models.endpoints import (
    ConsumerLeaksRequest,
    IPLeaksRequest,
    LastLeaksRequest,
    LeaksByIDRequest,
    OverallStatsRequest,
    SupplierRequest,
    ThreatFeedRequest,
    WatchlistManageRequest,
)


def test_empty_apikey_uses_environment(monkeypatch):
    monkeypatch.setenv("WHITEINTEL_API_KEY", "env-key")

    assert LastLeaksRequest(apikey="", query="example.com").apikey == "env-key"


def test_last_leaks_rejects_unknown_filters():
    with pytest.raises(ValidationError):
        LastLeaksRequest(apikey="key", query="example.com", data_type="unknown")

    with pytest.raises(ValidationError):
        LastLeaksRequest(apikey="key", query="example.com", breach_type="unknown")


def test_date_range_must_be_paired_and_ordered():
    with pytest.raises(ValidationError):
        ConsumerLeaksRequest(apikey="key", query="example.com", start_date="2026-01-01")

    with pytest.raises(ValidationError):
        ConsumerLeaksRequest(
            apikey="key",
            query="example.com",
            start_date="2026-01-02",
            end_date="2026-01-01",
        )


def test_threat_feed_uses_endpoint_specific_limits():
    with pytest.raises(ValidationError):
        ThreatFeedRequest(apikey="key", limit=101)

    with pytest.raises(ValidationError):
        ThreatFeedRequest(apikey="key", search="abc")

    with pytest.raises(ValidationError):
        ThreatFeedRequest(apikey="key", category=["one", "two", "three"])


def test_leaks_by_id_validates_single_and_batch_queries():
    assert LeaksByIDRequest(apikey="key", query=1).query == 1
    assert LeaksByIDRequest(apikey="key", query=[1, 2, 3]).query == [1, 2, 3]

    with pytest.raises(ValidationError):
        LeaksByIDRequest(apikey="key", query=0)

    with pytest.raises(ValidationError):
        LeaksByIDRequest(apikey="key", query=[1, 2, 3, 4, 5, 6])


def test_watchlist_action_required_fields():
    assert WatchlistManageRequest(apikey="key", action="list").action == "list"
    assert WatchlistManageRequest(
        apikey="key",
        action="add",
        entry_type="domain",
        entry="example.com",
    ).entry == "example.com"

    with pytest.raises(ValidationError):
        WatchlistManageRequest(apikey="key", action="add", entry_type="domain")

    with pytest.raises(ValidationError):
        WatchlistManageRequest(apikey="key", action="remove")


def test_metric_and_ip_validation():
    with pytest.raises(ValidationError):
        OverallStatsRequest(apikey="key", query="example.com", metric="unknown")

    with pytest.raises(ValidationError):
        IPLeaksRequest(apikey="key", query="not-an-ip")


def test_supplier_action_validation():
    assert SupplierRequest(apikey="key", action="list").limit == 50
    assert SupplierRequest(apikey="key", action="add", domain="example.com").domain == "example.com"
    assert SupplierRequest(apikey="key", action="remove", id=1).id == 1
    assert SupplierRequest(apikey="key", action="delete", domain="example.com").action == "delete"

    with pytest.raises(ValidationError):
        SupplierRequest(apikey="key", action="add")

    with pytest.raises(ValidationError):
        SupplierRequest(apikey="key", action="remove")

    with pytest.raises(ValidationError):
        SupplierRequest(apikey="key", action="list", limit=201)

    with pytest.raises(ValidationError):
        SupplierRequest(apikey="key", action="list", status="unknown")
