import pytest
from ai_capital_mcp.server import (
    get_capital_events,
    search_companies,
    summarize_market_activity,
    trigger_ingestion,
    get_ingestion_status
)

def test_get_capital_events_validation():
    res = get_capital_events(limit="ten")
    assert res.success is False
    assert "limit must be an integer" in res.error
    assert res.data is None

def test_search_companies_validation():
    res = search_companies(company_name=123)
    assert res.success is False
    assert "company_name must be a string" in res.error

    res = search_companies(company_name="a")
    assert res.success is False
    assert "company_name must be at least 2 characters long" in res.error

def test_summarize_market_activity_validation():
    res = summarize_market_activity(days="seven")
    assert res.success is False
    assert "days must be an integer" in res.error

def test_trigger_ingestion_validation():
    res = trigger_ingestion(source="invalid_source")
    assert res.success is False
    assert "source must be techcrunch or hackernews" in res.error

def test_get_ingestion_status_validation():
    res = get_ingestion_status(job_id=123)
    assert res.success is False
    assert "job_id must be a string" in res.error
